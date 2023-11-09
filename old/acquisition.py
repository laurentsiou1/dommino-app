"Module qui contient les fonctions pour enregistrer des spectres"

from oceandirect.OceanDirectAPI import OceanDirectError
from oceandirect.od_logger import od_logger
logger = od_logger()
import numpy as np

#La fonction récupère un spectre issu du moyennage sur le Spectro
#ça fonctionne mais c'est plus lent que de moyenner sur l'ordinateur
def get_spectrum_internal_averaging(device, avg):
    try:
        device.set_scans_to_average(avg) #avg est le nombre de moyennage
        #numb_pixel = len(device.get_formatted_spectrum()) #nb de points du spectre
        #spectra_m = [0 for x in range(numb_pixel)]
        spectra_m = device.get_formatted_spectrum() #acquisition du spectre

    except OceanDirectError as e:
        logger.error(e.get_error_details())
    
    return spectra_m

#Récupère autant de spectres que N_avg sur le spectro
#Fonction vérifiée qui fonctionne. Plus rapide que de faire le moyennage sur le spectro
def get_spectra(device, avg):
    try:
        device.set_scans_to_average(1)
        numb_pixel = len(device.get_formatted_spectrum())
        spectra_m = [[0 for x in range(numb_pixel)] for y in range(avg)]

        for i in range(avg):
            spectra_m[i] = device.get_formatted_spectrum()

    except OceanDirectError as e:
        logger.error(e.get_error_details())    

    return spectra_m 

#retourne la moyenne de l'ensemble des spectres
def average_spectra(spectra): 
    sp = np.array(spectra)
    avg_sp=np.mean(sp,0)
    avg_sp.tolist()
    return avg_sp

#intensité maximale d'un spectre
def get_max_intensity(spectrum):
    sp = np.array(spectrum)  #conversion en tableau numpy
    Imax=max(sp)
    print("Intensité maximale sur le spectre (unit counts) :", Imax)
    return Imax

def get_optimal_integration_time(spectra,int_time_us):
    Imax= get_max_intensity(spectra)
    optimal_int_time_us = 1000*int(int_time_us*15/Imax) #15000 unit count correspond au ST. 
    #Le capteur a une résolution de 14bit = 16300... unit count
    #ça doit être un multiple de 1000 pour être entier en millisecondes. 
    return optimal_int_time_us

def set_optimal_integration_time(device,spectra,int_time_us):
    Imax= get_max_intensity(spectra)
    optimal_int_time_us = int(int_time_us*15000/Imax) #15000 unit count correspond au ST. 
    #Le capteur a une résolution de 14bit = 16300... unit count
    device.set_integration_time(optimal_int_time_us)
    return optimal_int_time_us
