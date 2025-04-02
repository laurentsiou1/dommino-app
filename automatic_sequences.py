"""Classes des séquences de titrage
Elles gèrent toutes les actions propres aux séquences
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer
from datetime import datetime, timedelta
import threading

from windows.classic_sequence_window import ClassicSequenceWindow
from windows.custom_sequence_window import CustomSequenceWindow

from subsystems.pHmeter import *
from subsystems.dispenser import *
import subsystems.processing as proc

import file_manager as fm
from file_manager import Data

class AutomaticSequence:
    
    DISPLAY_DELAY_MS = 5000 #for letting the screen display once the measure in taken
    ALGO_TEST_PH = [4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10] #pour tester l'algo

    def __init__(self, ihm):
        self.ihm=ihm
        self.spectro=ihm.spectro_unit
        self.phmeter=ihm.phmeter
        self.dispenser=ihm.dispenser
        self.pump=ihm.peristaltic_pump
    
    def update_stab_time(self):
        self.phmeter.stab_time=self.window.stab_time.value()
    
    def update_stab_step(self):
        self.phmeter.stab_step=self.window.stab_step.value()
    
    #DIRECT
    def refresh_pH(self,ch,voltage): #arguments immuables
        self.phmeter.currentVoltage=voltage        
        pH = volt2pH(self.phmeter.a,self.phmeter.b,voltage)
        self.phmeter.currentPH=pH #actualisation de l'attribut de la classe pHmeter
        self.window.direct_pH.display(pH)

class CustomSequence(AutomaticSequence):    

    def __init__(self, ihm, config):
        
        # Create a QTimer object
        self.pause_timer = QTimer()    #for interface refreshing
        self.measure_timer = QTimer()   #chemical equilibrum and fluid circulation
        self.timer = QTimer()       #timer for reference recording sequence
        self.is_running=True    #flag indicating the running/pause state of sequence

        self.ihm=ihm
        self.spectro=ihm.spectro_unit
        self.phmeter=ihm.phmeter
        self.dispenser=ihm.dispenser
        self.pump=ihm.peristaltic_pump
        self.circuit=ihm.circuit
        self.syringe_B=ihm.dispenser.syringe_B  
        
        #Données de config      #comme titration sequence mais avec le fichier de config
        [self.experience_name,self.description,self.atmosphere,self.fibers,\
        self.flowcell,self.v_init_mL,self.dispense_mode,\
            self.sequence_config_file,self.saving_folder]=config
        self.param=config
        self.V_init=int(1000*self.v_init_mL) #volumes in microliters are integers
        #self.instrument_id = self.ihm.instrument_id
        
        t_start=datetime.now()
        self.start_date=str(t_start.strftime("%m/%d/%Y %H:%M:%S"))
        
        #Getting data from sequence instruction file
        self.syringes_to_use, self.instruction_table = fm.readSequenceInstructions(self.sequence_config_file)
        self.N_mes=len(self.instruction_table)
        self.remaining_time_seconds = sum([int(self.instruction_table[k][3])+int(self.instruction_table[k][4]) for k in range(self.N_mes)])
        self.pump_speeds_volt = [self.instruction_table[k][5] for k in range(self.N_mes)]
        self.reference_orders = [self.instruction_table[k][6] for k in range(self.N_mes)]
        #print("reference orders",self.reference_orders)
        self.reference_indexes = []
        for k in range(self.N_mes):
            if self.reference_orders[k]==1:
                self.reference_indexes.append(k+1)      #List of indexes where reference is taken
        self.N_ref = len(self.reference_indexes)    #Number of reference measures
        #total time
        #delays mixing + delays flow + 2minutes*number of references
        self.total_time_sec=sum(instruction[3]+instruction[4]+120*instruction[6] for instruction in self.instruction_table)
        #print("reference indexes",self.reference_indexes)

        self.update_infos() #données de séquence

        #Data to fill during sequence
        self.pH_mes = ['' for k in range(self.N_mes)]   #list of string, 
        self.initial_background = False #indicates if a reference has been recorded before launching sequence
        self.initial_reference = False
        self.backgrounds = []
        self.references = []
        self.reference_times = []
        if self.spectro.state=='open':
            self.lambdas=self.spectro.wavelengths
            self.N_lambda=len(self.lambdas)
            if self.spectro.dark_and_ref_stored():
                self.backgrounds = [self.spectro.active_background_spectrum]       # [ [bgd1], bgd2], ... , [bgdN] ]
                self.references = [self.spectro.active_ref_spectrum]       # [[ref1], [ref2], ... , [refN]]
                self.initial_background=True
                self.initial_reference=True
                self.reference_times = [self.spectro.active_ref_time]
        self.spec_abs = []
        self.intensity_spectra = []
        self.absorbance_spectra = []
        self.absorbance_spectra_cd = [] #corrected from dilution
        self.absorbance_spectrum1 = None #première mesure de spectre
        self.added_volumes = [[0,0,0] for i in range(self.N_mes)]   #table of volumes on 3 syringes 
        self.cumulate_volume = 0
        self.cumulate_volumes = []
        self.dilution_factor = 1
        self.dilution_factors = []
        self.measure_times=[]     #[time1 time2 ... time N_mes]
        self.equilibration_times=[]
        self.last_dispense_time = None
        self.stability_param=[] 

    def update_infos(self):
        #print(self.experience_name,self.description)
        self.infos=("\n\nExperience name : "+self.experience_name\
        +"\nDescription : "+self.description+"\nDate and time of start : "+self.start_date\
        +"\nAmbiant atmosphere : "+str(self.atmosphere)+"\nFibers : "+self.fibers+"\nFlowcell : "+self.flowcell\
        +"\nDispense mode : "+self.dispense_mode+"\nInitial volume : "+str(self.V_init)+"uL"\
        +"\nNumber of mesures : "+str(self.N_mes)+"\nSequence config file : "+self.sequence_config_file\
        +"\nTitration saving folder : "+self.saving_folder)

    def configure(self):
        
        #Création de la fenêtre graphique comme attribut de IHM
        self.ihm.openSequenceWindow('custom')
        self.window=self.ihm.sequenceWindow
        
        #Pousses seringue
        for k in range(3):
            if self.dispenser.state[k]=='closed':
                print("syringe pump "+identifier(k)+" not ready for use")
        self.dispenser.refill_empty_syringes()     

        #verification que tous les instruments nécessaires sont connectés. 
        #Doit on avoir tous les instruments connectés pour lancer séquence ?
        #On veut pouvoir aussi lancer pour tester, quelque soit les instrucments connectés. 
        #Mais il faut savoir si un instrument nécessaire à l'éxecution n'est pas connecté.
    
    def run_sequence(self):
        """Executed when user clicks on Ok in Configure sequence window"""
        self.ref_in_process=False
        self.measure_index=0
        self.timer.singleShot(self.DISPLAY_DELAY_MS,self.goToNextInstruction)

    def goToNextInstruction(self):
        if self.is_running:
            self.measure_index+=1
            self.execute_instruction(self.instruction_table[self.measure_index-1])
        else:
            pass
    
    def execute_instruction(self, line):
        print("executing instruction ", self.measure_index, ":", line)
        self.syringe_id=line[0]  #'A' or 'B'
        self.dispense_type=line[1]   #'DISP_ON_PH' or 'DISP_VOL_UL'
        self.value=line[2]   #50uL or pH4.5 ...
        self.delay_mixing=line[3]  #delay mixing : pump is stopped
        self.delay_flow=line[4]  #delay measure : pump is running
        self.pump_speed=line[5] #from 1 to 5. 0 means pump is stopped
        self.take_ref = line[6] #0 : no ref ; 1 : take a ref
        self.eq_time=self.delay_mixing+self.delay_flow  #delay between dispense and measure
        
        #1st step :
        self.pump.stop()    #Pump is stopped at the beginning
        self.spectro.close_shutter()    #shutter is closed as well
        
        #2nd step : dispense
        self.syr_num=identifier(self.syringe_id)
        self.syringe=self.dispenser.syringes[self.syr_num]
        self.dispense(self.dispense_type,self.value)
        
        """#3rd step : measure
        if self.flag_measure_after_ref: #if a refence has just been taken, 
            # and timing is under reference time : take measure directly
            self.measure_timer.singleShot(1000*40,self.measure)
        else:  #normal case : respect indicated timings
            self.measure_timer.singleShot(1000*(self.delay_mixing+self.delay_flow),self.measure)"""

        if self.measure_index==1:  #first instruction
            self.pause_timer.singleShot(1000*self.delay_mixing,self.run_measure_circuit)
        else:
            pass

    def run_measure_circuit(self):
        #à ajouter après la prise de réf
        if self.pump_speed in [1,2,3,4,5]:
            self.pump.set_speed_scale(self.pump_speed)
        self.circuit.run_measure_circuit()

    def dispense(self,dispense_type:str,value:float):
        #"""self.syr_num : index of syringe
        """dispense_type : 'DISP_ON_PH' or 'DISP_VOL_UL
        value : Either a volume (uL) or a pH value"""
        #print(datetime.now())
        if self.syringe.state=='open':
            if dispense_type=='DISP_ON_PH':
                target=value    #pH value
                #real pH
                current=self.phmeter.currentPH
                vol=int(dispense_data.get_volume_to_dispense_uL(current,target,self.atmosphere,C_NaOH=self.syringe_B.concentration,volume=self.v_init_mL))    #positive or null
                self.syringe.dispense(vol)
                print("Instruction number : ",self.measure_index)  
                print("current pH = ", current)
                print("target = ",target)          
                print("Dispensing vol = ",vol," uL")
                self.window.append_vol_in_table(self.measure_index,vol)
            elif dispense_type=='DISP_VOL_UL':
                vol=int(value)
                self.syringe.dispense(vol)    #volume value
                self.window.append_vol_in_table(self.measure_index,vol)
            self.added_volumes[self.measure_index-1][self.syr_num] = vol
            if vol!=0:  #if volume not null, recording dispense time 
                self.last_dispense_time = datetime.now()
                self.last_dispense_time.replace(microsecond=0)
            self.cumulate_volume += vol
        else:
            self.cumulate_volume += 0
        self.cumulate_volumes.append(self.cumulate_volume)
        self.dilution_factor=((self.cumulate_volume+self.V_init)/self.V_init)
        self.dilution_factors.append(self.dilution_factor)
        self.stage1()
    
    def stage1(self):
        #print("stage1")
        # reference in process but equilibration over 5 minutes
        # or no refenrence in porcess
        if (self.ref_in_process and self.eq_time>300) or self.ref_in_process==False:
            #Normal case
            #print("case1")
            self.pause_timer.singleShot(1000*self.delay_mixing,self.run_measure_circuit)
            self.measure_timer.singleShot(1000*self.eq_time,self.measure)
        elif self.ref_in_process:   # equilibration time < 300
            #waiting for the end of reference to be taken
            #print("case2")
            while self.ref_in_process:
                #print("in while")
                pass
            if self.pump_speed in [1,2,3,4,5]:
                self.circuit.run_measure_circuit()
                self.pump.set_speed_scale(self.pump_speed)
            self.measure_timer.singleShot(1000*40,self.measure)

    def measure(self):
        """Updates instruction parameters, opens shutter, records spectra and pH, then stops pump
        Goes to : take_ref_spectrum or end_of_instruction"""
        print("taking measure\n")
        N=self.measure_index
        
        ## Opening shutter before recording spectrum
        if self.spectro.dark_and_ref_stored():
            self.spectro.open_shutter()
            time.sleep(1)
        
        #recording time
        meas_time=datetime.now()
        meas_time=meas_time.replace(microsecond=0)
        self.measure_times.append(meas_time)
        if self.last_dispense_time!=None:
            eq_time=meas_time-self.last_dispense_time
        else:
            eq_time=meas_time-meas_time #time zero
        self.equilibration_times.append(eq_time) 
        self.window.append_time_in_table(N,eq_time)  #time
        #print(meas_time, self.last_dispense_time)

        #Measuring pH
        if self.phmeter.state=='open':
            pH=self.phmeter.currentPH
            self.pH_mes[N-1]=str(pH)  #ajout dans les tableaux
            self.stability_param.append((self.phmeter.stab_step, self.phmeter.stab_time))
            self.window.append_pH_in_table(N,str(pH))    #affichage
        else:
            self.pH_mes[N-1]='/'

        #Measuring absorbance
        if self.spectro.dark_and_ref_stored():
            spec=self.spectro.get_averaged_spectrum()
            self.spec_abs, proc_delay =proc.intensity2absorbance(spec,self.spectro.active_ref_spectrum,self.spectro.active_background_spectrum)
            if self.absorbance_spectrum1==None:
                self.absorbance_spectrum1=self.spec_abs  #First spectrum of sequence
            self.intensity_spectra.append(spec)
            self.absorbance_spectra.append(self.spec_abs)
            self.absorbance_spectra_cd.append(proc.correct_spectrum_from_dilution(self.spec_abs,self.dilution_factor))
            delta=[self.spec_abs[k]-self.absorbance_spectrum1[k] for k in range(self.N_lambda)]
            self.window.append_spectra(N,self.spec_abs,delta,spec)    #adding spectrum
            self.spectro.close_shutter()    #Closing shutter to protect fibers from overheating

        #Stop the pump after taking measure
        if self.pump.state=='open':
            self.pump.stop()

        #decides if taking reference or not
        self.stage2()
    
    def stage2(self):
        """Decides whether to take a reference or not"""
        #After measure : Take reference if needed
        if self.take_ref==1 and self.spectro.state=='open' and self.circuit.state=='open':
            self.take_reference_spectra()
        else:
            self.end_of_instruction()

            # next_instruction=self.instruction_table[self.measure_index] #instruction meas index + 1 
            # next_delay_mixing=next_instruction[3]
            # next_delay_flow=next_instruction[4]
            #if the next delay_mixing is under 3 minutes, there is not enough time to take the reference                
            #if next_delay_mixing+next_delay_flow>=300:  # 5 minutes
            #    self.take_reference_spectra()   #takes a ref and then restarts the pump
            #else:
            #    self.pause_timer.singleShot(1000*self.delay_mixing,self.run_measure_circuit)            
            # self.take_reference_spectra()
            # if next_delay_flow+next_delay_mixing<300:   # 5 minutes
            #     self.flag_measure_after_ref=True
            #     self.pause_timer.singleShot(1000*300,self.run_measure_circuit)
            #     self.measure_timer.singleShot(1000*340,self.end_of_instruction)  #problem
    
    def take_reference_spectra(self):
        """Empties measure circuit"""
        self.ref_in_process=True
        self.circuit.empty_measure_circuit()
        self.timer.singleShot(1000*15,self.take_reference_spectra_2)
    
    def take_reference_spectra_2(self):
        """Cleans WATER - BIN circuit"""
        self.circuit.run_water()  #speed 5 for cleaning
        delay = 30  #delay to clean
        self.timer.singleShot(1000*delay,self.take_reference_spectra_3)
    
    def take_reference_spectra_3(self):
        """Empties water - bin circuit"""
        self.pump.change_direction()    #respills in WATER beaker
        self.timer.singleShot(1000*22,self.take_reference_spectra_4)  #empty circuit properly

    def take_reference_spectra_4(self):
        """Flush water from water to bin with measure speed. 
        Pump speed is set according to sequence file value. 
        Speed 1 or 2 is better to ensure no bubbles get stuck. 
        Flow duration is 40 seconds to ensure flowcell is filled even at lowest speed"""
        self.circuit.run_water(speed=self.pump_speed)   #speed must be 1 or 2 to ensure no bubble.
        delay = 40
        self.timer.singleShot(1000*delay,self.take_reference_spectra_5)

    def take_reference_spectra_5(self):
        """Records background"""
        self.spectro.acquire_background_spectrum()
        delay=2*int(self.spectro.Irec_time)+5 #2times the measure time
        self.timer.singleShot(1000*delay,self.take_reference_spectra_6)

    def take_reference_spectra_6(self):
        """Records reference and computes last measure absorabnce spectra with new reference"""
        if self.spectro.state=='open':
            self.spectro.acquire_ref_spectrum()
            ref_time = datetime.now().replace(microsecond=0)
            #Append time and spectra in lists
            self.reference_times.append(ref_time)
            self.backgrounds.append(self.spectro.active_background_spectrum)
            self.references.append(self.spectro.active_ref_spectrum)
            #print("self.absorbance_spectra",self.absorbance_spectra)
            print("measure index ",self.measure_index)
            N_spec=len(self.absorbance_spectra)
            #print("N_spec",N_spec)
            if N_spec>0:    #Correction of last absorbance spectra with new reference
                self.absorbance_spectra[N_spec-1]=self.spec_abs
                self.absorbance_spectra_cd[N_spec-1]=proc.correct_spectrum_from_dilution(self.spec_abs,self.dilution_factor)
            #time delay
            delay=2*int(self.spectro.Irec_time)+5 #2times the measure time
        else:
            delay=1
        self.timer.singleShot(1000*delay,self.take_reference_spectra_7)
    
    def take_reference_spectra_7(self):
        """Respill clean water in water beaker"""
        #Stop the pump
        self.pump.stop()
        #Release water towards water beaker
        self.circuit.empty_water()
        #Connexion with next action 
        self.timer.singleShot(1000*12,self.take_reference_spectra_8)
    
    def take_reference_spectra_8(self):
        #Stop the pump : end of automatic reference sequence
        self.pump.stop()
        self.ref_in_process=False
        self.end_of_instruction()    #resume the instructions 

    def end_of_instruction(self):
        """Saves current sequence state and goes to following measure
        Restarts the pump"""
        self.ihm.seq_data.save_current_sequence_state()
        if self.measure_index==self.N_mes: #Last measure            
            self.circuit.clean_and_empty()
        else:   #next measure
            self.timer.singleShot(self.DISPLAY_DELAY_MS,self.goToNextInstruction)
        
        #Restarts the pump after reference
        # if self.pump_speed in [1,2,3,4,5]:
        #     self.pump.set_speed_scale(self.pump_speed)
        # self.circuit.run_measure_circuit()

    def pause_resume(self):
        """Button for pause/resume during sequence"""
        if self.is_running:
            self.window.pause()
            self.pause()
        else:
            self.resume()
            self.window.resume()

    def pause(self):
        """Puts sequence on pause"""
        self.is_running=False
        self.timer.stop()
        self.pause_timer.stop()
        self.measure_timer.stop()
        print("sequence on pause. current instruction finishing")

    def resume(self):
        """Resume sequence after a pause"""
        self.is_running=True
        self.timer.singleShot(self.DISPLAY_DELAY_MS,self.goToNextInstruction)
        self.timer.start()
        self.pause_timer.start()
        self.measure_timer.start()
        print("running again")

    def stop(self):
        """Stop all instruments"""
        self.is_running=False
        self.measure_timer.stop()
        self.pause_timer.stop()
        self.timer.stop()
        self.spectro.close_shutter()
        self.pump.stop()
        self.dispenser.stop()
        del self

"""class Data(AutomaticSequence):

    #à définir en reprenant le fichier file_manager"""