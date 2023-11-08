"Définition de la classe Spectrometer dans le cadre de l'instrument pytitrator"

"""Le spectro SR2 n'est pas muni de fonctionnalité buffer (qui permet de voir en direct)
Il faut donc à intervalle régulier, faire une mesure de spectre et l'afficher
Les fonctions :        
    adv.set_data_buffer_enable(True) #ne fonctionne pas sur le SR2        
    sur le SR2 on ne peut pas piloter la lampe non plus seulement le shutter"""

from oceandirect.OceanDirectAPI import OceanDirectError, OceanDirectAPI, Spectrometer, FeatureID
from oceandirect.od_logger import od_logger
logger = od_logger()

import numpy as np
import matplotlib.pyplot as plt
import math
import time
#from timeloop import Timeloop
#from datetime import timedelta
#tl = Timeloop()

try: #dépend depuis où est lancé le programme
    import spectro.processing as sp 
except:
    import processing as sp

"""
#La fonction récupère un spectre issu du moyennage sur le Spectro
#ça fonctionne mais c'est plus lent que de moyenner sur l'ordinateur
    def get_spectrum_internal_averaging(self, avg):
        try:
            Spectrometer.set_scans_to_average(self.device,avg) #avg est le nombre de moyennage
        	#numb_pixel = len(device.get_formatted_spectrum()) #nb de points du spectre
        	#spectra_m = [0 for x in range(numb_pixel)]
            mean_spectra = self.device.get_formatted_spectrum() #acquisition du spectre
        except OceanDirectError as e:
        	logger.error(e.get_error_details())
        return mean_spectra
"""
class AbsorbanceMeasure(Spectrometer):

    def __init__(self, od, spectro : Spectrometer): 
        if spectro!=None:
            self.state='open'
            self.model=spectro.get_model()
            #print(self.model)
            self.ocean_manager=od #instance de la classe OceanDirectAPI
            self.device=spectro
            self.adv=Spectrometer.Advanced(spectro) 
            
            #Processing corrections
            #Specific to models
            if self.model=='OceanSR2':
                self.device.set_boxcar_width(1) #moyennage sur 3 points (2n+1)
                #2k pix pour 700nm
                self.device.set_integration_time(30000)      
                print("spectro sr2 reconnu")
            elif self.model=='OceanST':
                self.device.set_boxcar_width(2) #moyennage sur 5 points (2n+1) 
                #2k pix pour 400nm
                self.device.set_integration_time(10000)
                print("spectro st-uv reconnu")
            elif self.model=='HR2000+':
                self.device.set_boxcar_width(4) 
                #moyenne sur 9 points (2k pixels sur 200nm soit 10 valeurs /nm)
                self.device.set_integration_time(50000)
                print("spectro HR2000+ reconnu")
            else:
                print("type de spectro non reconnu")
            self.device.set_scans_to_average(10) #to declare after int time
            self.device.set_nonlinearity_correction_usage(False)
            if self.model!='OceanST':
                self.device.set_electric_dark_correction_usage(True) #non pris en charge par le ST
            else:
                self.device.set_electric_dark_correction_usage(False)
                #print("Electric dark not included with OceanST")
            
            self.wavelengths = [ round(l,1) for l in spectro.wavelengths ]
            self.N_lambda = len(self.wavelengths)
            #time attributes in milliseconds. SDK methods outputs are in microseconds (us)
            self.t_int=self.device.get_integration_time()//1000 
            self.t_int_max=self.device.get_maximum_integration_time()//1000 
            self.t_int_min=self.device.get_minimum_integration_time()//1000 
            #print("min tint=",self.t_int_min,"\tmax tint=",self.t_int_max)
            self.averaging=self.device.get_scans_to_average()
            self.boxcar=self.device.get_boxcar_width()
            
            #Data
            #All spectra are saved with active corrections. It can be nonlinearity and/or electric dark 
            # when activated via methods "set_nonlinearity_correction_usage" and 
            # "set_electric_dark_correction_usage". None of these are corrected from 
            # the background spectrum. 
            self.active_background_spectrum=None  #Background Spectrum
            self.active_ref_spectrum=None   #Reference
            self.current_intensity_spectrum=None    #Sample or whatever is in the cell
            self.current_absorbance_spectrum=None   #Absorbance

        else:
            self.state='closed'

    def getIsOpen(self):
        if self.state=='open':
            a=True
        elif self.state=='closed':
            a=False
        return a

    def close(self,id): #fermeture de l'objet absorbanceMeasure
        self.adv.set_enable_lamp(False) #Protection des fibres
        print("shutter fermé\n")
        self.device.close_device()
        self.ocean_manager.close_device(id) #close_device(id)
        print("Spectromètre déconnecté \n")
        self.state='closed'

    def open_shutter(self):
        self.adv.set_enable_lamp(True)

    def close_shutter(self):
        self.adv.set_enable_lamp(False)

    def changeShutterState(self):
        new_state=not(self.adv.get_enable_lamp())
        self.adv.set_enable_lamp(new_state)

    #Récupère autant de spectres que N_avg sur le spectro
    #Fonction vérifiée qui fonctionne. Plus rapide que de faire le moyennage sur le spectro
    def get_N_spectra(self):
        N=self.device.get_scans_to_average()
        try:
            self.device.set_scans_to_average(1)
            spectra = [0 for k in range(N)]
            for i in range(N):
                spectra[i] = self.device.get_formatted_spectrum() #gets the current spectrum
                # with activated corrections (nonlinearity and/or electric dark) and with
                # NO substraction of the background
            self.device.set_scans_to_average(N)
        except OceanDirectError as e:
            logger.error(e.get_error_details())  
        return spectra
    
    def get_averaged_spectrum(self):
        spectra=self.get_N_spectra()
        avg=sp.average_spectra(spectra)
        #self.current_spectrum_non_corrected=avg
        return avg

    def acquire_background_spectrum(self):
        self.adv.set_enable_lamp(False)
        time.sleep(2)
        bgd=self.get_averaged_spectrum()
        self.active_background_spectrum=bgd

    def acquire_ref_spectrum(self):
        self.adv.set_enable_lamp(True)
        time.sleep(2)
        ref=self.get_averaged_spectrum()
        self.active_ref_spectrum=ref


                            ### Fonctions pas  utiles ? ###
    """def acquire_ref_and_dark_spectra(self):
        self.adv.set_enable_lamp(False)
        time.sleep(2)
        #Prise du spectre d'obscurité
        dark_spectrum=self.get_averaged_spectrum()
        #print("dark_spectrum=",dark_spectrum, "len=",len(dark_spectrum))
        self.device.set_stored_dark_spectrum(dark_spectrum)
        
        self.adv.set_enable_lamp(True)
        print("shutter ouvert ? ",self.adv.get_enable_lamp())
        time.sleep(2)
        ref_spectrum_non_corrected=self.get_averaged_spectrum()
        #correction du dark spectrum et nonlinearité
        ref_spectrum=self.device.nonlinearity_correct_spectrum2(dark_spectrum,ref_spectrum_non_corrected)
        #print("ref_spectrum=",ref_spectrum, "len=",len(ref_spectrum))

        #actualisation des attributs
        self.active_dark_spectrum=dark_spectrum
        self.active_ref_spectrum=ref_spectrum #corrigé
        
        #ajout sur les graphes
        AbsorbanceMeasure.add_spectrum_to_plot(self,dark_spectrum,name='dark spectrum')
        AbsorbanceMeasure.add_spectrum_to_plot(self,ref_spectrum,name='ref spectrum')
    
    def add_spectrum_to_plot(self, spectrum, type=None, name='name'):
        "type est un string 'intensity' ou 'absorbance'"
        "name est le nom de la courbe"
        spec = np.array(spectrum)#tracé
        wl=self.wavelengths
        plt.plot(wl, spec, label=name)
        if type=='intensity':
            plt.ylabel("Spectre d'intensité (unit counts)")
        elif type=='absorbance':
            plt.ylabel("Spectre d'Absorabnce (u.a.)")    
        plt.xlabel("Longueur d'onde (nm)")
        #print("isinteractive=",plt.isinteractive())
        plt.plot(block=False)

    def get_averaged_corrected_spectrum(self,dark_sp=None):
        if dark_sp!=None: # argument renseigné
            dsp=dark_sp
            pass
        elif self.active_dark_spectrum!=None: #attribut existant
            dsp=self.active_dark_spectrum
        else:   #aucun argument ni attribut de fourni
            #print("Spectrum has no dark correction")
            dsp=[0 for i in self.wavelengths] #correction nulle
            #print("dsp=",dsp)
        current_sp=self.get_averaged_spectrum()
        #print("spectrum non corrected =", current_sp[0:10])
        #correction de dark spectrum et nonlinearity
        #corr_spectrum = self.device.nonlinearity_correct_spectrum2(dsp,current_sp)
        return current_sp"""

    def get_optimal_integration_time(self, spectra):
        int_time_us=self.t_int*1000
        Imax=sp.max_intensity(spectra)
        if self.serial_number=='STUV002':
            optimal_int_time_us = 1000*int(int_time_us*15/Imax) #15000 unit count correspond au ST.
            #Le capteur a une résolution de 14bit = 16300... unit count
            #ça doit être un multiple de 1000 pour être entier en millisecondes.
            return optimal_int_time_us  
        elif self.serial_number=='SR200336':
            optimal_int_time_us = 1000*int(int_time_us*50/Imax) #15000 unit count correspond au ST. 
            return optimal_int_time_us
        else:
            print("numéro du spectro: ",self.serial_number)
        return optimal_int_time_us
                            ### Fonctions optionelles ###    

