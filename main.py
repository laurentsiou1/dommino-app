"Programme principal de l'application"
"""
https://www.hostinger.fr/tutoriels/commandes-git
Petit tuto des commandes git

Pour afficher l'arbre dans le terminal:
https://stackoverflow.com/questions/1064361/unable-to-show-a-git-tree-in-terminal
"""

#imports Phidget
from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.Stepper import *
from Phidget22.Devices.Log import *
from Phidget22.Devices.Manager import *

#imports OceanDirect
from oceandirect.OceanDirectAPI import OceanDirectError, OceanDirectAPI, Spectrometer as Sp
from oceandirect.od_logger import od_logger

#Classes crées pour les sous-systèmes
from syringePump import SyringePump
from pHmeter import PHMeter
from spectro.absorbanceMeasure import AbsorbanceMeasure

#modules et classes pour l'interface
from PyQt5 import QtCore, QtGui, QtWidgets
import IHM
from controlPannel import ControlPannel

import time

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
    U_stepper.openWaitForAttachment(2000) #au moins 2000
    stepper.openWaitForAttachment(2000)
    stepperIsconnected=True
    print("stepper connecté")
    #U_stepper.setOnAttachHandler(onAttach) #gestionnaire de connexion activé
    #U_stepper.setOnDetachHandler(onDetach)    
except:
    print("Stepper non connecté")
    stepperIsConnected=False
    pass

                        ## Spectromètre et lampe ##
logger = od_logger()
od = OceanDirectAPI()
device_count = od.find_usb_devices() #nb d'appareils détectés
device_ids = od.get_device_ids()
if device_ids!=[]:
    id=device_ids[0]
    try:
        spectro = od.open_device(id) #crée une instance de la classe Spectrometer
        adv = Sp.Advanced(spectro)
        spectroIsConnected=True
        print("Spectro connecté")
    except:
        spectro=None #on crée dans tous les cas un objet Spectrometer
        adv = None
        spectroIsConnected=False
        print("Ne peut pas se connecter au spectro numéro ", id)
        pass
else:
    spectro=None #on crée dans tous les cas un objet Spectrometer
    adv = None #Sp.Advanced(spectro)
    spectroIsConnected=False
    print("Spectro non connecté")
print("Nombre d'appareils OceanDirect détectés : ", device_count)
print("ID spectros: ", device_ids)

#Les instances pour chaque appareil/voie de mesure sont crées peu importe leur état de connexion
# activé/désactivé
#Les instances des sous-systèmes de même. 
ph_meter = PHMeter(U_pH)
syringe_pump=SyringePump(stepper, relay0, switch0)
spectrometry_set=AbsorbanceMeasure(od, spectro)
peristaltic_pump='classe de pompe péristaltique à créer'


### Lancement IHM ###
statut_phm=ph_meter.getIsOpen()
statut_ps=syringe_pump.getIsOpen()
statut_spectro=spectrometry_set.getIsOpen()

print(statut_ps,statut_phm,statut_spectro)


import sys
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ui = ControlPannel(ph_meter,spectrometry_set)
ui.setupUi(MainWindow)

MainWindow.show()        
sys.exit(app.exec_())

### fermeture des voies  ###
U_pH.close()
U_stepper.close()
switch0.close()
switch1.close()
relay0.close()
stepper.close()

adv.set_enable_lamp(False) #Protection des fibres
print("shutter fermé\n")
od.close_device(id)
print("Spectromètre déconnecté \n")



