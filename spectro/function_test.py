"Programme pour tester les fonctions"

from oceandirect.OceanDirectAPI import OceanDirectAPI, OceanDirectError, Spectrometer
from oceandirect.od_logger import od_logger

import numpy as np
import matplotlib.pyplot as plt
import time

import acquisition
import display


logger = od_logger()
od = OceanDirectAPI()

int_time_us = 18000 #microsecondes
avg = 1000
boxcar = 1

device_count = od.find_usb_devices() # 1 si appareils détectés
device_ids = od.get_device_ids()
device_count = len(device_ids)
print("\nnumber of devices found : ", device_count)
print("devices ID's : ", device_ids)

if device_count:
    for id in device_ids:

        device = od.open_device(id) #crée une instance de la classe Spectrometer
        adv = Spectrometer.Advanced(device)

        device.set_integration_time(int_time_us)
        device.set_boxcar_width(boxcar)
        device.set_scans_to_average(avg)
        wl = device.get_wavelengths()

        adv.set_enable_lamp(True) 
        time.sleep(1) #ouverture du shutter

        #print("début de l'acquisition")
        #s1 = acquisition.get_spectrum_internal_averaging(device, avg)
        #display.plot_spectrum(wl,s1)

        print("début de l'acquisition")
        s2 = acquisition.get_spectra(device, avg)
        print("size s2 = ",np.shape(s2))
        s2 = acquisition.average_spectra(s2)
        display.plot_spectrum(wl,s2)

        

        adv.set_enable_lamp(False) #Protection des fibres
        print("shutter fermé\n")

        print("closing device!")
        od.close_device(id)
        print("device closed \n")
