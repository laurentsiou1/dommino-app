"programme principal séquence de titrage"

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.Stepper import *
from Phidget22.Devices.Log import *
from Phidget22.Devices.Manager import *
import time

#import syringe_pump as sp
#import pHmeter as phm

from SyringePump import SyringePump

#event handlers
def onVoltageChange(self, voltage):
	print("Voltage: " + str(voltage))

def onAttach(self, channel):
	print("Channel: " + str(channel))
	
    ### Initialisation_composants ###

    ## Voltgage Inputs ##
U_pH = VoltageInput() #pH-mètre
U_pH.setDeviceSerialNumber(432846)
U_pH.setChannel(0)
U_pH.openWaitForAttachment(5000)

U_stepper = VoltageInput() #tension d'alim du stepper
U_stepper.setDeviceSerialNumber(683442)
U_stepper.setHubPort(0) #seulement pour les device avec VINT
U_stepper.setChannel(0)
U_stepper.openWaitForAttachment(5000)

    ## Digital inputs ##
interrupteur0 = DigitalInput() #interrupteur bout de course pousse seringue
interrupteur0.setDeviceSerialNumber(432846)
interrupteur0.setChannel(0)
interrupteur0.openWaitForAttachment(5000)

    ## Digital outputs ##
relay0_state = DigitalOutput() #contrôle électrovanne
relay0_state.setDeviceSerialNumber(432846)
relay0_state.setChannel(0)
relay0_state.openWaitForAttachment(5000)

    ## Stepper ##
stepper = Stepper() #object de type stepper : contrôle du moteur stepper
stepper.setDeviceSerialNumber(683442)
stepper.setHubPort(0) #seulement pour les device avec VINT
stepper.setChannel(0)
stepper.openWaitForAttachment(5000)    

deviceName1 = U_pH.getDeviceName()
deviceName2 = U_stepper.getDeviceName()
deviceName3 = interrupteur0.getDeviceName()
deviceName4 = relay0_state.getDeviceName()
deviceName5 = stepper.getDeviceName()

print("device pH meter: " + str(deviceName1))
print("Device stepper: " + str(deviceName2))
print("device interrupteur: " + str(deviceName3))
print("Device relai: " + str(deviceName4))    
print("device stepper: " + str(deviceName5))


## Configuration du pousse seringue
Uin = U_stepper.getVoltage() 
print("Voltage: " + str(Uin))
controlMode=stepper.getControlMode() #0 est le mode position set
print("ControlMode: " + str(controlMode))
        
stepper.setCurrentLimit(0.1)
stepper.setVelocityLimit(1000)

sp = SyringePump(stepper, relay0_state, interrupteur0)

#Activation de la sécurité de bout de rail pour la pousse seringue
sp.switch.setOnStateChangeHandler(sp.SecurityStop) #securitystop prend trois arguments : sp, sp.switch et state


sp.setZeroPosition()
sp.fill_syringe(150)
sp.dispense(20)
sp.empty_syringe()



U_pH.close()
U_stepper.close()
interrupteur0.close()
relay0_state.close()
stepper.close()