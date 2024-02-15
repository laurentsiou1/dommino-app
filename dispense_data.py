"""
Module appelé pendant la séquence pour obtenir les bons volumes à dispenser

Fit polynomial de degré 5 sur la courbe de dispense à la pipette du 23/01/2024
Fit fait sur excel
"""
import numpy as np
import math

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

#Fonctions pour la répartition des points de pH
def f_ratio_deprotone(x,m,lK):  #sigmoide modelise f1 f2 dans le traitement 
    return 10**(m*(x-lK))/(1+10**(m*(x-lK)))

def derivee_f(x,m,lK):  #dérivée de f_ratio_deprotonee
    return m*math.log(10)*10**(m*(x-lK))/((1+10**(m*(x-lK)))**2)

def evolution_absorbance(A1,m1,lK1,A2,m2,lK2,pH):  #fonction
    #return max(A1*derivee_f(pH,m1,lK1),A2*derivee_f(pH,m2,lK2))
    return max(A1[0]*derivee_f(pH,m1,lK1)+A2[0]*derivee_f(pH,m2,lK2),A1[1]*derivee_f(pH,m1,lK1)+A2[1]*derivee_f(pH,m2,lK2))

def delta_pH(A1,m1,lK1,A2,m2,lK2,pH,pH0,max_delta):
    return max_delta*evolution_absorbance(A1,m1,lK1,A2,m2,lK2,pH0)/evolution_absorbance(A1,m1,lK1,A2,m2,lK2,pH)

#données issues de l'optim sur les donnees du 26/01/2024
#A1=[0.1317,0.0419],m1=0.416,lK1=3.90,A2=[0.0727,0.1392],m2=0.197,lK2=9.94,pH0=6.486
absorbance_model_26_01_2024 = [[0.1317,0.0419],0.416,3.90,[0.0727,0.1392],0.197,9.94,6.486]

class ReferenceData:
    #Cette classe modélise un titrage qui peut servir de référence à plusieurs niveaux
    
    """def init(self,om_type,C):
        self.om_type=om_type
        self.concentration_ppmC=C"""

    def __init__(self,A1,m1,lK1,A2,m2,lK2):  #initialisation par les fonctions de référence
        self.A1=A1#maximum de la fonction A1
        self.m1=m1
        self.lK1=lK1
        self.A2=A2#maximum de la fonction A2
        self.m2=m2
        self.lK2=lK2

    ### Calcul d'espacement des courbes en pH
    #donnees de reference : 26/01/2024

    def evolution_absorbance(self,pH):   #représente la maximum d'évolution avec le pH\
        # entre les deux absorbance A(lambda1) et A(lambda2) qui correspondent aux longueurs d'onde\
        # d'intérêt pour les COOH et PhOH
        #max(A1(lambda1)*f1',A2(lambda2)*f2')
        return max(self.A1[0]*derivee_f(pH,self.m1,self.lK1)+self.A2[0]*derivee_f(pH,self.m2,self.lK2),self.A1[1]*derivee_f(pH,self.m1,self.lK1)+self.A2[1]*derivee_f(pH,self.m2,self.lK2))

    def min_abs_variation(self):
        import scipy.optimize 
        self.pH0 = scipy.optimize.fmin(lambda x: self.evolution_absorbance(x), 6)   #minimum de variation d'absorbance
        return self.pH0

    def delta_pH(self,pH,max_delta):
        #renvoie l'écart en pH en fonction du pH pour satisfaire le critère d'écart maximum\
        #entre deux valeurs de pH. 
        return max_delta*self.evolution_absorbance(self.pH0)/self.evolution_absorbance(pH)
    
    def plot_functions(self,max_delta=0.5):
        import matplotlib.pyplot as plt
        n=100
        x=np.linspace(3.5,10.5,100)
        F1=np.zeros_like(x)
        F2=np.zeros_like(x)
        G1=np.zeros_like(x)
        G2=np.zeros_like(x)
        y=np.zeros_like(x)
        z=np.zeros_like(x)
        for k in range(n):
            F1[k], F2[k] = self.A1[0]*f_ratio_deprotone(x[k],self.m1,self.lK1)+self.A2[0]*f_ratio_deprotone(x[k],self.m2,self.lK2), self.A1[1]*f_ratio_deprotone(x[k],self.m1,self.lK1)+self.A2[1]*f_ratio_deprotone(x[k],self.m2,self.lK2)
            G1[k], G2[k] = self.A1[0]*derivee_f(x[k],self.m1,self.lK1)+self.A2[0]*derivee_f(x[k],self.m2,self.lK2), self.A1[1]*derivee_f(x[k],self.m1,self.lK1)+self.A2[1]*derivee_f(x[k],self.m2,self.lK2)
            y[k]=self.evolution_absorbance(x[k])
            z[k]=self.delta_pH(x[k],max_delta)
        fig, ((ax1, ax2),(ax3,ax4)) = plt.subplots(2,2)
        fig.suptitle('courbe delta pH sur données du 26/01/2024')
        ax1.plot(x, F1, x, F2)
        ax1.set_title("modélisation max(A1)*f1, max(A2)*f2")
        ax2.plot(x, G1, x, G2)
        ax2.set_title("variation d'absorbance")
        ax3.plot(x, y)
        ax3.set_title("max d'augmentation sur l'absorbance")
        ax3.set(xlabel="pH")
        ax4.plot(x, z)
        ax4.set_title("pas de pH à viser avec maximum fixé à %f" %max_delta)
        ax4.set(xlabel="pH")
        plt.show()

if __name__=="__main__":
    #obtention de la courbe de référence
    dataSet = ReferenceData(A1=[0.1317,0.0419],m1=0.416,lK1=3.90,A2=[0.0727,0.1392],m2=0.197,lK2=9.94)    #26/01/2024
    #d'après le fichier matlab
    pH0 = dataSet.min_abs_variation()
    print(pH0)
    dataSet.plot_functions(0.8)    #max_delta

    """
    #Plot dispense function
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

    """
    while(True):
        ph0, ph1 = input("ph courant, ph cible: ").split()
        x0=float(ph0);x1=float(ph1)
        print("current: ", ph0)
        print("target: ", ph1)
        print("volume à ajouter : ", get_volume_to_dispense_uL(x0,x1))"""
