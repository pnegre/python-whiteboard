#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from calibration import Calibration
from cursor import FakeCursor


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
		#try:
			calibration = Calibration()
			Globals.wii.state = Wiimote.NONCALIBRATED
			calibration.doIt(Globals.wii)
		#except:
			# Calibration error
			#pass


class RunWiiThread(qt.QThread):
	def run(self):
		Globals.mutex = qt.QMutex()
		Globals.wiiActive = True
		while 1:
			Globals.mutex.lock()
			if Globals.wiiActive == False: 
				Globals.mutex.unlock()
				break
			Globals.mutex.unlock()
			Globals.wii.getMsgs()
			Globals.cursor.update()


class PBarDlg(QtGui.QDialog):
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self,parent)
		self.ui = uic.loadUi("pbar.ui",self)


class MainWindow(QtGui.QMainWindow):
	
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self,parent)
		self.ui = uic.loadUi("mainwindow.ui",self)	
		self.setWindowTitle("Linux-whiteboard")
		
		self.connected = False
		self.calibrated = False
		self.active = False

		self.center()
		self.batteryLevel.reset()
		self.batteryLevel.setRange(0,99)
		self.batteryLevel.setValue(0)

		self.connect(self.ui.pushButtonConnect,
			QtCore.SIGNAL("clicked()"), self.connectWii)
		
		self.connect(self.ui.pushButtonCalibrate,
			QtCore.SIGNAL("clicked()"), self.calibrateWii)
		
		self.connect(self.ui.pushButtonActivate,
			QtCore.SIGNAL("clicked()"), self.activateWii)
		
		pixmap = QtGui.QPixmap("screen.png")
		self.areasScene = QtGui.QGraphicsScene()
		self.areasScene.addPixmap(pixmap)
		self.screenAreas.setScene(self.areasScene)
		self.screenAreas.show()
		
		self.updateButtons()
		
		#print self.combo1.currentText()
		self.connect(self.ui.combo1,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo1)
		self.connect(self.ui.combo2,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo2)
		self.connect(self.ui.combo3,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo3)
		self.connect(self.ui.combo4,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo4)
		
		self.zones = {}
	
	def changeCombos(self,zone,text):
		if text == 'Right Click':
			self.zones[zone] = FakeCursor.RIGHT_BUTTON
		elif text == 'Left Click':
			self.zones[zone] = FakeCursor.LEFT_BUTTON
		elif text == 'Middle Click':
			self.zones[zone] = FakeCursor.MIDDLE_BUTTON

	def changeCombo1(self,text):
		self.changeCombos(FakeCursor.ZONE1,text)
	
	def changeCombo2(self,text):
		self.changeCombos(FakeCursor.ZONE2,text)
	
	def changeCombo3(self,text):
		self.changeCombos(FakeCursor.ZONE3,text)
	
	def changeCombo4(self,text):
		self.changeCombos(FakeCursor.ZONE4,text)
		

		
	def drawScreenGraphic(self):
		max_x = self.wiiScreen.geometry().width()
		max_y = self.wiiScreen.geometry().height()
		self.scene = qt.QGraphicsScene()
		self.scene.setSceneRect(0,0,max_x,max_y)
		quad = QtGui.QPolygonF()
		for p in Globals.wii.calibrationPoints:
			x = max_x * p[0]/Wiimote.MAX_X
			y = max_y * (1-float(p[1])/Wiimote.MAX_Y)
			quad.append(qt.QPointF(x,y))
		self.scene.addPolygon(quad)
		self.wiiScreen.setScene(self.scene)
		self.wiiScreen.show()


	def center(self):
		screen = QtGui.QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
		
		

	def updateButtons(self):
		if self.connected == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(0)
			return
		if self.calibrated == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(0)
			return
		if self.active == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(1)
			return
		else:
			self.ui.pushButtonConnect.setEnabled(0)
			self.ui.pushButtonCalibrate.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(1)
			

	def connectWii(self):
		if self.connected:
			if Globals.wii:
				Globals.wii.close()
			Globals.wii = None
			self.connected = False
			self.calibrated = False
			self.active = False
			self.pushButtonConnect.setText("Connect")
			self.updateButtons()
			return
			
		thread = ConnectThread()
		thread.start()
		
		pBar = PBarDlg(self)
		pBar.setModal( True )
		pBar.show()
		while not thread.wait(30):
			QtGui.QApplication.processEvents()
		pBar.close()

		if Globals.wii:
			self.connected = True
			self.calibrated = False
			self.active = False
			self.updateButtons()
			self.batteryLevel.setValue(Globals.wii.battery()*100)
			self.pushButtonConnect.setText("Disconnect")
		else:
			msgbox = QtGui.QMessageBox( self )
			msgbox.setText( "Error during connection" )
			msgbox.setModal( True )
			ret = msgbox.exec_()

	def calibrateWii(self):
		thread = CalibrateThread()
		thread.start()
		thread.wait()
		if Globals.wii.state == Wiimote.CALIBRATED:
			self.calibrated = True
			self.active = False
			self.drawScreenGraphic()
			self.updateButtons()
		else:
			msgbox = QtGui.QMessageBox( self )
			msgbox.setText( "Error during Calibration" )
			msgbox.setModal( True )
			ret = msgbox.exec_()

	
	def activateWii(self):
		if self.active:
			# Deactivate
			Globals.mutex.lock()
			Globals.wiiActive = False
			Globals.mutex.unlock()
			self.active = False
			self.pushButtonActivate.setText("Activate")
			self.updateButtons()
		else:
			Globals.cursor = FakeCursor(Globals.wii)
			for zone,click in self.zones.items():
				Globals.cursor.setZone(zone,click)
			
			Globals.threadWii = RunWiiThread()
			Globals.threadWii.start()
			self.active = True
			self.pushButtonActivate.setText("Deactivate")
			self.updateButtons()





if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	mainWin = MainWindow()
	mainWin.show()
	app.exec_()