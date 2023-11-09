from Phidget22.Phidget import *
from Phidget22.Devices.DCMotor import *

ch = DCMotor()
ch.openWaitForAttachment(3000)

ch.setAcceleration(0.5)

ch.close()