from configparser import ConfigParser

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog
from graphic.windows.sequence_cfg_win import Ui_sequenceConfig

#from IHM import IHM
from automatic_sequences import AutomaticSequence, ClassicSequence, CustomSequence

class SequenceConfigWindow(QDialog,Ui_sequenceConfig): #(object)
    
    def __init__(self, ihm, parent=None):
        super(SequenceConfigWindow,self).__init__(parent)
        self.setupUi(self)
        self.ihm=ihm

        self.parser = ConfigParser()
        self.parser.read(ihm.app_default_settings)

        #graphique
        #défaut
        self.dispense_mode.setCurrentText(self.ihm.dispense_mode)
        self.sequence_config_file.setText(self.ihm.sequence_config_file)
        self.fixed_delay_box.setValue(self.ihm.fixed_delay_sec)
        self.agitation_delay_box.setValue(self.ihm.mixing_delay_sec)
        #mise en gris
        self.grey_out_widgets()

        #connexions
        self.browse1.clicked.connect(self.browseConfigFile)
        self.saving_folder.setText(self.ihm.saving_folder)  #dossier de sauvegarde
        self.browse.clicked.connect(self.browsefolder)
        self.dialogbox.accepted.connect(self.updateSettings)
        self.dialogbox.accepted.connect(self.launchTitration)
        self.dispense_mode.currentTextChanged.connect(self.grey_out_widgets)

    def grey_out_widgets(self):
        if self.dispense_mode.currentText()=="from file":
            self.Nmes.setDisabled(True)
            self.pH_init.setDisabled(True)
            self.pH_fin.setDisabled(True)
            self.fixed_delay_box.setDisabled(True)
            self.agitation_delay_box.setDisabled(True)
            self.sequence_config_file.setDisabled(False) #chemin fichier de sequence
        else:
            self.Nmes.setDisabled(False)
            self.pH_init.setDisabled(False)
            self.pH_fin.setDisabled(False)
            self.fixed_delay_box.setDisabled(False)
            self.agitation_delay_box.setDisabled(False)
            self.sequence_config_file.setDisabled(True) #chemin du fichier de sequence

    def browsefolder(self):
        fld=self.parser.get('saving parameters', 'folder')  #affichage par défaut
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder', fld)
        self.saving_folder.setText(folderpath) #affichage du chemin de dossier
        self.ihm.saving_folder=self.saving_folder.text()
        self.ihm.updateDefaultParam()
    
    def browseConfigFile(self):
        seq_file=self.parser.get('custom sequence', 'sequence_file')  #affichage par défaut à l'ouverture
        filepath, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Select File', seq_file, filter="*.csv")
        self.sequence_config_file.setText(filepath) #affichage du chemin de dossier
        self.ihm.sequence_config_file=filepath
    
    def launchTitration(self):
        
        if self.dispense_mode.currentText() == "from file":
            config = [self.exp_name.toPlainText(),self.description.toPlainText(),self.OM_type.currentText(),\
            self.concentration.value(),bool(self.oxygen_box.currentText()),str(self.ihm.fibers),\
            str(self.ihm.flowcell),self.V0.value(),self.dispense_mode.currentText(),\
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
            "\nFibres : ", str(self.ihm.fibers),\
            "\nFlowcell : ",str(self.ihm.flowcell),\
            
            "\nMode de dispense : ","from file",\
            "\nFichier de configuration de séquence : ",self.sequence_config_file.text(),\
            "\nDossier de sauvegarde du titrage : ",self.ihm.seq.saving_folder)

        else:
            config = [self.exp_name.toPlainText(),\
            self.description.toPlainText(),\
            self.OM_type.currentText(),\
            self.concentration.value(),\
            bool(self.oxygen_box.currentText()),\
            str(self.ihm.fibers),\
            str(self.ihm.flowcell),\
            self.V0.value(),\
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
            "\nFibres : ",str(self.ihm.fibers),\
            "\nFlowcell : ",str(self.ihm.flowcell),\
            "\nMode de dispense : ",self.dispense_mode.currentText(),\
            "\nVolume initial (mL) : ", self.V0.value(),\
            "\npH initial : ",self.ihm.seq.pH_start,\
            "\npH final : ",self.ihm.seq.pH_end,\
            "\nNombre de mesures : ",self.ihm.seq.N_mes,\
            "\nFidex delay for pumping (seconds): ", self.ihm.seq.fixed_delay_sec,\
            "\nMixing delay for pump pausing (seconds): ", self.ihm.seq.mixing_delay_sec,\
            "\nDossier de sauvegarde du titrage : ",self.ihm.seq.saving_folder)
    
    def updateSettings(self):
        self.ihm.dispense_mode=self.dispense_mode.currentText()
        self.ihm.fixed_delay_sec=int(self.fixed_delay_box.value())
        self.ihm.mixing_delay_sec=int(self.agitation_delay_box.value())
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        file = open(self.ihm.app_default_settings,'r+')
        parser.set('sequence','dispense_mode',self.dispense_mode.currentText())
        parser.set('custom sequence', 'sequence_file',self.sequence_config_file.text())
        parser.set('classic titration sequence', 'fixed_delay_sec', str(self.fixed_delay_box.value()))
        parser.set('classic titration sequence', 'mixing_delay_sec', str(self.agitation_delay_box.value()))
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
    ui = SequenceConfigWindow(ihm,win)
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
