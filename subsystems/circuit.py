"Class for controlling pump motor along with electrovalves of measure circuit"

#from Phidget22.Devices.DigitalOutput import *

from subsystems.peristalticPump import PeristalticPump
from subsystems.electrovalve import Electrovalve
from PyQt5.QtCore import QTimer
import threading

from configparser import ConfigParser
import os
from pathlib import Path

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #répertoire pytitrator
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")

def require_pump_and_valves_connected(func):
    def wrapper(self, *args, **kwargs):
        if self.pump.state=='closed':
            raise Exception("Pump not connected")
        elif self.ev_state=='closed':
            raise Exception("Electrovalve not connected")
        return func(self, *args, **kwargs)
    return wrapper

class Circuit(): #la classe hérite des méthodes de la pompe

    app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
    #timer = QTimer()

    def __init__(self, pump : PeristalticPump):   #pump est un objet de la classe pump, passé en argument
        
        self.pump=pump
        self.ev0 = Electrovalve('circuit entrance')
        self.ev1 = Electrovalve('circuit exit')
        self.state='closed'

        parser = ConfigParser()
        parser.read(app_default_settings)
        self.circulation_delay_sec=int(parser.get('circuit', 'delay_sec'))  #delay of circulation at lowest speed (4V)

    def connect(self):
        self.pump.connect()
        self.ev0.connect()
        self.ev1.connect()
        self.updateState()
        self.update_infos()
        print(self.infos)

    def updateState(self):
        if self.pump.state=='open' and self.ev0.channel_state=='open' and self.ev1.channel_state=='open':
            self.state='open'
        else:
            self.state='closed'
    
    def update_infos(self):
        self.pump.update_infos()
        self.infos=self.pump.infos
        if self.state=='open':
            self.infos+=("\nElectrovalves : Connected"
            +"\nEntrance valve ev0 : "+str(self.ev0.state)
            +"\nExit valve ev1 : "+str(self.ev1.state))
        else:
            self.infos+="\nElectrovalves not connected"
    
    def close(self):
        if self.pump.state=='open':
            self.pump.close_pump()
        self.ev0.close()
        self.ev1.close()
        self.state='closed'

    def ev0_changeState(self):
        self.ev0.changeState()

    def ev1_changeState(self):
        self.ev1.changeState()

    def ev0_display(self):
        pass

    #Basic sequences in circuit
    """These sequences are basic actions on circuit. They can be used directly on the interface
    or also be runned as part of larger sequences defined in class System"""

    #button empty --> empty_circuit()
    #button water --> flush_water() #flushes indefinitely
    #button fill all --> fill_all()

    def empty(self):
        """Empties circuit by running pump from OUT to IN back in the sample beaker"""
        self.pump.stop()
        self.ev0.setState(False)
        self.ev1.setState(False)    #valves are set IN OUT
        self.pump.set_direction(-1)
        self.pump.set_speed_scale(5)
        self.pump.start()
    
    def runWater(self,delay=None):
        """Flush water from WATER to BIN
        delay : integer in seconds
        Executed function when pressing button Water
        Circuit needs to be empty when using this function, not to contaminate water"""
        # #Not to contaminate water when switching valve 
        #self.empty()
        self.ev0.setState(True)
        self.ev1.setState(True)    #valves are set IN OUT
        self.pump.set_direction(1)
        self.pump.set_speed_scale(5)
        self.pump.start()

        
        ###fill_all
    def fill_all(self):
        """Fills BIN and OUT with water. Then fills IN, and refills BIN"""
        self.runWater()
        timer = threading.Timer(10, self.fill_all_2)    #circuit in considered clean we just fill
        timer.start()
    
    def fill_all_2(self):
        self.ev1.setState(False)
        timer = threading.Timer(5, self.fill_all_3)     #fill the OUT way
        timer.start()
    
    def fill_all_3(self):
        self.pump.stop()
        self.ev0.setState(False)
        self.ev1.setState(True)
        self.pump.set_direction(-1)
        self.pump.set_speed_scale(1)
        self.pump.start()
        timer = threading.Timer(12, self.fill_all_4)     
        #at speed 3 we fill during 5seconds to fill to IN way
        timer.start()
    
    def fill_all_4(self):
        self.pump.stop()
        self.ev0.setState(True)
        self.pump.set_direction(1)
        self.pump.set_speed_scale(5)
        self.pump.start()
        timer = threading.Timer(10, self.fill_all_end)  #time to refill measure cell and OUT tubings
        timer.start()

    def fill_all_end(self):
        self.pump.stop()
        self.ev0.setState(False)
        self.ev1.setState(False)

        
        ###Clean and empty
    def clean_and_empty(self):
        """Empty measure circuit"""
        self.empty()
        timer = threading.Timer(12, self.clean_and_empty_2)
        timer.start() 

    def clean_and_empty_2(self):
        """Clean circuit from water to bin"""
        self.pump.stop()
        self.runWater()
        timer = threading.Timer(24, self.clean_and_empty_3)    #2times the circuit delay for cleaning
        timer.start()

    def clean_and_empty_3(self):    
        """Clean the OUT way of circuit"""
        self.ev1.setState(False)
        timer = threading.Timer(12, self.clean_and_empty_4)     #8sec for the OUT way
        timer.start() 

    def clean_and_empty_4(self):    #run pump in the opposite direction
        """Empties the measure circuit"""
        print("clean empty 4")
        self.pump.stop()
        #time.sleep(1)
        self.pump.change_direction()
        self.ev0.setState(False)
        self.ev1.setState(False)     #water gets out of BIN
        self.pump.start()
        timer = threading.Timer(12, self.clean_and_empty_end) #10sec to empty
        timer.start() 
    
    def clean_and_empty_end(self):
        self.pump.stop()
        self.pump.set_direction(1)
        #self.updateState

    def empty_circuit_button(self):
        """Executed function when pressing button Empty"""
        self.empty()
        timer = threading.Timer(12, self.pump.stop)
        timer.start()    
