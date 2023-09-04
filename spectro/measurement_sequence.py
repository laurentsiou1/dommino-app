from oceandirect.OceanDirectAPI import OceanDirectAPI, OceanDirectError, Spectrometer
from oceandirect.od_logger import od_logger

import numpy as np
import matplotlib.pyplot as plt
import time

import acquisition
import display

logger = od_logger()  
od = OceanDirectAPI()

device_count = od.find_usb_devices() # 1 si appareils détectés
device_ids = od.get_device_ids()
device_count = len(device_ids)
print("\nnumber of devices found : ", device_count)
print("devices ID's : ", device_ids)

int_time_us = 10000 #microsecondes
avg = 10
boxcar = 5 #valeur sur le ST-UV
print("Tint = %d us\navg = %d scans \nboxcar= %d" % (int_time_us, avg, boxcar))

#print("avg = %d scans \n" %avg)
#plt.ion()

if device_count:
    for id in device_ids: #jamais plus que un appareil de branché

        device = od.open_device(id) #crée une instance de la classe Spectrometer
        adv = Spectrometer.Advanced(device) #je crée une instance de la classe Spectrometer.advanced

        serialNumber = device.get_serial_number()
        print("Serial Number : %s" % serialNumber)

        device.set_integration_time(int_time_us)
        device.set_boxcar_width(boxcar)
        device.set_scans_to_average(avg)
        wl = device.get_wavelengths()
        
        #prise du spectre d'obscurité
        adv.set_enable_lamp(False)
        print("Shutter fermé")
        time.sleep(1)
        print("Acquisition du spectre d'obscurité")
        s0 = acquisition.get_spectra(device, avg)
        dark_spectrum = acquisition.average_spectra(s0) #renvoie le spectre moyenné au même format (liste)
        
        p0=plt.subplot(221)
        sp0 = np.array(dark_spectrum)
        p0.plot(wl,sp0)
        #display.plot_spectrum(wl,dark_spectrum)

        device.set_stored_dark_spectrum(dark_spectrum)
        device.set_nonlinearity_correction_usage(True) #nécessite d'avoir enregistré un dark spectrum
        #device.set_electric_dark_correction_usage(True) #Ne fonctionne pas sur le ST
        
        formatted_spectrum=device.get_formatted_spectrum()
        print("formatted_spectrum",len(formatted_spectrum))
        unformatted_spectrum=adv.get_unformatted_spectrum()
        print("unformatted_spectrum",len(unformatted_spectrum))

        #display.plot_spectrum(wl,formatted_spectrum)
        #display.plot_spectrum(wl,test2)

        #prise du blanc de référence
        adv.set_enable_lamp(True)
        print("shuter ouvert")
        time.sleep(1)
        print("Acquisition du blanc de référence")
        s1 = acquisition.get_spectra(device, avg)
        blanc_ref = acquisition.average_spectra(s1)
        
        p1=plt.subplot(222)
        sp1 = np.array(blanc_ref)
        p1.plot(wl,sp1)
        p1.set_title('Tint=18ms')
        #display.plot_spectrum(wl,blanc_ref)
        
        #réglage du temps d'intégration optimal
        optimal_int_time_us = acquisition.get_optimal_integration_time(blanc_ref,int_time_us)
        print("Nouveau temps d'intégration = ", optimal_int_time_us,"us")
        device.set_integration_time(optimal_int_time_us)

        print("Acquisition d'un blanc avec temps d'inté optimal")
        s2 = acquisition.get_spectra(device, avg)
        new_blanc = acquisition.average_spectra(s2)
        
        p2=plt.subplot(223)
        sp2 = np.array(new_blanc)
        p2.plot(wl,sp2)
        p2.set_title('nouveau Tint')
        #display.plot_spectrum(wl,new_blanc)  

        p3=plt.subplot(224)
        sp3 = sp1-sp2
        plt.plot(wl,sp3)
        p3.set_title('différence')

        adv.set_enable_lamp(False)
        #Pour protéger les fibres de la solarisation

        plt.show()

        print("closing device!")
        od.close_device(id)
        print("device closed \n")

    print("**** exiting program ****")    