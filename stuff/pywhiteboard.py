#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from calibration import Calibration
from cursor import FakeCursor
import Globals
from threads import *


import sys, time
from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt




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
		
		Globals.initGlobals()
		
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
		self.settings = QtCore.QSettings("pywhiteboard","pywhiteboard")
		self.loadSettings()
	
	
	def changeCombos(self,zone,text):
		print zone,text
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
			self.ui.combo1.setEnabled(1)
			self.ui.combo2.setEnabled(1)
			self.ui.combo3.setEnabled(1)
			self.ui.combo4.setEnabled(1)
			return
		else:
			self.ui.pushButtonConnect.setEnabled(0)
			self.ui.pushButtonCalibrate.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(1)
			self.ui.combo1.setEnabled(0)
			self.ui.combo2.setEnabled(0)
			self.ui.combo3.setEnabled(0)
			self.ui.combo4.setEnabled(0)
			

	def connectWii(self):
		if self.connected:
			TerminateWiiThread()
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
			InitiateIdleWiiThread()
			
		else:
			msgbox = QtGui.QMessageBox( self )
			msgbox.setText( "Error during connection" )
			msgbox.setModal( True )
			ret = msgbox.exec_()

	def calibrateWii(self):
		TerminateWiiThread()
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
		
		InitiateIdleWiiThread()

	
	def activateWii(self):
		if self.active:
			# Deactivate
			TerminateWiiThread()
			self.active = False
			self.pushButtonActivate.setText("Activate")
			self.updateButtons()
			InitiateIdleWiiThread()
		else:
			# Activate
			TerminateWiiThread()
			Globals.cursor = FakeCursor(Globals.wii)
			for zone,click in self.zones.items():
				Globals.cursor.setZone(zone,click)
			
			InitiateRunWiiThread()
			self.active = True
			self.pushButtonActivate.setText("Deactivate")
			self.updateButtons()
	
	
	def loadSettings(self):
		z1 = self.settings.value("zone1").toString()
		if z1 == '': return
		z2 = self.settings.value("zone2").toString()
		if z2 == '': return
		z3 = self.settings.value("zone3").toString()
		if z3 == '': return
		z4 = self.settings.value("zone4").toString()
		if z4 == '': return
		self.ui.combo1.setCurrentIndex(int(z1))
		self.ui.combo2.setCurrentIndex(int(z2))
		self.ui.combo3.setCurrentIndex(int(z3))
		self.ui.combo4.setCurrentIndex(int(z4))
	
	
	# Exit callback
	def closeEvent(self,e):
		self.settings.setValue("zone1", QtCore.QVariant(self.ui.combo1.currentIndex()))
		self.settings.setValue("zone2", QtCore.QVariant(self.ui.combo2.currentIndex()))
		self.settings.setValue("zone3", QtCore.QVariant(self.ui.combo3.currentIndex()))
		self.settings.setValue("zone4", QtCore.QVariant(self.ui.combo4.currentIndex()))
		
		TerminateWiiThread()
		if Globals.wii:
			Globals.wii.close()
		e.accept()




def main():
	app = QtGui.QApplication(sys.argv)
	mainWin = MainWindow()
	mainWin.show()
	app.exec_()
