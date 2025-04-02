"""Fenêtre Pop up - Demande pour quitter la séquence sur mesure"""

from PyQt5.QtWidgets import QDialog
from graphic.windows.Exit_confirmation_win import Ui_PopUp_Exit_Confirmation

class ExitConfirmationWindow(QDialog, Ui_PopUp_Exit_Confirmation):
    def __init__(self, parent_window):  
        super(ExitConfirmationWindow, self).__init__(parent_window)  # Définit le parent pour garder le lien
        self.setupUi(self) # Charge l'interface graphique de la pop-up
        self.parent_window = parent_window  # Stocke la référence vers la fenêtre principale (CustomSequenceWindow)

        # Connexion des boutons
        self.buttonBox.accepted.connect(self.confirm_exit)  # Si on clique sur "Oui" - Associe la fonction confir_exit
        self.buttonBox.rejected.connect(self.reject)   # Si on clique sur "Non" (ferme juste la pop-up) - fonction reject utilisé a partir de pyQt --> QDialog

    def confirm_exit(self):
        """
        If users clicks on Yes
        - stops sequence
        - closes sequence window
        - closes confirmation window
        """
        self.parent_window.seq.stop()  # Stops current sequence
        self.parent_window.close()  # Closes sequence window (Custom_sequence_window)
        self.accept()  # Closes confirmation pop up