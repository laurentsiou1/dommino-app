"""Module pour modifier et calculer des données
Contient des fonctions liées au spectro mais ne s'appliquant pas directement"""

import numpy as np
import matplotlib.pyplot as plt
import math

#retourne la moyenne de l'ensemble des spectres
def average_spectra(spectra): 
    sp = np.array(spectra)
    a=np.mean(sp,0)
    avg_spectra=a.tolist()
    return avg_spectra
#intensité maximale de plusieurs spectres
def max_intensity(spectra):
    l=np.zeros(1)
    for s in spectra:
        arr=np.array(s)
        m=max(arr)
        l=np.append(l,m)
    Imax=max(l)
    print("Intensité maximale sur l'ensemble des spectres (unit counts) :", Imax)
    return Imax

def get_optimal_integration_time(spectra,int_time_us):
    Imax= max_intensity(spectra)
    optimal_int_time_us = 1000*int(int_time_us*15/Imax) #15000 unit count correspond au ST. 
    #Le capteur a une résolution de 14bit = 16300... unit count
    #ça doit être un multiple de 1000 pour être entier en millisecondes. 
    return optimal_int_time_us

#Les spectres entrés sont supposés corrigés du bruit d'obscurité et de la non linéarité du capteur
def intensity2absorbance(spectrum, blanc_ref):
    if spectrum!=None and blanc_ref!=None:
        for intensity in blanc_ref:
            if intensity==0:
                intensity=1 #pour éviter une division par zéro
        abs_spectrum = [1-spectrum[k]/blanc_ref[k] for k in range(len(spectrum))]
    else:
        abs_spectrum=None
    return abs_spectrum

def plot_spectrum(wl, spectrum):
    sp = np.array(spectrum)#tracé
    plt.plot(wl,sp)
    plt.ylabel("Spectre d'intensité (unit counts)")
    plt.xlabel("Longueur d'onde (nm)")
    #print("isinteractive=",plt.isinteractive())
    plt.plot(block=False)
    return 1

if __name__ == "__main__":
    Imax=max_intensity([[1,2],[3,4]])