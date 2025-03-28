"Module qui gère la création des fichiers de données issues des expériences"

import os
from datetime import datetime

#from automatic_sequences import AutomaticSequence, CustomSequence, CLassicSequence, 

def readSequenceInstructions(file):  #file: sequence config file #chaine de caracteres
    import csv
    with open(str(file), newline='') as f:
        reader = csv.reader(f, delimiter=';')
        tab = []
        syringes_to_use=[0,0,0] #set of syringes to be used
        idx=0
        for line in reader:
            #print(idx)
            if idx==0:
                idx+=1
                continue    #On ne s'occupe pas de l'entête du fichier
            syringe_id=line[0]  #'A' or 'B'
            dispense_type=line[1]   #'DISP_ON_PH' or 'DISP_VOL_UL'
            value=float(line[2])   #50uL or pH4.5 ...
            mixing_time=int(line[3])  #around 30sec pump is stopped
            flow_time=int(line[4])   #eg 300sec time with pump running
            pump_speed=int(line[5])  #1, 2, ... , 5
            refresh_ref=bool(int(line[6]))
            #print(refresh_ref)
            if syringe_id=='A':
                syringes_to_use[0]=1
            elif syringe_id=='B':
                syringes_to_use[1]=1
            elif syringe_id=='C':
                syringes_to_use[2]=1
            line=[syringe_id,dispense_type,value,mixing_time,flow_time,pump_speed,refresh_ref]
            tab.append(line)
            idx+=1

    instruction_table=tab
    print("instruction table : ",instruction_table)
    return syringes_to_use, instruction_table  

