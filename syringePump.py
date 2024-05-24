"Classe SyringePump"

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.Stepper import *
import time
import dispense_data

"""def dispense_function(pH,coefs,x0):
    [y0, ba, ca, bb, cb] = coefs
    if type(pH)!=list:
        if pH<=y0:
            x=x0-ba*(10**((y0-pH)/ca)-1)
        else:
            x=x0+bb*(10**((pH-y0)/cb)-1)
    else:
        x=[]
        for y in pH:
            if y<=y0:
                x.append(x0-ba*(10**((y0-y)/ca)-1))
            else:
                x.append(x0+bb*(10**((y-y0)/cb)-1))
    return x"""

def volumeToAdd_uL(current, target, model='fixed volumes'): #pH courant et cible, modèle choisi par défaut le 5/05
    if model=='5th order polynomial fit on dommino 23/01/2024':
        vol = dispense_data.get_volume_to_dispense_uL(current,target)
    return int(vol)

def getPhStep(current):
    #fonction donnant le pas de pH à viser en fonction du pH. 
    #fonction affine en deux parties. C'est un triangle. 
    #A pH4 le pas est de 0.3. Il est de 0.5 à pH6.5 et de 0.4 à pH10
    if current<=6.5:
        step=0.08*current-0.02
    else:
        step=-0.028*current+0.68
    return step

#global GAIN_ON_PH_STEP
GAIN_ON_PH_STEP = 0.5

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


"Fenetre de controle des seringues"
#from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from ui.syringe_panel import Ui_SyringePanel

class SyringeWindow(QDialog,Ui_SyringePanel): #(object)
    
    def __init__(self, ihm, win, parent=None):
        super(SyringeWindow,self).__init__(parent)
        self.setupUi(self)


