"Fenetre de controle des seringues"

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from ui.syringe_panel import Ui_SyringePanel

#import os
#from pathlib import Path
from configparser import ConfigParser

#path = Path(__file__)
#ROOT_DIR = path.parent.absolute()
#app_default_settings = os.path.join(ROOT_DIR, "../config/app_default_settings.ini")

class SyringeWindow(QDialog,Ui_SyringePanel): #(object)
    
    def __init__(self, ihm, parent=None):
        #graphic
        super(SyringeWindow,self).__init__(parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        
        self.ihm=ihm
        self.dispenser=ihm.dispenser
        self.syringeA=self.dispenser.syringe_A
        self.syringeB=self.dispenser.syringe_B
        self.syringeC=self.dispenser.syringe_C

        #affichage des paramètres courants
        self.checkbox_A.setChecked(self.syringeA.use)   #bool
        self.checkbox_B.setChecked(self.syringeB.use)
        self.checkbox_C.setChecked(self.syringeC.use)
        self.reagentA.setPlainText(self.syringeA.reagent)   #string
        self.reagentB.setPlainText(self.syringeB.reagent)
        self.reagentC.setPlainText(self.syringeC.reagent)
        self.Ca.setValue(self.syringeA.concentration)   #float
        self.Cb.setValue(self.syringeB.concentration)
        self.Cc.setValue(self.syringeC.concentration)

        #Mise en gris des cases non utilisées
        if self.checkbox_A.isChecked()==False:
            self.reagentA.setDisabled(True)
            self.Ca.setDisabled(True)
            self.levelbarA.setDisabled(True)
            self.levelA_uL.setDisabled(True)
            self.full_reload_A.setDisabled(True)
            self.make_ref_A.setDisabled(True)
            self.load_button_A.setDisabled(True)
            self.load_box_A.setDisabled(True)
            self.unload_button_A.setDisabled(True)
            self.unload_box_A.setDisabled(True)
            self.dispense_button_A.setDisabled(True)
            self.dispense_box_A.setDisabled(True)

        if self.checkbox_B.isChecked()==False:
            self.reagentB.setDisabled(True)
            self.Cb.setDisabled(True)
            self.levelbarB.setDisabled(True)
            self.levelB_uL.setDisabled(True)
            self.full_reload_B.setDisabled(True)
            self.make_ref_B.setDisabled(True)
            self.load_button_B.setDisabled(True)
            self.load_box_B.setDisabled(True)
            self.unload_button_B.setDisabled(True)
            self.unload_box_B.setDisabled(True)
            self.dispense_button_B.setDisabled(True)
            self.dispense_box_B.setDisabled(True)

        if self.checkbox_C.isChecked()==False:
            self.reagentC.setDisabled(True)
            self.Cc.setDisabled(True)
            self.levelbarC.setDisabled(True)
            self.levelC_uL.setDisabled(True)
            self.full_reload_C.setDisabled(True)
            self.make_ref_C.setDisabled(True)
            self.load_button_C.setDisabled(True)
            self.load_box_C.setDisabled(True)
            self.unload_button_C.setDisabled(True)
            self.unload_box_C.setDisabled(True)
            self.dispense_button_C.setDisabled(True)
            self.dispense_box_C.setDisabled(True)

        #connexions pour modifs
        self.buttonBox.accepted.connect(self.updateDefaultParameters)
        self.checkbox_A.clicked.connect(self.update_syringes_config)
        self.checkbox_B.clicked.connect(self.update_syringes_config)
        self.checkbox_C.clicked.connect(self.update_syringes_config)
        self.reagentA.textChanged.connect(self.update_syringes_config)
        self.reagentB.textChanged.connect(self.update_syringes_config)
        self.reagentC.textChanged.connect(self.update_syringes_config)
        self.Ca.valueChanged.connect(self.update_syringes_config)
        self.Cb.valueChanged.connect(self.update_syringes_config)
        self.Cc.valueChanged.connect(self.update_syringes_config)



    def update_syringes_config(self):
        self.syringeA.use=self.checkbox_A.isChecked()   #bool
        self.syringeB.use=self.checkbox_B.isChecked()
        self.syringeC.use=self.checkbox_C.isChecked()
        self.syringeA.reagent=self.reagentA.toPlainText()    #string
        self.syringeB.reagent=self.reagentB.toPlainText()
        self.syringeC.reagent=self.reagentC.toPlainText()
        self.syringeA.concentration=self.Ca.value()     #float
        self.syringeB.concentration=self.Cb.value()
        self.syringeC.concentration=self.Cc.value()

    def updateDefaultParameters(self):
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        file = open(self.ihm.app_default_settings,'r+')
        parser.set(self.dispenser.syringe_A.id, 'use', str(self.syringeA.use))
        parser.set(self.dispenser.syringe_A.id, 'reagent', str(self.syringeA.reagent))
        parser.set(self.dispenser.syringe_A.id, 'concentration', str(self.syringeA.concentration))
        parser.set(self.dispenser.syringe_B.id, 'use', str(self.syringeB.use))
        parser.set(self.dispenser.syringe_B.id, 'reagent', str(self.syringeB.reagent))
        parser.set(self.dispenser.syringe_B.id, 'concentration', str(self.syringeB.concentration))
        parser.set(self.dispenser.syringe_C.id, 'use', str(self.syringeC.use))
        parser.set(self.dispenser.syringe_C.id, 'reagent', str(self.syringeC.reagent))
        parser.set(self.dispenser.syringe_C.id, 'concentration', str(self.syringeC.concentration))
        parser.write(file)
        file.close()