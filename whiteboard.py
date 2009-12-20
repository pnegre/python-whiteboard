#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from calibration import Calibration
from cursor import FakeCursor

#wii = Wiimote()
#wii.bind()
#calibration = Calibration()
#calibration.doIt(wii)
#curs = FakeCursor(wii)
#while(1):
	#wii.getMsgs()
	#curs.update()

class GlobalObjects:
	pass

Globals = GlobalObjects()


import sys, time
from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt


class ConnectThread(qt.QThread):
	def run(self):
		Globals.wii = Wiimote()
		if not Globals.wii.bind():
			Globals.wii = None


class CalibrateThread(qt.QThread):
	def run(self):
		calibration = Calibration()
		calibration.doIt(Globals.wii)


class RunWiiThread(qt.QThread):
	def run(self):
		Globals.wiiActive = True
		cursor = FakeCursor(Globals.wii)
		while Globals.wiiActive:
			Globals.wii.getMsgs()
			cursor.update()


class MainWindow(QtGui.QMainWindow):
	
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self,parent)
		self.ui = uic.loadUi("mainwindow.ui",self)	
		self.setWindowTitle("Linux-whiteboard")
		
		self.connected = False
		self.calibrated = False
		self.active = False
		self.daemonStarted = False

		self.connect(self.ui.pushButtonConnect,
			QtCore.SIGNAL("clicked()"), self.connectWii)
		
		self.connect(self.ui.pushButtonCalibrate,
			QtCore.SIGNAL("clicked()"), self.calibrateWii)
		
		self.connect(self.ui.pushButtonActivate,
			QtCore.SIGNAL("clicked()"), self.activateWii)
		
		self.connect(self.ui.pushButtonDeactivate,
			QtCore.SIGNAL("clicked()"), self.deactivateWii)
		
		self.updateButtons()


	def updateButtons(self):
		if self.connected == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonDeactivate.setEnabled(0)
			return
		if self.calibrated == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonDeactivate.setEnabled(0)
			return
		if self.active == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(1)
			self.ui.pushButtonDeactivate.setEnabled(0)
			return
		else:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonDeactivate.setEnabled(1)

	def connectWii(self):
		thread = ConnectThread()
		thread.start()
		thread.wait()
		if Globals.wii:
			self.connected = True
			self.calibrated = False
			self.active = False
			self.updateButtons()

	def calibrateWii(self):
		thread = CalibrateThread()
		thread.start()
		thread.wait()
		if Globals.wii.state == Wiimote.CALIBRATED:
			self.calibrated = True
			self.active = False
			self.updateButtons()

	
	def activateWii(self):
		thread = RunWiiThread()
		thread.start()
		self.active = True
		self.updateButtons()
	
	def deactivateWii(self):
		Globals.wiiActive = False
		self.active = False
		self.updateButtons()






if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	mainWin = MainWindow()
	mainWin.show()
	app.exec_()