"Test de connexion des phidgets"

from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *
#from Phidget22.Devices import *

"""dev=Phidget()
dev.setDeviceSerialNumber(432846)
dev.openWaitForAttachment(1000)

sn=dev.getDeviceSerialNumber()
print(sn)

state=dev.getAttached()
print(state)

id=dev.getDeviceID()

print(id)"""

pin1_deuterium = DigitalOutput()
pin1_deuterium.setDeviceSerialNumber(432846)
pin1_deuterium.setChannel(5)
pin1_deuterium.openWaitForAttachment(1000)

