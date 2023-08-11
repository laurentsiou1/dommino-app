"interface intulisant les modules créés sur qt designer et traduits en python"
# source
# https://realpython.com/qt-designer-python/#creating-a-dialog-with-qt-designer-and-python

import sys

from PyQt5.QtWidgets import (QApplication, QDialog, QMainWindow, QMessageBox)
from PyQt5.uic import loadUi

from controlPannel import ControlPannel

def launchIHM(phm,spec,sp):
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = ControlPannel(phm,spec)
    ui.setupUi(MainWindow)   
    MainWindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launch()