class PhidgetStepperPump(SyringePump): #remplace l'ancienne classe SyringePump
    
    stepper = Stepper() #contrôle du stepper
    security_switch = DigitalInput() #interrupteur bout de course seringue   
    reference_switch = DigitalInput() #interrupteur pour positionnement de référence
    electrovanne = DigitalOutput() #contrôle électrovannes
    
    def __init__(self,syringe_type='SGE500'): #par défaut une SGE500uL
        self.syringe_type=syringe_type
        #print("syringe type : ",self.syringe_type)
        self.state='closed'

    def connect(self):
        self.model='Phidget Stepper STC 10005_0 Syringe Pump'
        #Stepper
        self.stepper.setDeviceSerialNumber(683442)
        self.stepper.setHubPort(0)
        self.stepper.setChannel(0)
        try:
            self.stepper.openWaitForAttachment(4000)
            print("stepper connecté")
            print("limite de courant actuelle : ", self.stepper.getCurrentLimit())
            self.stepper.setCurrentLimit(0.2) #0.1A
            print("limite de courant après réglage : ", self.stepper.getCurrentLimit())
            self.stepper.setVelocityLimit(20)
            print("limite de vittesse stepper : ", self.stepper.getVelocityLimit())
            self.stepper.setAcceleration(5)
            print("acceleration stepper : ", self.stepper.getAcceleration())
            if self.syringe_type=='SGE500': #Trajan SGE 500uL
                #rescale factor calculé le 25/01/2024
                print("le syringe type est bon")
                self.stepper.setRescaleFactor(-0.01298) #rescale factor = -0.013115 avant 25/01/2024
                #baisse le rescale factor augmente la course
                #450uL dispensés sur une échelle de 30500 positions avec scale factor=1
                #soit 76,25 microsteps pour 1 uL.     
                self.size = 400 #en uL : c'est le volume utilse de la seringue. 
                #uL use only 400 on a 500uL syringe
                #Pour ne pas toucher le bout de la seringue
            else:
                print("dans le else")
                self.stepper.setRescaleFactor(-0.01303) #avant 0.013115
            print("rescale factor = ", self.stepper.getRescaleFactor())
        except:
            print("stepper non connecté")
        
        #Interrupteurs, electrovanne
        self.security_switch.setDeviceSerialNumber(432846)
        self.security_switch.setChannel(1)
        self.reference_switch.setDeviceSerialNumber(432846)
        self.reference_switch.setChannel(0)
        
        self.electrovanne.setDeviceSerialNumber(432846)
        self.electrovanne.setChannel(1)
        print(self.reference_switch)
        print(self.electrovanne)
        try:
            self.security_switch.openWaitForAttachment(1000)
            self.reference_switch.openWaitForAttachment(1000)
            self.electrovanne.openWaitForAttachment(1000)
            print("electrovanne et interrupteurs connectés")
        except:
            print("problème pour la connexion de l'électrovanne ou des interrupteurs")
        
        if (self.stepper.getIsOpen() and self.security_switch.getIsOpen() and \
        self.reference_switch.getIsOpen() and self.electrovanne.getIsOpen()):
            self.state='open'
        else:
            self.state='closed'
        #L'attribut state ne garantit pas que tous les appareils passifs sont branchés
        #Il s'agit seulement des Phidgets
        #Cela permet de ne pas avoir d'erreurs lors de l'exécution mais ne garantit pas 
        #qu'un interrupteur de sécurité ne soit mal branché. 

        if self.state=='open':
            self.reference_switch.setOnStateChangeHandler(self.ReferenceStop)
            self.security_switch.setOnStateChangeHandler(self.SecurityStop)
            self.base_level_uL=self.size
            #self.stepper.setOnStoppedHandler(PhidgetStepperPump.onMotorStop)  #test

    def ForceStop(self):
        self.stepper.setEngaged(False)
        print("arrêt forcé du stepper")

    def SecurityStop(self, security_switch, state): #à modifier
        if state == False: #l'interrupteru vient de s'ouvrir : on stop puis on recharge un peu
            print("security stop \nself:",self,"security_switch:",security_switch,"state",state)
            self.stepper.setEngaged(False)
            print("interrupteur ouvert : arrêt du moteur")
            self.simple_refill(54) #54uL ajusté à l'oeil
            self.base_level_uL=0
        else:   #l'interrupteur se referme, le moteur repart de l'autre côté, rien à faire
            pass

    def ReferenceStop(self, reference_switch, state):
        if state == False:
            self.stepper.setEngaged(False)
            print("reference switch open : motor stop")
            time.sleep(2) #stabilisation du moteur
            self.configForDispense(ev=0)
            #calculé pour revenir sur le trait 500 à partir de l'interrupteur
            #dépend de la seringue, des tubings, de l'ensemble
            self.stepper.setTargetPosition(self.stepper.getPosition()+50) #valeur le 25/01 #+62 jusqu'à présent
            
            self.stepper.setEngaged(True)
            print("start of movement")
            while(self.stepper.getIsMoving()==True):
                pass
            self.stepper.setEngaged(False)
            print("end of movement")
            time.sleep(2) #stabilisation méca du steper
            self.base_level_uL=self.size
            self.setReference()
            print("Moteur remis en position initiale : prêt à dispenser")
        else: #le piston se remet en position 0, rien à faire 
            pass

    
    def validity_code(self):
        target=self.stepper.getTargetPosition()-self.stepper.getPosition()
        #cas général : aucun interrupteur enfoncé, tout mouvement est possible
        if self.security_switch.getState()==True and self.reference_switch.getState()==True: #les sécurités sont fonctionnelles
            print("moteur au milieu au début")
            code=0
            if abs(target)>=1:
                valid=True
            else:
                valid=False
        #interrupteur de référence enfoncé
        elif self.security_switch.getState()==True and self.reference_switch.getState()==False:    
            print("interrupteur référence enfoncé")
            code=1
            if target>=1:
                valid=True
            else: 
                print("mauvaise direction, bout de course")
                valid=False
        #interrupteur de sécurité enfoncé 
        elif self.security_switch.getState()==False and self.reference_switch.getState()==True:
            code=2
            if target<=-1:
                valid=True
            else: 
                print("mauvaise direction, bout de course")
                valid=False
        else:
            code=3
            valid=False
            print("problème sur les interrupteurs : Au moins 1 non branché")   
        return code, valid
        
    
    def configForDispense(self,ev=1): #ev=1 electrovanne en position de dispense
        #paramètres stepper
        self.stepper.setCurrentLimit(0.4)
        self.stepper.setAcceleration(1)
        self.stepper.setVelocityLimit(10)
        #print("config pour dispense : \n\
        #    vitesse limite = ",self.stepper.getVelocityLimit(),"\n\
        #    limite en courant (A) : ", self.stepper.getCurrentLimit() )
        if ev==1:#electrovanne sur le mode dispense
            time.sleep(1)
            self.electrovanne.setState(True)
            print("etat de l'electrovanne : ",self.electrovanne.getState())
            time.sleep(1)

    def configForRefill(self): #ev=0 electrovanne en position de recharge
        #paramètres stepper
        self.stepper.setCurrentLimit(0.4)
        self.stepper.setAcceleration(3)
        self.stepper.setVelocityLimit(20)
        #print("config pour recharge : \n\
        #    vitesse limite = ",self.stepper.getVelocityLimit(),"\n\
        #    limite en courant (A) : ", self.stepper.getCurrentLimit() )
        if self.electrovanne.getState()==True: #toujours mettre l'electrovanne off pour recharger
            time.sleep(1)
            self.electrovanne.setState(False)
            time.sleep(1)

    def simple_dispense(self,vol,ev=1):
        pos0 = self.stepper.getPosition()
        #print("position avant dispense : ",pos0)
        if ev==1:
            print("syringe level before dispense = ",self.base_level_uL)
        else:
            print("syringe level before unfill = ", self.base_level_uL)
        disp=False #par défaut, avant dispense : pas encore de dispense effectuée
        if vol >= 0 and vol <= self.size-pos0+10:   
            #+10 est une marge pour pouvoir dépasser légèrement le niveau complet     
            self.configForDispense(ev)
            self.stepper.setTargetPosition(pos0+vol)
            #lancement
            code,valid=self.validity_code()
            if valid:
                self.stepper.setEngaged(True)
                print("start of movement")
                while(self.stepper.getIsMoving()==True):
                    pass
                print("end of movement")
                time.sleep(2) #stabilisation méca du steper
                self.stepper.setEngaged(False)
                self.electrovanne.setState(False) #On repasse en mode recharge (electrovanne hors tension)
                time.sleep(1)
                #affichage de la position atteinte
                position = self.stepper.getPosition()
                delta=round((position-pos0),0)
                self.base_level_uL-=delta
                #print("Position atteinte après dispense: ", position)
                #print("syringe level = ",self.base_level_uL)
                if ev==1:
                    self.added_base_uL+=delta
                    self.added_total_uL+=delta
                    self.base_dispense_log.append(delta)
                    disp=True #seulement si toutes les conditions sont réunies, la dispense\
                    #aura eu lieu
        elif vol<0:
            print("Impossible de dispenser : volume négatif")
        else:   #volume trop grand
            print("Volume diponible dans la seringue insuffisant, \
                  la dispense doit se faire en plusieurs étapes")
        return disp #bool about dispense was achived or not 
    
    def dispense(self, vol):
        #prévoir le cas où le piston touche le bout (car mauvaise valeur de position initiale)
        # 
        # il faut savoir compter la quantité lors de l'arrêt. 
        # Puis recharger
        # Puis reprendre la dispense là où elle s'est arrêtée. 

        print("début de dispense %f uL" %vol)
        capacity=self.size
        level=self.base_level_uL
        q=vol//capacity
        r=vol%capacity
        print("q,r=",q,r)
        if vol<=level: #cas classique de simple dispense
            self.simple_dispense(vol)
        else:           #vol>level
            r2=r-level
            print("r2=",r2)
            if r2<=0: #r<=level     #On peut dispenser le reste sans recharger
                #donc on commence par dispenser le reste
                self.simple_dispense(r)
                self.full_refill()
                #puis les dispenses entières
                for i in range(q):
                    self.simple_dispense(capacity)
                    self.full_refill()
            else: #r>level:     #Le reste est supérieur au niveau de la seringue
                print("recharge pour dispense du reste")
                self.full_refill()
                self.simple_dispense(r)
                self.full_refill()
                for i in range(q):
                    self.simple_dispense(capacity)
                    self.full_refill()
        print("fin de dispense %f uL" %vol)


    def simple_refill(self,vol):   
        print(self)
        pos0=self.stepper.getPosition()
        self.configForRefill()
        self.stepper.setTargetPosition(pos0-vol) #recharge donc target supérieur à position courante
        #lancement
        code,valid=self.validity_code()
        if valid:
            self.stepper.setEngaged(True)
            print("start of movement")
            while(self.stepper.getIsMoving()==True): #◙getEngaged
                pass
            print("end of movement")
            time.sleep(2)
            self.stepper.setEngaged(False)
            #affichage de la position atteinte
            position = self.stepper.getPosition()
            print("Position atteinte après recharge: ", position)
            delta=round((position-pos0),0)
            self.base_level_uL-=delta #idelta est negatif
    
    #def refill(self, vol):
    
    def full_refill(self):
        pos0=self.stepper.getPosition()
        self.configForRefill()
        self.stepper.setTargetPosition(pos0-2*self.size) #recharge donc target supérieur à position courante
        #lancement
        code,valid=self.validity_code()
        if valid:
            self.stepper.setEngaged(True)
            print("start of movement")
            while(self.stepper.getIsMoving()==True):
                pass
            print("arrivée en butée")
            time.sleep(20) #attente que le moteur se remette sur la référence
    
    def setReference(self): #permet de remettre à zéro la position mesurée par le stepper
        pos=self.stepper.getPosition()
        print("position du moteur avant remise à zéro : ",pos)
        self.stepper.addPositionOffset(-pos)
        pos1=self.stepper.getPosition()
        print("Remise à zéro. Position: ",pos1)

    
    def close(self):
        self.stepper.close()
        self.security_switch.close()
        self.reference_switch.close()
        self.electrovanne.close()
    
    """def setZeroPosition(self):
        dx = int(input("entrer le déplacement voulu : "))
        if dx<0:
            self.simple_refill(-dx) #
        else:
            self.simple_dispense(dx)
        pos=self.stepper.getPosition()
        self.stepper.addPositionOffset(-pos)
        pos1=self.stepper.getPosition()
        print("position du moteur après mise à zéro : ", pos1)"""

    """
    def empty_syringe(self, vol):
        pos0=self.stepper.getPosition()
        self.configForDispense(0) #electrovanne connectée sur recharge
        self.stepper.setTargetPosition(self.size) #recharge donc target supérieur à position courante
        #lancement
        self.validity_code()
        #affichage de la position atteinte
        position = self.stepper.getPosition()
        print("Position atteinte après vidage: ", position)"""


if __name__=="__main__":
    sp=PhidgetStepperPump()
    sp.connect()
    sp.full_refill()
    sp.dispense(100)
    #sp.setZeroPosition()
    #sp.simple_refill(50)
    #sp.simple_dispense(100,0)


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


