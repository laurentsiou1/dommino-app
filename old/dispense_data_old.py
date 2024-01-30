"""programme pour extraire les données de référence pour la dispense de base
Données du 23/01/2024 avec ph mètre hanna et ph mètre phidget adp1000 electyrode oakton
Il faut obtenir des paramètres qu'on recopiera dans le programme concerné. 
Ce programme n'est pas appelé par le reste des programmes.
A moins que l'on décide de programmer un calcul de fit qui s'adapte progressivement 
au fur et à mesure du titrage"""

"""import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def sigmoid(v,v_eq,a,b,k=2):
    #k est l'ordre
    #modèle : pH = a*(1/(1+10**(k*(Véq-V)))+b
    #b=pH(-infini), a=pH(+infini)-pH(-infini), Véq : volume équivalent, k : pente de la courbe
    if type(v)!=list and type(v)!=np.ndarray:
        pH = a/(1+10**(k*(v_eq-v)))+b
    else:
        pH=[]
        for vol in v:
            pH.append(a/(1+10**(k*(v_eq-vol)))+b)
    return pH

def inverse_function(pH,v_eq, a, b, k):
    if type(pH)!=list and type(pH)!=np.ndarray:
        x=v_eq-(1/k)*np.log10(a/(pH-b)-1)
    else:
        x=[]
        for y in pH:
            x.append(v_eq-(1/k)*np.log10(a/(y-b)-1))
    return x

def fit_curve(volume, pH_data):
    initial_guess = [0.7,8,4,2]
    params, covariance = curve_fit(sigmoid, volume, pH_data, p0=initial_guess, bounds=(0, [1,10,10,10]))
    print(params)
    return params

def plot_curve(volume, pH_data, params):
    #exp data
    plt.scatter(volume, pH_data, label='Experimental Data', color='blue')
    
    #fit
    v_eq,a,b,k=params[0],params[1],params[2],params[3]
    fitted_curve = sigmoid(volume, v_eq, a, b, k) 
    plt.plot(volume, fitted_curve, label='fit: Veq=%5.3f, a=%5.3g, b=%5.3f, k=%5.3g' %(v_eq,a,b,k), color='red')
    
    #manual curve
    #x = np.linspace(0,2,100)
    #y = np.array([sigmoid(vol,0.82,5.89,4.06,2.55) for vol in x])
    #plt.plot(x,y, color='green')
    
    plt.xlabel('Volume (mL)')
    plt.ylabel('pH')
    plt.title('Fitted Acid-Base Titration Curve')
    plt.legend()
    plt.show()

def volumeToAdd_uL(current, target, model='23_01'): #pH courant et cible, modèle choisi par défaut le 5/05
    if model=='23_01':
        coefs = [0.7, 3, 0.3, 2]
    elif model=='standard':
        coefs = [0.7, 3, 0.3, 2] #à compléter
    return (inverse_function(target,coefs)-inverse_function(current,coefs))*1000  #résultat en uL

def plot_inverse_function(params):
    v_eq,a,b,k=params[0],params[1],params[2],params[3]
    pH=np.linspace(3,11,100)
    vol=inverse_function(pH,v_eq,a,b,k)
    plt.scatter(pH, vol, label='date')
    plt.plot(pH, vol)
    plt.xlabel('pH')
    plt.ylabel('Volume (mL)')
    plt.title('dispense curve after fit')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    
    #x = np.linspace(0,2,100)
    #y = np.array([sigmoid(vol,0.7,3.3,0.3,2) for vol in x])
    #plt.plot(x,y)
    #plt.show()

    #v_05_23 = np.array([0,250,400,500,570,630,680,740,820,1020,1520])/1000
    #pH_05_23 = np.array([4.054,4.292,4.593,4.751,5.1,5.553,5.927,6.303,6.832,8.623,9.838])

    v_23_01_2024 = np.array([0,100,200,	300,400,500,550,600,650,700,750,800,850,900,950,1050,1150,1250,1450,1850])/1000
    pH_dommino_23_01_2024=np.array([4.01,	4.15,	4.27, 4.5, 4.82,	5.49, 5.85,	6.15,	6.5,	6.91,	7.33,	7.72,	8.18,	8.54,	8.75,	9.19,	9.4	, 9.51,	9.74,	10.03])
    pH_HI5221_23_01_2024=np.array([4.09,	4.21,	4.36,	4.56,	4.9,	5.59,	5.98,	6.34,	6.69,	7.09,	7.38,	7.75,	8.29,	8.69,	8.92,	9.32,	9.54,	9.69,	9.91,	10.19])
    #params_dommino_23_01_2024=fit_curve(v_23_01_2024,pH_dommino_23_01_2024)
    #params_HI5221_23_01_2024=fit_curve(v_23_01_2024,pH_HI5221_23_01_2024)
    params_dommino_23_01_2024=[0.692,6.006,3.892,2.391]
    params_HI5221_23_01_2024=[0.690,6.153,3.927,2.322]

    #PLOT
    volume=np.linspace(0,2,100)    #entre 0 et 2mL

    #exp data
    plt.scatter(v_23_01_2024, pH_dommino_23_01_2024, label='dommino 23/01', color='blue')
    plt.scatter(v_23_01_2024, pH_HI5221_23_01_2024, label='HI5221 23/01', color='red')

    #fit
    (v_eq,a,b,k)=tuple(params_dommino_23_01_2024)   #dommino 23/01/2024
    fit_dommino_23_01 = sigmoid(volume, v_eq, a, b, k) 
    plt.plot(volume, fit_dommino_23_01, label='fit: Veq=%5.3f, a=%5.3g, b=%5.3f, k=%5.3g' %(v_eq,a,b,k), color='blue')

    (v_eq,a,b,k)=tuple(params_HI5221_23_01_2024)   #HI5221 23/01/2024
    fit_HI5221_23_01 = sigmoid(volume, v_eq, a, b, k) 
    plt.plot(volume, fit_HI5221_23_01, label='fit: Veq=%5.3f, a=%5.3g, b=%5.3f, k=%5.3g' %(v_eq,a,b,k), color='red')

    plt.xlabel('Volume (mL)')
    plt.ylabel('pH')
    plt.title('Fit sur les données du 23/01/2024 avec les deux pH-mètres')
    plt.legend()
    plt.show()

    #PLOT INVERSE FUNCTION
    pH=np.linspace(4,10,100)

    plt.scatter(pH_dommino_23_01_2024, v_23_01_2024, label='dommino 23/01', color='blue')
    plt.scatter(pH_HI5221_23_01_2024, v_23_01_2024, label='HI5221 23/01', color='red')
    
    (v_eq,a,b,k)=tuple(params_dommino_23_01_2024)   #dommino 23/01/2024
    vol_dommino_23_01 = inverse_function(pH,v_eq,a,b,k)
    plt.plot(pH, vol_dommino_23_01, label='fit: Veq=%5.3f, a=%5.3g, b=%5.3f, k=%5.3g' %(v_eq,a,b,k), color='blue')

    (v_eq2,a2,b2,k2)=tuple(params_HI5221_23_01_2024)   #HI5221 23/01/2024
    vol_HI5221_23_01 = inverse_function(pH, v_eq2, a2, b2, k2) 
    plt.plot(pH, vol_HI5221_23_01, label='fit: Veq=%5.3f, a=%5.3g, b=%5.3f, k=%5.3g' %(v_eq2,a2,b2,k2), color='red')

    plt.xlabel('pH')
    plt.ylabel('Volume (mL)')
    plt.title('dispense curve after fit')
    plt.legend()
    plt.show()

    


#la courbe doit recouvrir complètement l'intervalle [4,9] en pH pour ne pas avoir des dispenses infinies. 
#Par sécurité, les dispenses doivent être plus faibles que exactes. Et il faut pouvoir corriger
#voici les coefficients obtenus par régression en cherchant une fonction en deux parties sous forme de log
#elle est continue au point f(x0)=y0. 
#x0 est imposé x0=0.4
#On pourrait relancer la régression en recalculant x0 avec précision avec la méthode des tangentes. Pour cela il faut connaître la 
#fonction. Or une sigmoide ne convient pas. 

avant le 25/01/2024"""