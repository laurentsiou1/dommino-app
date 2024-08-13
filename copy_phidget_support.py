"copie de PhidgetSupport.py"

import threading
import sys
import ctypes
from ctypes import *
import os

class PhidgetSupport:
	__dll = None

	@staticmethod
	def getDll():
		if PhidgetSupport.__dll is None:
			print("sys.platform:",sys.platform)
			if sys.platform == 'win32':
				# Load phidget22.dll from within the Python package itself
				print("path(__file__):",os.path.abspath(__file__))
				libs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".libs")
				#print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
				#print(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"lib"))
				if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"lib")):
					#cas du dossier contenant le .exe
					dll_location=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"lib")
					print("path: ",dll_location," exists")
					PhidgetSupport.__dll = windll.LoadLibrary(os.path.join(dll_location,"phidget22.dll"))
					print("dll load from path specified")
				elif os.path.exists(os.path.join(libs_path, "phidget22.dll")):
					print("path:",os.path.join(libs_path, "phidget22.dll")," exists")
					PhidgetSupport.__dll = windll.LoadLibrary(os.path.join(libs_path, "phidget22.dll"))
				else:
					print("all paths printed above don't exist")
					#PhidgetSupport.__dll = windll.LoadLibrary("phidget22.dll")
					#print("dll loaded")
			elif sys.platform == 'darwin':
				PhidgetSupport.__dll = cdll.LoadLibrary("/Library/Frameworks/Phidget22.framework/Versions/Current/Phidget22")
			else:
				PhidgetSupport.__dll = cdll.LoadLibrary("libphidget22.so.0")
		return PhidgetSupport.__dll

	def __init__(self):
		self.handle = None

	def __del__(self):
		pass

	@staticmethod
	def versionChecked_ord(character):
		if(sys.version_info[0] < 3):
			return character
		else:
			return ord(character)
