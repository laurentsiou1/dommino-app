"Acquisition du pH"

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.PHSensor import *
import time
#from controlPannel import ControlPannel

def volt2pH(V1,V2,U):
	pH=3*((U-V1)/(V2-V1))+4
	return pH

class PHMeter:

	CALcoefs=(1,2)
	CALdate='00-00-0000'

	def __init__(self, ch): #ch est un VoltageInput
		self.voltagechannel = ch 

	def configure_pHmeter(self):
		#self.voltagechannel.setOnVoltageChangeHandler(PHMeter.DoOnVoltageChange)
		self.voltagechannel.setDataRate(1)
		self.voltagechannel.setVoltageChangeTrigger(0.00001) #précision de 10mV
    
	def Two_point_calibration(self, pH_set):
		ch=self.voltagechannel
		if pH_set==(4,7):
			try:
				input("insérer électrode à pH=4 et presser enter lorsque l'électrode est stabilisée\n")
			except(KeyboardInterrupt):
				pass
			finally:   
				V1=ch.getVoltage()
				#time.sleep(1) 
				print(V1)
			try:
				input("insérer électrode à pH=7 et presser enter lorsque l'électrode est stabilisée\n")
			except(KeyboardInterrupt):
				pass
			finally:
				V2=ch.getVoltage()
				#time.sleep(5) 
				print(V2)
			
			if V2!=V1:  #à température constante le pH est une fonction linéaire de la tension. 
				print("calibration valide")
				# pH = 3*V/(V2-V1) + 4-3*V1/(V2-V1)
				# pH = a*V + b 
				a = 3/(V2-V1); b=4-3*V1/(V2-V1)
				return (a,b)
			else:
				print("calibration non valide : signal identique sur les deux échantillons")
				pass
		print("Valeurs de tension:\nU(Ph4)=%dV U(pH7)=%dV\n" %(V1, V2))


	#si le voltagechangetrigger est à zéro, cela se produit périodiquement
	def doOnVoltageChange(self, volt):  
		print("Voltage: " + str(volt)+"V")
		#print("self=",self)
		return volt 
		# buffer.append(self._VoltageChange)
		# del(buffer[0])
		# return buffer


if __name__ == "__main__":
    #création d'un canal pour la tension d'entrée
	ch = VoltageInput()
	ch.setDeviceSerialNumber(432846)
	ch.setChannel(0)
	ch.openWaitForAttachment(1000)
	ch.setOnVoltageChangeHandler(PHMeter.DoOnVoltageChange)
	
	phm = PHMeter(ch)
	phm.configure_pHmeter()


	#ch.setOnVoltageChangeHandler(PHMeter.DoOnVoltageChange)
	
	#ch.setDataRate(1)
	#ch.setVoltageChangeTrigger(0.0001) #précision de 10mV

	
	
	# pH_set = (4,7)
	# CALcoefs=phm.Two_point_calibration(pH_set)

	# ch.setSensorType(VoltageSensorType.SENSOR_TYPE_1130_PH)
	# sensorValue = ch.getSensorValue() #pour comparer aux valeurs calculées avec calibration
	# print("SensorValue: pH = " + str(sensorValue))

	ch.close()

#def main():
    
    # #stabTime=
    # bufferSize=1
    # buffer=[]

    # #création d'un canal pour la tension d'entrée
    # self = VoltageInput()
    # self.setOnVoltageChangeHandler(DoOnVoltageChange)
    # #self.setOnVoltageChangeHandler(vc2)
    # self.openWaitForAttachment(5000)
    # self.setDataRate(1)
    # self.setVoltageChangeTrigger(0.0001) #précision de 10mV


    # pH_set = (4,7)
    # Two_point_calibration(self, pH_set)


    # #lv = []
    # #voltage = self.getVoltage()
    # #print("Voltage: " + str(voltage) + "V")
    
    # try:
    #     input("Press Enter to Stop\n")
    # except (Exception, KeyboardInterrupt):
    #     pass    

    # self.setSensorType(VoltageSensorType.SENSOR_TYPE_1130_PH)
    # sensorValue = self.getSensorValue() #pour comparer aux valeurs calculées avec calibration
    # print("SensorValue: pH = " + str(sensorValue))

    # self.close()

#main()
# class data_buffer:
    
#     def __init__(self):
#         self.values = []
#         self.size = 0
    
#     def set_buffer_size(self,Nmes):
#         self.size = Nmes
# 
# # def vc2(self, buffer):
#     v=self.getVoltage()
#     buffer.append(v)
#     del(buffer[0])
#     return buffer