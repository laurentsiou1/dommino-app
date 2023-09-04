"Module pour l'affichage de graphes et de données"

import numpy as np
import matplotlib.pyplot as plt
from oceandirect.OceanDirectAPI import OceanDirectAPI, Spectrometer



def plot_spectrum(wl, spectrum):
    sp = np.array(spectrum)#tracé
    plt.plot(wl,sp)
    plt.ylabel("Spectre d'intensité (unit counts)")
    plt.xlabel("Longueur d'onde (nm)")
    #print("isinteractive=",plt.isinteractive())
    plt.plot(block=False)
    return 1
