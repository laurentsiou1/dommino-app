"Fenetre de controle des seringues"

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from graphic.windows.syringe_panel import Ui_SyringePanel

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
        
        self.ihm=ihm
        self.dispenser=ihm.dispenser
        self.syringe_A=self.dispenser.syringe_A
        self.syringe_B=self.dispenser.syringe_B
        self.syringe_C=self.dispenser.syringe_C

        #affichage des paramètres courants
        self.syringeA.setEnabled(self.syringe_A.use)   #bool
        self.syringeB.setEnabled(self.syringe_B.use)
        self.syringeC.setEnabled(self.syringe_C.use)
        self.reagentA.setText(self.syringe_A.reagent)   #string
        self.reagentB.setText(self.syringe_B.reagent)
        self.reagentC.setText(self.syringe_C.reagent)
        self.Ca.setText(str(self.syringe_A.concentration))   #float
        self.Cb.setText(str(self.syringe_B.concentration))
        self.Cc.setText(str(self.syringe_C.concentration))
        self.refresh_volumes()

        #Mise en gris des cases non utilisées
        if self.syringe_A.use==False:
            self.reagentA.setDisabled(True)
            self.Ca.setDisabled(True)
            self.levelbarA.setDisabled(True)
            self.levelA_uL.setDisabled(True)
            self.full_reload_button_A.setDisabled(True)
            self.make_ref_A.setDisabled(True)
            self.load_button_A.setDisabled(True)
            self.load_box_A.setDisabled(True)
            self.unload_button_A.setDisabled(True)
            self.unload_box_A.setDisabled(True)
            self.dispense_button_A.setDisabled(True)
            self.dispense_box_A.setDisabled(True)

        if self.syringe_B.use==False:
            self.reagentB.setDisabled(True)
            self.Cb.setDisabled(True)
            self.levelbarB.setDisabled(True)
            self.levelB_uL.setDisabled(True)
            self.full_reload_button_B.setDisabled(True)
            self.make_ref_B.setDisabled(True)
            self.load_button_B.setDisabled(True)
            self.load_box_B.setDisabled(True)
            self.unload_button_B.setDisabled(True)
            self.unload_box_B.setDisabled(True)
            self.dispense_button_B.setDisabled(True)
            self.dispense_box_B.setDisabled(True)

        if self.syringe_C.use==False:
            self.reagentC.setDisabled(True)
            self.Cc.setDisabled(True)
            self.levelbarC.setDisabled(True)
            self.levelC_uL.setDisabled(True)
            self.full_reload_button_C.setDisabled(True)
            self.make_ref_C.setDisabled(True)
            self.load_button_C.setDisabled(True)
            self.load_box_C.setDisabled(True)
            self.unload_button_C.setDisabled(True)
            self.unload_box_C.setDisabled(True)
            self.dispense_button_C.setDisabled(True)
            self.dispense_box_C.setDisabled(True)

        #connexions pour moteurs
        #reference
        self.make_ref_A.disconnect()
        self.make_ref_A.clicked.connect(self.ref_A)
        self.make_ref_B.disconnect()
        self.make_ref_B.clicked.connect(self.ref_B)
        self.make_ref_C.disconnect()
        self.make_ref_C.clicked.connect(self.ref_C)
        #stop
        self.stop.disconnect()
        self.stop.clicked.connect(self.dispenser.stop)
        #reset
        self.reset.disconnect()
        self.reset.clicked.connect(self.reset_volume_count)
        #mouvement on syringe
        self.unload_button_A.disconnect()
        self.unload_button_A.clicked.connect(self.unload_A)
        self.unload_button_B.disconnect()
        self.unload_button_B.clicked.connect(self.unload_B)
        self.unload_button_C.disconnect()
        self.unload_button_C.clicked.connect(self.unload_C)
        self.load_button_A.disconnect()
        self.load_button_A.clicked.connect(self.load_A)
        self.load_button_B.disconnect()
        self.load_button_B.clicked.connect(self.load_B)
        self.load_button_C.disconnect()
        self.load_button_C.clicked.connect(self.load_C)
        self.full_reload_button_A.disconnect()
        self.full_reload_button_A.clicked.connect(self.full_reload_A)
        self.full_reload_button_B.disconnect()
        self.full_reload_button_B.clicked.connect(self.full_reload_B)
        self.full_reload_button_C.disconnect()
        self.full_reload_button_C.clicked.connect(self.full_reload_C)
        self.dispense_button_A.disconnect()
        self.dispense_button_A.clicked.connect(self.dispense_A)
        self.dispense_button_B.disconnect()
        self.dispense_button_B.clicked.connect(self.dispense_B)
        self.dispense_button_C.disconnect()
        self.dispense_button_C.clicked.connect(self.dispense_C)
    
    def ref_A(self):
        self.syringe_A.setReference()
        self.refresh_volumes()
    def ref_B(self):
        self.syringe_B.setReference()
        self.refresh_volumes()
    def ref_C(self):
        self.syringe_C.setReference()
        self.refresh_volumes()
    def unload_A(self):
        vol=self.unload_box_A.value()
        self.syringe_A.simple_dispense(vol,ev=0)
        self.refresh_volumes()
    def unload_B(self):
        vol=self.unload_box_B.value()
        self.syringe_B.simple_dispense(vol,ev=0)
        self.refresh_volumes()
    def unload_C(self):
        vol=self.unload_box_C.value()
        self.syringe_C.simple_dispense(vol,ev=0)
        self.refresh_volumes()
    def load_A(self):
        vol=self.load_box_A.value()
        self.syringe_A.simple_refill(vol)
        self.refresh_volumes()
    def load_B(self):
        vol=self.load_box_B.value()
        self.syringe_B.simple_refill(vol)
        self.refresh_volumes()
    def load_C(self):
        vol=self.load_box_C.value()
        self.syringe_C.simple_refill(vol)
        self.refresh_volumes()
    def full_reload_A(self):
        self.syringe_A.full_refill()
        self.refresh_volumes()
    def full_reload_B(self):
        self.syringe_B.full_refill()
        self.refresh_volumes()
    def full_reload_C(self):
        self.syringe_C.full_refill()
        self.refresh_volumes()
    def dispense_A(self):
        vol=self.dispense_box_A.value()
        self.syringe_A.simple_dispense(vol)
        self.refresh_volumes()
    def dispense_B(self):
        vol=self.dispense_box_B.value()
        self.syringe_B.simple_dispense(vol)
        self.refresh_volumes()
    def dispense_C(self):
        vol=self.dispense_box_C.value()
        self.syringe_C.simple_dispense(vol)
        self.refresh_volumes()

    def reset_volume_count(self):
        self.syringe_A.added_vol_uL=0
        self.syringe_B.added_vol_uL=0
        self.syringe_C.added_vol_uL=0
        self.dispenser.vol.added_total_uL=0
        self.refresh_volumes()

    def refresh_volumes(self):
        self.levelbarA.setProperty("value", self.syringe_A.level_uL)
        self.levelA_uL.setText("%d uL" % self.syringe_A.level_uL)
        self.levelbarB.setProperty("value", self.syringe_B.level_uL)
        self.levelB_uL.setText("%d uL" % self.syringe_B.level_uL)
        self.levelbarC.setProperty("value", self.syringe_C.level_uL)
        self.levelC_uL.setText("%d uL" % self.syringe_C.level_uL)
        self.added_A_uL.setText("%d" %self.syringe_A.added_vol_uL)
        self.added_B_uL.setText("%d" %self.syringe_B.added_vol_uL)
        self.added_C_uL.setText("%d" %self.syringe_C.added_vol_uL)
        self.added_total.setText("%d" %self.dispenser.vol.added_total_uL)
        self.ihm.controlPanel.refresh_volumes() #Sur controlPanel également
    
    def update_syringes_config(self):
        self.syringe_A.use=self.checkbox_A.isChecked()   #bool
        self.syringe_B.use=self.checkbox_B.isChecked()
        self.syringe_C.use=self.checkbox_C.isChecked()
        self.syringe_A.reagent=self.reagentA.toPlainText()    #string
        self.syringe_B.reagent=self.reagentB.toPlainText()
        self.syringe_C.reagent=self.reagentC.toPlainText()
        self.syringe_A.concentration=self.Ca.value()     #float
        self.syringe_B.concentration=self.Cb.value()
        self.syringe_C.concentration=self.Cc.value()