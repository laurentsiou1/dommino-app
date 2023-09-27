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
from IHM import IHM
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
legato_run_indicator = DigitalInput() #pin 15 DIGITAL IO à 1 si en mouvement
legato_run_indicator.setDeviceSerialNumber(432846)
legato_run_indicator.setChannel(5)
legato_direction = DigitalInput() #pin7 DIGITAL IO à 1 si infusion 0 si recharge
legato_direction.setDeviceSerialNumber(432846)
legato_direction.setChannel(7)
#Digital outputs
electro_valve = DigitalOutput() #contrôle électrovanne
electro_valve.setDeviceSerialNumber(432846)
electro_valve.setChannel(0)
try:
    U_pH.openWaitForAttachment(1000)
    switch0.openWaitForAttachment(1000)
    switch1.openWaitForAttachment(1000)
    electro_valve.openWaitForAttachment(1000)
    pHmeterIsconnected=True
    print("carte d'interfaçage connectée")
    print("pH-mètre connecté")
    U_pH.setOnAttachHandler(onAttach)   #état de connexion de la carte
    U_pH.setOnDetachHandler(onDetach)
except:
    pHmeterIsconnected=False
    print("carte d'interfaçage non connectée")
    print("pH-mètre non connecté")
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

                        ###     Pousse seringue du commerce     ###
try:
    ser=serial.Serial('COM3', timeout = 2, stopbits=2)  #COM3 peut changer, à vérifier
    print("Liaison série établie avec le KDS Legato100\n", ser)
except:
    pass

#Les instances pour chaque appareil/voie de mesure sont crées peu importe leur état de connexion
# activé/désactivé
#Les instances des sous-systèmes de même. 
ph_meter = PHMeter(U_pH)
syringe_pump=SyringePump('Legato') #ou 'Phidget'
spectrometry_set=AbsorbanceMeasure(od, spectro)
peristaltic_pump='classe de pompe péristaltique à créer'


### Lancement IHM ###

import sys
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
ihm=IHM(ph_meter,spectrometry_set,syringe_pump)
ui = ControlPannel(ph_meter,spectrometry_set,ihm)
ui.setupUi(MainWindow)

MainWindow.show()        
sys.exit(app.exec_())

### fermeture des voies  ###
U_pH.close()
U_stepper.close()
switch0.close()
switch1.close()
electro_valve.close()
stepper.close()

adv.set_enable_lamp(False) #Protection des fibres
print("shutter fermé\n")
od.close_device(id)
print("Spectromètre déconnecté \n")



