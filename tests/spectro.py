"Test de moyennage sur le spectro"

"""
#La fonction récupère un spectre issu du moyennage sur le Spectro
#ça fonctionne mais c'est plus lent que de moyenner sur l'ordinateur
    def get_spectrum_internal_averaging(self, avg):
        try:
            Spectrometer.set_scans_to_average(self.device,avg) #avg est le nombre de moyennage
        	#numb_pixel = len(device.get_formatted_spectrum()) #nb de points du spectre
        	#spectra_m = [0 for x in range(numb_pixel)]
            mean_spectra = self.device.get_formatted_spectrum() #acquisition du spectre
        except OceanDirectError as e:
        	logger.error(e.get_error_details())
        return mean_spectra
"""

#Pour test des fonctions de la classe
if __name__ == "__main__":

    od = OceanDirectAPI()
    device_count = od.find_usb_devices() # 1 si appareils détectés
    device_ids = od.get_device_ids()
    device_count = len(device_ids)
    #print("\nNombre d'appareils OceanDirect détectés : ", device_count)
    #print("ID spectros: ", device_ids)
    if device_ids!=[]:
        id=device_ids[0]
        print("Spectro connecté")
        device = od.open_device(id) #crée une instance de la classe Spectrometer
        absorbance_unit=AbsorbanceMeasure(od,device)
        adv = Spectrometer.Advanced(device)
        """
        #ref et dark
        absorbance_unit.acquire_ref_and_dark_spectra()

        #test de get spectrum
        spec=AbsorbanceMeasure.get_averaged_corrected_spectrum(absorbance_unit)
        #print(spec)
        """
        
        #dark
        try:
            input("taper entrer lorsque le shutter est fermé")
        except(KeyboardInterrupt):
            pass
        absorbance_unit.acquire_background_spectrum()

        #ref
        try:
            input("taper entrer lorsque le shutter est ouvert")
        except(KeyboardInterrupt):
            pass
        absorbance_unit.acquire_ref_spectrum()

        #sample
        try:
            input("taper entrer lorsque le shutter est ouvert")
        except(KeyboardInterrupt):
            pass
        spec=absorbance_unit.get_averaged_spectrum()

        #tracé
        absorbance_unit.add_spectrum_to_plot(spec)
        absorbance_unit.add_spectrum_to_plot(absorbance_unit.active_background_spectrum,'intensity')
        absorbance_unit.add_spectrum_to_plot(absorbance_unit.active_ref_spectrum,'intensity')
    
        plt.legend() #tracé
        plt.show()
        

        device.details()
        print(device.get_device_type())
        print(device.get_model())
        print(device.model_name,device.model)
        print(device.get_serial_number())
        print(device.serial_number)




        #fermeture
        absorbance_unit.close_shutter()
        print("shutter ouvert ? ",adv.get_enable_lamp())
        print("shutter fermé")
        device.close_device()
        print("device closed")