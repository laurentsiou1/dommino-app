"Classe System qui contient des fonctions système utilisant plusieurs instruments"

from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *

from PyQt5.QtCore import QTimer

class System:

        timer = QTimer()

        def __init__(self, circuit, spectro_unit):
            """Définition des séquences impliquant à la fois le circuit et le spectromètre."""
            if circuit.state=='open' and spectro_unit.state=='open':
                self.state='open'
            else:    
                self.state='closed'


if __name__=="__main__":
        system=System()
        print(system.state)