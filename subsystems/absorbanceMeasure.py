"""
File absorbanceMeasure.py defines class AbsorbanceMeasure
It allows to control both spectrometer and lamp
This class inherits from class Spectrometer of OceanDirectAPI
"""

from lib.oceandirect.OceanDirectAPI import OceanDirectError, OceanDirectAPI, Spectrometer, FeatureID
from lib.oceandirect.od_logger import od_logger
logger = od_logger()

from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *

from configparser import ConfigParser
import os, time
from datetime import datetime
from pathlib import Path

from PyQt5 import QtCore

import subsystems.processing as sp

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #répertoire pytitrator
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")

class AbsorbanceMeasure(Spectrometer):
    
    #getting board numbers and wiring
    parser = ConfigParser()
    parser.read(device_ids)
    board_number = int(parser.get('main board', 'id'))
    VINT_number = int(parser.get('VINT', 'id'))
    ch_shutter=int(parser.get('lamp', 'shutter'))
    ch_deuterium=int(parser.get('lamp', 'deuterium'))
    ch_halogen=int(parser.get('lamp', 'halogen'))

    #Lamp control
    shutter = DigitalOutput()
    shutter.setDeviceSerialNumber(board_number)
    shutter.setChannel(ch_shutter)
    deuterium = DigitalOutput()
    deuterium.setDeviceSerialNumber(board_number)
    deuterium.setChannel(ch_deuterium)
    halogen = DigitalOutput()
    halogen.setDeviceSerialNumber(board_number)
    halogen.setChannel(ch_halogen)

    def __init__(self):
        self.state='closed'
        
        #All spectra are saved with active corrections. It can be nonlinearity and/or electric dark 
        # when activated via methods "set_nonlinearity_correction_usage" and 
        # "set_electric_dark_correction_usage". None of these are corrected from 
        # the background spectrum. 

        #Before connecting the instrument, all attributes are instanciated with None
        self.active_background_spectrum=None  #Background Spectrum
        self.active_ref_spectrum=None   #Reference
        self.reference_absorbance=None  #courbe d'absorbance juste après la prise de réf
        self.current_intensity_spectrum=None    #Sample or whatever is in the cell
        self.current_absorbance_spectrum=None   #Absorbance
        self.absorbance_spectrum1=None
        self.wavelengths=None
        self.model=''
        self.serial_number=''
        self.Irec_time=0
        
        #timer for spectra acquisition
        self.timer = QtCore.QTimer()
        self.timer.setInterval(3000)
        
        self.update_infos()

    def connect(self):
        """
        Connection of spectrometer and lamp. 
        If either lamp control (via interface board) or spectrometer is not connected or under tension
        connection state will stay on 'closed'. 
        Creates an instance of class Spectrometer self.device. And sets basic parameters on spectro.

        """
        od = OceanDirectAPI()
        device_count = od.find_usb_devices() #ne pas enlever cette ligne pour détecter le spectro
        #print(device_count)
        device_ids = od.get_device_ids()
        #print(device_ids)
        if device_ids!=[]:
            self.id=device_ids[0]
            try:
                spectro = od.open_device(self.id) #crée une instance de la classe Spectrometer
                adv = Spectrometer.Advanced(spectro)
                det=0
                try:
                    self.shutter.openWaitForAttachment(1000)
                    self.shutter_connected=True
                except:
                    self.shutter_connected=False
                    det+=1
                try:
                    self.deuterium.openWaitForAttachment(1000)
                    self.deuterium_connected=True
                except:
                    self.deuterium_connected=False
                    det+=1
                try:
                    self.halogen.openWaitForAttachment(1000)
                    self.halogen_connected=True
                except:
                    self.halogen_connected=False
                    det+=1
                if det==0:
                    self.state='open'
                else:
                    self.state='closed'
            except:
                print("Can not connect to spectrometer identified : ",self.id)
        else:
            self.state='closed'
        
        #if absorbanceMeasure object is in state 'closed', some methods would retunr error message
        if self.state=='open':
            self.wavelengths = [ round(l,1) for l in spectro.wavelengths ]
            self.N_lambda = len(self.wavelengths)
            self.model=spectro.get_model()
            #print(self.model)
            self.serial_number=spectro.get_serial_number()
            self.ocean_manager=od #instance de la classe OceanDirectAPI
            self.device=spectro
            self.adv=Spectrometer.Advanced(spectro) 

            parser = ConfigParser()
            parser.read(app_default_settings)
            former_model=parser.get('spectrometry', 'model')
            self.t_int=int(parser.get('spectrometry', 'tint'))  #ms
            self.averaging=int(parser.get('spectrometry', 'avg'))
            self.acquisition_delay=self.t_int*self.averaging

            #Nonlinearity correction : normally available on most of Ocean spectrometers 
            self.device.set_nonlinearity_correction_usage(True)
            
                    ## Settings specific to models 
            
            #Electric dark correction
            try:
                ed=self.device.get_electric_dark_correction_usage()
                #self.device.set_electric_dark_correction_usage()
                self.electric_dark=ed
            except: #feature not available for OceanST or OceanSR spectrometers
                self.electric_dark = False

            #All spectra are saved with active corrections. It can be nonlinearity and/or electric dark 
            # when activated via methods "set_nonlinearity_correction_usage" and 
            # "set_electric_dark_correction_usage". None of these are corrected from 
            # the background spectrum. 

            #Integration time and averaging
            if self.model==former_model:
                self.device.set_integration_time(1000*self.t_int)
                self.device.set_scans_to_average(self.averaging)
            else:
                self.device.set_integration_time(15000) 
                self.device.set_scans_to_average(10)
            
            #boxcar
            if self.model=='OceanSR':  #2k pix pour 700nm   #SR4 or SR6
                self.device.set_boxcar_width(1) #moyennage sur 3 points (2n+1)  
            elif self.model=='OceanST': #2k pix pour 400nm
                self.device.set_boxcar_width(2) #moyennage sur 5 points (2n+1) 
            else:
                print("Spectrometer model not recognized")

            #time attributes in milliseconds. SDK methods outputs are in microseconds (us)
            self.t_int=self.device.get_integration_time()//1000 
            self.t_int_max=self.device.get_maximum_integration_time()//1000 
            self.t_int_min=self.device.get_minimum_integration_time()//1000 
            self.averaging=self.device.get_scans_to_average()
            self.boxcar=self.device.get_boxcar_width()
            
            self.timer.start()
            self.timer.timeout.connect(self.updateSpectra)
        
        self.update_infos()
        print(self.infos)
    
    def update_infos(self):
        """
        Updates attribute self.infos according to current parameters of spectrometer 
        """
        if self.state=='open':
            self.infos="\nSpectrometer : connected"\
            +"\nModel : "+self.model\
            +"\nIntegration time (ms) : "+str(self.t_int/1000)\
            +"\nAveraging : "+str(self.averaging)\
            +"\nBoxcar : "+str(self.boxcar)\
            +"\nNonlinearity correction usage : "+str(self.device.get_nonlinearity_correction_usage())\
            +"\nElectric dark correction usage : "+str(self.electric_dark)\
            +"\nAbsorbance formula : A = log10[(reference-background)/(sample-background)]"\
            +"\nOutput pins :"\
            +"\nShutter pin : "+str(self.shutter_connected)\
            +"\nDeuterium pin : "+str(self.deuterium_connected)\
            +"\nHalogen pin : "+str(self.halogen_connected)
        else:
            self.infos="\nCan not connect to spectrometer"

    def close(self,id): 
        """
        Closing of object AbsorbanceMeasure. It closes spectrometer and lamp shutter 
        to protect fibers from solarization
        """
        self.timer.stop()
        self.shutter.setState(False)
        print("shutter closed\n")
        self.device.close_device()
        self.ocean_manager.close_device(id) #close_device(id)
        print("Spectrometer disconnected\n")
        self.state='closed'

    def get_shutter_state(self):
        """
        Returns shutter's current state"""
        if self.state=='open':
            self.shutter_state=self.shutter.getState()
        else:
            self.shutter_state=False
        return self.shutter_state

    def open_shutter(self):
        """
        Opens lamp shutter.
        """
        if self.state=='open':
            self.shutter.setState(True)

    def close_shutter(self):
        """
        Closes lamp shutter.
        """
        if self.state=='open':
            self.shutter.setState(False)

    def changeShutterState(self):
        """
        Changes the current shutter state --> ON or OFF
        """
        state=self.shutter.getState()
        self.shutter.setState(not(state))
    
    def update_acquisition_delay(self):
        """
        Updates attribute self.acquisition_delay. This value is purely theoretical. 
        The attibute is also updated via a timer inside method get_N_spectra()
        """
        self.acquisition_delay=self.t_int*self.averaging #ms

    def get_N_spectra(self):
        """
        It launches method get_formatted_spectrum from oceanDirectAPI N times, with N 
        the current scans_to_average number
        Returns spectra a list of N spectra : List[List[floats]]
        Each spectrum is a list of float of size (self.wavelength)
        """
        t0=time.time()
        N=self.device.get_scans_to_average()
        try:
            self.device.set_scans_to_average(1) #every spectrum recorded is a single spectrum
            spectra = [0 for k in range(N)]
            for i in range(N):
                spectra[i] = self.device.get_formatted_spectrum() #gets the current spectrum
                # with activated corrections (nonlinearity and/or electric dark) and with
                # NO substraction of the background
            self.device.set_scans_to_average(N)
        except OceanDirectError as e:
            logger.error(e.get_error_details())  
        t1=time.time()
        #print("spectra",spectra)
        self.acquisition_delay=t1-t0
        #print("acquisition delay :",t1-t0)
        return spectra
    
    def get_averaged_spectrum(self):
        """
        Launches record of N spectra. Returns the average List[float]
        """
        t0=time.time()
        spectra=self.get_N_spectra()
        t1=time.time()
        avg=sp.average_spectra(spectra)
        t2=time.time()
        self.Irec_time=t1-t0
        self.avg_delay=t2-t1
        #print("averaging delay : ", self.avg_delay)
        self.update_refresh_rate()
        #print(type(avg))
        return avg

    def acquire_background_spectrum(self):
        """
        Acquires background spectrum (including closing shutter) and time
        """
        self.active_background_time = datetime.now().replace(microsecond=0)
        self.shutter.setState(False)
        time.sleep(2)
        bgd=self.get_averaged_spectrum()
        self.active_background_spectrum=bgd
        time.sleep(2)
        print("background spectrum recorded")

    def acquire_ref_spectrum(self):
        """
        Acquires reference spectrum (including opening shutter) and time
        If the background is taken, it also computes absorbance
        """
        self.active_ref_time = datetime.now().replace(microsecond=0)
        self.shutter.setState(True)
        time.sleep(2)
        ref=self.get_averaged_spectrum()
        ref2=self.get_averaged_spectrum()
        self.active_ref_spectrum=ref
        bgd=self.active_background_spectrum
        if bgd!=None:
            self.reference_absorbance, self.Aproc_delay = sp.intensity2absorbance(ref2,ref,bgd)
        time.sleep(2)
        print("reference spectrum recorded")

    def update_intensity_spectrum(self):
        """
        Updates the current spectrum by taking a measure.
        The method is executed periodically with timer.
        """
        self.current_intensity_spectrum=self.get_averaged_spectrum()
    
    def update_absorbance_spectrum(self):
        """
        Computes the absorbance spectrum from the current intensity spectrum.
        """
        self.current_absorbance_spectrum, self.Aproc_delay = sp.intensity2absorbance(self.current_intensity_spectrum,self.active_ref_spectrum,self.active_background_spectrum)

    def dark_and_ref_stored(self):
        """
        Returns True if a background and a reference spectrum have been stored
        False otherwise
        """
        opened=(self.state=='open')
        bgd=(self.active_background_spectrum!=None)
        ref=(self.active_ref_spectrum!=None)
        return opened*bgd*ref

    def updateSpectra(self):
        """
        Executes on timer. Updates current spectra.
        """
        self.update_intensity_spectrum()
        if self.dark_and_ref_stored(): #background and ref recorded
            self.update_absorbance_spectrum()

    def update_refresh_rate(self):   
        """
        Modifies the period with which spectra are recorded and displayed.
        """
        #the rate is set 500ms higher than the entire acquisition time
        #to let the interface refresh between two acquisitions.
        self.refresh_rate=int(self.acquisition_delay*1000+500)   #ms
        self.timer.setInterval(self.refresh_rate)

class Advanced(AbsorbanceMeasure):  ### Fonctions optionelles ###    
    
    def get_optimal_integration_time(self, spectra):
        """
        Method not used for the moment. It would allows to set automatically 
        the appropriate integration time on spectrometer. 
        """
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