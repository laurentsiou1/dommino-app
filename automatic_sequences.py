"""programme principal séquence de titrage
Il gère toutes les actions propres à la séquence
En lien entre les instruments et la fenêtre titration_window
"""

from PyQt5 import QtCore

from IHM import IHM
from titrationWindow import TitrationWindow
from windowHandler import WindowHandler

from pHmeter import *

class TitrationSequence:
    
    def __init__(self, ihm:IHM, win:WindowHandler):
        
        self.spectro=ihm.spectro_unit
        self.phmeter=ihm.phmeter
        self.syringe=ihm.syringe_pump
        self.pump=ihm.peristaltic_pump
        self.window_handler=win

        #Données initiales
        self.N_mes=None
        self.experience_name=None
        self.description=None
        self.OM_type=None
        self.concentration=None
        self.fibers=None
        self.flowcell=None
        self.initial_pH=None
        self.final_pH=None
        self.N_mes=None

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
        self.pH_mes = []
        self.absorbance_spectra = []
        self.absorbance_spectrum1 = None
        self.added_acid_uL = 0
        self.added_volumes = []

        #variables d'itération
        self.added_base_uL = []
        
        #Données de sortie
        self.Abs_spectra_corr_dilu = []

    def configure(self):
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
        
        #config du bouton acid ok
        self.window.ajout_ok.clicked.connect(self.mesure1_acid)


    def mesure1_acid(self): #déclenchée lorsque l'on a ajouté l'acide et cliqué sur OK
        
        vol=self.window.added_acid.value()
        self.added_acid_uL=vol
        self.added_volumes.append(vol)
        self.window.append_vol_in_table(1,vol)

        #On enregistre le spectre et pH et volume ajouté
        self.absorbance_spectrum1=self.spectro.current_absorbance_spectrum
        self.pH_mes.append(self.phmeter.currentPH)

        #On peut désormais afficher quelque chose sur le graphe en delta. 
        #est-ce qu'on affiche vraiment les courbes en delta ? 
        self.SpectraDelta=self.window_handler.titration_window1.delta_all_abs.plot([0],[0])
        self.timer_display.timeout.connect(self.window.updateCurrentSpectrum_delta)

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