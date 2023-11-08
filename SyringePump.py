"Classe SyringePump"

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.Stepper import *
import time


class SyringePump: #Nouvelle classe SyringePump globale : classe mère
        
    mode = 'manual' #peut être 'titration'

    #niveau courant des seringues
    acid_level_uL=None
    base_level_uL=None

    #monitoring de la dispense sur le titrage
    added_acid_uL = 0
    added_base_uL = 0
    added_total_uL = 0

    acid_dispense_log = []
    base_dispense_log = []
    
    def __init__(self, model):
        if model=='Phidget':
            self.model='Stepper Phidget'
            PhidgetStepperPump.__init__(self)
        elif model=='Legato':
            self.model='KDSLegato100'
            KDS_Legato100.__init__(self)
        else:
            self.model='unknown'


class PhidgetStepperPump(SyringePump): #remplace l'ancienne classe SyringePump
    
    stepper = Stepper() #contrôle du stepper
    security_switch = DigitalInput() #interrupteur bout de course seringue   
    reference_switch = DigitalInput() #interrupteur pour positionnement de référence
    electrovanne = DigitalOutput() #contrôle électrovannes
    
    def __init__(self,syringe_type='SGE500'):
        
        #print("self=",self)
        self.model='Phidget Stepper STC 10005_0 Syringe Pump'
        #Stepper
        self.stepper.setDeviceSerialNumber(683442)
        self.stepper.setHubPort(0)
        self.stepper.setChannel(0)
        try:
            self.stepper.openWaitForAttachment(4000)
            print("stepper connecté")
        except:
            print("stepper non connecté")
            pass
        
        if self.stepper.getIsOpen():
            print("limite de courant actuelle : ", self.stepper.getCurrentLimit())
            self.stepper.setCurrentLimit(0.2) #0.1A
            print("limite de courant après réglage : ", self.stepper.getCurrentLimit())
            self.stepper.setVelocityLimit(20)
            print("limite de vittesse stepper : ", self.stepper.getVelocityLimit())
            self.stepper.setAcceleration(5)
            print("acceleration stepper : ", self.stepper.getAcceleration())
            if syringe_type=='SGE500': #Trajan SGE 500uL
                self.stepper.setRescaleFactor(-0.013115) 
                #450uL dispensés sur une échelle de 30500 positions avec scale factor=1
                #soit 76,25 microsteps pour 1 uL.     
                self.size = 450 #en uL : c'est le volume utilse de la seringue. 
                #Sur une seringue de 500uL j'utilise un volume utile de 400uL
                #Pour ne pas toucher le bout de la seringue
            else:
                #par défaut c'est une 500uL SGE...
                print("dans le else")
                self.stepper.setRescaleFactor(-0.01303) #avant 0.013115
            print("rescale factor = ", self.stepper.getRescaleFactor())

        #Interrupteurs, electrovanne
        self.security_switch.setDeviceSerialNumber(432846)
        self.security_switch.setChannel(0)
        self.reference_switch.setDeviceSerialNumber(432846)
        self.reference_switch.setChannel(1)
        self.electrovanne.setDeviceSerialNumber(432846)
        self.electrovanne.setChannel(0)
        try:
            self.security_switch.openWaitForAttachment(1000)
            self.reference_switch.openWaitForAttachment(1000)
            self.electrovanne.openWaitForAttachment(1000)
        except:
            pass
    
    def getIsOpen(self):
    #cette fonction ne garantit pas que tous les appareils passifs sont branchés
    #Il s'agit seulement des Phidgets
    #Cela permet de ne pas avoir d'erreurs lors de l'exécution mais ne garantit pas 
    #qu'un interrupteur de sécurité ne soit mal branché. 
        if self.stepper.getIsOpen() and self.electrovanne.getIsOpen():
            #la carte est branchée ainsi que le stepper
            state=True
        else:
            state=False
        return state
    
    def close(self):
        self.stepper.close()
        self.security_switch.close()
        self.reference_switch.close()
        self.electrovanne.close()

    def SecurityStop(self, security_switch, state): #à modifier
        if state == 0:
            print("security stop \nself:",self,"security_switch:",security_switch,"state",state)
            self.stepper.setEngaged(False)
            print("interrupteur ouvert : arrêt du moteur")
        else:
            print("interrupteur fermé")

    def ReferenceStop(self, reference_switch, state):
        if state == 0:
            print("reference stop \nself:",self,"\nreference_switch:",reference_switch,"state",state)
            self.stepper.setEngaged(False)
            print("interrupteur de référence ouvert : arrêt du moteur")
            self.goToZeroPosition()
        else: #moteur qui tourne vers 
            print("interrupteur fermé ReferenceStop")      
            self.setReference()

    def goToZeroPosition(self): #se déclenche suite à la pression sur l'interrupteur de réf     
        self.simple_dispense(62,ev=0)
        self.setReference()
        print("Moteur remis en position initiale : prêt à dispenser")
    
    def motorStopped(self): #agit sur un objet Stepper
        self.setEngaged(False)
        time.sleep(2) #marge pour stabilisation du moteur
    
    def waitForStop(self):
        #cette fonction tourne jusqu'à ce que le moteur s'arrête
        mv=self.stepper.getEngaged()
        print("mv=",mv)
        if mv==True:
            print("start of movement")
            while(self.stepper.getEngaged()==True):
                pass
            print("end of movement")
        else:
            print("no movement")
    
    def engageMovement(self):
        #cas général : rail au milieu, aucun interrupteur enfoncé
        if self.security_switch.getState()==True and self.reference_switch.getState()==True:
            print("moteur au milieu au début")
            self.security_switch.setOnStateChangeHandler(self.SecurityStop)
            self.stepper.setOnStoppedHandler(PhidgetStepperPump.motorStopped)     
            self.reference_switch.setOnStateChangeHandler(self.ReferenceStop)
            self.stepper.setOnStoppedHandler(PhidgetStepperPump.motorStopped)                 
        #interrupteur de référence enfoncé
        elif self.security_switch.getState()==True and self.reference_switch.getState()==False:    
            print("interrupteur référence enfoncé")
            self.security_switch.setOnStateChangeHandler(self.SecurityStop)
            self.stepper.setOnStoppedHandler(PhidgetStepperPump.motorStopped)
        #interrupteur de sécurité enfoncé 
        elif self.reference_switch.getState()==True and self.security_switch.getState()==False:
            print("interrupteur sécu enfoncé")
            self.reference_switch.setOnStateChangeHandler(self.ReferenceStop)
            self.stepper.setOnStoppedHandler(PhidgetStepperPump.motorStopped)    
        else:
            print("problème sur les interrupteurs :\
        Au moins 1 ne fonctionne pas correctement ")   
        print("Motor rotating, press ctrl+Z to Stop\n")
        try:
            #print("aa")
            self.stepper.setEngaged(True)
            #print("aa")
            self.waitForStop()
            #print("aa")
        except(KeyboardInterrupt):
            self.stepper.setEngaged(False)         
    
    def configForDispense(self,ev=1): #ev=1 electrovanne en position de dispense
        #paramètres stepper
        self.stepper.setCurrentLimit(0.4)
        self.stepper.setAcceleration(1)
        self.stepper.setVelocityLimit(10)
        print("config pour dispense : \n\
            vitesse limite = ",self.stepper.getVelocityLimit(),"\n\
            limite en courant (A) : ", self.stepper.getCurrentLimit() )
        if ev==1:#electrovanne sur le mode dispense
            time.sleep(1)
            self.electrovanne.setState(True)
            print("etat de l'electrovanne : ",self.electrovanne.getState())
            time.sleep(1)

    def configForRefill(self): #ev=0 electrovanne en position de recharge
        #paramètres stepper
        self.stepper.setCurrentLimit(0.2)
        self.stepper.setAcceleration(5)
        self.stepper.setVelocityLimit(20)
        print("config pour recharge : \n\
            vitesse limite = ",self.stepper.getVelocityLimit(),"\n\
            limite en courant (A) : ", self.stepper.getCurrentLimit() )
        if self.electrovanne.getState()==True: #toujours mettre l'electrovanne off pour recharger
            time.sleep(1)
            self.electrovanne.setState(False)
            time.sleep(1)

    def simple_dispense(self,vol,ev=1):
        pos0 = self.stepper.getPosition()
        print("position avant dispense : ",pos0)
        if vol <= self.size-pos0:
            self.configForDispense(ev)
            self.stepper.setTargetPosition(pos0+vol)
            #lancement
            self.engageMovement()
            #On repasse en mode recharge (electrovanne hors tension)
            time.sleep(1)
            self.electrovanne.setState(False)
            time.sleep(1)
            #affichage de la position atteinte
            position = self.stepper.getPosition()
            print("Position atteinte après dispense: ", position)
            if ev==1:
                delta=round((position-pos0),0)
                self.added_base_uL+=delta
                self.added_total_uL+=delta
                self.base_dispense_log.append(delta)
                print("volume cumulé de base ajouté = ", self.added_base_uL)
                print("volume cumulé de fluide ajouté = ", self.added_total_uL)
        else:
            print("Volume diponible dans la seringue insuffisant, \
                  la dispense doit se faire en plusieurs étapes")

    def simple_refill(self,vol):   
        pos0=self.stepper.getPosition()
        self.configForRefill()
        self.stepper.setTargetPosition(pos0-vol) #recharge donc target supérieur à position courante
        #lancement
        self.engageMovement()
        #affichage de la position atteinte
        position = self.stepper.getPosition()
        print("Position atteinte après recharge: ", position)
    
    def full_refill(self):
        pos0=self.stepper.getPosition()
        self.configForRefill()
        self.stepper.setTargetPosition(-500) #recharge donc target supérieur à position courante
        #lancement
        self.engageMovement()
        #affichage de la position atteinte
        position = self.stepper.getPosition()
        print("Position atteinte après recharge: ", position)

    def setZeroPosition(self):
        dx = int(input("entrer le déplacement voulu : "))
        if dx<0:
            self.simple_refill(-dx) #
        else:
            self.simple_dispense(dx)
        pos=self.stepper.getPosition()
        self.stepper.addPositionOffset(-pos)
        pos1=self.stepper.getPosition()
        print("position du moteur après mise à zéro : ", pos1)
    
    def setReference(self):
        pos=self.stepper.getPosition()
        self.stepper.addPositionOffset(-pos)
        pos1=self.stepper.getPosition()
        print("position du moteur après mise à zéro : ", pos1)
    
    #def refill(self, vol):

    #def dispense(self, vol):
    
    def empty_syringe(self, vol):
        pos0=self.stepper.getPosition()
        self.configForDispense(0) #electrovanne connectée sur recharge
        self.stepper.setTargetPosition(self.size) #recharge donc target supérieur à position courante
        #lancement
        self.engageMovement()
        #affichage de la position atteinte
        position = self.stepper.getPosition()
        print("Position atteinte après vidage: ", position)


