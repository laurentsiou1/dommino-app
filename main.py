"Programme principal de l'application"

from PyQt5 import QtWidgets
from IHM import IHM

#Lancement application
import sys
qApp = QtWidgets.QApplication(sys.argv)
app=IHM()
app.openControlPanel() 
sys.exit(qApp.exec_())

"""
https://www.hostinger.fr/tutoriels/commandes-git
Petit tuto des commandes git

Pour en faire un executable pour windows
https://www.pythonguis.com/tutorials/packaging-pyqt6-applications-windows-pyinstaller/
"""
