"""file IHM.py
IHM is the principal class of dommino application.
It contains all subsytems (instruments) as attribute along with all windows of interface"""

from PyQt5 import QtCore

from configparser import ConfigParser
import os
from pathlib import Path
from datetime import datetime

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.Manager import *

from lib.oceandirect.OceanDirectAPI import Spectrometer as Sp, OceanDirectAPI
from lib.oceandirect.od_logger import od_logger

#Instruments
from subsystems.pHmeter import PHMeter
from subsystems.absorbanceMeasure import AbsorbanceMeasure
from subsystems.dispenser import Dispenser, PhidgetStepperPump
from subsystems.peristalticPump import PeristalticPump
from subsystems.circuit import Circuit

#Windows
from windows.control_panel import ControlPanel
from windows.sequence_config_window import SequenceConfigWindow
from windows.phmeter_calib_window import PhMeterCalibWindow
from windows.custom_sequence_window import CustomSequenceWindow
from windows.classic_sequence_window import ClassicSequenceWindow
from windows.spectrometry_window import SpectrometryWindow
from windows.dispenser_window import DispenserWindow
from windows.settings_window import SettingsWindow

path = Path(__file__)
ROOT_DIR = path.parent.absolute()

class IHM:

    #param files
    app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
    device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")
    #calibration_file = os.path.join(ROOT_DIR, "config/latest_cal.ini")

    parser = ConfigParser()
    parser.read(device_ids)
    id01 = int(parser.get('main board id', 'dommino01'))
    id02 = int(parser.get('main board id', 'dommino02'))
    #print("app_default_settings ihm : ", app_default_settings, "\ndevice_ids : ", device_ids)
    
    #Sub systems
    #An instance of each subsytem (correpsonding to instruments) is created here
    #Each instrument is set to state='closed' at the begining.
    spectro_unit=AbsorbanceMeasure()
    phmeter=PHMeter()
    dispenser=Dispenser()
    peristaltic_pump=PeristalticPump()
    circuit=Circuit(peristaltic_pump)

    manager=Manager()   #for connection/disconnection handling

    instrument_id=''    #SN unknown at opening

    def __init__(self):
        
        #Config for savings
        parser = ConfigParser()
        parser.read(self.app_default_settings)
        self.saving_folder=parser.get('saving parameters', 'folder')       
  
        #Configs for Automatic sequence
        self.experience_name=None
        self.description=None
        self.fibers=parser.get('setup', 'fibers')
        self.flowcell=parser.get('setup', 'flowcell')
        self.N_mes=None #number of pH/spectra measures
        self.dispense_mode=parser.get('sequence', 'dispense_mode')

        #classic
        self.fixed_delay_sec=int(parser.get('classic titration sequence', 'fixed_delay_sec'))
        self.mixing_delay_sec=int(parser.get('classic titration sequence', 'mixing_delay_sec'))
        self.initial_pH=None
        self.final_pH=None
        self.added_total_uL = 0
        self.added_A_uL = 0
        self.added_B_uL = 0
        self.added_C_uL = 0

        #custom
        self.sequence_config_file=parser.get('custom sequence', 'sequence_file') 

        #display timer. Used for refreshing screen
        self.timer_display = QtCore.QTimer()
        self.timer_display.setInterval(1000)    #timeout every 1s
        self.timer_display.start()

        #Handling of connections/disonnections
        self.manager.setOnAttachHandler(self.AttachHandler)
        self.manager.setOnDetachHandler(self.DetachHandler)
        self.manager.open()
        self.board_number=0
        self.VINT_number=0
        self.instrument_id=str(0)

        #Variable for alerts on switchs
        self.switch_alerts = {}
        
        #Definition of switches 
        self.switch_names = {
        self.dispenser.syringe_A.ch_full: "Full A",
        self.dispenser.syringe_A.ch_empty: "Empty A", 
        self.dispenser.syringe_B.ch_full: "Full B", 
        self.dispenser.syringe_B.ch_empty: "Empty B", 
        self.dispenser.syringe_C.ch_full: "Full C",
        self.dispenser.syringe_C.ch_empty: "Empty C" 
        } 

    def AttachHandler(self, man, channel):
        """
        Executes when putting under tension Phidgets boards
        It prints which board is connected
        three arguments can't be modified"""
        serialNumber = channel.getDeviceSerialNumber()
        deviceName = channel.getDeviceName()
        channelName = channel.getChannelName()
        ch_num=channel.getChannel()
        hubPort=channel.getHubPort()
        isChannel=channel.getIsChannel()
        #print("Connected : ",serialNumber,deviceName,"port : ",hubPort,isChannel,channelName,"channel : ",ch_num)

        #executes only once
        if deviceName=='6-Port USB VINT Hub Phidget':
            self.loadBoardsSerialNumbers('VINT',serialNumber)
        elif deviceName=='PhidgetInterfaceKit 8/8/8' and channelName=='Digital Output' and ch_num==7:
            self.loadBoardsSerialNumbers('interface board',serialNumber)

    def loadBoardsSerialNumbers(self, board, nb):
        """
        Writes VINT and interface board serial numbers in file device_id.ini 
        """
        parser = ConfigParser()
        parser.read(self.device_ids)
        if board=='VINT':
            self.VINT_number = nb   #S/N as attribute of IHM
            print("VINT S/N = ", nb)
            parser.set('VINT', 'id', str(nb))   #S/N written in file device_id
            file = open(self.device_ids,'w')
            parser.write(file)
            file.close()
        elif board=='interface board':
            self.board_number = nb
            print('Interfacing board S/N = ', nb)
            parser.set('main board', 'id', str(nb))
            file = open(self.device_ids,'w')
            parser.write(file)
            file.close()
            self.getInstrumentSerialNumber()

    def getInstrumentSerialNumber(self):
        """
        Gets the id of DOMMINO box (01 or 02) according to the SN of main board
        """
        parser = ConfigParser()
        parser.read(self.device_ids)
        if self.board_number == self.id01:
            self.instrument_id='DOMMINO01'
        elif self.board_number == self.id02:
            self.instrument_id='DOMMINO02'
        else:
            self.instrument_id='unknown'
        print("instrument S/N =", self.instrument_id)
        try:
            self.controlPanel.label_instrument_SN.setText("instrument S/N : "+self.instrument_id)
        except:
            #no attribute control Panel yet
            pass

    def DetachHandler(self, man, channel):
        """
        Executes when a Phidget channel is out of voltage.
        Three arguments can't be modified.
        """
        serialNumber = channel.getDeviceSerialNumber()
        deviceName = channel.getDeviceName()
        channelName = channel.getChannelName()
        ch_num=channel.getChannel()
        hubPort=channel.getHubPort()
        isChannel=channel.getIsChannel()
        #print("Disconnected : ",serialNumber,"--",deviceName,"--","port : ",hubPort,isChannel,"--",channelName,"--","channel : ",ch_num)

        #pH meter
        if deviceName=='PhidgetInterfaceKit 8/8/8' and channelName=='Voltage Input' and ch_num==self.phmeter.ch_phmeter:
            self.phmeter.state='closed'
            print("pH meter disconnected")
            self.controlPanel.led_phmeter.setPixmap(self.controlPanel.pixmap_red)
        #Lamp control

        #--Dispenser
        #Switch
        if deviceName == 'PhidgetInterfaceKit 8/8/8' and channelName == 'Digital Input':     # modif LS
            if ch_num in self.switch_names:  # Vérifie si le channel correspond à un switch connu
                print(f"Détection d'un problème sur {self.switch_names[ch_num]} (Channel {ch_num})")  # Test 
                self.dispenser.state = 'closed'
                self.controlPanel.led_disp.setPixmap(self.controlPanel.pixmap_red)

            # Affiche un message une seule fois par switch
                if ch_num not in self.switch_alerts:
                    switch_name = self.switch_names[ch_num]  # Récupère le nom du switch
                    print("Syringe pump disconnected due to", f"switch {switch_name} ({ch_num})")
                    self.switch_alerts[ch_num] = True  # Marquer ce switch comme déjà signalé     

        #Moteurs    
        if deviceName=='4A Stepper Phidget' and hubPort==self.dispenser.syringe_A.port_a: # modif LS - "==0" "self.phidgetstepperpump.port_a"
            #stepper A de pousse seringue débranché
            self.dispenser.syringe_A.state='closed'
            print("Stepper A disconnected")
        if deviceName=='4A Stepper Phidget' and hubPort==self.dispenser.syringe_B.port_b: # modif LS - "==1" "self.phidgetstepperpump.port_b"
            #stepper B de pousse seringue débranché
            self.dispenser.syringe_B.state='closed'
            print("Stepper B disconnected")
        if deviceName=='4A Stepper Phidget' and hubPort==self.dispenser.syringe_C.port_c: # modif LS - "==2" "self.phidgetstepperpump.port_c"
            #stepper C de pousse seringue débranché
            self.dispenser.syringe_C.state='closed'
            print("Stepper C disconnected")
        
        self.dispenser.refresh_state()
        
        if self.dispenser.state=='closed':
            self.controlPanel.led_disp.setPixmap(self.controlPanel.pixmap_red)
        
        if deviceName=='4A DC Motor Phidget' and hubPort==self.peristaltic_pump.port_motor:  # modif LS - "==3" par "self.peristaltic_pump.port_motor" 
            self.peristaltic_pump.state='closed'
            print("Peristaltic pump disconnected")
            self.controlPanel.led_pump.setPixmap(self.controlPanel.pixmap_red)
        
        #Lamp control unaccessible
        if deviceName=='PhidgetInterfaceKit 8/8/8' and channelName=='Digital Output' and ch_num==self.spectro_unit.ch_shutter: # modif LS
            self.spectro_unit.state='closed'
            print("Unable to control lamp")
            self.controlPanel.led_spectro.setPixmap(self.controlPanel.pixmap_red)

    def close_all_devices(self):
        """
        Closes all intruments, their state is set to false and lights turn red. 
        """
        print("Closing all device")
        self.updateDefaultParam()
        if self.spectro_unit.state=='open':
            self.spectro_unit.close(self.spectro_unit.id)
        if self.phmeter.state=='open':
            self.phmeter.close()
        if self.dispenser.state=='open':
            self.dispenser.close()
        if self.circuit.state=='open':
            self.circuit.close()
        elif self.peristaltic_pump.state=='open':
            self.peristaltic_pump.close()

              
    def updateDefaultParam(self):
        """
        Updates current parameters as default in file 'config/app_default_settings'
        """
        parser = ConfigParser()
        parser.read(self.app_default_settings)
        parser.set('saving parameters','folder',str(self.saving_folder))
        parser.set('custom sequence', 'sequence_file', self.sequence_config_file)
        if self.peristaltic_pump.state=='open':
            parser.set('pump', 'speed_volts', str(self.peristaltic_pump.mean_voltage))
        if self.phmeter.state=='open':
            parser.set('phmeter', 'epsilon', str(self.phmeter.stab_step))
            parser.set('phmeter', 'delta', str(self.phmeter.stab_time))
            #parser.set('calibration', 'file', str(self.phmeter.relative_calib_path))
            parser.set('phmeter', 'default', str(self.phmeter.model))
            parser.set('electrode', 'default', str(self.phmeter.electrode))
        if self.dispenser.state=='open':
            parser.set(self.dispenser.syringe_A.id, 'level', str(self.dispenser.syringe_A.level_uL))
            parser.set(self.dispenser.syringe_B.id, 'level', str(self.dispenser.syringe_B.level_uL))
            parser.set(self.dispenser.syringe_C.id, 'level', str(self.dispenser.syringe_C.level_uL))
        file = open(self.app_default_settings,'w')
        parser.write(file) 
        file.close()
        print("updates current parameters in default file")

    def createDirectMeasureFile(self):
        """
        Creates a file containing instant data on system : pH, spectrum, dispenser data
        Saves it to the saving folder (application settings)
        """
        dt = datetime.now()
        date_text=dt.strftime("%m/%d/%Y %H:%M:%S")
        date_time=dt.strftime("%m-%d-%Y_%Hh%Mmin%Ss")
        name = "mes_"
        header = ("Instant measure on Dommino titrator\n"+"date and time : "+str(date_text)\
            +"\n"+"Device : "+self.instrument_id+"\nMain board S/N : "+str(self.board_number)\
            +"\nVINT S/N : "+str(self.VINT_number)+"\n\n")
        data = ""
        print("saving instant measure - ")
        #saving pH measure
        if self.phmeter.state=='open':
            name+="pH-"
            header+=("current calibration data\n"+"date and time: "+self.phmeter.CALdate+"\nnumber of points: "+str(self.phmeter.CALtype)+"\n"+
            "recorded voltages : U4 = "+str(self.phmeter.U1)+"V; U7="+str(self.phmeter.U2)+"V; U10="+str(self.phmeter.U3)+"V\n"+
            "calibration coefficients : a="+str(self.phmeter.a)+ "; b="+str(self.phmeter.b)+"\n\n"
            )
            pH = self.phmeter.currentPH
            V = self.phmeter.currentVoltage
            data+="pH = "+str(pH)+"; U = "+str(V)+"V\n\n"
        else:
            header+="pH meter not connected\n\n"

        #saving dispensed volumes
        if self.dispenser.state=='open':
            name+="titr-"
            header+=("Syringe Pump : \n"+str("500uL Trajan gas tight syringe\n")
            +str(self.dispenser.infos)+"\n")
            data+=("added syringe A : "+str(self.dispenser.syringe_A.added_vol_uL)+"uL\n"
            +"added syringe B : "+str(self.dispenser.syringe_B.added_vol_uL)+"uL\n"
            +"added syringe C : "+str(self.dispenser.syringe_C.added_vol_uL)+"uL\n"
            +"total added : "+str(self.dispenser.vol.added_total_uL)+"uL\n\n")
        else:
            header+="Syringe pump not connected\n"

        if self.spectro_unit.state=='open':
            name+="Abs_"
            header+=("\nSpectrometer : "+str(self.spectro_unit.model)
            +"\nSerial number : "+str(self.spectro_unit.serial_number)
            +"\nIntegration time (ms) : "+str(self.spectro_unit.t_int/1000)
            +"\nAveraging : "+str(self.spectro_unit.averaging)
            +"\nBoxcar : "+str(self.spectro_unit.boxcar)
            +"\nNonlinearity correction usage : "+str(self.spectro_unit.device.get_nonlinearity_correction_usage())
            +"\nElectric dark correction usage : "+str(self.spectro_unit.electric_dark)
            +"\nAbsorbance formula : A = log10[(reference-background)/(sample-background)]\n")

            background = self.spectro_unit.active_background_spectrum
            ref = self.spectro_unit.active_ref_spectrum
            sample = self.spectro_unit.current_intensity_spectrum
            absorbance = self.spectro_unit.current_absorbance_spectrum
            wl = self.spectro_unit.wavelengths
            spectra=[wl,background,ref,sample,absorbance]
            Nc=len(spectra)-1
            if background==None or ref==None: #pas de calcul d'absorbance possible
                data+="lambda(nm)\tsample (unit count)\n"
                for l in range(self.spectro_unit.N_lambda):
                    data+=str(spectra[0][l])+'\t'
                    data+=str(spectra[3][l])+'\n'
            else:
                data+="lambda(nm)\tbackground (unit count)\treference ('')\tsample ('')\tabsorbance (abs unit)\n"
                for l in range(self.spectro_unit.N_lambda):
                    for c in range(Nc):
                        data+=str(spectra[c][l])+'\t'
                    data+=str(spectra[Nc][l])+'\n'
        else:
            header+="Spectrometer closed\n"

        name+=str(date_time)
        output=header+"\n\n"+data
        
        f_out = open(self.saving_folder+'/'+name+'.txt','w') #création d'un fichier dans le répertoire
        f_out.write(output)
        f_out.close()    

                                            
                                            ### Window handling ###

    def openControlPanel(self):
        """
        Creates controlPanel as attribute of IHM and displays it.
        """
        self.controlPanel=ControlPanel(self)
        self.controlPanel.show()

    def openConfigWindow(self):
        """
        Creates seqConfig as attribute of IHM and displays it.
        """
        self.seqConfig = SequenceConfigWindow(self)
        self.seqConfig.show()
        for button in self.seqConfig.dialogbox.buttons():   #Disconnexion of Keyboard Enter event
            button.setAutoDefault(False)  # Prevent auto-triggering on Enter
            button.setDefault(False)  # Remove default button behavior

    def openSpectroWindow(self):
        """
        Creates spectroWindow as attribute of IHM and displays it.
        """
        self.spectroWindow = SpectrometryWindow(self)
        self.spectroWindow.show()

    def openDispenserWindow(self):
        """
        Creates syringePanel as attribute of IHM and displays it.
        """
        self.syringePanel = DispenserWindow(self)
        self.syringePanel.show()

    def openCalibWindow(self):
        """
        Creates calib_window as attribute of IHM and displays it.
        """
        self.calib_window = PhMeterCalibWindow(self)
        self.calib_window.show()

    def openSettingsWindow(self):
        """
        Creates settings_win as attribute of IHM and displays it.
        """
        self.settings_win = SettingsWindow(self)
        self.settings_win.show()
        #Disconnexion of Keyboard Enter event
        for button in self.settings_win.buttonBox.buttons():   
            button.setAutoDefault(False)  
            button.setDefault(False)  

    def openSequenceWindow(self,type):
        """
        Creates sequencewindow as attribute of IHM and displays it.
        """
        if type=="classic":
            self.sequenceWindow = ClassicSequenceWindow(self)
            self.sequenceWindow.show()
        elif type=="custom":
            self.sequenceWindow = CustomSequenceWindow(self)
            self.sequenceWindow.show()

#This is executed only if you launch file IHM.py with Python interpreter
if __name__=="main":
    interface = IHM()
    print(interface.saving_folder)