if __name__=="__main__":
    sp=PhidgetStepperPump()
    #sp.setZeroPosition()
    #sp.simple_dispense(100)


class KDS_Legato100(SyringePump):
    #Le pousse seringue doit être configuré en amont avec la bonne seringue

    def __init__(self):
        self.ser=serial.Serial('COM3', timeout = 2, stopbits=2)  #COM3 peut changer, à vérifier
        print(self.ser)
        self.dir = DigitalInput() #direction courante
        self.dir.setDeviceSerialNumber(432846)
        self.dir.setChannel(7)
        self.movement = DigitalInput() #mouvement en cours ou pas
        self.movement.setDeviceSerialNumber(432846)
        self.movement.setChannel(5)
        self.electrovanne=DigitalOutput() #contrôle electrovanne
        self.electrovanne.setDeviceSerialNumber(432846)
        self.electrovanne.setChannel(0)
        try:
            self.dir.openWaitForAttachment(1000)
            self.movement.openWaitForAttachment(1000)    
            self.electrovanne.openWaitForAttachment(1000) 
        except:
            pass
        
        self.size=300    #définition de la courser complète (en mL)
    
    def setValveOnRefill(self):
        time.sleep(1)
        self.electrovanne.setState(False)
        time.sleep(1)
    
    def setValveOnDispense(self):
        time.sleep(1)
        self.electrovanne.setState(True)
        time.sleep(1)

    def send(self,cmd): #envoyer une commande en RS232
        command=cmd+"\r"
        command_ascii=[]
        for ch in command:
            ch3=ord(ch) #code ascii
            #print(ch, ch3)
            command_ascii.append(ch3)
        #print(command_ascii)
        bytes_command=bytearray(command_ascii) #conversion en bytes
        #print(bytes_command)
        self.ser.write(bytes_command) #renvoie le byte string given 
        y=0
        x=self.ser.in_waiting
        while(y==0 or x!=0):
            if x > 0:
                #print("ser.in_waiting=",x)
                out = self.ser.read(100)
                answer=out.decode()
                y=1
            else:
                y=0
                pass
            x=self.ser.in_waiting
        print(answer)
        #print(out)
    
    def waitForStop(self):
        #attendre le signal de la seringue annonçant le moteur s'arrete
        mv=self.movement.getState()
        #print("mv=",mv)
        if mv==True:
            print("start of movement")
            while(self.movement.getState()==True):
                pass
            print("end of movement")
        else:
            print("no movement")

    def simple_dispense(self,vol,pos):
        self.setValveOnDispense()
        stroke=self.size-pos
        if vol>stroke:
            print("erreur : ne peut pas faire une simple dispense")
        else: #vol<=stroke
            if vol!=0:
                self.send("cvolume") #impératif pour pas avoir le message erreur
                print("simple dispense of %d uL"%vol)
                self.send("tvolume %d u" %vol)
                self.send("irun")
                self.waitForStop()
            else: #volume nul 
                pass   
            ending_position=pos+vol    
            return ending_position
            
    def dispense(self,vol,pos): 
        # vol: volume (uL) 
        # pos: position avant dispense (uL)  /!\ impératif /!\
        stroke=self.size-pos #le type de dispense en dépend
        
        #dispense simple
        if vol<=stroke: 
            ending_position=self.simple_dispense(vol,pos)
        
        #dispense en plusieures parties
        else: 
            #Calcul des quatités
            vol2=vol-stroke #reste à dispenser après un aller en bout de course
            q=vol2//self.size;r=vol2%self.size
            print("Déroulé de la dispense :\nvolume=%duL (bout de course) \n+%d*%duL (nombre de courses)\
                   \n+%duL (dernière dispense)" % (stroke, q, self.size ,r))
            
            #Première dispense jusqu'en bout de course
            self.simple_dispense(stroke, pos)
            print("première dispense de %d uL effectuée"%stroke)
            #input("Tapez entrée pour recharger")
            self.refill(self.size)
            #input("Taper entrée pour dispenser")
            
            #dispenses course complète
            for n in range(q):
                self.simple_dispense(self.size,0)
                print(" %d dispense(s) sur course complète effectuée(s) sur %d"%(n+1,q))
                #input("taper entrée pour recharger") #les input seront 
                #à remplacer par des commandes sur l'électrovanne pour security_switcher (dispense/recharge)
                self.refill(self.size)
                #input("taper entrée pour dispenser")

            #dernière dispense avec le reste
            self.simple_dispense(r,0)   
            print("dernière dispense de %d uL effectuée"%r)
            ending_position=r #remainder of euclidian division 
        
        print("ending position : %d"%ending_position)
        return ending_position

    def refill(self,pos):
        self.setValveOnRefill()
        if (self.electrovanne.getState()==False): #Attention à ne pas recharger la seringue avec
            #l'électrovanne en position dispense. La valve anti-retour va bloquer et la seringue 
            #soit va caler, soit va prendre de l'air où elle peut (donc bulles) soit va endommanger la
            #valve anti retour. 
            self.send("cvolume")
            self.send("tvolume %d u" %pos)
            self.send("wrun")
            self.waitForStop()

    def run_sequence(self,seq):
    # seq est une liste de volumes en microlitres [50, 30, 20, 10, 15, 30, 80, 200] par exemple
        a=input("Voulez-vous recharger la seringue ? 'y' for YES, any key otherwise : ")
        #Recharge optionnelle au début
        if a=='y':
            self.refill(self.size)
        else:
            pass
        pos=0 #position courante de la seringue
        #séquence de dispenses
        for vol in seq:
            #("taper entrée pour dispenser la séquence suivante")
            #if volume_count<=self.size:
            end_pos=self.dispense(vol,pos) 
            pos=end_pos
            print("position courante: ", pos)
        #input("Taper entrée pour remettre la seringue en position initiale")
        self.refill(pos) #remet en position initiale


