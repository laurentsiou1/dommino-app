"""
Class Dispenser
Controls the set of three syringe pumps in the titration box
"""

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.Stepper import *

import time
from configparser import ConfigParser
import os
from pathlib import Path

path = Path(__file__)
ROOT_DIR = path.parent.parent.absolute() #répertoire pytitrator
app_default_settings = os.path.join(ROOT_DIR, "config/app_default_settings.ini")
device_ids = os.path.join(ROOT_DIR, "config/device_id.ini")

def getPhStep(current):
    """
    fonction donnant le pas de pH à viser en fonction du pH. 
    fonction affine en deux parties. C'est un triangle. 
    A pH4 le pas est de 0.3. Il est de 0.5 à pH6.5 et de 0.4 à pH10
    Working for sequence mode 'variable step'
    """
    if current<=6.5:
        step=0.08*current-0.02
    else:
        step=-0.028*current+0.68
    return step

def identifier(x):
    """
    Input 0, 1, 2 
    Returns : the identifier of syringes
    """
    if x==0:
        y='A'
    elif x==1:
        y='B'
    elif x==2:
        y='C'
    elif x=='A':
        y=0
    elif x=='B':
        y=1
    elif x=='C':
        y=2
    else:
        y='error'
    return y

def getChannel():
    if 'valve_in':
        ch=0
    elif 'valve_out':
        ch=1
    elif 'valve_A':
        ch=2
    elif 'valve_B':
        ch=3
    elif 'valve_C':
        ch=4
    return ch

def tobool(str):
    """
    Converts string 'True' or 'False' to boolean True and False
    """
    if str=='True' or str=='true':
        b=True
    else:
        b=False
    return b

class VolumeCount:

    def __init__(self):
        self.added_total_uL = 0
    
    def add(self, vol):
        self.added_total_uL+=vol

    def reset(self):
        self.added_total_uL = 0

class Dispenser:
    
    def __init__(self):
        self.vol=VolumeCount()
        #Syringe pumps are objects of class PhidgetStepperPump
        #3 syringes are attributes of object Dispenser
        self.syringe_A=PhidgetStepperPump('A',self.vol)
        self.syringe_B=PhidgetStepperPump('B',self.vol)
        self.syringe_C=PhidgetStepperPump('C',self.vol)
        self.syringes=[self.syringe_A,self.syringe_B,self.syringe_C]
        self.use=[self.syringe_A.use,self.syringe_B.use,self.syringe_C.use]
        self.update_infos()
        self.state='closed'
    
    def update_param_from_file(self):
        """
        Updates syringe pumps parameters from file app_default_settings.ini
        """
        self.syringe_A.update_param_from_file()
        self.syringe_B.update_param_from_file()
        self.syringe_C.update_param_from_file()
    
    def update_infos(self):
        """
        Combines infos of three syringes
        """
        self.refresh_state()
        self.infos=self.syringe_A.infos+"\n"+self.syringe_B.infos+"\n"+self.syringe_C.infos

    def refresh_state(self):
        """
        Dispenser state is 'open' only if 3 syringes are in state 'open'
        """
        connected=0
        use=0
        for syr in self.syringes:
            if syr.use==True:
                use=1
                if syr.state=='closed':
                    connected=-10
                    break
                else:
                    connected=1
            else:
                pass
        if use==1 and connected==1:
            self.state='open'
        else:
            self.state='closed'
        return self.state

    def connect(self):
        """
        Connects 3 syringe pumps.
        """
        if self.use[0]:
            self.syringe_A.connect()
        if self.use[1]:
            self.syringe_B.connect()
        if self.use[2]:
            self.syringe_C.connect()
        self.refresh_state()
        self.update_infos()
    
    def refill_empty_syringes(self):
        """
        Refills syringes that are not full.
        """
        for syr in self.syringes:
            if syr.state=='open' and syr.level_uL<syr.size:   #not empty
                syr.full_refill()

    def stop(self):
        """
        Immediatly stops all syringes.
        """
        for syr in self.syringes:
            syr.stopSyringe()
        print("Stop dispenser")
    
    def close(self):
        """
        Closes all syringe pumps.
        """
        self.syringe_A.close()
        self.syringe_B.close()
        self.syringe_C.close()
        print('Closing dispenser')
        self.state='closed'

#global
GAIN_ON_PH_STEP = 0.5

class SyringePump(Dispenser): #This class could be removed.
    mode = 'manual'
    level_uL=0
    added_vol_uL = 0
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

