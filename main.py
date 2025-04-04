"""
main.py : Program to execute for launching Dommino application
Updated April 4 2025
@autor : François Ollitrault, IDIL fibres optiques
"""

import sys
from PyQt5 import QtWidgets     #pyqt5 is the Qt graphic interface module for python
#IHM is the central class of the application. It handles both instruments and windows
from IHM import IHM     

qApp = QtWidgets.QApplication(sys.argv)
ihm=IHM()   #instance of class IHM. ihm 
ihm.openControlPanel() 
sys.exit(qApp.exec_())