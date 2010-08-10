#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from cursor import FakeCursor
from threads import *

from calibration import doCalibration
from configuration import Configuration, ConfigDialog


import sys, time, locale
from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt


class AboutDlg(QtGui.QDialog):
	
	def __init__(self, parent=None):
		super(AboutDlg, self).__init__(parent)
		self.ui = uic.loadUi("about.ui",self)
		self.connect(self.ui.butOK,
			QtCore.SIGNAL("clicked()"), self.close)



class PBarDlg(QtGui.QDialog):
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self,parent)
		self.ui = uic.loadUi("pbar.ui",self)
		self.cancelled = False
		self.connect(self.ui.butCancel,
			QtCore.SIGNAL("clicked()"), self.cancelConnection)
	
	def cancelConnection(self):
		self.cancelled = True
		self.ui.butCancel.setEnabled(False)
		self.ui.label.setText(self.tr("Cancelling..."))


class MainWindow(QtGui.QMainWindow):
	
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = uic.loadUi("mainwindow.ui",self)
		self.setWindowTitle("python-whiteboard")
		
		self.connected = False
		self.calibrated = False
		self.active = False
		self.mustquit = False
		
		self.wii = None
		self.cursor = None
		
		self.batteryLevel.reset()
		self.batteryLevel.setRange(0,99)
		self.batteryLevel.setValue(0)
		
		conf = Configuration()

		self.connect(self.ui.pushButtonConnect,
			QtCore.SIGNAL("clicked()"), self.connectWii)
		
		self.connect(self.ui.pushButtonCalibrate,
			QtCore.SIGNAL("clicked()"), self.calibrateWiiScreen)
		
		self.connect(self.ui.pushButtonActivate,
			QtCore.SIGNAL("clicked()"), self.activateWii)
		
		self.connect(self.ui.pushButtonLoadCal,
			QtCore.SIGNAL("clicked()"), self.calibrateWiiFromSettings)
		
		self.connect(self.ui.pushButtonSettings,
			QtCore.SIGNAL("clicked()"), self.showHideSettings)
		
		self.updateButtons()
		
		self.connect(self.ui.actionQuit,
			QtCore.SIGNAL("activated()"), self.mustQuit)
		self.connect(self.ui.actionHelp,
			QtCore.SIGNAL("activated()"), self.showAboutDlg)
		
		
		if conf.getValueStr('moveonly') == 'Yes':
			self.ui.moveOnlyCheck.setChecked(True)
		self.connect(self.ui.moveOnlyCheck,
			QtCore.SIGNAL("stateChanged(int)"), self.checkMoveOnly)
		
		if conf.getValueStr("autoconnect") == "Yes":
			self.timer = qt.QTimer(self)
			self.timer.setInterval(500)
			self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.autoConnect)
			self.timer.start()
		
		self.timer2 = qt.QTimer(self)
		self.timer2.setInterval(4000)
		self.connect(self.timer2, QtCore.SIGNAL("timeout()"), self.checkWii)
		self.timer2.start()
		
		self.confDialog = ConfigDialog(self, self.wii)
		layout = QtGui.QGridLayout()
		layout.addWidget(self.confDialog)
		self.ui.confContainer.setLayout(layout)
		self.ui.confContainer.setVisible(False)
		self.center()
	
	
	def showHideSettings(self):
		self.ui.confContainer.setVisible(not self.ui.confContainer.isVisible())
		QtGui.QApplication.processEvents()
		if self.ui.confContainer.isVisible():
			self.ui.pushButtonSettings.setText(self.tr('Hide settings'))
			self.resize(771,583)
		else:
			self.ui.pushButtonSettings.setText(self.tr('Show settings'))
			self.adjustSize()
	
	
	def checkMoveOnly(self,i):
		conf = Configuration()
		if self.sender().isChecked():
			conf.saveValue('moveonly','Yes')
		else:
			conf.saveValue('moveonly','No')
	
	
	def showAboutDlg(self):
		about = AboutDlg(self)
		about.show()
		about.exec_()
	
	
	def checkWii(self):
		if self.wii == None: return
		if self.connected == False: return
		if self.wii.checkStatus() == False:
			# Deactivate cursor
			self.deactivateWii()
			# Deactivate device
			self.connected = False
			self.calibrated = False
			self.active = False
			self.pushButtonConnect.setText(self.tr("Connect"))
			self.updateButtons()
			self.ui.label_utilization.setText(self.tr("Utilization: 0%"))
			self.clearScreenGraphic()
			self.batteryLevel.setValue(0)
			
			msgbox = QtGui.QMessageBox( self )
			msgbox.setText( self.tr("Wii device disconnected") )
			msgbox.setModal( True )
			ret = msgbox.exec_()
			return
		self.batteryLevel.setValue(self.wii.battery()*100)
	
	
	def autoConnect(self):
		if self.isVisible():
			self.timer.stop()
			self.connectWii()
		else:
			self.timer.start()
		

		
	def drawScreenGraphic(self):
		max_x = self.wiiScreen.geometry().width()
		max_y = self.wiiScreen.geometry().height()
		self.scene = qt.QGraphicsScene()
		self.scene.setSceneRect(0,0,max_x,max_y)
		quad = QtGui.QPolygonF()
		for p in self.wii.calibrationPoints:
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
			self.ui.frame_mouseControl.setEnabled(1)
			self.statusBar().showMessage("")
			return
		
		self.statusBar().showMessage(self.tr("Connected to ") + self.wii.addr)
		
		if self.calibrated == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonLoadCal.setEnabled(1)
			self.ui.frame_mouseControl.setEnabled(1)
			return
		if self.active == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(1)
			self.ui.pushButtonLoadCal.setEnabled(1)
			self.ui.frame_mouseControl.setEnabled(1)
			return
		else:
			self.ui.pushButtonConnect.setEnabled(0)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonLoadCal.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(1)
			self.ui.frame_mouseControl.setEnabled(0)
	
	
	def disconnectDevice(self):
		if self.active:
			if self.cursor:
				self.cursor.finish()
			self.active = False
		
		if self.wii:
			self.wii.disable()
			self.wii.close()
			self.wii = None
			self.connected = False
			self.calibrated = False
			self.active = False
			self.pushButtonConnect.setText(self.tr("Connect"))
			self.updateButtons()
			self.ui.label_utilization.setText(self.tr("Utilization: 0%"))
			self.clearScreenGraphic()
			self.batteryLevel.setValue(0)
			self.confDialog.wii = None
			self.confDialog.checkButtons()
			return

	def connectWii(self):
		if self.connected:
			self.disconnectDevice()
			return
		
		self.wii = Wiimote()
		pBar = PBarDlg(self)
		pBar.setModal( True )
		pBar.show()
		while 1:
			thread = self.wii.createConnectThread()
			thread.start()
			
			while not thread.wait(30):
				QtGui.QApplication.processEvents()
			
			if pBar.cancelled == True:
				if self.wii.isConnected():
					self.wii.close()
					
				self.wii = None
				pBar.close()
				return

			if self.wii.isConnected():
				self.connected = True
				self.calibrated = False
				self.active = False
				self.updateButtons()
				self.batteryLevel.setValue(self.wii.battery()*100)
				self.pushButtonConnect.setText(self.tr("Disconnect"))
				
				pBar.close()
				
				self.confDialog.wii = self.wii
				self.confDialog.checkButtons()
				
				# Start calibration if configuration says so
				conf = Configuration()
				if conf.getValueStr("autocalibration") == "Yes":
					self.calibrateWii()
				return
			
			if self.wii.error:
				self.wii = None
				msgbox = QtGui.QMessageBox( self )
				msgbox.setWindowTitle( self.tr('Error') )
				msgbox.setText( self.tr("Error. Check your bluetooth driver") )
				msgbox.setModal( True )
				ret = msgbox.exec_()
				pBar.close()
				return
			
			
			

	# doscreen: if doscreen is true, calibrate by manual pointing
	def calibrateWii(self,doScreen=True):
		self.deactivateWii()
		self.ui.label_utilization.setText(self.tr("Utilization: 0%"))
		self.clearScreenGraphic()
		
		self.calibrated = False
		self.active = False
		
		self.wii.state = Wiimote.NONCALIBRATED
		if doScreen:
			doCalibration(self,self.wii)
		else:
			self.loadCalibration(self.wii)
		
		if self.wii.state == Wiimote.CALIBRATED:
			self.calibrated = True
			self.active = False
			self.drawScreenGraphic()
			self.updateButtons()
			self.ui.label_utilization.setText(self.tr("Utilization: ") + "%d%%" % (100.0*self.wii.utilization))
			self.saveCalibrationPars(self.wii)
			
			# Activate cursor after calibration (always)
			self.activateWii()
			
		else:
			self.updateButtons()
			msgbox = QtGui.QMessageBox( self )
			msgbox.setText( self.tr("Error during Calibration") )
			msgbox.setModal( True )
			ret = msgbox.exec_()

	
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
		
	
	def deactivateWii(self):
		if self.active:
			self.cursor.finish()
			self.active = False
			self.pushButtonActivate.setText(self.tr("Activate"))
			self.updateButtons()
	
	
	def activateWii(self):
		if self.active:
			# Deactivate
			self.deactivateWii()
		else:
			# Activate
			self.cursor = FakeCursor(self.wii)
			if self.ui.moveOnlyCheck.isChecked():
				self.cursor.noClicks = True
			
			conf = Configuration()
			zones = [ conf.getValueStr(z) for z in ("zone1","zone2","zone3","zone4") ]
			self.cursor.setZones(zones)
			self.cursor.runThread()
			self.active = True
			self.pushButtonActivate.setText(self.tr("Deactivate"))
			self.updateButtons()
	
	
	# Exit callback
	def closeEvent(self,e):
		if self.mustquit:
			self.disconnectDevice()
			e.accept()
		else:
			msgbox = QtGui.QMessageBox(self)
			msgbox.setText(self.tr("The application will remain active (systray).") + "\n" + \
				self.tr("To quit, use file->quit menu") )
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



def getTranslator():
	trl = qt.QTranslator()
	loc = locale.getdefaultlocale()[0]
	if loc:
		code = loc.lower()
		if len(code) > 1:
			code = code[0:2]
			fname = "/usr/share/qt4/translations/pywhiteboard_" + code + ".qm"
			trl.load(fname)
	return trl





def main():
	app = QtGui.QApplication(sys.argv)
	t = getTranslator()
	app.installTranslator(t)
	mainWin = MainWindow()
	stray = SysTrayIcon("icon.xpm", mainWin)
	stray.show()
	mainWin.show()
	app.exec_()
