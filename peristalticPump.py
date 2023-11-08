"Classe permettant de controller le moteur de pompe péristaltique"

from Phidget22.Phidget import *
from Phidget22.Devices.DCMotor import *
import time

class PeristalticPump(DCMotor): #Elle est crée comme une sous classe de DCMotor

    def __init__(self):
        DCMotor.__init__(self)
        self.setDeviceSerialNumber(683442)
        self.setChannel(0)
        self.setHubPort(2)

        try:
            self.openWaitForAttachment(4000)
            print("moteur de pompe alimenté")
        except:
            print("moteur de pompe non alimenté")

        if self.getIsOpen():
            self.direction=1 # +1 or -1 according to the direction
            self.setCurrentLimit(1) #1A
            self.setAcceleration(0.5)
            self.velocity_rpm=60
            self.duty_cycle=(0.3+0.05*(self.velocity_rpm/60))*self.direction
            print("moteur configuré:\n\
            limite de courant (A):",self.getCurrentLimit(),\
            "\nAcceleration: ",self.getAcceleration(),\
            "\nDuty cycle: ", self.duty_cycle,\
            "\nAverage Voltage (V) : ", self.duty_cycle*12,\
            "\nDirection : ", self.direction, "\n")

    def setVelocity_rpm(self,omega):
        self.velocity_rpm=omega
        self.duty_cycle=0.3+0.05*(self.velocity_rpm/60)
        self.start()

    def start(self):
        self.setTargetVelocity(self.duty_cycle*self.direction)

    def stop(self): 
        self.setTargetVelocity(0)        

    def change_direction(self):
        self.stop()
        self.direction*=-1
        time.sleep(2)
        self.start()

if __name__=="__main__":
    pump = PeristalticPump()
    pump.close()
