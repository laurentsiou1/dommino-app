"Classe System qui contient des fonctions système utilisant plusieurs instruments"

from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *

class System: 
        digitalOutput_test = DigitalOutput()
        digitalOutput_test.setDeviceSerialNumber(432846)
        def __init__(self):
                self.state='disconnected'
                sn=self.digitalOutput_test.getDeviceSerialNumber()
                print(sn)
                try:
                        self.digitalOutput_test.openWaitForAttachment(1000)
                except:
                        print("Board not powered or plugged")
                if self.digitalOutput_test.getIsOpen():
                        nb=self.digitalOutput_test.getDeviceSerialNumber()
                        name=self.digitalOutput_test.getDeviceClassName()
                        print("\nserial number : ",nb,"\nName : ", name)
                        self.state='connected'

if __name__=="__main__":
        system=System()
        print(system.state)
        

        """def acquire_ref_and_dark_spectra(self):
                self.adv.set_enable_lamp(False)
                time.sleep(2)
                #Prise du spectre d'obscurité
                dark_spectrum=self.get_averaged_spectrum()
                #print("dark_spectrum=",dark_spectrum, "len=",len(dark_spectrum))
                self.device.set_stored_dark_spectrum(dark_spectrum)
        
                self.adv.set_enable_lamp(True)
                print("shutter ouvert ? ",self.adv.get_enable_lamp())
                time.sleep(2)
                ref_spectrum_non_corrected=self.get_averaged_spectrum()
                #correction du dark spectrum et nonlinearité
                ref_spectrum=self.device.nonlinearity_correct_spectrum2(dark_spectrum,ref_spectrum_non_corrected)
                #print("ref_spectrum=",ref_spectrum, "len=",len(ref_spectrum))

                #actualisation des attributs
                self.active_dark_spectrum=dark_spectrum
                self.active_ref_spectrum=ref_spectrum #corrigé
        
                #ajout sur les graphes
                AbsorbanceMeasure.add_spectrum_to_plot(self,dark_spectrum,name='dark spectrum')
                AbsorbanceMeasure.add_spectrum_to_plot(self,ref_spectrum,name='ref spectrum')"""