# -*- coding: utf-8 -*-

import Globals


from wiimote import Wiimote
from calibration import Calibration
from cursor import FakeCursor
import Globals


import PyQt4.Qt as qt


class ConnectThread(qt.QThread):
	def run(self):
		Globals.wii = Wiimote()
		if not Globals.wii.bind():
			Globals.wii = None



class CalibrateThread(qt.QThread):
	def run(self):
		#try:
			calibration = Calibration()
			Globals.wii.state = Wiimote.NONCALIBRATED
			calibration.doIt(Globals.wii)
		#except:
			# Calibration error
			#pass


class IdleWiiThread(qt.QThread):
	def run(self):
		while 1:
			Globals.mutex.lock()
			if Globals.mutexWiiRun == False:
				Globals.mutex.unlock()
				break
			Globals.mutex.unlock()
			Globals.wii.getMsgs()


class RunWiiThread(qt.QThread):
	def run(self):
		while 1:
			Globals.mutex.lock()
			if Globals.mutexWiiRun == False: 
				Globals.mutex.unlock()
				break
			Globals.mutex.unlock()
			Globals.wii.getMsgs()
			Globals.cursor.update()



def InitiateIdleWiiThread():
	Globals.mutexWiiRun = True
	Globals.threadWii = IdleWiiThread()
	Globals.threadWii.start()



def InitiateRunWiiThread():
	Globals.mutexWiiRun = True
	Globals.threadWii = RunWiiThread()
	Globals.threadWii.start()



def TerminateWiiThread():
	if Globals.threadWii:
		Globals.mutex.lock()
		Globals.mutexWiiRun = False
		Globals.mutex.unlock()
		Globals.threadWii.wait()
		Globals.threadWii = None





