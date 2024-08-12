from configparser import ConfigParser

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog
from graphic.windows.config_sequence import Ui_sequenceConfig

#from IHM import IHM
from automatic_sequences import AutomaticSequence, ClassicSequence, CustomSequence

class SequenceConfig(QDialog,Ui_sequenceConfig): #(object)
    
    def __init__(self, ihm, parent=None):
        super(SequenceConfig,self).__init__(parent)
        self.setupUi(self)
        self.ihm=ihm

        #graphique
        #défaut
        self.dispense_mode.setCurrentText(self.ihm.dispense_mode)
        self.sequence_config_file.setText(self.ihm.sequence_config_file)
        #mise en gris
        self.grey_out_widgets()

        self.browse1.clicked.connect(self.browseConfigFile)
        self.saving_folder.setText(self.ihm.saving_folder)  #dossier de sauvegarde
        self.browse.clicked.connect(self.browsefolder)
        self.dialogbox.accepted.connect(self.updateSettings)
        self.dialogbox.accepted.connect(self.launchTitration)
        self.dispense_mode.currentTextChanged.connect(self.grey_out_widgets)

    def grey_out_widgets(self):
        if self.dispense_mode.currentText()=="from file":
            self.V0.setDisabled(True)
            self.Nmes.setDisabled(True)
            self.pH_init.setDisabled(True)
            self.pH_fin.setDisabled(True)
            self.fixed_delay_box.setDisabled(True)
            self.agitation_delay_box.setDisabled(True)
            self.sequence_config_file.setDisabled(False) #chemin fichier de sequence
        else:
            self.V0.setDisabled(False)
            self.Nmes.setDisabled(False)
            self.pH_init.setDisabled(False)
            self.pH_fin.setDisabled(False)
            self.fixed_delay_box.setDisabled(False)
            self.agitation_delay_box.setDisabled(False)
            self.sequence_config_file.setDisabled(True) #chemin du fichier de sequence

    def browsefolder(self):
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', "H:/A Nouvelle arbo/DOCUMENTS TECHNIQUES/Projets Collaboratifs/DOMMINO/MESURES")
        self.saving_folder.setText(folderpath) #affichage du chemin de dossier
        self.ihm.saving_folder=self.saving_folder.text()
        self.ihm.updateSettings()
    
    def browseConfigFile(self):
        filepath, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Select File', "H:/A Nouvelle arbo/DOCUMENTS TECHNIQUES/Projets Collaboratifs/DOMMINO/CONCEPTION/V1/logiciel", filter="*.csv")
        self.sequence_config_file.setText(filepath) #affichage du chemin de dossier
        self.ihm.sequence_config_file=filepath
    
    def launchTitration(self):
        
        if self.dispense_mode.currentText() == "from file":
            config = [self.exp_name.toPlainText(),self.description.toPlainText(),self.OM_type.currentText(),\
            self.concentration.value(),bool(self.oxygen_box.currentText()),self.fibers.currentText(),\
            self.flowcell.currentText(),self.V0.value(),self.dispense_mode.currentText(),\
            self.sequence_config_file.text(),self.saving_folder.text()]#fichier de config de sequence

            self.ihm.seq=CustomSequence(self.ihm,config) #création de l'objet dans l'IHM
            self.ihm.seq.configure()
            self.ihm.seq.run_sequence()
            
            #affichage des données pour la séquence auto
            print("\nNom de l'expérience : ",self.exp_name.toPlainText(),\
            "\nDescription : ",self.description.toPlainText(),\
            "\nType de matière organique : ",self.OM_type.currentText(),\
            "\nConcentration : ",self.concentration.value(),\
            "\nPresence of oxygen : ",self.oxygen_box.currentText(),\
            "\nFibres : ",self.fibers.currentText(),\
            "\nFlowcell : ",self.flowcell.currentText(),\
            
            "\nMode de dispense : ","from file",\
            "\nFichier de configuration de séquence : ",self.sequence_config_file.text(),\
            "\nDossier de sauvegarde du titrage : ",self.ihm.seq.saving_folder)

        else:
            config = [self.exp_name.toPlainText(),\
            self.description.toPlainText(),\
            self.OM_type.currentText(),\
            self.concentration.value(),\
            bool(self.oxygen_box.currentText()),\
            self.fibers.currentText(),\
            self.flowcell.currentText(),\
            1000*self.V0.value(),\
            self.dispense_mode.currentText(),\
            self.Nmes.value(),\
            self.pH_init.value(),\
            self.pH_fin.value(),\
            self.fixed_delay_box.value(),\
            self.agitation_delay_box.value(),\
            self.saving_folder.text()]
            
            self.ihm.seq=ClassicSequence(self.ihm,config) #création de l'objet dans l'IHM
            self.ihm.seq.configure()
        
            #affichage des données pour la séquence auto
            print("\nNom de l'expérience : ",self.exp_name.toPlainText(),\
            "\nDescription : ",self.description.toPlainText(),\
            "\nType de matière organique : ",self.OM_type.currentText(),\
            "\nConcentration : ",self.concentration.value(),\
            "\nPresence of oxygen : ",self.oxygen_box.currentText(),\
            "\nFibres : ",self.fibers.currentText(),\
            "\nFlowcell : ",self.flowcell.currentText(),\
            "\nMode de dispense : ",self.dispense_mode.currentText(),\
            "\nVolume initial : ", self.V0.value(),\
            "\npH initial : ",self.ihm.seq.pH_start,\
            "\npH final : ",self.ihm.seq.pH_end,\
            "\nNombre de mesures : ",self.ihm.seq.N_mes,\
            "\nFidex delay between measures (seconds): ", self.ihm.seq.fixed_delay_sec,\
            "\nMixing delay for pump pausing (seconds): ", self.ihm.seq.mixing_delay_sec,\
            "\nFichier de configuration de séquence : ",self.ihm.seq.sequence_config_file,\
            "\nDossier de sauvegarde du titrage : ",self.ihm.seq.saving_folder)
    
    def updateSettings(self):
        self.ihm.dispense_mode=self.dispense_mode.currentText()

        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        file = open(self.ihm.app_default_settings,'r+')
        parser.set('custom sequence', 'sequence_file',self.sequence_config_file.text())
        parser.set('sequence','dispense_mode',self.dispense_mode.currentText())
        parser.set('saving parameters','folder',self.saving_folder.text())
        parser.write(file)
        file.close()

#Lancement direct du programme avec run
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ihm=IHM()
    win=WindowHandler()
    ui = SequenceConfig(ihm,win)
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
