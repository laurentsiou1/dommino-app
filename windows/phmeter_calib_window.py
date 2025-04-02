"fenêtre de calibration du pH mètre"

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5.QtGui import QIcon
from graphic.windows.phmeter_calib_win import Ui_calibration_window

from subsystems.pHmeter import *
from datetime import datetime

import os

class PhMeterCalibWindow(QDialog, Ui_calibration_window):
    def __init__(self, ihm, parent=None):
        super(PhMeterCalibWindow,self).__init__(parent)
        self.setupUi(self)
        self.ihm=ihm
        
        # Icone windows
        icon_path = os.path.join(os.path.dirname(__file__), "..", "graphic", "images", "icon-appli.ico")
        self.setWindowIcon(QIcon(icon_path))

        #connexions
        self.buttonBox.clicked.connect(self.on_button_clicked)

        if self.ihm.phmeter.state=='open':
            self.ihm.timer_display.timeout.connect(self.setOnDirectVoltage) #voltage current update

        #connexions 
        self.button_ph4.clicked.connect(lambda : self.saveAndShowVoltage(self.U_ph4))
        self.button_ph7.clicked.connect(lambda : self.saveAndShowVoltage(self.U_ph7))
        self.button_ph10.clicked.connect(lambda : self.saveAndShowVoltage(self.U_ph10))

        self.U4=0
        self.U7=0
        self.U10=0
        self.used_pH_buffers=set()
    
    def on_button_clicked(self, button):
        if self.buttonBox.standardButton(button) == QDialogButtonBox.Apply:
            self.validateCal()
            self.ihm.phmeter.onCalibrationChange()
            self.ihm.controlPanel.refreshCalibrationText()
            self.accept()
            self.reject()

    def setOnDirectVoltage(self): #, ch, voltage):
        self.lcdNumber.display(1000*self.ihm.phmeter.currentVoltage)

    def saveAndShowVoltage(self, screen): #sreen est un objet QLCDNumber
        U=self.ihm.phmeter.currentVoltage
        print("save voltage")
        if screen==self.U_ph4:
            self.U4=U
            self.used_pH_buffers.add(4)
        if screen==self.U_ph7:
            self.U7=U
            self.used_pH_buffers.add(7)
        if screen==self.U_ph10:
            self.U10=U
            self.used_pH_buffers.add(10)
        print("voltage=",U)
        screen.display(U)

    def validateCal(self): #pH_buffers est un tuple contenant les valeurs de pH des tampons
        print("validate cal")
        pH_buffers=sorted(list(self.used_pH_buffers))
        self.used_pH_buffers = pH_buffers
        #print("pH buffers : ",type(pH_buffers),pH_buffers)
        dt = datetime.now()
        if pH_buffers == [4]:
            u_cal = [self.U4]
        elif pH_buffers == [7]:
            u_cal = [self.U7]
        elif pH_buffers == [4,7]:
            u_cal = [self.U4, self.U7]
            print("calib 2 pts")
        elif pH_buffers == [4,7,10]:
            u_cal = [self.U4, self.U7, self.U10]
            print("calib 3 pts")
        else:
            print("This type of calibration is not suppported")
        (a,b)=PHMeter.computeCalCoefs(self.ihm.phmeter,u_cal,pH_buffers) #calcul des coefficients de calib
        PHMeter.saveCalData(self.ihm.phmeter, dt.strftime("%m/%d/%Y %H:%M:%S"), pH_buffers, u_cal, (a,b)) #enregistrer dans le fichier

