# -*- coding: utf-8 -*-

import Globals


from wiimote import Wiimote
from cursor import FakeCursor
from configuration import Configuration


import PyQt4.Qt as qt


class ConnectThread(qt.QThread):
	def run(self):
		Globals.wii = Wiimote()
		conf = Configuration()
		mac = str(conf.getValueStr("selectedmac"))
		if mac == "All Devices":
			mac = ''
		
		if not Globals.wii.bind(mac):
			Globals.wii = None



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
		conf = Configuration()
		delayloop = int(conf.getValueStr("delayloop"))
		while 1:
			Globals.mutex.lock()
			if Globals.mutexWiiRun == False: 
				Globals.mutex.unlock()
				break
			Globals.mutex.unlock()
			Globals.wii.getMsgs()
			Globals.cursor.update()
			qt.QThread.usleep(delayloop)



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





