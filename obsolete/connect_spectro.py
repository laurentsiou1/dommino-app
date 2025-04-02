"test de connexion d'un nouveau spectro"

from subsystems.oceandirect.OceanDirectAPI import OceanDirectError, OceanDirectAPI, Spectrometer, FeatureID
from subsystems.oceandirect.od_logger import od_logger
logger = od_logger()

try: #dépend depuis où est lancé le programme
    import subsystems.processing as sp 
except:
    pass

def connect():
    od = OceanDirectAPI()
    device_count = od.find_usb_devices() #ne pas enlever cette ligne pour détecter le spectro
    device_ids = od.get_device_ids()
    if device_ids!=[]:
        id=device_ids[0]
        try:
            spectro = od.open_device(id) #crée une instance de la classe Spectrometer
            adv = Spectrometer.Advanced(spectro)
            name = spectro.model_name
            print(name)
            model = spectro.get_model()
            print(model)
            state='open'
            print("Spectro connecté")
        except:
            print("Ne peut pas se connecter au spectro numéro ", id)
            state='closed'
    else:
        state='closed'
        print("Spectro non connecté")
    print("ID spectro: ", device_ids)

connect()