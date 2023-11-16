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
        self.directSpectrum=self.window_handler.titration_window1.direct_abs.plot([0],[0])
        #mise à jour de l'absorbance
        self.timer_display.timeout.connect(self.updateCurrentSpectrum)

        #actualisation sur le pH mètre
        self.phmeter.voltagechannel.setOnVoltageChangeHandler(self.refresh_pH)


    def mesure1_acid(self):
        self.SpectraDelta=self.window_handler.titration_window1.delta_all_abs.plot([0],[0])
        self.timer_display.timeout.connect(self.updateCurrentSpectrum_delta)

    #DIRECT
    #Actualisation du spectre en direct
    def updateCurrentSpectrum(self):
        if self.spectro.current_absorbance_spectrum!=None:
            #print("il y a un spectre courant")
            #spectre courant
            self.directSpectrum.setData(self.lambdas,self.spectro.current_absorbance_spectrum)
    
    #spectre courant sur le graphe en delta 
    def updateCurrentSpectrum_delta(self): #il y a déjà un spectre enregistré
        self.window.delta_all_abs.plot(self.lambdas,self.spectro.current_absorbance_spectrum-self.absorbance_spectrum1)

    def refresh_pH(self,ch,voltage): #arguments immuables
        #print("pH change")
        self.phmeter.currentVoltage=voltage        
        pH = volt2pH(self.phmeter.a,self.phmeter.b,voltage)
        self.phmeter.currentPH=pH #actualisation de l'attribut de la classe pHmeter
        self.window.direct_pH.display(pH)
    
    def measure_all_data(self):
        pass

    def add_spectrum(self):
        self.absorbance_spectra.append(self.spectro.current_absorbance_spectrum)



    def correct_spectra_from_dilution(self,spectra,dilution_factors):
        #attention il y a un log! Il faut revoir la formule.
        corrected_spectra=[]
        for k in range(self.N):
            corrected_spectra[k]=spectra[k]*dilution_factors[k] 