class PhidgetStepperPump(SyringePump):
    """
    This class materializes one Syringe pump. 
    It includes control of phidget stepper motor, two end of pitch switches and one electrovalve.
    """

    #ports of stepper motors
    parser = ConfigParser()
    parser.read(device_ids)
    board_number = int(parser.get('main board', 'id'))
    VINT_number = int(parser.get('VINT', 'id'))
    port_a = int(parser.get('VINT', 'stepper_a'))
    port_b = int(parser.get('VINT', 'stepper_b'))
    port_c = int(parser.get('VINT', 'stepper_c'))

    def __init__(self,id,vol,syringe_type='Trajan SGE 500uL'): #par défaut une Trajan SGE 500uL
        
        self.vol=vol
        self.added_vol_uL=0

        #Syringe pump components
        self.stepper = Stepper()
        self.security_switch = DigitalInput() #end of pitch switch (syringe empty)
        self.reference_switch = DigitalInput() #end of pitch (syringe full)
        self.electrovalve = DigitalOutput()

        parser2 = ConfigParser()
        parser2.read(device_ids)
        #print("device_ids : ", device_ids)
        
        self.stepper.setDeviceSerialNumber(self.VINT_number)  #683442
        
        self.syringe_type=syringe_type
        if syringe_type=='Trajan SGE 500uL':
            #total volume of syringe
            self.size = 500 #uL 
            #practical volume on syringe pump is around 450mL (hitting empty switch)
        else:
            pass

        self.model='Phidget Stepper STC1005_0'
        self.id=id
        
        #connecting the right stepper, switches and valve
        if id=='A':
            self.stepper.setHubPort(self.port_a)
            self.stepper.setChannel(0)
            self.ch_full=int(parser2.get('switchs','full_A'))
            self.ch_empty=int(parser2.get('switchs','empty_A'))
            self.ch_valve=int(parser2.get('relay','valve_A'))
            self.id='Syringe A'
            #print(id,'interrupteurs sur DigitalInputs ',self.ch_full,self.ch_empty,'electrovalve sur sortie relai ',self.ch_valve)
        elif id=='B':
            self.stepper.setHubPort(self.port_b)
            self.stepper.setChannel(0)
            self.ch_full=int(parser2.get('switchs','full_B'))
            self.ch_empty=int(parser2.get('switchs','empty_B'))
            self.ch_valve=int(parser2.get('relay','valve_B'))
            self.id='Syringe B'
            #print(id,self.ch_full,self.ch_empty,self.ch_valve)
        elif id=='C':
            self.stepper.setHubPort(self.port_c)
            self.stepper.setChannel(0)
            self.ch_full=int(parser2.get('switchs','full_C'))
            self.ch_empty=int(parser2.get('switchs','empty_C'))
            self.ch_valve=int(parser2.get('relay','valve_C'))
            self.id='Syringe C'
            #print(id,self.ch_full,self.ch_empty,self.ch_valve)
        #print("Syringe", id,': switchs full/empty on DigitalInputs ',self.ch_full,"/",self.ch_empty,'\nelectrovalve on relay pin',self.ch_valve)
        self.state='closed'
        self.infos=self.id+" : "+self.state

        self.update_param_from_file()
        #print("syringe",id,self.use,self.reagent,self.concentration, self.level_uL)

    def update_param_from_file(self):
        """
        Retrieves Syringe pump parameters from file app_default_settings.ini
        """
        parser = ConfigParser()
        parser.read(app_default_settings)
        self.rescale_factor=float(parser.get(self.id, 'rescale_factor'))
        self.offset_ref=int(parser.get(self.id, 'offset_ref'))
        self.use=tobool(parser.get(self.id, 'use'))
        self.reagent=parser.get(self.id, 'reagent') #string
        self.concentration=float(parser.get(self.id, 'concentration'))
        self.level_uL=round(float(parser.get(self.id, 'level')))

    def connect(self):
        """
        Connects all sub sytems of syringe pump
        """
        print("connecting syringe",self.stepper,self.id,self.ch_full,self.ch_empty,self.ch_valve,\
            self.stepper.getHubPort(),self.stepper.getChannel(),self.stepper.getDeviceSerialNumber())
        #Stepper
        try:
            self.stepper.openWaitForAttachment(4000)
            print("stepper "+self.id+" connected")
            #print("Current limit (A) : ", self.stepper.getCurrentLimit())
            self.stepper.setCurrentLimit(0.4) #0.1A
            print("Current limit (A) : ", self.stepper.getCurrentLimit())
            self.stepper.setVelocityLimit(20)
            print("Velocity limit : ", self.stepper.getVelocityLimit())
            self.stepper.setAcceleration(3)
            print("motor Acceleration : ", self.stepper.getAcceleration())
            
            self.stepper.setRescaleFactor(self.rescale_factor) 
            # decreasing rescale factor increases pitch.
            # 450uL dispensed on a 30500 positions scale with factor=1.
            # approximately 76.25 microsteps for 1uL.    
            print("rescale factor = ", self.stepper.getRescaleFactor())
        except:
            print("stepper "+self.id+": not connected")
        
        #Switches, electrovalve
        self.security_switch.setDeviceSerialNumber(self.board_number)  #452846
        self.security_switch.setChannel(self.ch_empty)
        disp="security switch : "
        try:
            self.security_switch.openWaitForAttachment(1000)
            disp+="on"
        except:
            disp+="off"
        print(disp)
        self.reference_switch.setDeviceSerialNumber(self.board_number)
        self.reference_switch.setChannel(self.ch_full)
        disp="reference switch : "
        try:
            self.reference_switch.openWaitForAttachment(1000)
            disp+="on"
        except:
            disp+="off"
        print(disp)
        self.electrovalve.setDeviceSerialNumber(self.VINT_number)
        self.electrovalve.setHubPort(4)     #modifier pour mettre la valeur du fichier de cablage
        self.electrovalve.setChannel(self.ch_valve)
        disp="electrovalve : "
        try:
            self.electrovalve.openWaitForAttachment(1000)
            disp+="on"
        except:
            disp+="off"
        print(disp)
        if (self.stepper.getIsOpen() and self.security_switch.getIsOpen() and \
        self.reference_switch.getIsOpen() and self.electrovalve.getIsOpen()):
            self.state='open'
            self.infos=self.id+" : "+self.state+"\nSyringe : "+self.syringe_type\
                +"\nReagent : "+self.reagent+"\nConcentration : "+str(self.concentration)+" mol/L"
        else:
            self.state='closed'
        #State attibutes guarantees only that phidget channels are accessible. 
        # If a wire is cut at some place, it does not take it into account. 

        if self.state=='open':
            #connexions for end of pitch, and end of dispense signals
            self.reference_switch.setOnStateChangeHandler(self.stop_syringe_full)
            self.security_switch.setOnStateChangeHandler(self.stop_syringe_empty)   
            self.stepper.setOnStoppedHandler(self.on_motor_stop)
            self.mode='normal'         
            self.purging=False

    def set_valve_state(self, bool):
        self.electrovalve.setState(bool)
    
    def get_valve_state(self):
        try:
            state=self.electrovalve.getState()
        except:
            state=False
        return state

    ### Linked with Phidget Handlers 
    def stop_syringe_full(self, reference_switch, state):
        """
        Executes when an changeState event appear on the full syringe switch.
        The arguments can not be modified. 
        """
        print("state change on full syringe switch :", state)
        if state == False:
            self.stepper.setEngaged(False)
            print("reference switch hit - motor stop")
            time.sleep(1) #stabilisation du moteur
            if self.mode=='normal':
                print("going to reference position")
                self.go_to_ref_position()
            elif self.mode=='purge':
                print("full dispensing")
                self.full_dispense()
        else:
            print("switch closes again")

    def stop_syringe_empty(self, security_switch, state):
        """
        Executes when an changeState event appear on the empty syringe switch.
        The arguments can not be modified. 
        """
        print("state change on empty syringe switch :", state)
        if state == False: #switch has just opened
            print("state=false")
            self.stepper.setEngaged(False)
            print("empty switch hit - motor stop")
            if self.mode=='normal':
                print("go to zero position")
                self.go_to_zero_position()
            elif self.mode=='purge':
                print("full refilling")
                self.full_refill()
        else:
            print("switch closes again")
    
    def on_motor_stop(self, self_stepper):
        """
        Executes each time the motor stops
        self_stepper is attribute self.stepper
        """
        print("motor has stopped")
        if self.method=='go_to_ref':
            self.go_to_ref_position2()
        elif self.method[0]=='simple_refill':
            self.simple_refill2(self.method[1])
        elif self.method[0]=='simple_disp':
            self.simple_dispense_end(self.method[1],self.method[2])
        elif self.method=='full_refill':
            pass
    
    def go_to_ref_position(self):
        """
        Supposes syringe is on the full switch position. 
        It places plunger back to reference position (graduation 500uL)
        """
        self.configForDispense(ev=0)
        #offset_ref depends on each syringe pump. Its value in uL is set in app_default_settings.
        self.stepper.setTargetPosition(self.stepper.getPosition()+self.offset_ref) 
        self.method='go_to_ref'
        self.stepper.setEngaged(True)
        # while(self.stepper.getIsMoving()==True):
        #     pass
    
    def go_to_ref_position2(self):
        self.stepper.setEngaged(False)
        time.sleep(1) #stabilisation méca du stepper
        self.setReference()
        print("Plunger back in reference position - ready for dispense")
    
    def go_to_zero_position(self):
        """
        Supposes syringe hits empty syringe switch.
        """
        self.simple_refill(44) #54uL ajusté à l'oeil
        self.level_uL=0
    
    def validity_code(self):
        """
        Returns : 
        - code : indication on state of syringe pump
        - valid : boolean whether or not the required moovement is valid
        """
        target=self.stepper.getTargetPosition()-self.stepper.getPosition()
        time.sleep(1)   #time for reading on switches
        state0=self.reference_switch.getState()
        state1=self.security_switch.getState()
        #print("state1, state0 :", state1, ",", state0)
        
        #general case : no switch open, every movement is possible.
        if state1==True and state0==True: #Securities are working
            #print("motor in the middle at start")
            code=0
            if abs(target)>=1:
                valid=True
            else:
                valid=False
        
        #Reference switch pushed
        elif state1==True and state0==False:    
            print("reference switch is pushed")
            code=1
            if target>=1:
                valid=True
            else: 
                print("wrong direction - end of pitch")
                valid=False
        
        #empty syringe switch pushed
        elif state1==False and state0==True:
            print("security switch is pushed")
            code=2
            if target<=-1:
                valid=True
            else: 
                print("wrong direction - end of pitch")
                valid=False
        else:
            code=3
            valid=False
            print("Switches not connected - No dispense")   
        return code, valid
    
    def configForDispense(self,ev=1):
        """
        Configures valve and motor for a dispense
        """
        # stepper parameters
        self.stepper.setCurrentLimit(0.4)
        self.stepper.setAcceleration(2)
        self.stepper.setVelocityLimit(15)
        if ev==1:#electrovalve sur le mode dispense
            time.sleep(1)
            self.electrovalve.setState(True)    #always ON for dispense
            print("electrovalve state : ",self.electrovalve.getState())
            time.sleep(1)

    def configForRefill(self):
        """
        Configures valve and motor for refill
        """
        #motor param
        self.stepper.setCurrentLimit(0.4)
        self.stepper.setAcceleration(3)
        self.stepper.setVelocityLimit(20)
        if self.electrovalve.getState()==True: #always off for refill
            time.sleep(1)
            self.electrovalve.setState(False)
            time.sleep(1)

    def simple_dispense(self,vol,ev=1):
        """
        Dispense running in an unique movement. 
        """
        pos0 = self.stepper.getPosition()
        #print("position avant dispense : ",pos0)
        if ev==1:
            pass
            #print("syringe level before dispense = ",self.level_uL)
        else:
            pass
            #print("syringe level before unfill = ", self.level_uL)
        disp=False #par défaut, avant dispense : pas encore de dispense effectuée
        if vol >= 0:     #and vol <= self.size-pos0+10:   
            #+10 est une marge pour pouvoir dépasser légèrement le niveau complet     
            self.configForDispense(ev)
            self.stepper.setTargetPosition(pos0+vol)
            #lancement
            code,valid=self.validity_code()
            if valid:
                self.stepper.setEngaged(True)
                self.method=('simple_disp',ev,pos0)
                
                # while(self.stepper.getIsMoving()==True):
                #     pass
        elif vol<0:
            print("Unable to dispense : negative volume")
        else:   #volume trop grand
            print("Dispense with mulitple stages")
        return disp #bool about dispense was achived or not 

    def simple_dispense_end(self,ev,pos0):
        """
        Executes once motor has stopped
        """
        time.sleep(1) #stabilisation méca du steper
        self.stepper.setEngaged(False)
        self.electrovalve.setState(False) #On repasse en mode recharge (electrovalve hors tension)
        time.sleep(1)
        #affichage de la position atteinte
        position = self.stepper.getPosition()
        delta=round(position-pos0)
        self.level_uL-=delta
        print("Current level (uL) :", self.level_uL)
        if ev==1 and self.mode=='normal':
            self.added_vol_uL+=delta
            self.vol.add(delta)
            self.base_dispense_log.append(delta)
            disp=True #dispense is effectively proceed
        else:
            disp=False
        return disp
    
    def dispense(self, vol):
        """
        General case for dispense. It uses simple_dispense().
        """

        print("starting dispense %f uL" %vol)
        capacity=400 # modif LS
        level_500=self.level_uL
        level_400 = self.level_uL-100
        q=int(vol//capacity)
        r=vol%capacity
        print(q,"x",capacity,"+",r,"uL")
        if vol<=level_400: #cas classique de simple dispense
            self.simple_dispense(vol)
        else:   #vol>level_400 #dispense with multiple stages
            r2=r-level_400
            #print("r2=",r2)
            if r2<=0: #r<=level_400     #On peut dispenser le reste sans recharger
                #donc on commence par dispenser le reste
                self.simple_dispense(r)
                self.full_refill()
                #puis les dispenses entières
                for i in range(q):
                    self.simple_dispense(capacity)
                    self.full_refill()
            else: #r>level_400:     #Le reste est supérieur au niveau de la seringue
                #print("recharge pour dispense du reste")
                self.full_refill()
                self.simple_dispense(r)
                self.full_refill()
                for i in range(q):
                    self.simple_dispense(capacity)
                    self.full_refill()
        #self.vol.add(vol)   #update in volume tracking
        print("end of dispense\n")

    def standard_dispense_for_calib(self):
        """
        Used for motor calibration.
        """
        print("400uL target dispense for calibration")
        self.dispense(400)  #visée 400uL
    
    def compute_rescale_factor(self,reached_uL):
        """
        Used when calibrating motor.
        """
        current_factor=self.rescale_factor
        new_factor=(reached_uL/400)*current_factor  #new rescale_factor
        self.rescale_factor=new_factor
        print("Syringe",self.id,":\nRescale factor has been ajusted from %f to %f \n \
              Now you can ajust the reference offset" % (current_factor,new_factor))

    def simple_refill(self,vol):   
        """
        Refills volume vol (uL)
        """
        pos0=self.stepper.getPosition()
        self.configForRefill()
        self.stepper.setTargetPosition(pos0-vol) #recharge donc target supérieur à position courante
        #lancement
        code,valid=self.validity_code()
        if valid:
            self.stepper.setEngaged(True)
            self.method=('simple_refill',pos0)
    
    def simple_refill2(self,pos0):
        """After syringe is back in position 100uL"""
        time.sleep(1)
        self.stepper.setEngaged(False)
        #Displaying reached position
        position = self.stepper.getPosition()
        #print("Position atteinte après recharge: ", position)
        delta=round(position-pos0)
        print("delta", delta)
        self.level_uL-=delta #delta est negatif
        print("Current level (uL) :",self.level_uL)
    
    def full_refill(self):
        """
        Completely refills syringe. When switch is pressed method go_to_ref_position activates
        """
        pos0=self.stepper.getPosition()
        self.configForRefill()
        self.stepper.setTargetPosition(pos0-2*self.size) #recharge donc target supérieur à position courante
        #lancement
        code,valid=self.validity_code()
        if valid:
            self.method='full_refill'
            self.stepper.setEngaged(True)

    def full_dispense(self):
        """
        Dispenses until switch is hit.
        """
        self.simple_dispense(2*self.size)   #dispense jusqu'à la position d'arrêt avec l'interrupteur
    
    def setReference(self): 
        """
        Specifies plunger is back on full position (graduation 500uL)
        """
        pos=self.stepper.getPosition()
        #print("position du moteur avant remise à zéro : ",pos)
        self.stepper.addPositionOffset(-pos)
        pos1=self.stepper.getPosition()
        self.level_uL=self.size
    
    def purge(self):
        """
        Starts refilling all and dispensing all until we ask to stop.
        """
        if self.mode=='normal': #not currently purging
            self.mode='purge'
            print("Start purge")  
            self.full_refill()
        elif self.mode=='purge':
            self.mode='normal'
            print("last movement before end of purge")

    def close(self):
        """
        Closes all attributes.
        """
        self.stopSyringe()
        self.stepper.close()
        self.security_switch.close()
        self.reference_switch.close()
        self.electrovalve.close()
        print('Closing syringe pump ',self.id)
        self.state='closed'
    
    def stopSyringe(self):
        """
        Immediately stops the syringe.
        """
        if self.state=='open':
            self.stepper.setEngaged(False)