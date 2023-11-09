"Module contentant les fonctions du pousse seringue"
import Phidget22.Devices.Stepper 
import Phidget22.Devices.DigitalOutput
import Phidget22.Devices.DigitalInput 
import time

def ReachedPosition(self):
    time.sleep(1) #attendre la stabilisation du moteur
    position = self.getPosition()
    print("Position atteinte : " + str(position))
    return position

def setZeroPosition(stepper):
    dx = int(input("entrer le déplacement voulu : "))
    pos = stepper.getPosition()
    stepper.setTargetPosition(pos+dx)
    stepper.setEngaged(True)
    try:
        input("taper entrée pour arrêter\n")
    except (Exception, KeyboardInterrupt):
        pass
    pos=stepper.getPosition()
    stepper.addPositionOffset(-pos)

#fonction de recharge de la seringue selon la quantité vol (uL)
#On donne les objets phidgets à la fonction
def fill_syringe(stepper, relay, switch, vol):
    position = stepper.getPosition()
    print("Position initiale piston: " + str(position))
    
    stepper.setTargetPosition(100*vol)
    stepper.setEngaged(True)
    stepper.setOnStoppedHandler(ReachedPosition)

    try:
        input("Press Enter to Stop\n")
    except (Exception, KeyboardInterrupt):
        pass

def empty_syringe(stepper):

    #Retour à la position 0 à la fin
    stepper.setTargetPosition(0)
    stepper.setEngaged(True)

    try:
        input("taper entrée pour arrêter. Retour à la position initiale\n")
    except (Exception, KeyboardInterrupt):
        pass

