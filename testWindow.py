import sys
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi

class SavingConfig(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi('../config_enregistrement2.ui', self)
        self.browse.clicked.connect(self.browsefolder)
        

    def browsefolder(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', "C:/Users/francois.ollitrault/Desktop")
        self.folder_name.setText(folderpath)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SavingConfig()
    win.show()
    sys.exit(app.exec())