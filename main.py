"Program to execute for launching application"

from PyQt5 import QtWidgets
from IHM import IHM

#Lancement application
import sys
qApp = QtWidgets.QApplication(sys.argv)
app=IHM()
app.openControlPanel() 
sys.exit(qApp.exec_())

# [End]