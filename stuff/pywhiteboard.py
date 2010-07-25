#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from cursor import FakeCursor
import Globals
from threads import *

from calibration import doCalibration
from configuration import Configuration, ConfigDialog


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
		self.center()
		
		self.connected = False
		self.calibrated = False
		self.active = False
		self.mustquit = False
		
		Globals.initGlobals()
		
		self.batteryLevel.reset()
		self.batteryLevel.setRange(0,99)
		self.batteryLevel.setValue(0)

		self.connect(self.ui.pushButtonConnect,
			QtCore.SIGNAL("clicked()"), self.connectWii)
		
		self.connect(self.ui.pushButtonCalibrate,
			QtCore.SIGNAL("clicked()"), self.calibrateWiiScreen)
		
		self.connect(self.ui.pushButtonActivate,
			QtCore.SIGNAL("clicked()"), self.activateWii)
		
		self.connect(self.ui.pushButtonLoadCal,
			QtCore.SIGNAL("clicked()"), self.calibrateWiiFromSettings)
		
		pixmap = QtGui.QPixmap("screen.png")
		self.areasScene = QtGui.QGraphicsScene()
		self.areasScene.addPixmap(pixmap)
		self.screenAreas.setScene(self.areasScene)
		self.screenAreas.show()
		
		self.updateButtons()
		
		self.connect(self.ui.actionQuit,
			QtCore.SIGNAL("activated()"), self.mustQuit)
		self.connect(self.ui.actionConfiguration,
			QtCore.SIGNAL("activated()"), self.showConfiguration)
		
		self.zones = {}
		self.loadSettings()
		
	
	
	def showConfiguration(self):
		dialog = ConfigDialog(self, Globals.wii)
		dialog.show()
		dialog.exec_()
	
	
	#def changeCombos(self,zone,text):
		#print zone,text
		#if text == 'Right Click':
			#self.zones[zone] = FakeCursor.RIGHT_BUTTON
		#elif text == 'Left Click':
			#self.zones[zone] = FakeCursor.LEFT_BUTTON
		#elif text == 'Middle Click':
			#self.zones[zone] = FakeCursor.MIDDLE_BUTTON
		#elif text == 'Only Move':
			#self.zones[zone] = FakeCursor.ONLY_MOVE

	#def changeCombo1(self,text):
		#self.changeCombos(FakeCursor.ZONE1,text)
	
	#def changeCombo2(self,text):
		#self.changeCombos(FakeCursor.ZONE2,text)
	
	#def changeCombo3(self,text):
		#self.changeCombos(FakeCursor.ZONE3,text)
	
	#def changeCombo4(self,text):
		#self.changeCombos(FakeCursor.ZONE4,text)
		

		
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
	
	
	def clearScreenGraphic(self):
		if self.wiiScreen.scene():
			self.scene.clear()


	def center(self):
		screen = QtGui.QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
		
		

	def updateButtons(self):
		if self.connected == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonLoadCal.setEnabled(0)
			self.statusBar().showMessage("")
			return
		
		self.statusBar().showMessage("Connected to " + Globals.wii.addr)
		
		if self.calibrated == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonLoadCal.setEnabled(1)
			return
		if self.active == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(1)
			self.ui.pushButtonLoadCal.setEnabled(1)
			self.ui.combo1.setEnabled(1)
			self.ui.combo2.setEnabled(1)
			self.ui.combo3.setEnabled(1)
			self.ui.combo4.setEnabled(1)
			return
		else:
			self.ui.pushButtonConnect.setEnabled(0)
			self.ui.pushButtonCalibrate.setEnabled(0)
			self.ui.pushButtonLoadCal.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(1)
			self.ui.combo1.setEnabled(0)
			self.ui.combo2.setEnabled(0)
			self.ui.combo3.setEnabled(0)
			self.ui.combo4.setEnabled(0)
	
	
	def disconnectDevice(self):
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
			self.ui.label_utilization.setText("Utilization: 0%")
			self.clearScreenGraphic()
			self.batteryLevel.setValue(0)
			return

	def connectWii(self):
		if self.connected:
			self.disconnectDevice()
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

	# doscreen: if doscreen is true, calibrate by manual pointing
	def calibrateWii(self,doScreen):
		self.ui.label_utilization.setText("Utilization: 0%")
		self.clearScreenGraphic()
		TerminateWiiThread()
		
		self.calibrated = False
		self.active = False
		
		Globals.wii.state = Wiimote.NONCALIBRATED
		if doScreen:
			doCalibration(self,Globals.wii)
		else:
			self.loadCalibration(Globals.wii)
		
		if Globals.wii.state == Wiimote.CALIBRATED:
			self.calibrated = True
			self.active = False
			self.drawScreenGraphic()
			self.updateButtons()
			self.ui.label_utilization.setText("Utilization: %d%%" % (100.0*Globals.wii.utilization))
			self.saveCalibrationPars(Globals.wii)
		else:
			self.updateButtons()
			msgbox = QtGui.QMessageBox( self )
			msgbox.setText( "Error during Calibration" )
			msgbox.setModal( True )
			ret = msgbox.exec_()
		
		InitiateIdleWiiThread()

	
	def calibrateWiiScreen(self):
		self.calibrateWii(True)
	
	
	def calibrateWiiFromSettings(self):
		self.calibrateWii(False)


	def saveCalibrationPars(self,wii):
		conf = Configuration()
		for i,p in enumerate(wii.screenPoints):
			conf.saveValue("screenPoint"+str(i)+"x",str(p[0]))
			conf.saveValue("screenPoint"+str(i)+"y",str(p[1]))
		
		for i,p in enumerate(wii.calibrationPoints):
			conf.saveValue("wiiPoint"+str(i)+"x",str(p[0]))
			conf.saveValue("wiiPoint"+str(i)+"y",str(p[1]))
	
	
	def loadCalibration(self,wii):
		try:
			conf = Configuration()
			pwii = []
			pscr = []
			for i in range(0,4):
				p = []
				p.append(float(conf.getValueStr("screenPoint"+str(i)+"x")))
				p.append(float(conf.getValueStr("screenPoint"+str(i)+"y")))
				q = []
				q.append(float(conf.getValueStr("wiiPoint"+str(i)+"x")))
				q.append(float(conf.getValueStr("wiiPoint"+str(i)+"y")))
				pwii.append(list(q))
				pscr.append(list(p))
			wii.calibrate(pscr,pwii)
		except:
			pass
		
	
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
			conf = Configuration()
			zones = [ conf.getValueStr(z) for z in ("zone1","zone2","zone3","zone4") ]
			Globals.cursor.setZones(zones)
			InitiateRunWiiThread()
			self.active = True
			self.pushButtonActivate.setText("Deactivate")
			self.updateButtons()
	
	
	def loadSettings(self):
		pass
	
	
	# Exit callback
	def closeEvent(self,e):
		if self.mustquit:
			self.disconnectDevice()
			e.accept()
		else:
			msgbox = QtGui.QMessageBox(self)
			msgbox.setText("The application will remain active (systray)." + "\n" + \
				"To quit, use file->quit menu" )
			msgbox.setModal( True )
			ret = msgbox.exec_()
			self.showHide()
			e.ignore()
	
	
	def showHide(self):
		if self.isVisible():
			self.hide()
		else:
			self.show()


	def mustQuit(self):
		self.mustquit = True
		self.close()





class SysTrayIcon(object):
	def __init__(self, fname, mainWindow):
		self.mainWindow = mainWindow
		self.stray = QtGui.QSystemTrayIcon()
		self.stray.setIcon(QtGui.QIcon(fname))

		QtCore.QObject.connect(self.stray,
			QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"), self.activate)
	
	def activate(self, reason):
		if reason == QtGui.QSystemTrayIcon.Trigger:
			self.mainWindow.showHide()
		
	def show(self):
		self.stray.show()





def main():
	app = QtGui.QApplication(sys.argv)
	mainWin = MainWindow()
	stray = SysTrayIcon("icon.xpm", mainWin)
	stray.show()
	mainWin.show()
	app.exec_()
