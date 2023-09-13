import sys
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog, QCheckBox
from PyQt5.uic import loadUi
from IHM import IHM

class SavingConfig(QDialog):
    def __init__(self, ihm: IHM, parent=None):
        super().__init__(parent)
        loadUi('../config_enregistrement.ui', self)
        self.ihm = ihm #création d'un attribut ihm dans SavingConfig

        #affichage du dossier de sauvegarde courant s'il existe
        self.folder_name.setText(self.ihm.saving_folder) #répertoire de la dernière utilisation
        self.save_absorbance.setChecked(bool(self.ihm.save_absorbance))
        self.save_pH.setChecked(bool(self.ihm.save_pH))
        self.save_titration_data.setChecked(bool(self.ihm.save_titration_data))
        self.additional_file_checkbox.setChecked(bool(self.ihm.create_detailed_param_file))
        self.compatibility_checkbox.setChecked(bool(self.ihm.compatible_format)) #avec traitement données
        
        #connection des boutons
        self.browse.clicked.connect(self.browsefolder) #browse folder
        
        self.buttonBox.accepted.connect(self.updateIHM) #mise à jour des attributs IHM
        self.buttonBox.accepted.connect(self.ihm.updateConfigFile) #puis maj dans le fichier de config
    
    def browsefolder(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', "C:/Users/francois.ollitrault/Desktop")
        self.folder_name.setText(folderpath) #affichage du chemin de dossier
        self.ihm.saving_folder=folderpath #mis à jour du nouveau répertoire dans IHM 

    def updateIHM(self):
        #self.ihm.saving_folder=self.folder_name.getText()
        self.ihm.save_absorbance=bool(self.save_absorbance.checkState())
        self.ihm.save_pH=bool(self.save_pH.checkState())
        self.ihm.save_titration_data=bool(self.save_titration_data.checkState())
        self.ihm.create_detailed_param_file=bool(self.additional_file_checkbox.checkState())
        self.ihm.compatible_format=bool(self.compatibility_checkbox.checkState())
        print(self.ihm.saving_folder,self.ihm.save_absorbance,self.ihm.save_pH)
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ihm=IHM()
    win = SavingConfig(ihm)
    win.show()
    sys.exit(app.exec())