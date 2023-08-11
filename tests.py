"programme pour tests"

#print "taper enter lorsque stabilisé", nn = input()

# a=input("taper entrer lorsque l'électrode est en contact du tampon pH4\n")

# print(str(a))

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *

U_pH = VoltageInput() #pH-mètre
U_pH.setDeviceSerialNumber(432846)
#U_pH.setHubPort(4) seulement pour les device avec VINT
U_pH.setChannel(0)
U_pH.openWaitForAttachment(5000)

U_stepper = VoltageInput() #tension d'alim du stepper
U_stepper.setDeviceSerialNumber(683442)
U_stepper.setHubPort(0) #seulement pour les device avec VINT
U_stepper.setChannel(0)
U_stepper.openWaitForAttachment(5000)

deviceName1 = U_pH.getDeviceName()
print("device pH meter: " + str(deviceName1))
deviceName2 = U_stepper.getDeviceName()
print("Device stepper: " + str(deviceName2))


# count = U_pH.getDeviceChannelCount(ChannelClass.PHIDCHCLASS_VOLTAGEINPUT)
# print("number of voltage input channels: " + str(count))
# channel = U_pH.getChannel()
# print("Channel: " + str(channel))
# #U_pH.setChannel(1)

# attached = U_pH.getAttached()
# print("Attached: " + str(attached))


# channel = U_stepper.getChannel()
# print("Channel: " + str(channel))

# attached = U_pH.getAttached()
# print("Attached: " + str(attached))