"""programme pour extraire les données de référence pour la dispense de base
Données du 5/05/2023 avec le titreur metrohm
Il faut obtenir des paramètres qu'on recopiera dans le programme concerné. Ce programme n'est pas appelé par le reste des programmes."""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


x0_4_05 = 0.3 #4/05/2023
x0_5_05 = 0.38 #5/05/2023

volume_4_05 = np.array([ 0,  210,    317,    439,    592,    869.5,  1235,   2138,   4026.5,    5162    ])/1000  #4/05/2023
volume_5_05 = np.array([0,0.112,0.204,0.288,0.373,0.4205,0.482,0.5995,0.763,0.9515,1.4205,2.9205]) #5/05/2023

pH_data_4_05 = np.array([    4.3,	4.7,	5.5,	6.3,	6.8,	7.2,	7.4,	7.8,	8.52,   9   ]) #4/05/2023
pH_data_5_05 = np.array([4.1,4.22,4.42,4.75,5.42,6,6.45,6.95,7.55,8,8.4,8.8]) #5/05/2023

def experimental_data(date='4_05'):
    if date=='4_05':
        return 

def log_acid_4_05(x, y0, ba, ca):
    return y0-ca*np.log10(1+(x0_4_05-x)/ba)

def log_base_4_05(x, y0, bb, cb):
    return y0+cb*np.log10(1+(x-x0_4_05)/bb)

def logarithmic_2parts_4_05(x, y0, ba, ca, bb, cb):
    return np.piecewise( x, [x<=x0_4_05, x>x0_4_05], [lambda x: log_acid_4_05(x, y0, ba, ca), lambda x: log_base_4_05(x, y0, bb, cb)])


def log_acid_5_05(x, y0, ba, ca):       #5/05/2023
    return y0-ca*np.log10(1+(x0_5_05-x)/ba)
def log_base_5_05(x, y0, bb, cb):
    return y0+cb*np.log10(1+(x-x0_5_05)/bb)
def logarithmic_2parts_5_05(x, y0, ba, ca, bb, cb):
    return np.piecewise( x, [x<=x0_5_05, x>x0_5_05], [lambda x: log_acid_5_05(x, y0, ba, ca), lambda x: log_base_5_05(x, y0, bb, cb)])


def fit_titration_curve(volume, pH_data):
    # Fit the titration curve to the sigmoidal function
    initial_guess = [5,0.01,1,0.1,2] #[3.5, 9, 0.5, 0.2] pour sigmoide
    params, covariance = curve_fit(logarithmic_2parts_5_05, volume, pH_data, p0=initial_guess, bounds=(0,[10,1,10,1,10])) #sigmoidal_function, bounds=([0,9.4,0,0],[10,9.6,1,1]))
    return params

def plot_titration_curve(volume, pH_data, fit_params):
    # Plot the titration curve and the fitted curve
    plt.scatter(volume, pH_data, label='Experimental Data', color='blue')
    fitted_curve = logarithmic_2parts_5_05(volume, *fit_params) #sigmoidal_function(volume, *fit_params)
    pm=tuple(fit_params+[x0_5_05])
    print(pm)
    plt.plot(volume, fitted_curve, label='fit: y0=%5.3f, ba=%5.3g, ca=%5.3f, bb=%5.3g, cb=%5.3f, x0_5_05=%5.3f mol/L' % tuple(fit_params+[x0_5_05]), color='red')
    plt.xlabel('Volume (mL)')
    plt.ylabel('pH')
    plt.title('Fitted Acid-Base Titration Curve')
    plt.legend()
    plt.show()

def calculate_coefs(volume, pH_data, x0): 
    # Fit the titration curve
    fit_params = fit_titration_curve(volume, pH_data)
    print(fit_params)
    # Plot the titration curve and the fitted curve
    plot_titration_curve(volume, pH_data, fit_params) #[3,9,0.4,0.26]
    #plot_titration_curve(volume, pH_data, [3.45743466, 8.54267733, 0.4509939,  0.19647047])

def volumeToAdd_uL(current, target, model='5_05'): #pH courant et cible, modèle choisi par défaut le 5/05
    if model=='5_05':
        x0, coefs = 0.38, [5.44910654, 0.0393133,  1.34849333, 0.03735145, 1.92836309]
    elif model=='standard':
        x0, coefs = 0.35, [0,0,0,0,0] #à compléter
    return (inverse_function(target,coefs,x0)-inverse_function(current,coefs,x0))*1000  #résultat en uL
    

def inverse_function(pH,coefs,x0):
    [y0, ba, ca, bb, cb] = coefs
    if type(pH)!=list:
        if pH<=y0:
            x=x0-ba*(10**((y0-pH)/ca)-1)
        else:
            x=x0+bb*(10**((pH-y0)/cb)-1)
    else:
        x=[]
        for y in pH:
            if y<=y0:
                x.append(x0-ba*(10**((y0-y)/ca)-1))
            else:
                x.append(x0+bb*(10**((y-y0)/cb)-1))
    return x

def plot_inverse_function(coefs1,coefs2):
    pH=np.linspace(4,9,100)
    vol1=inverse_function(pH,coefs1,x0_5_05)
    vol2=inverse_function(pH,coefs2,x0_4_05)
    plt.scatter(pH_data_4_05, volume_4_05, label='4/05', color='blue')
    plt.scatter(pH_data_5_05, volume_5_05, label='5/05', color='black')
    plt.plot(pH, vol1, color='red')
    plt.plot(pH, vol2, color='green')
    plt.xlabel('pH')
    plt.ylabel('Volume (mL)')
    plt.title('Fitted Acid-Base Titration Curve')
    plt.legend()
    plt.show()


if __name__ == "__main__":
    #5/05
    #coefs_5_05=[5.67491592, 0.04336829, 1.61873639, 0.04047191, 1.82865151]
    #coefs_5_05=[6.29078491, 0.03225815, 1.84654972, 0.43935166, 2.390873  ] #n°2
    coefs_5_05 = [5.44910654, 0.0393133,  1.34849333, 0.03735145, 1.92836309]
    #4/05
    coefs_4_05=[5.35840565, 0.01839799, 0.85479386, 0.06805281, 1.84207387]
    
    #plot_inverse_function(coefs_5_05,coefs_4_05) 

    
    #calculate_coefs(volume_5_05, pH_data_5_05, x0_5_05)

#la courbe doit recouvrir complètement l'intervalle [4,9] en pH pour ne pas avoir des dispenses infinies. 
#Par sécurité, les dispenses doivent être plus faibles que exactes. Et il faut pouvoir corriger
#voici les coefficients obtenus par régression en cherchant une fonction en deux parties sous forme de log
#elle est continue au point f(x0)=y0. 
#x0 est imposé x0=0.4
#On pourrait relancer la régression en recalculant x0 avec précision avec la méthode des tangentes. Pour cela il faut connaître la 
#fonction. Or une sigmoide ne convient pas. 