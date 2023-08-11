"Classe SyringePump"

import Phidget22.Devices.Stepper 
import Phidget22.Devices.DigitalOutput
import Phidget22.Devices.DigitalInput 
import time

class SyringePump:

    def __init__(self, stp, rly, swc):
        self.stepper = stp
        self.relay = rly
        self.switch = swc
    
    def SecurityStop(self, switch, state): #self est un syringe pump
        #print(self, switch, state) #x2 est interrupteur0 et x3=state
        if state == 1:
            self.stepper.setEngaged(False)
            print("Piston en bout de course, moteur coupé")

    def ReachedPosition(self): #agit sur un objet Stepper
        time.sleep(1) #attendre la stabilisation du moteur
        position = self.getPosition()
        print("Position atteinte : " + str(position))
        return position
    
    def setZeroPosition(self):
        dx = int(input("entrer le déplacement voulu : "))
        pos = self.stepper.getPosition()
        self.stepper.setTargetPosition(pos+dx)
        self.stepper.setEngaged(True)
        try:
            input("taper entrée pour arrêter\n")
        except (Exception, KeyboardInterrupt):
            pass
        pos=self.stepper.getPosition()
        print("position actuelle avant offset", pos)
        self.stepper.addPositionOffset(-pos)
        pos=self.stepper.getPosition()
        print("position après offset", pos)
    
    def fill_syringe(self, vol):
        position = self.stepper.getPosition()
        print("Position piston avant recharge: " + str(position))
        self.stepper.setTargetPosition(100*vol)
        self.stepper.setEngaged(True)
        self.stepper.setOnStoppedHandler(SyringePump.ReachedPosition)
        try:
            input("Press Enter to Stop\n")
        except (Exception, KeyboardInterrupt):
            pass

    def dispense(self, vol):
        pos0 = self.stepper.getPosition()
        if vol*100 <= pos0:
            self.relay.setState(True)
            self.stepper.setTargetPosition(pos0-100*vol)
            self.stepper.setOnStoppedHandler(SyringePump.ReachedPosition)
            self.stepper.setEngaged(True)
        else:
            print("Volume diponible dans la seringue insuffisant")
        try:
            input("Press Enter to Stop\n")
            
        except (Exception, KeyboardInterrupt):
            pass
            #print("Position piston avant dispense: " + str(pos0))
        self.relay.setState(False)
    
    def empty_syringe(self):
        self.stepper.setTargetPosition(0)
        self.stepper.setEngaged(True)
        print("vidage de la seringue")
        try:
            input("Taper entrée pour interrompre\n")
        except (Exception, KeyboardInterrupt):
            pass