"programme pour tester les fonctions du module syringe_pump"

from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.Stepper import *
from Phidget22.Devices.VoltageInput import *
import time

class pompe:

    attribut='attribut commun'    
    
    def __init__(self, model):
        if model=='A':
            pompeA.__init__(self)
        if model=='B':
            self=pompeB()
    
    def get_volume(self):
        self.volume=20
        return self.volume
    
    def test_attribut(self):
        print(self.attribut)

        
class pompeA(pompe): #pompe stepper phidget

    attributA=2

    def __init__(self):
        print("self=",self)
        U_stepper = VoltageInput() #tension d'alim
        U_stepper.setDeviceSerialNumber(683442)
        U_stepper.setHubPort(0) #seulement pour les device avec VINT
        U_stepper.setChannel(0)    
        stepper = Stepper() #contrôle du stepper
        stepper.setDeviceSerialNumber(683442)
        stepper.setHubPort(0)
        stepper.setChannel(0)
        try:
            U_stepper.openWaitForAttachment(2000)
            stepper.openWaitForAttachment(2000)
        except:
            pass
        self.stp=stepper

        print(self.attributA)

class pompeB(pompe): #pompe Legato
    def __init__(self):
        legato_run_indicator = DigitalInput() #pin 15 DIGITAL IO à 1 si en mouvement
        legato_run_indicator.setDeviceSerialNumber(432846)
        legato_run_indicator.setChannel(5)
        try:
            legato_run_indicator.openWaitForAttachment(1000)
        except:
            pass
        self.run_indicator=legato_run_indicator

if __name__=="__main__":
    #a=pompeA()
    #print(a.stp)
    #print(a)
    #print(a.get_volume())
    #print(a.attribut)

    c=pompe('A')
    print("pompe('A')=",c)
    print(c.stp)
    c.test_attribut()

