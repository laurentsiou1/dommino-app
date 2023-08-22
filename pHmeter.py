"Acquisition du pH"

from Phidget22.Phidget import *
from Phidget22.Devices.VoltageInput import *
from Phidget22.Devices.PHSensor import *
#from controlPannel import ControlPannel
import math
import numpy as np
from configparser import ConfigParser
import os
from pathlib import Path

path = Path(__file__)
ROOT_DIR = path.parent.absolute()
cal_data_path = os.path.join(ROOT_DIR, "calData\cal_data.ini")

def volt2pH(a,b,U): #m: pente, c: ordonnée à l'origine
	#U=a*pH+b
	if a!=0:
		pH=(U-b)/a
	else:
		pH=1000
	return pH

class PHMeter:

	def __init__(self, ch): #ch est un VoltageInput
		self.voltagechannel = ch 
		parser = ConfigParser()
		parser.read(cal_data_path)
		#print(cal_data_path)
		self.currentCALdate=parser.get('data', 'date')
		self.currentCALtemperature=float(parser.get('data', 'temperature'))
		self.currentCALtype=int(parser.get('data', 'calib_type'))
		self.currentU1=float(parser.get('data', 'U1'))
		self.currentU2=float(parser.get('data', 'U2'))
		self.currentU3=float(parser.get('data', 'U3'))
		self.current_a = float(parser.get('data', 'a'))
		self.current_b = float(parser.get('data', 'b'))

		print("Données de la calibration courante:\n","date et heure: ",self.currentCALdate)
		print("température: ", self.currentCALtemperature, "nombre de points: ", self.currentCALtype)
		print("Tensions mesurées: ", self.currentU1, self.currentU2, self.currentU3)
		print("coefficents de calibration actuels:\na=",self.current_a, "b=", self.current_b)

		#https://www.tresfacile.net/manipulation-des-fichiers-de-configuration-en-python/
		#fichiers de config python

	def getIsOpen(self):
		return(self.voltagechannel.getIsOpen())

	def configure_pHmeter(self):
		#self.voltagechannel.setOnVoltageChangeHandler(PHMeter.DoOnVoltageChange)
		self.voltagechannel.setDataRate(1)
		self.voltagechannel.setVoltageChangeTrigger(0.00001) #précision de 10mV
	
	#si le voltagechangetrigger est à zéro, cela se produit périodiquement
	def doOnVoltageChange(self, volt):  
		print("Voltage: " + str(volt)+"V")
		return volt 
	
	def onCalibrationChange(self):
		parser = ConfigParser()
		parser.read(cal_data_path)
		self.currentCALdate=parser.get('data', 'date')
		self.currentCALtemperature=float(parser.get('data', 'temperature'))
		self.currentCALtype=int(parser.get('data', 'calib_type'))
		self.currentU1=float(parser.get('data', 'U1'))
		self.currentU2=float(parser.get('data', 'U2'))
		self.currentU3=float(parser.get('data', 'U3'))
		self.current_a = float(parser.get('data', 'a'))
		self.current_b = float(parser.get('data', 'b'))
		print(self.currentCALdate, "oncalibration change ph meter")
	
	def saveCalData(self,date,temperature,caltype,u_cal,coeffs):
		parser = ConfigParser()
		parser.read(cal_data_path)
		file = open(cal_data_path,'r+')
		parser.set('data', 'date', str(date)) 
		parser.set('data', 'temperature', str(temperature))
		parser.set('data', 'calib_type', str(caltype))
		print(u_cal)
		parser.set('data', 'U1', str(u_cal[0]))	
		parser.set('data', 'U2', str(u_cal[1]))
		parser.set('data', 'U3', str(u_cal[2]))
		print(coeffs)
		parser.set('data', 'a', str(coeffs[0]))
		parser.set('data', 'b', str(coeffs[1]))
		parser.write(file) 
		file.close()

		#sauvegarde de toutes les calibration
		oldCal = open("CALdata/CALlog.txt", "a")
		oldCal.write(str(date)+"\n"+str(temperature)+"°C \nType de calibration: "+str(caltype)+"\nVoltages calib:\n"+str(u_cal)+"\nCoefficients U=a*pH+b\n(a,b)="+str(coeffs)+"\n\n")
		oldCal.close()

	def computeCalCoefs(self,u_cal,method):
		if method == 2:
			pH = np.array([4,7])
			u = np.array([u_cal[0:2]]).T #seulement pH4 et 7
		if method == 3:
			pH = np.array([4,7,10])
			u = np.array([u_cal[0:3]]).T #pH 4, 7 et 10
		print("pH : ",pH," tensions de calib: ", u)
		A = np.vstack([pH.T, np.ones(len(pH)).T]).T
		x = np.linalg.lstsq(A, u, rcond=None)[0]		#a: pente, b: ord à l'origine
		a=x[0].item();b=x[1].item()
		#print("pente: ", a, "; ord à l'origine: ", b)
		self.current_a=a
		self.current_b=b
		return a, b

"""
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
"""

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