#Pour test des fonctions de la classe
if __name__ == "__main__":

    od = OceanDirectAPI()
    device_count = od.find_usb_devices() # 1 si appareils détectés
    device_ids = od.get_device_ids()
    device_count = len(device_ids)
    #print("\nNombre d'appareils OceanDirect détectés : ", device_count)
    #print("ID spectros: ", device_ids)
    if device_ids!=[]:
        id=device_ids[0]
        print("Spectro connecté")
        device = od.open_device(id) #crée une instance de la classe Spectrometer
        absorbance_unit=AbsorbanceMeasure(od,device)
        adv = Spectrometer.Advanced(device)
        """
        #ref et dark
        absorbance_unit.acquire_ref_and_dark_spectra()

        #test de get spectrum
        spec=AbsorbanceMeasure.get_averaged_corrected_spectrum(absorbance_unit)
        #print(spec)
        """
        
        #dark
        try:
            input("taper entrer lorsque le shutter est fermé")
        except(KeyboardInterrupt):
            pass
        absorbance_unit.acquire_background_spectrum()

        #ref
        try:
            input("taper entrer lorsque le shutter est ouvert")
        except(KeyboardInterrupt):
            pass
        absorbance_unit.acquire_ref_spectrum()

        #sample
        try:
            input("taper entrer lorsque le shutter est ouvert")
        except(KeyboardInterrupt):
            pass
        spec=absorbance_unit.get_averaged_spectrum()

        #tracé
        absorbance_unit.add_spectrum_to_plot(spec)
        absorbance_unit.add_spectrum_to_plot(absorbance_unit.active_background_spectrum,'intensity')
        absorbance_unit.add_spectrum_to_plot(absorbance_unit.active_ref_spectrum,'intensity')
    
        plt.legend() #tracé
        plt.show()
        

        device.details()
        print(device.get_device_type())
        print(device.get_model())
        print(device.model_name,device.model)
        print(device.get_serial_number())
        print(device.serial_number)




        #fermeture
        absorbance_unit.close_shutter()
        print("shutter ouvert ? ",adv.get_enable_lamp())
        print("shutter fermé")
        device.close_device()
        print("device closed")
