# -*- coding: utf-8 -*-


from wiimote import Wiimote
from configuration import Configuration


import PyQt4.Qt as qt


class ConnectThread(qt.QThread):
	def run(self):
		self.wii = Wiimote()
		conf = Configuration()
		mac = str(conf.getValueStr("selectedmac"))
		if mac == "All Devices":
			mac = ''
		
		if not self.wii.bind(mac):
			self.wii = None
	
	def getWii(self):
		return self.wii



def CreateThreadClass(func):
	class Thread(qt.QThread):
		def run(self):
			func()
	return Thread






