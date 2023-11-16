"Programme principal de l'application"

#modules et classes pour l'interface
from PyQt5 import QtWidgets
from controlPannel import ControlPannel
from IHM import IHM
from windowHandler import WindowHandler

### Lancement IHM ###

import sys
app = QtWidgets.QApplication(sys.argv)
MainWindow = QtWidgets.QMainWindow()
itf=IHM()
win=WindowHandler()
ui = ControlPannel(ihm=itf,win=win)
ui.setupUi(MainWindow)
MainWindow.show()        
sys.exit(app.exec_())


"""
https://www.hostinger.fr/tutoriels/commandes-git
Petit tuto des commandes git

Pour en faire un executable pour windows
https://www.pythonguis.com/tutorials/packaging-pyqt6-applications-windows-pyinstaller/
"""
