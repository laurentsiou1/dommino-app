"""
Module appelé pendant la séquence pour obtenir les bons volumes à dispenser

Fit polynomial de degré 5 sur la courbe de dispense à la pipette du 23/01/2024
Fit fait sur excel
"""
import numpy as np

#data du 23/01/2024
v_23_01_2024 = np.array([0,100,200,	300,400,500,550,600,650,700,750,800,850,900,950,1050,1150,1250,1450,1850])
pH_dommino_23_01_2024=np.array([4.01,	4.15,	4.27, 4.5, 4.82,	5.49, 5.85,	6.15,	6.5,	6.91,	7.33,	7.72,	8.18,	8.54,	8.75,	9.19,	9.4	, 9.51,	9.74,	10.03])
pH_HI5221_23_01_2024=np.array([4.09,	4.21,	4.36,	4.56,	4.9,	5.59,	5.98,	6.34,	6.69,	7.09,	7.38,	7.75,	8.29,	8.69,	8.92,	9.32,	9.54,	9.69,	9.91,	10.19])

#fit sur pH-mètre dommino le 23/01/2024
param_dommino_23_01_2024 = [3.9266, -133.37, 1792.2, -11910., 39276., -51141.] 

def polynomial_5th_order(x, a5, a4, a3, a2, a1, a0):
    #x correspond au pH
    if type(x)!=list and type(x)!=np.ndarray:
        v=a5*x**5+a4*x**4+a3*x**3+a2*x**2+a1*x+a0
    else:
        v=[]
        for ph in x:
            v.append(a5*ph**5+a4*ph**4+a3*ph**3+a2*ph**2+a1*ph+a0)
    return v

def dispense_function_uL(pH, model='polynomial 5th order', ref_data='dommino 23/01/2024'):
    if model=='polynomial 5th order' and ref_data=='dommino 23/01/2024':
        (a5, a4, a3, a2, a1, a0) = tuple(param_dommino_23_01_2024)
        v = polynomial_5th_order(pH, a5, a4, a3, a2, a1, a0)
    return v

def get_volume_to_dispense_uL(current_pH, target_pH):
    return dispense_function_uL(target_pH)-dispense_function_uL(current_pH)


if __name__=="__main__":
    import matplotlib.pyplot as plt

    """
    #Plot
    plt.scatter(pH_dommino_23_01_2024, v_23_01_2024, label='dommino 23/01', color='black')
    x=np.linspace(3.5,10.5,100)
    y=dispense_function_uL(x)
    plt.plot(x,y,color='red')
    plt.xlabel('Volume (mL)')
    plt.ylabel('pH')
    plt.title('Fit sur les données du 23/01/2024 avec les deux pH-mètres')
    plt.legend()
    plt.show()
    """

    while(True):
        ph0, ph1 = input("ph courant, ph cible: ").split()
        x0=float(ph0);x1=float(ph1)
        print("current: ", ph0)
        print("target: ", ph1)
        print("volume à ajouter : ", get_volume_to_dispense_uL(x0,x1))
