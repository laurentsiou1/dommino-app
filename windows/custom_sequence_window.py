"""nouvelle version de titrationWindow"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from ui.custom_sequence import Ui_CustomSequenceWindow

import pyqtgraph as pg
from windows.spectrumConfig import SpectrumConfigWindow
import numpy as np
import matplotlib.pyplot as plt

#from IHM import IHM

class CustomSequenceWindow(QMainWindow,Ui_CustomSequenceWindow):
    
    def __init__(self, win, parent=None):   #win:WindowHandler
        super(CustomSequenceWindow,self).__init__(parent)
        self.setupUi(self)

        #self.ihm=ihm
        self.win=win

        #ajouts
        size=self.spectra_tabs.size()
        rect=QtCore.QRect(QtCore.QPoint(0,0),size)
        self.delta_all_abs = pg.PlotWidget(self.tab1)
        self.delta_all_abs.setGeometry(rect)  #.geometry() #meme dimension que le contenant
        #mais position sur l'origine car le repère est relatif
        self.delta_all_abs.setObjectName("delta_all_abs")
        self.all_abs = pg.PlotWidget(self.tab2)
        self.all_abs.setGeometry(rect)
        self.all_abs.setObjectName("all_abs")
        self.direct_intensity = pg.PlotWidget(self.tab3)
        self.direct_intensity.setGeometry(rect) 
        self.direct_intensity.setObjectName("direct_intensity")

        self.spectra_tabs.addTab(self.tab1, "delta") 
        self.spectra_tabs.addTab(self.tab2, "raw abs")
        self.spectra_tabs.addTab(self.tab3, "intensity")

        #spectre en direct
        self.direct_intensity_plot=self.direct_intensity.plot([0],[0])
        
        #timer pour renouvellement de l'affichage
        self.timer_display = QtCore.QTimer()
        self.timer_display.setInterval(1000) #10 secondes
        self.timer_display.start()

        self.absorbance_spectrum1=None

        self.spectrometry.clicked.connect(self.openSpectroWindow)
        self.syringes.clicked.connect(self.win.openSyringeWindow)

    #DIRECT
    def refresh_stability_level(self):
        self.stabilisation_level.setProperty("value", self.phmeter.stab_purcent)
        self.label_stability.setText(str(self.phmeter.stab_purcent)+"%")

    def refreshDirectSpectrum(self):
        #if self.spectro_unit.current_intensity_spectrum!=None:
        if self.spectro_unit.state=='open':
            self.direct_intensity_plot.setData(self.lambdas,self.spectro_unit.current_intensity_spectrum)



    #spectre courant sur le graphe en delta 
    def update_spectra(self): #il y a déjà un spectre enregistré
        if self.spectro_unit.current_absorbance_spectrum!=None:
            self.current_abs_curve.setData(self.lambdas,self.spectro_unit.current_absorbance_spectrum)
            if self.absorbance_spectrum1!=None:
                #le spectre en delta est une donnée graphique, pas une donnée fondamentale
                self.current_absorbance_spectrum_delta=[self.spectro_unit.current_absorbance_spectrum[k]-self.absorbance_spectrum1[k] for k in range(self.N_lambda)]
                self.current_delta_abs_curve.setData(self.lambdas,self.current_absorbance_spectrum_delta)

    #ENREGISTREMENT

    #Spectres en delta
    def append_abs_spectra(self,N,spec,delta):
        print(spec[300:310],delta[300:310])
        #delta
        a=self.delta_all_abs.plot([0],[0],pen=pg.mkPen(color=self.colors[N-1])) #pen='g'
        a.setData(self.lambdas,delta)
        #abs
        b=self.all_abs.plot([0],[0],pen=pg.mkPen(color=self.colors[N-1]))
        b.setData(self.lambdas,spec)
    
    def append_vol_in_table(self,nb,vol): #nb numero de mesure 1 à Nmes
        self.table_vol_pH[0][nb-1].setObjectName("vol"+str(nb))
        self.grid_instructions_pH_vol.addWidget(self.table_vol_pH[0][nb-1], 1, nb, 1, 1)
        self.table_vol_pH[0][nb-1].clear()
        self.table_vol_pH[0][nb-1].setText(str(vol))
    
    #pH et volume
    def append_pH_in_table(self,nb,pH): #nb=numero de la mesure 1 à Nmes
        self.table_vol_pH[1][nb-1].setObjectName("pH"+str(nb))
        self.grid_instructions_pH_vol.addWidget(self.table_vol_pH[1][nb-1], 2, nb, 1, 1)
        self.table_vol_pH[1][nb-1].clear()
        self.table_vol_pH[1][nb-1].setText(str(pH))

    def append_total_vol_in_table(self,tot):
        #self.total_volume.
        self.grid_instructions_pH_vol.addWidget(self.table_vol_pH[0][self.N_mes], 1, self.N_mes+1, 1, 1)
        self.total_volume.clear()
        self.total_volume.setText(str(tot))
    
    #INITIALISATION
    def param_init(self, seq, ihm=None): #seq est de la classe automatic_sequence

        self.ihm=ihm
        self.spectro_unit=ihm.spectro_unit
        self.phmeter=ihm.phmeter
        self.peristaltic_pump=ihm.peristaltic_pump
        self.syringe_pump=ihm.syringe_pump
        
        self.N_mes=seq.N_mes

        """#timer pour renouvellement de l'affichage
        self.timer_display = QtCore.QTimer()
        self.timer_display.setInterval(1000) #10 secondes
        self.timer_display.start()"""
        
        #Paramètres d'expérience
        if seq.dispense_mode=="from file":
            self.experiment_parameters.setPlainText("\nNom de l'expérience : "+str(seq.experience_name)\
            +"\nDescription : "+str(seq.description)\
            +"\nType de matière organique : "+str(seq.OM_type)\
            +"\nConcentration : "+str(seq.concentration)\
            +"\nFibres : "+str(seq.fibers)\
            +"\nFlowcell : "+str(seq.flowcell)\
            +"\nDispense mode : "+str(seq.dispense_mode))
        else:
            self.experiment_parameters.setPlainText("\nNom de l'expérience : "+str(seq.experience_name)\
            +"\nDescription : "+str(seq.description)\
            +"\nType de matière organique : "+str(seq.OM_type)\
            +"\nConcentration : "+str(seq.concentration)\
            +"\nFibres : "+str(seq.fibers)\
            +"\nFlowcell : "+str(seq.flowcell)\
            +"\nDispense mode : "+str(seq.dispense_mode)\
            +"\nNombre de mesures : "+str(seq.N_mes)\
            +"\npH initial : "+str(seq.pH_start)\
            +"\npH final : "+str(seq.pH_end)\
            +"\nFixed delay for chemical stability: "+str(seq.fixed_delay_sec//60)+"minutes, "+str(seq.fixed_delay_sec%60)+"secondes\n"\
            "Agitation delay (pump stopped) : "+str(seq.mixing_delay_sec//60)+"minutes, "+str(seq.mixing_delay_sec%60)+"secondes\n\n")

        #Spectro
        if ihm.spectro_unit.state=='open':
            self.lambdas=self.spectro_unit.wavelengths 
            self.N_lambda=len(self.lambdas) 
        #Display current spectrum
        self.timer_display.timeout.connect(self.refreshDirectSpectrum) #abs in direct

        #display countdown
        self.timer_display.timeout.connect(seq.refreshCountdown)
        
        #graphique
        cmap = plt.get_cmap('tab10')  # You can choose a different colormap
        aa = [cmap(i) for i in np.linspace(0, 1, self.N_mes)]
        self.colors = [(int(r * 255), int(g * 255), int(b * 255)) for r, g, b, _ in aa]
        
        #tableau de données "QLabels" volume/pH mesuré. à compléter au fil de l'expérience
        #2 colonnes et autant de lignes que N_mes
        self.table_vol_pH=[[QtWidgets.QLabel(self.gridLayoutWidget),QtWidgets.QLabel(self.gridLayoutWidget)] for k in range(self.N_mes)]
        
        #Tableau d'instructions
        for j in range(self.N_mes): 
            self.tab_jk = QtWidgets.QLabel(self.gridLayoutWidget_2)
            self.tab_jk.setAlignment(QtCore.Qt.AlignCenter)
            self.grid_instructions.addWidget(self.tab_jk, j+1, 0, 1, 1)
            self.tab_jk.setText(str(j+1))
            for k in range(5):
                self.tab_jk = QtWidgets.QLabel(self.gridLayoutWidget_2)
                self.tab_jk.setAlignment(QtCore.Qt.AlignCenter)
                self.grid_instructions.addWidget(self.tab_jk, j+1, k+1, 1, 1)
                self.tab_jk.setText(str(seq.instruction_table[j][k]))
        
        #Tableau volume dispensé/pH mesuré
        #Mise en forme. A compléter par la suite
        for j in range(self.N_mes):
            for k in range(2):
                self.mes_jk = QtWidgets.QLabel(self.gridLayoutWidget)
                self.mes_jk.setAlignment(QtCore.Qt.AlignCenter)
                self.grid_mes_pH_vol.addWidget(self.mes_jk, j, k, 1, 1)
                self.mes_jk.setText("")

        #compléter avec les données du fichier de sequence
        #2ème colonne : seringues
        """for j in range(1,self.N_mes+1): 
            self.syr_j = QtWidgets.QLabel(self.gridLayoutWidget_2)
            self.syr_j.setAlignment(QtCore.Qt.AlignCenter)
            self.grid_instructions_pH_vol.addWidget(self.syr_j, j, 0, 1, 1)
            self.syr_j.setText(str(j))"""
        """self.syr1=QtWidgets.QLabel(self.gridLayoutWidget_2)
        self.syr1.setAlignment(QtCore.Qt.AlignCenter)
        self.grid_instructions_pH_vol.addWidget(self.syr1, 1, 1, 1, 1)
        self.syr1.setText('B')"""

        #pompe
        if self.peristaltic_pump.state=='open':
            self.pump_speed_volt.setProperty("value", self.peristaltic_pump.current_speed)

        #pH meter
        self.stab_time.setProperty("value", self.phmeter.stab_time)
        self.stab_time.valueChanged.connect(seq.update_stab_time)
        self.stab_step.setProperty("value", self.phmeter.stab_step)
        self.stab_step.valueChanged.connect(seq.update_stab_step)

        #saving
        self.actionsave.triggered.connect(seq.createFullSequenceFiles)
    
    #configuration du spectro
    def openSpectroWindow(self):
        self.window2 = QtWidgets.QDialog()
        self.ui2 = SpectrumConfigWindow(self.spectro_unit,self.ihm)
        self.ui2.setupUi(self.window2)
        self.window2.show()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ihm=IHM()
    titrationwindow = CustomSequenceWindow(ihm=ihm)
    titrationwindow.show()

    rc=app.exec_()
    sys.exit(rc)