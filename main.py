"Programme principal de l'application"

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.Stepper import *
from Phidget22.Devices.Log import *
from Phidget22.Devices.Manager import *
import time

from syringePump import SyringePump
from pHmeter import PHMeter

from PyQt5 import QtCore, QtGui, QtWidgets
import IHM
from controlPannel import ControlPannel

# class Sous_Systeme:
#     isConnected
#     def isConnected(self):
#         return self.isConnected

#event handlers
def onVoltageChange(self, voltage):
	print("Voltage: " + str(voltage))

def onAttach(self):
    #print(self)
    Name=self.getDeviceName()
    print(Name, " est connecté: ")
        
def onDetach(self):
    #print(self)
    Name=self.getDeviceName()
    print(Name, " est déconnecté: ")
	
### Initialisation_composants ###
    
                            ## carte Phidget Interface Kit ##
#VoltageInputs
U_pH = VoltageInput() #pH-mètre
U_pH.setDeviceSerialNumber(432846)
U_pH.setChannel(0)
#Digital inputs
switch0 = DigitalInput() #interrupteur bout de course seringue vide
switch0.setDeviceSerialNumber(432846)
switch0.setChannel(0)
switch1 = DigitalInput() #interrupteur bout de course seringue pleine
switch1.setDeviceSerialNumber(432846)
switch1.setChannel(1)
#Digital outputs
relay0 = DigitalOutput() #contrôle électrovanne
relay0.setDeviceSerialNumber(432846)
relay0.setChannel(0)
try:
    U_pH.openWaitForAttachment(1000)
    switch0.openWaitForAttachment(1000)
    switch1.openWaitForAttachment(1000)
    relay0.openWaitForAttachment(1000)
    pHmeterIsconnected=True
    print("carte d'interfaçage connectée")
    U_pH.setOnAttachHandler(onAttach)   #état de connexion de la carte
    U_pH.setOnDetachHandler(onDetach)
except:
    pHmeterIsconnected=False
    print("carte d'interfaçage non connectée")
    pass

                            ## hub Phidget ##
    #Stepper
U_stepper = VoltageInput() #tension d'alim
U_stepper.setDeviceSerialNumber(683442)
U_stepper.setHubPort(0) #seulement pour les device avec VINT
U_stepper.setChannel(0)    
stepper = Stepper() #contrôle du stepper
stepper.setDeviceSerialNumber(683442)
stepper.setHubPort(0)
stepper.setChannel(0)
try:
    U_stepper.openWaitForAttachment(1000)
    stepper.openWaitForAttachment(1000)
    stepperIsconnected=True
    print("stepper connecté")
    U_stepper.setOnAttachHandler(onAttach) #gestionnaire de connexion activé
    U_stepper.setOnDetachHandler(onDetach)    
except:
    print("Stepper non connecté")
    stepperIsConnected=False
    pass


ph_meter = PHMeter(U_pH)
syringe_pump=SyringePump(stepper, relay0, switch0)
spectrometer='classe à créer'
peristaltic_pump='classe de pompe péristaltique à créer'

### Lancement IHM
ph_meter.getIsOpen()
syringe_pump.getIsOpen()


import sys
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = ControlPannel(ph_meter,spectrometer)
ui.setupUi(MainWindow)
#ui.phmeter.voltagechannel.setOnVoltageChangeHandler(ui.setOnDirectPH)
MainWindow.show()        
sys.exit(app.exec_())

U_pH.close()
U_stepper.close()
switch0.close()
switch1.close()
relay0.close()
stepper.close()
