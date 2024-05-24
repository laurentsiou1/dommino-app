"Classe pour gérer les différentes fenêtres de l'IHM"

#from IHM import IHM

from windows.main_window import MainWindow
"""from expConfig import ExpConfig
from calBox import CalBox
from spectrumConfig import SpectrumConfigWindow
from savingConfig import SavingConfig"""

from PyQt5 import QtWidgets
from windows.syringe_window import SyringeWindow

class WindowHandler():

    def __init__(self, ihm):
        self.ihm=ihm

    def openControlPanel(self):
        self.controlPanel=MainWindow(self.ihm)
        self.controlPanel.show()
    
    def openSpectroWindow(self):
        self.spectro_window = QtWidgets.QDialog()
        self.ui = SpectrumConfigWindow(self.spectro_unit,super(WindowHandler,self))
        self.ui.setupUi(self.spectro_window)
        self.spectro_window.show()
    
    def openSyringeWindow(self):
        self.syr_window=SyringeWindow(self.ihm)