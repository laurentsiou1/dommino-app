"Fenetre de controle des seringues"

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from ui.syringe_panel import Ui_SyringePanel

#from windowHandler import WindowHandler
#from IHM import IHM

class SyringeWindow(QDialog,Ui_SyringePanel): #(object)
    
    def __init__(self, ihm, parent=None):
        super(SyringeWindow,self).__init__(parent)
        self.setupUi(self)

#Lancement direct du programme avec run
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ihm=IHM()
    win=WindowHandler(ihm)
    ui = SyringeWindow(ihm,win)
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())