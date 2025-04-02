"""
AFIN DE GENERER UN EXECUTABLE : 
Si on veut générer un executbale, il faut copier les lignes entre les commentaires et les 
coller dans le fichier PhidgetSupport.py se trouvant dans le dossier de la librairie Phidget22  
dans l'environnement virtuel : 
dommino_env/Lib/site-package/Phidget22/PhidgetSupport.py"""

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
			libs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".libs")
			if sys.platform == 'win32':
				if os.path.exists(os.path.join(libs_path, "phidget22.dll")):
					print("boucle1")
					PhidgetSupport.__dll = windll.LoadLibrary(os.path.join(libs_path, "phidget22.dll"))
					###	début de l'ajout le 28-03-2025 pour lancement via executable
				elif os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), \
									 "lib/x64/phidget22.dll")):
					print("boucle2")
					#dll_path ../../PhidgetSupport.py=dommino_env/Lib
					dll_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), \
							 "lib/x64/phidget22.dll")
					print("phidget22.dll path", dll_path)
					PhidgetSupport.__dll = windll.LoadLibrary(dll_path)
				elif os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(\
					os.path.dirname(os.path.abspath(__file__))))), "lib/x64/phidget22.dll")):
					print("boucle3")
					#dll_path pytitrator/dommino_env/Lib/site-packages/Phidget22/PhidgetSupport.py - 
					# remontée 5 niveaux vers pytitrator - descente vers = lib/x64/phidget22.dll
					dll_path = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(\
						os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "lib/x64/phidget22.dll"))
					print("phidget22.dll path", dll_path)
					PhidgetSupport.__dll = windll.LoadLibrary(dll_path)
					### fin de l'ajout 28-03
				else:
					print("boucle4")
					PhidgetSupport.__dll = windll.LoadLibrary("phidget22.dll")
			elif sys.platform == 'darwin':
				if os.path.exists(os.path.join(libs_path, "libphidget22.dylib")):
					PhidgetSupport.__dll = cdll.LoadLibrary(os.path.join(libs_path, "libphidget22.dylib"))
				else:
					PhidgetSupport.__dll = cdll.LoadLibrary("libphidget22.dylib")
			else:
				if os.path.exists(os.path.join(libs_path, "libphidget22.so")):
					PhidgetSupport.__dll = cdll.LoadLibrary(os.path.join(libs_path, "libphidget22.so"))
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
