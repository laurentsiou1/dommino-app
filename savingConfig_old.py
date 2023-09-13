import sys
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi

class SavingConfig(QDialog):
    def __init__(self):
        super(SavingConfig,self).__init__()
        loadUi("../config_enregistrement2.ui",self) #mettre le bon ui
        self.browse.clicked.connect(self.browsefolder)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        #self.buttonBox.accepted.connect(self.accept) # le nom de la mainwindow
        #self.buttonBox.rejected.connect(self.reject)
        #QtCore.QMetaObject.connectSlotsByName(self)

    def browsefolder(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', "C:/Users/francois.ollitrault/Desktop")
        self.folder_name.setText(folderpath)

if __name__ == "__main__":
    app=QApplication(sys.argv)
    window=SavingConfig()
    widget=QtWidgets.QStackedWidget()
    widget.addWidget(window)
    widget.setFixedWidth(800)
    widget.setFixedHeight(300)
    widget.show()
    sys.exit(app.exec_())