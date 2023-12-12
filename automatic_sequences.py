"""programme principal séquence de titrage
Il gère toutes les actions propres à la séquence
En lien entre les instruments et la fenêtre titration_window
"""

from PyQt5 import QtCore, QtWidgets

from IHM import IHM
from titrationWindow import TitrationWindow
from windowHandler import WindowHandler

from pHmeter import *
from syringePump import *


class TitrationSequence:
    
    def __init__(self, ihm:IHM, win:WindowHandler, config):
        self.ihm=ihm
        self.spectro=ihm.spectro_unit
        self.phmeter=ihm.phmeter
        self.syringe=ihm.syringe_pump
        self.pump=ihm.peristaltic_pump
        self.window_handler=win

        #Données de config
        [self.experience_name,self.description,self.OM_type,self.concentration,self.fibers,\
            self.flowcell,self.dispense_mode,self.N_mes,self.pH_start,self.pH_end,self.saving_folder]=config
        if self.dispense_mode=='fit on 5/05/2023':
            self.target_pH_list=[4+5*k/(self.N_mes-1) for k in range(self.N_mes)]
        elif self.dispense_mode=='fixed volumes':
            self.target_volumes_list=[100,50]
            #bonne liste [200,100,100,50,50,10,200,200,500,1500] #uL
            self.N_mes=len(self.target_volumes_list)+1  #bon nombre 11 #10 dispenses de base : 11 mesures
        else: #cas d'une dispense adaptée sur le pH initial. 
            self.target_pH_list=[self.pH_start+(self.pH_start-self.pH_end)*k/(self.N_mes-1) for k in range(self.N_mes)]
            self.target_acid=50

        #Spectro
        #2self.lambdas=self.spectro.wavelengths
        
        #ref initial
        self.backgroundSpectrum_init=[]
        self.referenceSpectrum_init=[]
        #ref fin
        self.backgroundSpectrum_end=[]
        self.referenceSpectrum_end=[]

        #tableaux à compléter pendant la séquence. Variable locales
        self.pH_mes = [0 for k in range(self.N_mes)]
        self.absorbance_spectra = [[] for k in range(self.N_mes)]
        self.absorbance_spectrum1 = None
        self.added_acid_uL = 0
        self.added_volumes = [0 for k in range(self.N_mes)]
        self.total_added_volume=0
        
        #itération
        self.added_base_uL = []
        self.current_measure = 1
        
        #Données de sortie
        self.Abs_spectra_corr_dilu = []

        #connexion des appareils
        #listing des appareils connectés
        print("\n\n### Lancement de la séquence de titrage automatique ###\n\n")
        if self.ihm.phmeter.state=='closed':
            try:
                self.ihm.phmeter.connect()
                print("pH-meter connected\n")
            except:
                pass
        if self.ihm.syringe_pump.state=='closed':
            try:
                self.ihm.syringe_pump.connect()
                print("syringe pump connected\n")
            except:
                pass
        if self.ihm.spectro_unit.state=='closed':
            try:
                self.ihm.spectro_unit.connect()
                print("spectrometer connected\n")
            except:
                pass
        if self.ihm.peristaltic_pump.state=='closed':
            try:
                self.ihm.peristaltic_pump.connect()
                print("peristaltic pump connected\n")
            except:
                pass
        self.lambdas=self.spectro.wavelengths
        self.N_lambda=len(self.lambdas)

    def configure(self):
        #Normalement On doit régler le spectro avant la séquence auto. 
        #Le pH mètre est calibré manuellement aussi 
        #Le pousse seringue doit être mis sur la position zéro ? 
        #On a donc déjà des attributs qui sont open pour les sous systèmes. 
        #Devoir connecter les sous-sytèmes est un signe de non ou mauvais réglage. 

        #arrêt des timers liés à control panel. 
        # pour consacrer toute la mémoire sur la séquence
        self.ihm.timer1s.stop()
        self.ihm.timer3s.stop()

        #création de la fenêtre
        self.window_handler.titration_window0=QtWidgets.QMainWindow()
        self.window_handler.titration_window0.show()
        self.window_handler.titration_window1 = TitrationWindow(self.ihm)
        self.window_handler.titration_window1.graphical_setup(self.window_handler.titration_window0)
        self.window_handler.titration_window1.param_init() 
        time.sleep(3)

        #graphique
        self.window=self.window_handler.titration_window1

        #actualisation sur le pH mètre
        self.phmeter.voltagechannel.setOnVoltageChangeHandler(self.refresh_pH)
        self.phmeter.activateStabilityLevel()
        self.phmeter.stab_timer.timeout.connect(self.window.refresh_stability_level)
        
        #Pousses seringue
        self.syringe.full_refill()
        self.window.base_level_number.setText("%d uL" %self.syringe.base_level_uL)
        self.window.base_level_bar.setProperty("value", self.syringe.base_level_uL)
        self.window.ajout_ok.clicked.connect(self.acid_added)


    def acid_added(self): #déclenchée lorsque l'on a ajouté l'acide et cliqué sur OK
        #modif et affichage volume
        vol=self.window.added_acid.value()
        self.added_acid_uL=vol
        self.added_volumes[0]=vol
        self.window.append_vol_in_table(1,vol)
        print("added_volumes=",self.added_volumes)

        try:
            self.phmeter.signals.stability_reached.disconnect() #disconnect s'applique sur les QObjects
            #permet de déconnecter la laison dans le cas où on clique plusieurs fois sur le bouton
        except:
            pass
        self.phmeter.signals.stability_reached.connect(self.mesure1_acid) #connection du slot mesure1_acid avec le signal stability_reached
        

    def mesure1_acid(self): 
        #la fonction s'execute une fois après un clic sur OK, lorsque le pH est stabilisé
        #print("passage dans mesure 1 acid")

        #mesure
        spec=self.spectro.current_absorbance_spectrum
        pH=self.phmeter.currentPH
        
        #ajout dans les tableaux
        self.absorbance_spectrum1=spec
        self.absorbance_spectra[0]=spec
        self.pH_mes[0]=pH
        print("pH_mes=",self.pH_mes)

        #affichage pH
        self.window.append_pH_in_table(1,pH)
        
        #graphe en delta
        #self.window.SpectraDelta=self.window_handler.titration_window1.delta_all_abs.plot([0],[0])
        self.window.timer_display.timeout.connect(self.window.updateCurrentSpectrum_delta) #affichage de l'absorbance courante
        #¶self.window.delta_all_abs.plot(self.lambdas,self.window.current_absorbance_spectrum_delta)

        #Lancement de la première dispense de base
        try: #On déconnecte le slot d'actualisation de valeur du pH
            self.phmeter.signals.stability_reached.disconnect() #disconnect s'applique sur les QObjects
            #permet de déconnecter la laison dans le cas où on clique plusieurs fois sur le bouton
        except:
            pass
        
        self.current_measure=2
        self.add_base() #premier ajout de base correspond à la mesure n°2
        self.phmeter.signals.stability_reached.connect(self.mesureN)
    
    #Séquence pour ajouter la base
    def add_base(self):
        N=self.current_measure
        if self.dispense_mode=='fixed volumes':
            vol=self.target_volumes_list[N-2]
            self.syringe.dispense(vol)
        elif self.dispense_mode=='fit on 5/05/2023':
            current=self.pH_mes[N-2] #lors de la mesure 1 de base, le pH est pH_mes[0]
            target=self.target_pH_list[N-1]
            vol=volumeToAdd_uL(current, target, model='fit on 5/05/2023')
            self.syringe.dispense(vol)
        
        #ajout sur le tableau
        self.added_volumes[N-1]=vol
        self.window.append_vol_in_table(N,vol) #N numéro de mesure

        #niveau de la seringue
        self.window.base_level_bar.setProperty("value", self.syringe.base_level_uL)
        self.window.base_level_number.setText("%d uL" % self.syringe.base_level_uL)

        print("added_volumes=",self.added_volumes)

    #Séquence d'executions pour chaque ajout de base
    def mesureN(self):
        try: #On déconnecte le slot d'actualisation de valeur du pH
            self.phmeter.signals.stability_reached.disconnect() #le signal de stabilité 
            #de l'electrode ne pourra enclencher la fonction  
        except:
            pass

        N=self.current_measure
        #mesure
        spec=self.spectro.current_absorbance_spectrum
        pH=self.phmeter.currentPH
        self.pH_mes[N-1]=pH

        #ajout dans les tableaux
        self.absorbance_spectra[N-1]=spec

        #affichage pH
        self.window.append_pH_in_table(N,pH) #N numéro de la mesure
        time.sleep(2) #pour laisser le temps d'afficher 

        #graphe en delta
        print("mesureN",np.shape(self.lambdas),np.shape(self.window.current_absorbance_spectrum_delta))
        a=self.window.delta_all_abs.plot([0],[0],pen='g')
        a.setData(self.lambdas,self.window.current_absorbance_spectrum_delta)
        

        #Quand on a mesuré, on passe au numéro suivant, 
        if N!=self.N_mes:
            self.current_measure+=1
            self.add_base() 
            self.phmeter.signals.stability_reached.connect(self.mesureN) #mise en attente pour mesure suivante
        else: #on est sur la dernière mesure
            self.ihm.saving_folder
            #actions à réaliser à la fin du titrage
            self.total_added_volume=sum(self.added_volumes)
            self.window.append_total_vol_in_table(self.total_added_volume)

    #DIRECT

    def refresh_pH(self,ch,voltage): #arguments immuables
        #print("pH change")
        #print("self=",self,"\nvoltage=",voltage)
        self.phmeter.currentVoltage=voltage        
        pH = volt2pH(self.phmeter.a,self.phmeter.b,voltage)
        self.phmeter.currentPH=pH #actualisation de l'attribut de la classe pHmeter
        self.window.direct_pH.display(pH)

    """def add_spectrum(self):
        self.absorbance_spectra.append(self.spectro.current_absorbance_spectrum)"""


    def correct_spectra_from_dilution(self,spectra,dilution_factors):
        #attention il y a un log! Il faut revoir la formule.
        corrected_spectra=[]
        for k in range(self.N):
            corrected_spectra[k]=spectra[k]*dilution_factors[k] 

if __name__=="__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    itf=IHM()
    win=WindowHandler()

    ui.setupUi(MainWindow)
    MainWindow.show()        
    sys.exit(app.exec_())