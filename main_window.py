# main_window.py

from PyQt5.QtWidgets import QMainWindow, QApplication #, QWidget, QLabel, QLineEdit, QPushButton
from ui.panneau_de_controle import Ui_MainWindow

from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
from IHM import IHM
from expConfig import ExpConfig
from calBox import CalBox
from spectrumConfig import SpectrumConfigWindow
from savingConfig import SavingConfig
from windowHandler import WindowHandler

from pHmeter import *
from spectro.absorbanceMeasure import AbsorbanceMeasure
from syringePump import *
from peristalticPump import *

from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.Devices.DigitalInput import DigitalInput
from Phidget22.Devices.DigitalOutput import DigitalOutput
from Phidget22.Devices.Stepper import Stepper
from oceandirect.OceanDirectAPI import Spectrometer as Sp, OceanDirectAPI
from oceandirect.od_logger import od_logger

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None, ihm:IHM=None, win:WindowHandler=None):
        #graphique
        super(MainWindow,self).__init__(parent)
        self.setupUi(self)
        #ajout
        self.Abs_direct = pg.PlotWidget(self.tab1)
        self.Abs_direct.setGeometry(QtCore.QRect(0, 0, 511, 371))
        self.Abs_direct.setObjectName("Abs_direct")
        self.Spectrum_direct = pg.PlotWidget(self.tab_2)
        self.Spectrum_direct.setGeometry(QtCore.QRect(0, 0, 511, 371))
        self.Spectrum_direct.setObjectName("Spectrum_direct")
        
        #appareils
        print("initialisation du panneau de contrôle") 
        self.ihm=ihm
        self.win=win
        self.phmeter=ihm.phmeter
        self.spectro_unit=ihm.spectro_unit
        self.syringe_pump=ihm.syringe_pump
        self.peristaltic_pump=ihm.peristaltic_pump

        #connexions
        self.connect_phmeter.clicked.connect(self.link_pHmeter2IHM)
        self.cal_button.clicked.connect(self.openCalibWindow)
        self.reglage_spectro.clicked.connect(self.OnClick_reglage_spectro)
        self.connect_syringe_pump.clicked.connect(self.connectSyringePump)
        self.connect_pump.clicked.connect(self.connectPeristalticPump)   
        
        self.titration_button.clicked.connect(self.openConfigWindow)
        self.saving_config.clicked.connect(self.openSavingConfigWindow)
        self.save_button.clicked.connect(self.ihm.createDirectMeasureFile)

        self.close_all.clicked.connect(self.ihm.close_all_devices)
        self.close_all.clicked.connect(self.clear_IHM)

    ### Méthodes pour le pH mètre
    def link_pHmeter2IHM(self):
        if self.phmeter.state=='closed':
            self.phmeter.connect()
        if self.phmeter.state=='open':
            #affichage des données de calibration
            self.onCalibrationChange()
            #pH en direct
            self.direct_pH.display(self.phmeter.currentPH) #pH instantané
            self.phmeter.voltagechannel.setOnVoltageChangeHandler(self.displayDirectPH) #à chaque changement
            self.phmeter.activateStabilityLevel()
            self.phmeter.stab_timer.timeout.connect(self.refresh_stability_level)
            self.stab_time.valueChanged.connect(self.update_stab_time)
    
    def update_stab_time(self):
        self.phmeter.stab_time=self.stab_time.value()

    def clear_IHM(self):
        self.direct_pH.display(None) #   setDisabled()

    def displayDirectPH(self,ch,voltage): #arguments immuables
        self.phmeter.currentVoltage=voltage        
        pH = volt2pH(self.phmeter.a,self.phmeter.b,voltage)
        self.phmeter.currentPH=pH #actualisation de l'attribut de la classe pHmeter
        self.direct_pH.display(pH)
        #print("voltage change")
    
    def refresh_stability_level(self):
        self.stabilisation_level.setProperty("value", self.phmeter.stab_purcent)
        self.stability_label.setText(str(self.phmeter.stab_purcent)+"%")

    def openCalibWindow(self):
        self.window1 = QtWidgets.QDialog()
        self.ui1 = CalBox(self.ihm.phmeter, self, self.ihm)
        self.ui1.setupUi(self.window1)
        self.window1.show()
    
    def onCalibrationChange(self):
        self.calib_text = "Current calibration data:\n"+"date: "+str(self.phmeter.CALdate)+"\n"+"temperature: "+str(self.phmeter.CALtemperature)+"°C\npH buffers: "+str(self.phmeter.CALtype)+"\nRecorded voltages:\nU4="+str(self.phmeter.U1)+"V\nU7="+str(self.phmeter.U2)+"V\nU10="+str(self.phmeter.U3)+"V\ncoefficients U=a*pH+b\na="+str(self.phmeter.a)+"\nb="+str(self.phmeter.b)
        self.calText.clear()
        self.calText.appendPlainText(self.calib_text)

    ### Méthodes pour le spectromètre
    def OnClick_reglage_spectro(self):
        #self.spectro_unit=self.ihm.spectro_unit
        if self.spectro_unit.state=='closed':
            self.spectro_unit.connect()
        if self.spectro_unit.state=='open':
            self.link_spectro2IHM()
        self.openSpectroWindow()

    def openSpectroWindow(self):
        self.window2 = QtWidgets.QDialog()
        self.ui2 = SpectrumConfigWindow(self.spectro_unit,self.ihm)
        self.ui2.setupUi(self.window2)
        self.window2.show()
    
    def changeShutterState(self):
        #if self.spectro_unit.state=='open':
        self.spectro_unit.changeShutterState()
        self.shutter.setChecked(not(self.spectro_unit.adv.get_enable_lamp()))

    def updateSpectrum(self):
        if self.spectro_unit.state == 'open':   #intensité direct
            self.intensity_direct_plot=self.Spectrum_direct.plot([0],[0],clear = True)
            self.intensity_direct_plot.setData(self.lambdas,self.spectro_unit.current_intensity_spectrum)
        if self.spectro_unit.active_ref_spectrum!=None:
            self.reference_plot=self.Spectrum_direct.plot([0],[0],pen='g')
            self.reference_plot.setData(self.lambdas,self.spectro_unit.active_ref_spectrum)
        if self.spectro_unit.active_background_spectrum!=None:      
            self.background_plot=self.Spectrum_direct.plot([0],[0],pen='r')
            self.background_plot.setData(self.lambdas,self.spectro_unit.active_background_spectrum)
        if self.spectro_unit.current_absorbance_spectrum!=None: #abs direct
            self.abs_direct_plot=self.Abs_direct.plot([0],[0],clear = True)
            self.abs_direct_plot.setData(self.lambdas,self.spectro_unit.current_absorbance_spectrum)
        if self.spectro_unit.reference_absorbance!=None:    #abs ref
            self.reference_abs_plot=self.Abs_direct.plot([0],[0],pen='y')
            self.reference_abs_plot.setData(self.lambdas,self.spectro_unit.reference_absorbance)  

    def link_spectro2IHM(self):
        #mise sur timer
        self.ihm.timer3s.timeout.connect(self.updateSpectrum)            
        #état réel du shutter
        self.shutter.setChecked(not(self.spectro_unit.adv.get_enable_lamp()))
        self.shutter.clicked.connect(self.changeShutterState)
        #config de l'affichage du spectre courant
        self.lambdas=self.spectro_unit.wavelengths      
        self.abs_direct_plot=self.Abs_direct.plot([0],[0])
        self.intensity_direct_plot=self.Spectrum_direct.plot([0],[0])

    #Méthodes pour l'enregistrement des données et configuration des séquences
    def openConfigWindow(self):
        self.window3 = QtWidgets.QDialog()
        self.ui3 = ExpConfig(self.ihm, self.win)
        self.ui3.setupUi(self.window3)
        self.window3.show()
    
    def openSavingConfigWindow(self):
        self.win4 = SavingConfig(self.ihm) #l'instance de IHM est passée en attribut
        self.win4.show()

    ### Méthodes pour le pousse-seringue
    def connectSyringePump(self):
        self.syringe_pump.connect()
        if self.syringe_pump.state=='open':
            self.link_SyringePump2IHM()

    #Suppose que le pousse seringue soit ouvert
    def link_SyringePump2IHM(self):
    #attention. les connexions clicked.connect de signaux avec des slots sont recréées à chaque appel.
    #Il faut donc supprimer les connexions pour pas que les slots soient effectués plusieurs fois de suite
        self.base_level=self.syringe_pump.size-self.syringe_pump.stepper.getPosition()
        #reference
        self.make_ref_button.disconnect()
        self.make_ref_button.clicked.connect(self.set_reference_position)
        #action buttons
        self.stop_syringe.disconnect()
        self.stop_syringe.clicked.connect(self.syringe_pump.ForceStop)
        self.unload_base_button.disconnect()
        self.unload_base_button.clicked.connect(self.unload_base)
        self.load_base_button.disconnect()
        self.load_base_button.clicked.connect(self.load_base)
        self.full_reload_button.disconnect()
        self.full_reload_button.clicked.connect(self.full_reload)
        self.dispense_base_button.disconnect()
        self.dispense_base_button.clicked.connect(self.dispense_base)
        self.added_acid.disconnect()
        self.added_acid.valueChanged.connect(self.actualize_counts_on_acid_value_change)
        self.reset_added_count.disconnect()
        self.reset_added_count.clicked.connect(self.reset_volume_count)
        #Display
        self.base_level_bar.setProperty("value", self.base_level)
        self.base_level_number.setText("%d uL" % self.base_level)
        self.added_base.setText("0")       

    def set_reference_position(self):
        self.syringe_pump.setReference()
        #maj levelbar
        self.base_level=self.syringe_pump.size-round(self.syringe_pump.stepper.getPosition(),0)
        self.base_level_bar.setProperty("value", self.base_level)
        self.base_level_number.setText("%d uL" % self.base_level)

    def unload_base(self): #appelée lors de l'appui sur le bouton unload base
        print(self)
        vol=self.unload_base_box.value()
        self.syringe_pump.simple_dispense(vol,ev=0)
        #maj levelbar
        self.base_level_bar.setProperty("value", self.syringe_pump.base_level_uL)
        self.base_level_number.setText("%d uL" % self.syringe_pump.base_level_uL)

    def load_base(self): #lors de l'appui sur load_base_button
        vol=self.load_base_box.value()
        self.syringe_pump.simple_refill(vol)
        #maj levelbar
        self.base_level_bar.setProperty("value", self.syringe_pump.base_level_uL)
        self.base_level_number.setText("%d uL" % self.syringe_pump.base_level_uL)
    
    def full_reload(self):
        self.syringe_pump.full_refill()
        #maj levelbar
        self.base_level_bar.setProperty("value", self.syringe_pump.size)
        self.base_level_number.setText("%d uL"%self.syringe_pump.size)

    def dispense_base(self):
        vol=self.dispense_base_box.value()
        self.syringe_pump.simple_dispense(vol) #ev=1 default
        #maj levelbar
        self.base_level_bar.setProperty("value", self.syringe_pump.base_level_uL)
        self.base_level_number.setText("%d uL" % self.syringe_pump.base_level_uL)
        #maj volume count
        self.added_base.setText("%d" %self.syringe_pump.added_base_uL)
        self.added_total.setText("%d" %self.syringe_pump.added_total_uL)
    
    def reset_volume_count(self):
        self.syringe_pump.added_acid_uL=0
        self.syringe_pump.added_base_uL=0
        self.syringe_pump.added_total_uL=0
        self.syringe_pump.acid_dispense_log=[]
        self.syringe_pump.base_dispense_log=[]
        self.added_acid.setValue(0)
        self.added_base.setText("0")
        self.added_total.setText("0" )

    def actualize_counts_on_acid_value_change(self):
        #modification de acid et total dans la classe syringe_pump
        self.syringe_pump.added_acid_uL=self.added_acid.value()
        self.syringe_pump.added_total_uL=self.syringe_pump.added_acid_uL+self.syringe_pump.added_base_uL
        #modif de l'affichage total count
        self.added_total.setText("%d" %self.syringe_pump.added_total_uL)
        self.syringe_pump.acid_dispense_log = self.syringe_pump.added_acid_uL


    ### Méthodes pour la pompe péristaltique
    def connectPeristalticPump(self):
        self.peristaltic_pump.connect()
        if self.peristaltic_pump.state=='open':
            self.link_pump2IHM()
    
    def link_pump2IHM(self):
        #print("pompe péristaltique reliée au panneau de controle")
        self.start_pump.clicked.connect(self.peristaltic_pump.start)
        self.stop_pump.clicked.connect(self.peristaltic_pump.stop)
        self.change_dir.clicked.connect(self.peristaltic_pump.change_direction)
        self.pump_speed_rpm.valueChanged.connect(self.update_pump_speed)

    def update_pump_speed(self):
        self.peristaltic_pump.setVelocity_rpm(self.pump_speed_rpm.value())

if __name__=="__main__":
    import sys
    app = QApplication(sys.argv)
    #créations des classes nécessaires
    itf=IHM()
    win=WindowHandler()
    MainWindow = MainWindow(ihm=itf,win=win)
    MainWindow.show()

    rc=app.exec_()
    sys.exit(rc)
    #sys.exit(app.exec_())
