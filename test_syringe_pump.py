"programme pour tester les fonctions du module syringe_pump"

from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
from Phidget22.Devices.Log import *
from Phidget22.LogLevel import *
from Phidget22.Devices.Stepper import *
from Phidget22.Devices.VoltageInput import *
import traceback
import time

#Declare any event handlers here. These will be called every time the associated event occurs.

def onStepper0_Attach(self):
	print("Attach!")

def onStepper0_Detach(self):
	print("Detach!")

def onStepper0_Error(self, code, description):
	print("Code: " + ErrorEventCode.getName(code))
	print("Description: " + str(description))
	print("----------")

def onVoltageInput0_VoltageChange(self, voltage):
    return
    #print("Voltage: " + str(voltage))

def onVoltageInput0_Attach(self):
	print("Attach!")

def onVoltageInput0_Detach(self):
	print("Detach!")

def onVoltageInput0_Error(self, code, description):
	print("Code: " + ErrorEventCode.getName(code))
	print("Description: " + str(description))
	print("----------")

def ReachedPosition(self):
    time.sleep(1) #attendre la stabilisation du moteur
    print("Stopped")
    position = self.getPosition()
    print("Position: " + str(position))
    return position

def main():
    try:
        Log.enable(LogLevel.PHIDGET_LOG_INFO, "phidgetlog.log")
        #Create your Phidget channels
        stepper0 = Stepper()
        voltageInput0 = VoltageInput()

		#Set addressing parameters to specify which channel to open (if any)

		#Assign any event handlers you need before calling open so that no events are missed.
        stepper0.setOnAttachHandler(onStepper0_Attach)
        stepper0.setOnDetachHandler(onStepper0_Detach)
        stepper0.setOnErrorHandler(onStepper0_Error)
        voltageInput0.setOnVoltageChangeHandler(onVoltageInput0_VoltageChange)
        voltageInput0.setOnAttachHandler(onVoltageInput0_Attach)
        voltageInput0.setOnDetachHandler(onVoltageInput0_Detach)
        voltageInput0.setOnErrorHandler(onVoltageInput0_Error)

		#Open your Phidgets and wait for attachment
        stepper0.openWaitForAttachment(5000)
        voltageInput0.openWaitForAttachment(5000)
        voltage = voltageInput0.getVoltage()
        print("Voltage: " + str(voltage))

		#Do stuff with your Phidgets here or in your event handlers.
        controlMode=stepper0.getControlMode() #0 est le mode position set
        print("ControlMode: " + str(controlMode))
        
        stepper0.setCurrentLimit(0.1)
        stepper0.setVelocityLimit(1000)
        stepper0.setTargetPosition(5000)
        
        position = stepper0.getPosition()
        print("Position: " + str(position))

        stepper0.setEngaged(True)
        stepper0.setOnStoppedHandler(ReachedPosition)

        try:
            input("Press Enter to Stop\n")
        except (Exception, KeyboardInterrupt):
            pass

        #Retour à la position 0 à la fin
        stepper0.setTargetPosition(0)
        stepper0.setEngaged(True)

        try:
            input("taper entrée pour arrêter. Retour à la position initiale\n")
        except (Exception, KeyboardInterrupt):
            pass

		#Close your Phidgets once the program is done.
        stepper0.close()
        voltageInput0.close()

    except PhidgetException as ex:
		#We will catch Phidget Exceptions here, and print the error informaiton.
        traceback.print_exc()
        print("")
        print("PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)


main()