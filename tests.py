"programme pour tests"

from Phidget22.Phidget import *
from Phidget22.Devices.Log import *
from Phidget22.LogLevel import *
from Phidget22.Devices.VoltageInput import *
import time

def onVoltageChange(self, voltage):
	print("Voltage: " + str(voltage))

def onError(self, code, description):
	print("Code: " + ErrorEventCode.getName(code))
	print("Description: " + str(description))
	print("----------")

def main():
	Log.enable(LogLevel.PHIDGET_LOG_INFO, "phidgetlog.log")
	voltageInput0 = VoltageInput()

	voltageInput0.setHubPort(3)
	voltageInput0.setDeviceSerialNumber(683442)q
	voltageInput0.setOnVoltageChangeHandler(onVoltageChange)
	voltageInput0.setOnErrorHandler(onError)

	voltageInput0.openWaitForAttachment(5000)

	try:
		input("Press Enter to Stop\n")
	except (Exception, KeyboardInterrupt):
		pass

	voltageInput0.close()

main()