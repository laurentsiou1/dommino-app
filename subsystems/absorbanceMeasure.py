"Définition de la classe Spectrometer dans le cadre de l'instrument pytitrator"

"""Le spectro SR2 n'est pas muni de fonctionnalité buffer (qui permet de voir en direct)
Il faut donc à intervalle régulier, faire une mesure de spectre et l'afficher
Les fonctions :        
    adv.set_data_buffer_enable(True) #ne fonctionne pas sur le SR2        
    sur le SR2 on ne peut pas piloter la lampe non plus seulement le shutter"""

from lib.oceandirect.OceanDirectAPI import OceanDirectError, OceanDirectAPI, Spectrometer, FeatureID
from lib.oceandirect.od_logger import od_logger
logger = od_logger()

import numpy as np
import matplotlib.pyplot as plt
import time

from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *

from configparser import ConfigParser
import os
from pathlib import Path

from PyQt5 import QtCore

import subsystems.processing as sp
"""try: #dépend depuis où est lancé le programme
    import subsystems.processing as sp 
except:
    pass"""

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #répertoire pytitrator
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")

class AbsorbanceMeasure(Spectrometer):

    #Contrôle de la lampe   #pin10 : GND
    pin1_deuterium = DigitalOutput()
    pin1_deuterium.setDeviceSerialNumber(432846)
    pin1_deuterium.setChannel(5)
    pin1_deuterium.openWaitForAttachment(1000)
    pin5_halogen = DigitalOutput()
    pin5_halogen.setDeviceSerialNumber(432846)
    pin5_halogen.setChannel(4)
    pin5_halogen.openWaitForAttachment(1000)
    pin13_shutter = DigitalOutput()
    pin13_shutter.setDeviceSerialNumber(432846)
    pin13_shutter.setChannel(3)
    pin13_shutter.openWaitForAttachment(1000)

    def __init__(self): #ihm:IHM est un argument optionnel 
        self.state='closed'
        #Data
        #All spectra are saved with active corrections. It can be nonlinearity and/or electric dark 
        # when activated via methods "set_nonlinearity_correction_usage" and 
        # "set_electric_dark_correction_usage". None of these are corrected from 
        # the background spectrum. 
        self.active_background_spectrum=None  #Background Spectrum
        self.active_ref_spectrum=None   #Reference
        self.reference_absorbance=None  #courbe d'absorbance juste après la prise de réf
        self.current_intensity_spectrum=None    #Sample or whatever is in the cell
        self.current_absorbance_spectrum=None   #Absorbance
        self.wavelengths=None
        self.model=""
        
        #timer pour acquisition des spectres
        self.timer = QtCore.QTimer()
        self.timer.setInterval(3000)

    def connect(self):
        od = OceanDirectAPI()
        device_count = od.find_usb_devices() #ne pas enlever cette ligne pour détecter le spectro
        device_ids = od.get_device_ids()
        if device_ids!=[]:
            self.id=device_ids[0]
            try:
                spectro = od.open_device(self.id) #crée une instance de la classe Spectrometer
                adv = Spectrometer.Advanced(spectro)
                self.state='open'
                print("Spectro connecté")
            except:
                print("Ne peut pas se connecter au spectro numéro ", self.id)
                self.state='closed'
        else:
            self.state='closed'
            print("Spectro non connecté")
        #print("ID spectro: ", device_ids)
        
        if self.state=='open':
            
            self.wavelengths = [ round(l,1) for l in spectro.wavelengths ]
            self.N_lambda = len(self.wavelengths)
            self.model=spectro.get_model()
            self.ocean_manager=od #instance de la classe OceanDirectAPI
            self.device=spectro
            self.adv=Spectrometer.Advanced(spectro) 

            parser = ConfigParser()
            parser.read(app_default_settings)
            former_model=parser.get('spectrometry', 'model')
            self.t_int=int(parser.get('spectrometry', 'tint'))  #ms
            self.averaging=int(parser.get('spectrometry', 'avg'))
            self.acquisition_delay=self.t_int*self.averaging
            
            #Settings specific to models    #Tint and avg
            self.device.set_nonlinearity_correction_usage(True)
            if self.model==former_model:
                self.device.set_integration_time(1000*self.t_int)
                self.device.set_scans_to_average(self.averaging)
            else:
                self.device.set_scans_to_average(10)
                self.device.set_integration_time(10000)  
            
            if self.model=='OceanSR2':  #2k pix pour 700nm
                self.device.set_boxcar_width(1) #moyennage sur 3 points (2n+1)    
                print("spectro SR2 reconnu")
            elif self.model=='OceanSR6':    #2k pix pour 700nm à vérifier pour le SR6
                self.device.set_boxcar_width(1) #moyennage sur 3 points (2n+1)
                print("spectro SR6 reconnu")
            elif self.model=='OceanST': #2k pix pour 400nm
                self.device.set_boxcar_width(2) #moyennage sur 5 points (2n+1) 
                print("spectro ST reconnu")
            elif self.model=='HR2000+':
                self.device.set_boxcar_width(4) #moyenne sur 9 points (2k pixels sur 200nm soit 10 valeurs /nm)
                print("spectro HR2000+ reconnu")
            else:
                print("type de spectro non reconnu")
            
            if self.model!='OceanST' or self.model!='OceanSR6':
                self.device.set_electric_dark_correction_usage(False)   #non pris en charge par le ST
            else:
                self.device.set_electric_dark_correction_usage(True) 

            #time attributes in milliseconds. SDK methods outputs are in microseconds (us)
            self.t_int=self.device.get_integration_time()//1000 
            self.t_int_max=self.device.get_maximum_integration_time()//1000 
            self.t_int_min=self.device.get_minimum_integration_time()//1000 
            self.averaging=self.device.get_scans_to_average()
            self.boxcar=self.device.get_boxcar_width()
            
            self.timer.start()
            self.timer.timeout.connect(self.updateSpectra)

    def close(self,id): #fermeture de l'objet absorbanceMeasure
        self.timer.stop()
        self.pin13_shutter.setState(False)
        print("shutter fermé\n")
        self.device.close_device()
        self.ocean_manager.close_device(id) #close_device(id)
        print("Spectromètre déconnecté \n")
        self.state='closed'

    def open_shutter(self):
        self.pin13_shutter.setState(True)

    def close_shutter(self):
        self.pin13_shutter.setState(False)

    def changeShutterState(self):
        state=self.pin13_shutter.getState()
        self.pin13_shutter.setState(not(state))
    
    def update_acquisition_delay(self):
        self.acquisition_delay=self.t_int*self.averaging #ms

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
        t0=time.time()
        spectra=self.get_N_spectra()
        t1=time.time()
        avg=sp.average_spectra(spectra)
        t2=time.time()
        self.Irec_time=t1-t0
        self.avg_delay=t2-t1
        return avg

    def acquire_background_spectrum(self):
        self.pin13_shutter.setState(False)
        time.sleep(2)
        bgd=self.get_averaged_spectrum()
        self.active_background_spectrum=bgd

    def acquire_ref_spectrum(self):
        self.pin13_shutter.setState(True)
        time.sleep(2)
        ref=self.get_averaged_spectrum()
        ref2=self.get_averaged_spectrum()
        self.active_ref_spectrum=ref
        bgd=self.active_background_spectrum
        if bgd!=None:
            self.reference_absorbance, self.Aproc_delay = sp.intensity2absorbance(ref2,ref,bgd)

    def update_intensity_spectrum(self):    #ontimer
        self.current_intensity_spectrum=self.get_averaged_spectrum()
    
    def update_absorbance_spectrum(self):
        self.current_absorbance_spectrum, self.Aproc_delay = sp.intensity2absorbance(self.current_intensity_spectrum,self.active_ref_spectrum,self.active_background_spectrum)

    def updateSpectra(self):
        bgd=(self.active_background_spectrum!=None)
        ref=(self.active_ref_spectrum!=None)
        self.update_intensity_spectrum()
        if bgd*ref: #background and ref recorded
            self.update_absorbance_spectrum()
        #update refresh rate
        self.refresh_rate=self.Irec_time*1000+500   #ms
        self.timer.setInterval(self.refresh_rate)

class Advanced(AbsorbanceMeasure):  ### Fonctions optionelles ###    
    
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