class Data():
    """contains all data of a sequence and deals with the writing in files"""

    def __init__(self, seq):
        self.seq=seq
        self.saving_folder = seq.saving_folder
        self.count = 0

        self.data_abs=''
        self.data_intens=''
        self.formatted_data=''
        self.metadata=''

    def update_names(self,date):
        #filenames with start date (temporary until last measure)
        self.name_data_intens = "seq_"+self.seq.experience_name+"_data_intensity_"+date
        self.name_data_abs = "seq_"+self.seq.experience_name+"_data_absorbance_"+date
        self.name_formatted_data = "seq_"+self.seq.experience_name+"_formatted_data_"+date
        self.name_metadata = "seq_"+self.seq.experience_name+"_metadata_"+date
        #path (temporary until last measure)
        self.data_intens_path = self.saving_folder+'/'+self.name_data_intens+'.txt'
        self.data_abs_path = self.saving_folder+'/'+self.name_data_abs+'.txt'
        self.formatted_data_path = self.saving_folder+'/'+self.name_formatted_data+'.txt'
        self.metadata_path = self.saving_folder+'/'+self.name_metadata+'.txt'
    
    def save_current_sequence_state(self):
        """At each measure this overwrites the 4 data files. 
        It allows to keep a backup of sequence data in case of disconnexion"""
        self.count+=1
        if self.count==1:
            dt=datetime.now()
            self.date_start=str(dt.strftime("%Y-%m-%d_%Hh%M"))
            self.update_names(self.date_start)  #names with start time
            self.createSequenceFiles(self.seq) #create 4 files
        else: #already a set of four files with the name of date_start
            self.createSequenceFiles(self.seq) #overwrites 4 files
        if self.count==self.seq.N_mes:
            self.update_name_full_sequence_data_files()

    def update_name_full_sequence_data_files(self):
        """Puts the end of experiment date in the file names"""
        dt=datetime.now()
        self.date_end=str(dt.strftime("%Y-%m-%d_%Hh%M"))

        old_data_intens_path = self.data_intens_path
        old_data_abs_path = self.data_abs_path
        old_formatted_data_path = self.formatted_data_path
        old_metadata_path = self.metadata_path
        
        self.update_names(self.date_end)
        
        os.rename(old_data_intens_path,self.data_intens_path)
        os.rename(old_data_abs_path,self.data_abs_path)
        os.rename(old_formatted_data_path,self.formatted_data_path)
        os.rename(old_metadata_path,self.metadata_path)

        self.count=0 #if another experiment is led this allows\
        #to create new files

    def createSequenceFiles(self, seq):
        """This function is executed after each sequence instruction.
        If sequence is interrupted, files are kept saved in the state
        Creation of 4 files :
        - data_absorbance_--.txt and data_intensity_--.txt containing all measured data during sequence,
            with no correction on absorbance and intensity
        - formatted_data_--.txt containing :
            - pH 
            - wavelengths 
            - Absorbance corrected from dilution
            The file is compatible for data processing
        - metadata_--.txt containing :
            - Sequence informations
            - sequence configuration file content 
            - general parameters on instruments
            - The set of background and reference measures on spectrometer"""


                                ### METADATA

        #Sequence general and chemical informations
        metadata = ("Instrument : "+seq.ihm.instrument_id+"\nMain board S/N : "\
        +str(seq.ihm.board_number)+"\nVINT S/N : "+str(seq.ihm.VINT_number)+seq.infos\
        +"\n\nInstruction table :\nSyringe\tDipense type\tValue\tdelay mixing\tdelay flow\tspeed\treference\n")
        
        #Sequence configuration file printed here
        tab = seq.instruction_table
        Nl = len(tab)
        for l in range(Nl):
            for c in range(7):
                metadata += (str(tab[l][c]))+"\t"
            metadata+="\n"
        #Instrument informations
        metadata += "\n"+seq.spectro.infos+"\n\n"+seq.phmeter.infos\
        +"\n\n"+seq.pump.infos+"\n\n"+seq.dispenser.infos+"\n\n"
        
        #background and reference spectra
        if seq.spectro.state=='open':   
            #N° measure where reference is taken
            metadata += "reference taken after measure N°\t"
            if seq.initial_reference==True and seq.initial_background==True:
                metadata += "Initial\t\t"
            for c in range(seq.N_ref):
                metadata += str(seq.reference_indexes[c])+"\t\t"
            
            N_refs=len(seq.references)  #real number of references taken
            #print("n refs ", N_refs)
            #Times of reference measures
            metadata += "\ntimes (h:min:sec)\t"
            for c in range(N_refs):
                #print(c)
                metadata += str(seq.reference_times[c])+"\t\t"
            #Labels bgd or ref
            metadata += "\nWavelengths(nm)\t"
            for c in range(N_refs):
                metadata += "background\treference\t"
            #spectra (units counts)     #lambda bgd ref bgd ref bgd ref ...
            for lambda_k in range(seq.N_lambda):
                metadata += "\n"+str(seq.lambdas[lambda_k])
                for ref_k in range(N_refs):
                    metadata += "\t"+str(seq.backgrounds[ref_k][lambda_k])+"\t"+str(seq.references[ref_k][lambda_k])
        
        stream=open(self.metadata_path,'w')
        stream.write(metadata)
        stream.close()
                                
                                ### DATA AND FORMATTED DATA
        
        print("saving titration sequence data")
        data="measure n°\t"    #entête
        for k in range(seq.N_mes):
            data+=str(k+1)+'\t'

        #DISPENSER
        print(seq.dispense_mode)
        if seq.dispense_mode=='from file':
            data+="\nsyringe A (uL)\t"
            for k in range(seq.N_mes):
                data+=str(seq.added_volumes[k][0])+'\t'
            data+="\nsyringe B (uL)\t"
            for k in range(seq.N_mes):
                data+=str(seq.added_volumes[k][1])+'\t'
            data+="\nsyringe C (uL)\t"
            for k in range(seq.N_mes):
                data+=str(seq.added_volumes[k][2])+'\t'
            #Initial volume
            data+="\nInitial volume (uL)\t"+str(seq.V_init)    #volume in uL
            data+="\ncumulate (uL)\t"
            for k in range(len(seq.cumulate_volumes)):  #the list is filled during sequence
                data+=str(seq.cumulate_volumes[k])+'\t'
            data+="\nDilution\t"    #filled during sequence
            for k in range(len(seq.dilution_factors)):  #the list is filled during sequence
                data+=str(seq.dilution_factors[k])+'\t'
        else:
            data+='\ttotal\n'
            data+="added acid (uL)\t"+str(seq.added_acid_uL)+"\n"
            data+="dispensed base (uL)\t"                                                               
            for k in range(seq.N_mes):
                data+=str(seq.added_base_uL[k])+'\t'   
            data+='\t'+str(seq.total_added_volume)                                                                       
            data+='\ncumulate base (uL)\t'
            for k in range(seq.N_mes):
                data+=str(seq.cumulate_base_uL[k])+'\t'   
            data+='\ndilution factors\t'
            for k in range(seq.N_mes):
                data+=str(seq.dilution_factors[k])+'\t'

        #Pump speeds
        data+="\nPump mean voltage (Volt)\t"
        for speed in seq.pump_speeds_volt:
            data+=str(speed)+"\t"    #speed in volts

        #Reference and dark recording
        data+="\nNew reference and background\t"
        for r in seq.reference_orders:
            data+=str(bool(r))+"\t"    #speed in volts

        #Times
        data+="\ntimes (h:min:sec)\t"   #heures de mesures
        for k in range(len(seq.measure_times)):
            data+=str(seq.measure_times[k].strftime("%H:%M:%S"))+'\t'   
        data+="\nequilibration delay (h:min:sec)\t"   #temps entre mesures
        for k in range(len(seq.equilibration_times)):
            data+=str(seq.equilibration_times[k].seconds//60)+":"+str(seq.equilibration_times[k].seconds%60)+'\t' 

        #PHMETER
        if seq.phmeter.state=='open':    
            data+="\npH\t"
            for k in range(seq.N_mes):
                data+=seq.pH_mes[k]+'\t'
            data+="\nepsilon stab (pH unit)\t"
            for k in range(len(seq.stability_param)):
                data+=str(seq.stability_param[k][0])+'\t'
            data+="\ndt stab (seconds)\t"
            for k in range(len(seq.stability_param)):
                data+=str(seq.stability_param[k][1])+'\t'
        #1st line for formatted file (absorbance corrected from dilution)  
        processed_formatted_data="\t"   
        for k in range(seq.N_mes):
            processed_formatted_data+=seq.pH_mes[k]+'\t'
        processed_formatted_data+="\n"

        #SPECTROMETER
        data_abs = data
        data_intens = data
        if seq.spectro.state=='open':           
            #absorbance spectra
            data_abs+="\n\nWavelengths (nm)\tAbsorbance (OD) not corrected from dilution\n" 
            table_abs = [seq.spectro.wavelengths]+seq.absorbance_spectra
            for l in range(seq.spectro.N_lambda):
                for c in range(len(seq.absorbance_spectra)):
                    #print(l,c)
                    data_abs+=str(table_abs[c][l])+'\t'
                data_abs+=str(table_abs[len(seq.intensity_spectra)][l])+'\n'
            #intensity spectra
            data_intens+="\n\nWavelengths (nm)\tIntensity (Unit counts) not corrected from dilution\n" 
            table_intens = [seq.spectro.wavelengths]+seq.intensity_spectra
            for l in range(seq.spectro.N_lambda):  
                for c in range(len(seq.intensity_spectra)):
                    data_intens+=str(table_intens[c][l])+'\t'
                data_intens+=str(table_intens[len(seq.intensity_spectra)][l])+'\n'
            #absorabnce spectra corrected from dilution
            table_formatted = [seq.spectro.wavelengths]+seq.absorbance_spectra_cd
            for l in range(seq.spectro.N_lambda):  #spectres
                for c in range(len(seq.absorbance_spectra_cd)):
                    processed_formatted_data+=str(table_formatted[c][l])+'\t'
                processed_formatted_data+=str(table_formatted[len(seq.absorbance_spectra_cd)][l])+'\n'

        f_formatted_data = open(self.formatted_data_path,'w')
        f_formatted_data.write(processed_formatted_data)
        f_formatted_data.close()
        
        #création d'un fichier dans le répertoire
        file = open(self.data_abs_path,'w') 
        file.write(data_abs)
        file.close()

        file = open(self.data_intens_path,'w')
        file.write(data_intens)
        file.close()