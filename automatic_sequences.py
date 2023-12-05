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
            self.flowcell,self.dispense_mode,self.N_mes,self.pH_start,self.pH_end]=config
        if self.dispense_mode=='fit on 5/05/2023':
            self.target_pH_list=[4+5*k/(self.N_mes-1) for k in range(self.N_mes)]
        elif self.dispense_mode=='fixed volumes':
            self.N_mes=11 #10 dispenses de base : 11 mesures
            self.target_volumes_list=[200,100,100,50,50,10,200,200,500,1500] #uL
        else: #cas d'une dispense adaptée sur le pH initial. 
            self.target_pH_list=[self.pH_start+(self.pH_start-self.pH_end)*k/(self.N_mes-1) for k in range(self.N_mes)]
            self.target_acid=50

        #Spectro
        self.lambdas=self.spectro.wavelengths
        self.N_lambda=len(self.lambdas)
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
        self.added_base_uL = [] #itération
        self.added_volumes = [0 for k in range(self.N_mes)]
        
        #Données de sortie
        self.Abs_spectra_corr_dilu = []


    def configure(self):
        #Normalement On doit régler le spectro avant la séquence auto. 
        #Le pH mètre est calibré manuellement aussi 
        #Le pousse seringue doit être mis sur la position zéro ? 
        #On a donc déjà des attributs qui sont open pour les sous systèmes. 
        #Devoir connecter les sous-sytèmes est un signe de non ou mauvais réglage. 

        #arrêt des timers pour consacrer toute la mémoire sur la séquence
        self.ihm.timer1s.stop()
        self.ihm.timer3s.stop()
        #déconnecter les spectres du control panel 
        #self.ihm.timer_spectra continue pour l'affichage des spectres

        #connexion des appareils
        """nc=0
        if self.ihm.spectro_unit.state=='closed':
            self.ihm.spectro_unit.connect()
            nc+=1
        if self.ihm.phmeter.state=='closed':
            self.ihm.phmeter.connect()
            nc+=1
        if self.ihm.syringe_pump.state=='closed':
            self.ihm.syringe_pump.connect()
        if self.ihm.peristaltic_pump.state=='closed':
            self.ihm.peristaltic_pump.connect()

        #vérification que tout est connecté
        if nc==0:
            print("\ntous les instruments sont configurés\n\n    ### Lancement de la séquence de titrage automatique ###\n\n")
                #experiment parameters
        """

        #création de la fenêtre
        self.window_handler.titration_window0=QtWidgets.QMainWindow()
        self.window_handler.titration_window0.show()
        self.window_handler.titration_window1 = TitrationWindow(self.ihm)
        self.window_handler.titration_window1.graphical_setup(self.window_handler.titration_window0)
        self.window_handler.titration_window1.param_init() 

        #graphique
        self.window=self.window_handler.titration_window1

        #timer pour renouvellement du calcul de l'absorbance
        self.timer_display = QtCore.QTimer()
        self.timer_display.setInterval(1000) #10 secondes
        self.timer_display.start()
        
        #config de l'affichage du spectre courant
        #idée : spectre de référence affiché en permanence? 
        self.directSpectrum=self.window_handler.titration_window1.direct_abs.plot([0],[0])
        #mise à jour de l'absorbance
        self.timer_display.timeout.connect(self.updateCurrentSpectrum)

        #actualisation sur le pH mètre
        self.phmeter.voltagechannel.setOnVoltageChangeHandler(self.refresh_pH)
        self.phmeter.activateStabilityLevel()
        self.phmeter.stab_timer.timeout.connect(self.window.refresh_stability_level)
        
        #Pousses seringue
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

        #Mise en attente de la stabilisation
        try:
            self.phmeter.signals.stability_reached.disconnect() #disconnect s'applique sur les QObjects
            #permet de déconnecter la laison dans le cas où on clique plusieurs fois sur le bouton
        except:
            pass
        self.phmeter.signals.stability_reached.connect(self.mesure1_acid) #connection du slot mesure1_acid avec le signal stability_reached
        

    def mesure1_acid(self): #la fonction s'execute une fois, lorsque le pH est stabilisé
        print("passage dans mesure 1 acid")
        #appel
        #self.phmeter.signals.stability_reached.disconnect() #la fonction ne s'exécutera qu'une fois par clic sur "acid OK"

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
        self.SpectraDelta=self.window_handler.titration_window1.delta_all_abs.plot([0],[0])
        self.timer_display.timeout.connect(self.window.updateCurrentSpectrum_delta) #affichage de l'absorbance courante

        #Lancement de la première dispense de base
        self.add_base(1) #premier ajout de base
    
    #Séquence pour ajouter la base
    def add_base(self, N):
        if self.dispense_mode=='fixed volumes':
            self.syringe.dispense(self.volumes[N-1])
        elif self.dispense_mode=='fit on 5/05/2023':
            current=self.pH_mes
            target=self.target_pH_list(N)
            vol=volumeToAdd_uL(current, target, model='fit on 5/05/2023')
            self.syringe.dispense()

    #Séquence d'executions pour chaque ajout de base
    def mesureN(self, N):
        return
    
    #DIRECT
    #Actualisation du spectre en direct
    def updateCurrentSpectrum(self):
        if self.spectro.current_absorbance_spectrum!=None:
            #print("il y a un spectre courant")
            #spectre courant
            self.directSpectrum.setData(self.lambdas,self.spectro.current_absorbance_spectrum)
    
    """#spectre courant sur le graphe en delta 
    def updateCurrentSpectrum_delta(self): #il y a déjà un spectre enregistré
        self.current_absorbance_spectrum_delta=[self.spectro.current_absorbance_spectrum[k]-self.absorbance_spectrum1[k] for k in range(len(self.N_lambda))]
        self.window.delta_all_abs.plot(self.lambdas,self.current_absorbance_spectrum_delta)"""

    def refresh_pH(self,ch,voltage): #arguments immuables
        #print("pH change")
        #print("self=",self,"\nvoltage=",voltage)
        self.phmeter.currentVoltage=voltage        
        pH = volt2pH(self.phmeter.a,self.phmeter.b,voltage)
        self.phmeter.currentPH=pH #actualisation de l'attribut de la classe pHmeter
        self.window_handler.titration_window1.direct_pH.display(pH)
    
    def measure_all_data(self):
        pass

    def add_spectrum(self):
        self.absorbance_spectra.append(self.spectro.current_absorbance_spectrum)


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