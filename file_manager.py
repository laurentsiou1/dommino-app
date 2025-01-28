"Module qui gère la création des fichiers de données issues des expériences"

from datetime import datetime

import subsystems.processing as proc

def readSequenceInstructions(file):  #file: sequence config file #chaine de caracteres
    import csv
    with open(str(file), newline='') as f:
        reader = csv.reader(f, delimiter=';')
        tab = []
        syringes_to_use=[0,0,0] #set of syringes to be used
        idx=0
        for line in reader:
            print(idx)
            if idx==0:
                idx+=1
                continue    #On ne s'occupe pas de l'entête du fichier
            syringe_id=line[0]  #'A' or 'B'
            dispense_type=line[1]   #'DISP_ON_PH' or 'DISP_VOL_UL'
            value=float(line[2])   #50uL or pH4.5 ...
            delay_stop=int(line[3])  #30sec
            delay_mes=int(line[4])   #300sec
            if syringe_id=='A':
                syringes_to_use[0]=1
            elif syringe_id=='B':
                syringes_to_use[1]=1
            elif syringe_id=='C':
                syringes_to_use[2]=1
            row=[syringe_id,dispense_type,value,delay_stop,delay_mes]
            tab.append(row)
            idx+=1

    instruction_table=tab
    print("table d'instruction lue",instruction_table)
        
    return syringes_to_use, instruction_table

def createDirectMeasureFile(ihm):
    pass

def createFullSequenceFiles(seq):
    #cette fonction s'adapte à une séquence terminée ou en cours (cas d'interruption de séquence)
    #création d'un fichier compatible avec le traitement de données
    #Ainsi que d'un fichier metadata qui contient toutes les informations annexes à propos de l'expérience
    dt=datetime.now()
    date_for_file=str(dt.strftime("%m-%d-%Y_%Hh%Mmin%Ss"))

    #METADATA
    metadata = seq.infos+"\n\n"+seq.spectro.infos+"\n\n"+seq.phmeter.infos+"\n\n"+seq.pump.infos\
        +"\n\n"+seq.dispenser.infos+"\n\n"
    if seq.spectro.state=='open':   #background and reference spectra
        bgd_and_ref=[seq.spectro.wavelengths,seq.spectro.active_background_spectrum,seq.spectro.active_ref_spectrum]
        metadata+="lambda(nm)\tbackground (unit count)\treference ('')\n"
        for l in range(seq.spectro.N_lambda):
            for c in range(2):
                metadata+=str(bgd_and_ref[c][l])+'\t'
            metadata+=str(bgd_and_ref[2][l])+'\n'
    name_metadata = "seq_"+seq.experience_name+"_metadata_"+date_for_file
    f_metadata=open(seq.saving_folder+'/'+name_metadata+'.txt','w')
    f_metadata.write(metadata)
    f_metadata.close()
    
    print("saving titration sequence data")
    seq.N_mes=min(len(seq.pH_mes),len(seq.absorbance_spectra)) #if one measure is missing

    data="measure n°\t"    #entête
    for k in range(seq.N_mes):
        data+=str(k+1)+'\t'

    #DISPENSER
    print(seq.dispense_mode)
    if seq.dispense_mode=='from file':
        data+="\nsyringe A\t"
        for k in range(seq.N_mes):
            data+=str(seq.added_volumes[k][0])+'\t'
        data+="\nsyringe B\t"
        for k in range(seq.N_mes):
            data+=str(seq.added_volumes[k][1])+'\t'
        data+="\nsyringe C\t"
        for k in range(seq.N_mes):
            data+=str(seq.added_volumes[k][2])+'\t'
        data+="\ncumulate\t"
        for k in range(seq.N_mes):
            data+=str(seq.cumulate_volumes[k])+'\t'
        data+="\nDilution\t"
        for k in range(seq.N_mes):
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
        data+='\n' 
    
    processed_formatted_data=''
    
    #PHMETER
    if seq.phmeter.state=='open':    
        data+="\npH\t"
        for k in range(seq.N_mes):
            data+=str(seq.pH_mes[k])+'\t'
        data+="\ntimes\t"   #heures de mesures
        for k in range(seq.N_mes):
            data+=str(seq.measure_times[k].strftime("%H:%M:%S"))+'\t'   
        data+="\ndelays between measures\t"   #temps entre mesures
        for k in range(seq.N_mes):
            data+=str(seq.measure_delays[k].seconds//60)+":"+str(seq.measure_delays[k].seconds%60)+'\t' 
        data+="\nepsilon stab\t"
        for k in range(seq.N_mes):
            data+=str(seq.stability_param[k][0])+'\t'
        data+="\ndt stab\t"
        for k in range(seq.N_mes):
            data+=str(seq.stability_param[k][1])+'\t'
        data+="\nV0 (uL)\t"+str(seq.V_init)+"\n"    #volume en uL
        data+="Pump mean voltage (Volt) : "+str(12*seq.pump.duty_cycle)+"\n\n"    #vitesse de pompe
        data+="wavelengths (nm)\tabsorbance\n" 
            
        processed_formatted_data="\t"   #corrected from dilution
        for k in range(seq.N_mes):
            processed_formatted_data+=str(seq.pH_mes[k])+'\t'
        processed_formatted_data+="\n"
    
    if seq.spectro.state=='open':           
        #absorbance measured
        table = [seq.spectro.wavelengths]+seq.absorbance_spectra
        for l in range(seq.spectro.N_lambda):  #spectres
            for c in range(seq.N_mes):
                #print(l,c)
                data+=str(table[c][l])+'\t'
            data+=str(table[seq.N_mes][l])+'\n'

        #absorbance corrected from dilution
        seq.absorbance_spectra_cd=proc.correct_spectra_from_dilution(seq.absorbance_spectra,seq.dilution_factors[0:seq.N_mes])
        #on ne prend que les dilutions factors pour lequels on a un spectre enregistré 
        table_formatted = [seq.spectro.wavelengths]+seq.absorbance_spectra_cd
        for l in range(seq.spectro.N_lambda):  #spectres
            for c in range(seq.N_mes):
                processed_formatted_data+=str(table_formatted[c][l])+'\t'
            processed_formatted_data+=str(table_formatted[seq.N_mes][l])+'\n'
    
    name_formatted_data = "seq_"+seq.experience_name+"_formatted_data_"+date_for_file
    f_formatted_data = open(seq.saving_folder+'/'+name_formatted_data+'.txt','w')
    f_formatted_data.write(processed_formatted_data)
    f_formatted_data.close()
    
    name_data = "seq_"+seq.experience_name+"_data_"+date_for_file
    f_data = open(seq.saving_folder+'/'+name_data+'.txt','w') #création d'un fichier dans le répertoire
    f_data.write(data)
    f_data.close()