"""Classe IHM qui contient des attributs communs à toutes les fenêtres PyQt"""

from configparser import ConfigParser
import os
from pathlib import Path
from datetime import datetime

#import format_data

from pHmeter import PHMeter
from spectro.absorbanceMeasure import AbsorbanceMeasure
from syringePump import SyringePump

path = Path(__file__)
print(path)
ROOT_DIR = path.parent.absolute()
app_config_path = os.path.join(ROOT_DIR, "config\\app_config.ini")


class IHM:
    def __init__(self, phm: PHMeter, spectro_unit: AbsorbanceMeasure, syringe_pump: SyringePump):
        self.phmeter=phm
        self.spectro_unit=spectro_unit
        self.syringe_pump=syringe_pump
        
        parser = ConfigParser()
        parser.read(app_config_path)
        
        self.saving_folder=parser.get('saving_parameters', 'folder')
        self.save_absorbance=parser.get('saving_parameters', 'save_absorbance')   
        self.save_pH=parser.get('saving_parameters', 'save_pH')
        self.save_titration_data=parser.get('saving_parameters', 'save_titration_data')
        self.create_detailed_param_file=parser.get('saving_parameters', 'create_detailed_param_file')
        self.compatible_format=parser.get('saving_parameters', 'compatible_format')         
        print(self.save_absorbance)          
              
    def updateConfigFile(self):
        parser = ConfigParser()
        parser.read(app_config_path)
        file = open(app_config_path,'r+')
        parser.set('saving_parameters', 'folder', str(self.saving_folder)) 
        parser.set('saving_parameters', 'save_absorbance', str(self.save_absorbance)) 
        parser.set('saving_parameters', 'save_pH', str(self.save_pH)) 
        parser.set('saving_parameters', 'save_titration_data', str(self.save_titration_data)) 
        parser.set('saving_parameters', 'create_detailed_param_file', str(self.create_detailed_param_file)) 
        parser.set('saving_parameters', 'compatible_format', str(self.compatible_format)) 
        parser.write(file) 
        file.close()
        print("update dans l'IHM")

    def createDirectMeasureFile(self):
        set = {}
        dt = datetime.now()
        date_text=dt.strftime("%m/%d/%Y %H:%M:%S")
        date_time=dt.strftime("%m-%d-%Y_%Hh%Mmin%Ss")
        name = "mes_"
        header = "Mesure sur Pytitrator\n"+"date et heure : "+str(date_text)+"\n\n"
        data = ""
        print("saving instant measure - ",self.phmeter.CALdate)
        if self.save_pH: #saving pH measure
            if self.phmeter.getIsOpen():
                name+="pH-"
                
                header+=("Données de la calibration courante\n"+"date et heure: "+self.phmeter.CALdate+"\n"+
                "température: "+str(self.phmeter.CALtemperature)+"\n"+"nombre de points: "+str(self.phmeter.CALtype)+"\n"+
                "Tensions mesurées: U4="+str(self.phmeter.U1)+"V; U7="+str(self.phmeter.U2)+"V; U10="+str(self.phmeter.U3)+"V\n"+
                "coefficents de calibration actuels: a="+str(self.phmeter.a)+ "; b="+str(self.phmeter.b)+"\n\n"
                )
                pH = self.phmeter.currentPH
                V = self.phmeter.currentVoltage
                data+="pH = "+str(pH)+"; U = "+str(V)+"V\n\n"
            else:
                header+="pH meter not connected\n\n"

        if self.save_titration_data: #saving dispensed volumes
            if self.syringe_pump.getIsOpen():
                name+="titr-"
                header+=("Syringe Pump : "+str(self.syringe_pump.model)+"\n"
                +"Syringe : "+str("500uL Trajan gas tight syringe\n"))
                data+=("Fluid dispense log \n"
                       +"acid : "+str(self.syringe_pump.acid_dispense_log)+"uL\n"
                       +"base : "+str(self.syringe_pump.base_dispense_log)+"uL\n"
                +"Added acid : "+str(self.syringe_pump.added_acid_uL)+"uL\n"
                +"added base : "+str(self.syringe_pump.added_base_uL)+"uL\n"
                +"total added : "+str(self.syringe_pump.added_total_uL)+"uL\n")
            else:
                header+="Syringe pump not connected\n\n"

        if self.save_absorbance: #saving absorbance
            if self.spectro_unit.state=='open':
                name+="Abs_"
                header+=("Spectrometer : "+str(self.spectro_unit.model)+"\n"
                +"Integration time (ms) : "+str(self.spectro_unit.t_int/1000)+"\n"
                +"Averaging : "+str(self.spectro_unit.averaging)+"\n"
                +"Boxcar : "+str(self.spectro_unit.boxcar)+"\n"
                +"Nonlinearity correction usage : "+str(self.spectro_unit.nonlinearity_correction_usage)+"\n"
                +"Electric dark correction usage : "+str(self.spectro_unit.electric_dark_correction_usage)+"\n")
                dark_ref = self.spectro_unit.active_dark_spectrum
                blanc_ref = self.spectro_unit.active_ref_spectrum
                absorbance = self.spectro_unit.current_Abs_spectrum
                intensity = self.spectro_unit.current_spectrum
                wl = self.spectro_unit.wavelengths
                spectra=[wl,dark_ref,blanc_ref,intensity,absorbance]
            
                data+="lambda(nm)\tdark spectrum (pixel count)\treference (pixel count)\tintensity (pixel count)\tabsorbance (abs unit)\n"
                for l in range(self.spectro_unit.N_lambda):
                    for c in range(4):
                        data+=str(spectra[c][l])+'\t'
                    data+=str(spectra[4][l])+'\n'
            else:
                header+="Spectrometer closed\n"

        
        name+=str(date_time)
        output=header+"\n\n"+data
        f_out = open(self.saving_folder+'/'+name+'.txt','w') #création d'un fichier dans le répertoire
        f_out.write(output)
        f_out.close()
        

 

    def createFullSequenceFile(self):
        #création du fichier au format compatible avec le traitement de données
        output_name_csv='test_saving_ihm'
        
        #remplissage du fichier       
        output_string = "\t"
        for j in range(N_mes-1):
            output_string += str(str(pH[j]))+'\t'
        output_string += str(pH[N_mes-1])+'\n'    

        for l in range(N_lambda): #chaque élément de la liste correspond à une ligne sur le .csv
            output_string += str(wl[l])+'\t'
            for j in range(N_mes-1):
                output_string += str(Absorbance_set[j][l])+'\t'
            output_string += str(Absorbance_set[N_mes-1][l])+'\n'
        
        f_out = open(self.saving_folder+'/'+output_name_csv+'.txt','w') #création d'un fichier dans le répertoire
        f_out.write(output_string)
        f_out.close()


if __name__=="main":
    interface = IHM()
    print(interface.saving_folder)