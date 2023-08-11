"Programme principal de l'application"

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.Stepper import *
from Phidget22.Devices.Log import *
from Phidget22.Devices.Manager import *
import time

from SyringePump import SyringePump
from pHmeter import PHMeter

from PyQt5 import QtCore, QtGui, QtWidgets
import IHM
from controlPannel import ControlPannel

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
#def initialize_components():
    
                                ## carte Phidget Interface Kit ##
    # carte = Phidget()
    # carte.setDeviceSerialNumber(432846)
    # carte.setOnAttachHandler(onAttach)
    # carte.setOnDetachHandler(onDetach)
    
try:

    #VoltageInputs
    U_pH = VoltageInput() #pH-mètre
    U_pH.setDeviceSerialNumber(432846)
    U_pH.setChannel(0)
    U_pH.openWaitForAttachment(1000)
    print("carte d'interfaçage connectée")
    U_pH.setOnAttachHandler(onAttach)   #état de connexion de la carte
    U_pH.setOnDetachHandler(onDetach)
    phm = PHMeter(U_pH)
        
    #Digital inputs
    interrupteur0 = DigitalInput() #interrupteur bout de course seringue vide
    interrupteur0.setDeviceSerialNumber(432846)
    interrupteur0.setChannel(0)
    interrupteur0.openWaitForAttachment(1000)

    interrupteur1 = DigitalInput() #interrupteur bout de course seringue pleine
    interrupteur1.setDeviceSerialNumber(432846)
    interrupteur1.setChannel(1)
    interrupteur1.openWaitForAttachment(1000)

    #Digital outputs
    relay0_state = DigitalOutput() #contrôle électrovanne
    relay0_state.setDeviceSerialNumber(432846)
    relay0_state.setChannel(0)
    relay0_state.openWaitForAttachment(1000)

except:
    pass
                                            ## hub Phidget ##
    # hub = Phidget()
    # hub.setDeviceSerialNumber(683442)
    # hub.setOnAttachHandler(onAttach)
    # hub.setOnDetachHandler(onDetach)
    
try:
    #VoltageInput
    U_stepper = VoltageInput() #tension d'alim du stepper
    U_stepper.setDeviceSerialNumber(683442)
    U_stepper.setHubPort(0) #seulement pour les device avec VINT
    U_stepper.setChannel(0)
    U_stepper.openWaitForAttachment(1000)
    print("stepper connecté")
        
    U_stepper.setOnAttachHandler(onAttach) #connection du hub
    U_stepper.setOnDetachHandler(onDetach)
        
    #Stepper
    stepper = Stepper() #object de type stepper : contrôle du moteur stepper
    stepper.setDeviceSerialNumber(683442)
    stepper.setHubPort(0)
    stepper.setChannel(0)
    stepper.openWaitForAttachment(1000)

except:
    print("Stepper non connecté")
    pass

'''
name1 = U_pH.getDeviceName()
name2 = U_stepper.getDeviceName()
print("carte d'interfaçage: " + str(name1))
print("stepper: " + str(name2))
'''

### Lancement IHM
spec='spectrometer'
if U_pH.getIsOpen():
    print("Carte d'interfaçage connectée")
if stepper.getIsOpen():
    print("VINT hub connecté")

import sys
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = ControlPannel(phm,spec)
ui.setupUi(MainWindow)
ui.phmeter.voltagechannel.setOnVoltageChangeHandler(ui.setOnDirectPH)
MainWindow.show()        
sys.exit(app.exec_())

try:
    input("taper entrée pour quitter\n")
except (Exception, KeyboardInterrupt):
    pass

#U_pH.close()
'''
U_stepper.close()
interrupteur0.close()
interrupteur1.close()
relay0_state.close()
stepper.close()
'''