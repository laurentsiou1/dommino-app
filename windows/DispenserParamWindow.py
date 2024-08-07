"""classe pour dispenser_param"""

from PyQt5.QtWidgets import QDialog

from ui.dispenser_param import Ui_Dialog    #fenetre créée sur Qt designer

"""import os
from pathlib import Path"""
from configparser import ConfigParser
"""path = Path(__file__)
ROOT_DIR = path.parent.absolute()
app_default_settings = os.path.join(ROOT_DIR, "../config/app_default_settings.ini")"""

class DispenserParamWindow(QDialog,Ui_Dialog): #(object)
    
    def __init__(self, ihm, parent=None):
        super(DispenserParamWindow,self).__init__(parent)
        self.setupUi(self)
        self.ihm=ihm

        #Sauvegarde de la config
        self.buttonBox.accepted.connect(self.update)

        #affichage des paramètres courants
        self.syringeA.setChecked(self.ihm.dispenser.syringe_A.use)   #bool
        self.syringeB.setChecked(self.ihm.dispenser.syringe_B.use)
        self.syringeC.setChecked(self.ihm.dispenser.syringe_C.use)
        self.reagentA.setText(self.ihm.dispenser.syringe_A.reagent)   #string
        self.reagentB.setText(self.ihm.dispenser.syringe_B.reagent)
        self.reagentC.setText(self.ihm.dispenser.syringe_C.reagent)
        self.Ca.setValue(self.ihm.dispenser.syringe_A.concentration)  #float
        self.Cb.setValue(self.ihm.dispenser.syringe_B.concentration)
        self.Cc.setValue(self.ihm.dispenser.syringe_C.concentration)
    
    def update(self):
        parser = ConfigParser()
        parser.read(self.ihm.app_default_settings)
        file = open(self.ihm.app_default_settings,'r+')
        parser.set('Syringe A', 'use', str(self.syringeA.isChecked()))
        parser.set('Syringe A', 'reagent', str(self.reagentA.toPlainText()))
        parser.set('Syringe A', 'concentration', str(self.Ca.value()))
        parser.set('Syringe B', 'use', str(self.syringeB.isChecked()))
        parser.set('Syringe B', 'reagent', str(self.reagentB.toPlainText()))
        parser.set('Syringe B', 'concentration', str(self.Cb.value()))
        parser.set('Syringe C', 'use', str(self.syringeC.isChecked()))
        parser.set('Syringe C', 'reagent', str(self.reagentC.toPlainText()))
        parser.set('Syringe C', 'concentration', str(self.Cc.value()))
        parser.write(file)
        file.close()
        
        self.ihm.dispenser.update_dispenser_param() #modif des attributs de la classe Dispenser