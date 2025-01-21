"Classe permettant de controller le moteur de pompe péristaltique"

from Phidget22.Phidget import *
from Phidget22.Devices.DCMotor import *
import time

from configparser import ConfigParser
import os
from pathlib import Path

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #répertoire pytitrator
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")


class PeristalticPump(DCMotor): #Elle est créée comme une sous classe de DCMotor

    parser = ConfigParser()
    parser.read(device_ids)
    board_number = int(parser.get('main board', 'id'))
    VINT_number = int(parser.get('VINT', 'id'))

    def __init__(self):
        DCMotor.__init__(self)
        self.setDeviceSerialNumber(self.VINT_number)  #683442
        self.setChannel(0)
        self.setHubPort(3)
        self.state='closed'
        self.duty_cycle=0
        self.circuit_delay_sec=30
        self.update_infos()

    def connect(self):
        try:
            self.openWaitForAttachment(4000)
            print("moteur de pompe alimenté")
            #sécu
            self.setCurrentLimit(1) #1A
            self.setAcceleration(0.5)
            #param
            self.direction=1 # +1 or -1 according to the direction
            parser = ConfigParser()
            parser.read(app_default_settings)
            voltage=parser.get('pump', 'speed_volts')
            print("voltage=",voltage)
            self.mean_voltage=float(voltage)
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
        self.update_infos()

    def update_infos(self):
        if self.state=='open':
            self.infos="Peristaltic Pump : Connected"\
            +"\nPump model : 12VDC Motor"\
            +"\nCircuit delay : "+str(self.circuit_delay_sec)+"seconds"\
            +"\nCurrent speed (Volts) : "+str(self.mean_voltage)
        else:
            self.infos="Peristaltic pump not connected"

    #@require_attribute('state', 'open')
    def setSpeed_voltage(self,v):
        self.mean_voltage=v
        self.duty_cycle=v/12
        self.target_speed=self.duty_cycle*self.direction
        self.current_speed=self.getTargetVelocity()
        if self.current_speed!=0:   #pour pouvoir changer la vitesse sans reappuyer sur start
            self.setTargetVelocity(self.target_speed)
        self.update_infos()

    #@require_attribute('state', 'open')
    def start(self):
        if self.state=='open':
            self.setTargetVelocity(self.target_speed)

    #@require_attribute('state', 'open')
    def stop(self): 
        if self.state=='open':
            self.setTargetVelocity(0)        

    #@require_attribute('state', 'open')
    def change_direction(self):
        self.stop()
        time.sleep(1)
        self.direction*=-1
        self.start()
    
    def close(self):
        self.stop()
        self.state='closed'
        print("Peristaltic pump closed")

if __name__=="__main__":
    pump = PeristalticPump()
    pump.close()
