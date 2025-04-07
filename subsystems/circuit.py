"""
file circuit contains class Circuit
class Circuit allows to control peristaltic pump along with 2 electrovalves of measure circuit
"""

from subsystems.peristalticPump import PeristalticPump
from subsystems.electrovalve import Electrovalve
import threading    #for Timers

from configparser import ConfigParser
import os
from pathlib import Path

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #project directory
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")

def require_pump_and_valves_connected(func):
    """
    Decorator of methods for requiring both pump and electrovalves state opened.
    """
    def wrapper(self, *args, **kwargs):
        if self.pump.state=='closed':
            raise Exception("Pump not connected")
        elif self.ev_state=='closed':
            raise Exception("Electrovalve not connected")
        return func(self, *args, **kwargs)
    return wrapper

class Circuit():

    app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")

    def __init__(self, pump : PeristalticPump):   
        """
        pump is an object of type PeristalticPump. Has to be specified as argument
        """
        self.pump=pump
        self.ev0 = Electrovalve('circuit entrance')
        self.ev1 = Electrovalve('circuit exit')
        self.state='closed'

        parser = ConfigParser()
        parser.read(app_default_settings)
        self.circulation_delay_sec=int(parser.get('circuit', 'delay_sec'))  #delay of circulation at lowest speed (4V)

    def connect(self):
        """
        Connects the arguments of class : pump and electrovalves
        """
        self.pump.connect()
        self.ev0.connect()
        self.ev1.connect()
        self.updateState()
        self.update_infos()
        print(self.infos)

    def updateState(self):
        """
        Updates object state according to its attributes states
        """
        if self.pump.state=='open' and self.ev0.channel_state=='open' and self.ev1.channel_state=='open':
            self.state='open'
        else:
            self.state='closed'
    
    def state2Text(self, state):
        """
        Returns display on Connect/Disconnect button.
        """
        if state=='open':
            text="Disconnect"
        else:
            text="Connect"
        return text
    
    def update_infos(self):
        """
        Updates circuit informations with attributes infos.
        """
        self.pump.update_infos()
        self.infos=self.pump.infos
        if self.state=='open':
            self.infos+=("\nElectrovalves : Connected"
            +"\nEntrance valve ev0 : "+str(self.ev0.state)
            +"\nExit valve ev1 : "+str(self.ev1.state))
        else:
            self.infos+="\nElectrovalves not connected"
    
    def close(self):
        """
        Closes attributes.
        """
        if self.pump.state=='open':
            self.pump.close_pump()
        self.ev0.close()
        self.ev1.close()
        self.state='closed'

    def ev0_changeState(self):
        """
        ev0 is the Entrance valve (WATER/IN)
        """
        self.ev0.changeState()

    def ev1_changeState(self):
        """
        ev1 is the exit valve (OUT/BIN)
        """
        self.ev1.changeState()

    #Basic sequences in circuit
    """These sequences are basic actions on circuit. They can be used directly on the interface with buttons :
    run water, empty, fill water, clean and empty."""
    
    #button run water --> run_water() #flushes indefinitely
    #button empty --> empty_circuit_button()
    #button fill water --> fill_all()
    #button Clean and empty --> clean_and_empty()

    def empty_measure_circuit(self):
        """
        Empties circuit by running pump from OUT to IN back in the sample beaker.
        """
        self.pump.stop()
        self.ev0.setState(False)
        self.ev1.setState(False)    #valves are set IN OUT
        self.empty()
    
    def empty_water(self):
        """
        Releases clean water back in the water beaker.
        Used during sequence when taking a reference.
        """
        self.pump.stop()
        self.ev0.setState(True)
        self.ev1.setState(True)    #valves are set IN OUT
        self.empty()
    
    def empty(self):
        """
        Empties circuit as it is without changing electrovalves.
        """
        self.pump.set_direction(-1)
        self.pump.set_speed_scale(5)
        self.pump.start()
    
    def run_measure_circuit(self):
        """
        Function executed during sequence for circulating sample into the flowcell.
        """
        self.pump.set_direction(1)
        self.ev0.setState(False)
        self.ev1.setState(False)    #valves are set IN OUT
        self.pump.start()
    
    def run_water(self,speed=5,delay=None):
        """
        Flush water from WATER to BIN
        delay : integer in seconds
        Executed function when pressing button Water
        Circuit needs to be empty when using this function, not to contaminate water
        """
        self.pump.stop()
        self.ev0.setState(True)
        self.ev1.setState(True)    #valves are set IN OUT
        self.pump.set_direction(1)
        self.pump.set_speed_scale(speed)
        self.pump.start()
        
        ###fill_all
    def fill_all(self):
        """
        Fills BIN and OUT with water. Then fills IN, and refills BIN
        Cut in multiple methods 2, 3, 4, end.
        """
        self.run_water()
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
        
    def clean_and_empty(self):
        """
        Empties measure circuit, cleans all with water. And empties all.
        Cut in multiple methods : 2, 3, 4, end.
        """
        self.empty_measure_circuit()
        timer = threading.Timer(12, self.clean_and_empty_2)
        timer.start() 

    def clean_and_empty_2(self):
        """Clean circuit from water to bin"""
        self.pump.stop()
        self.run_water()
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
        self.pump.change_direction()
        self.ev0.setState(False)
        self.ev1.setState(False)     #water gets out of BIN
        self.pump.start()
        timer = threading.Timer(12, self.clean_and_empty_end) #10sec to empty
        timer.start() 
    
    def clean_and_empty_end(self):
        self.pump.stop()
        self.pump.set_direction(1)

    def empty_circuit_button(self):
        """
        Executed function when pressing button Empty
        """
        self.empty_measure_circuit()
        timer = threading.Timer(12, self.pump.stop)
        timer.start()    
