"Program to execute for launching application"

from PyQt5 import QtWidgets
from IHM import IHM

#Lancement application
import sys
qApp = QtWidgets.QApplication(sys.argv)
app=IHM()
app.openControlPanel() 
sys.exit(qApp.exec_())

# [INFO] - Version Github FO du 28.03.2025 - ajout des modifications LS