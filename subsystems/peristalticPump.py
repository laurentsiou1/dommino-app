"Classe permettant de controller le moteur de pompe péristaltique"

from Phidget22.Phidget import *
from Phidget22.Devices.DCMotor import *
import time

class PeristalticPump(DCMotor): #Elle est créée comme une sous classe de DCMotor

    def __init__(self):
        DCMotor.__init__(self)
        self.setDeviceSerialNumber(683442)
        self.setChannel(0)
        self.setHubPort(2)
        self.state='closed'

    def connect(self):
        try:
            self.openWaitForAttachment(4000)
            print("moteur de pompe alimenté")
            #sécu
            self.setCurrentLimit(1) #1A
            self.setAcceleration(0.5)
            #param
            self.direction=1 # +1 or -1 according to the direction
            self.mean_voltage=4
            self.duty_cycle=self.mean_voltage/12
            self.target_speed=self.direction*self.duty_cycle
            self.current_speed=self.getTargetVelocity()
            print("moteur configuré:\n\
            limite de courant (A):",self.getCurrentLimit(),\
            "\nAcceleration: ",self.getAcceleration(),\
            "\nDuty cycle: ", self.duty_cycle,\
            "\nAverage Voltage (V) : ", self.duty_cycle*12,\
            "\nDirection : ", self.direction, "\n")
            self.state='open'
        except:
            print("moteur de pompe non alimenté")
            self.state='closed'

    def setSpeed_voltage(self,v):
        self.duty_cycle=v/12
        self.target_speed=self.duty_cycle*self.direction
        self.current_speed=self.getTargetVelocity()
        if self.current_speed!=0:   #pour pouvoir changer la vitesse sans reappuyer sur start
            self.setTargetVelocity(self.target_speed)

    def start(self):
        self.setTargetVelocity(self.target_speed)

    def stop(self): 
        self.setTargetVelocity(0)        

    def change_direction(self):
        self.stop()
        time.sleep(1)
        self.direction*=-1
        self.start()


if __name__=="__main__":
    pump = PeristalticPump()
    pump.close()
