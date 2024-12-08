#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from cursor import FakeCursor
from threads import *

from calibration import doCalibration, CalibrationAbort
from configuration import Configuration, ConfigDialog


import sys, time, locale, traceback
import hashlib

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import PyQt5.Qt as qt

def old_div(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a // b
    else:
        return a / b

class AboutDlg(QtWidgets.QDialog):
	
	def __init__(self, parent=None):
		super(AboutDlg, self).__init__(parent)
		self.ui = uic.loadUi("about.ui",self)
		self.ui.butOK.clicked.connect(self.close)



class PBarDlg(QtWidgets.QDialog):
	def __init__(self, parent=None):
		super(PBarDlg,self).__init__(parent, qt.Qt.CustomizeWindowHint | qt.Qt.WindowTitleHint)
		
		self.ui = uic.loadUi("pbar.ui",self)
		self.cancelled = False
		self.choice = 0
		self.ui.butCancel.clicked.connect(self.cancelConnection)
		self.ui.butChoose.clicked.connect(self.makeChoice)
		self.ui.butChoose.hide()
	
	def reInit(self,mac='*'):
		self.cancelled = False
		self.choice = 0
		self.ui.butChoose.hide()
		self.ui.butCancel.setEnabled(True)
		self.ui.butChoose.setEnabled(True)
		if mac == '*':
			self.ui.label.setText(self.tr("Press 1+2 on your wiimote or SYNC on your wiimote plus"))
		else:
			self.ui.label.setText(self.tr("Press 1+2 or SYNC on") + " " + mac)
	
	def cancelConnection(self):
		self.cancelled = True
		self.ui.butCancel.setEnabled(False)
		self.ui.label.setText(self.tr("Cancelling..."))
	
	def makeChoice(self):
		self.choice = True
		self.ui.label.setText(self.tr("Wait..."))
		self.ui.butChoose.setEnabled(False)
		self.ui.butCancel.setEnabled(False)
	
	def inform(self,txt):
		self.ui.butChoose.setText(txt)
		self.ui.butChoose.show()


class MainWindow(QtWidgets.QMainWindow):
	
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.ui = uic.loadUi("mainwindow.ui",self)
		self.setWindowTitle("python-whiteboard")
		self.setWindowFlags( qt.Qt.CustomizeWindowHint | qt.Qt.WindowMinimizeButtonHint |
			qt.Qt.WindowCloseButtonHint )
		
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

		self.ui.pushButtonConnect.clicked.connect(self.connectWii)
		self.ui.pushButtonCalibrate.clicked.connect(self.calibrateWiiScreen)
		self.ui.pushButtonActivate.clicked.connect(self.activateWii)
		self.ui.pushButtonLoadCal.clicked.connect(self.calibrateWiiFromSettings)
		self.ui.pushButtonSettings.clicked.connect(self.showHideSettings)
		self.ui.comboProfiles.currentIndexChanged.connect(self.changeProfile)
		self.updateButtons()

		self.ui.actionQuit.triggered.connect(self.mustQuit)
		self.ui.actionHelp.triggered.connect(self.showAboutDlg)
		self.ui.actionNew_Profile.triggered.connect(self.addProfile)
		self.ui.actionDelete_Current_Profile.triggered.connect(self.delCurrentProfile)
		self.ui.actionWipe_configuration.triggered.connect(self.wipeConfiguration)

		self.ui.moveOnlyCheck.setChecked( conf.getValueStr('moveonly') == 'Yes' )
		self.ui.moveOnlyCheck.stateChanged.connect(self.checkMoveOnly)

		if conf.getValueStr("autoconnect") == "Yes":
			self.timer = qt.QTimer(self)
			self.timer.setInterval(500)
			self.timer.timeout.connect(self.autoConnect)
			self.timer.start()
		
		self.timer2 = qt.QTimer(self)
		self.timer2.setInterval(4000)
		self.timer2.timeout.connect(self.checkWii)
		self.timer2.start()
		
		self.confDialog = ConfigDialog(self, self.wii)
		layout = QtWidgets.QGridLayout()
		layout.addWidget(self.confDialog)
		self.ui.confContainer.setLayout(layout)
		self.ui.confContainer.setVisible(False)
		
		self.refreshProfiles()
		
		self.center()
	
	
	def changeProfile(self,i):
		conf = Configuration()
		if i == 0:
			conf.setGroup("default")
		else:
			g = str(self.ui.comboProfiles.currentText())
			conf.setGroup(hashlib.md5(g.encode('utf-8')).hexdigest())
		
		self.confDialog.refreshWidgets()
		self.ui.moveOnlyCheck.setChecked( conf.getValueStr('moveonly') == 'Yes' )
	
	
	def refreshProfiles(self):
		conf = Configuration()
		self.ui.comboProfiles.clear()
		self.ui.comboProfiles.addItem(self.tr("default"))
		
		for p in conf.getProfileList():
			self.ui.comboProfiles.addItem(p)
		
		self.confDialog.refreshWidgets()
		self.ui.moveOnlyCheck.setChecked( conf.getValueStr('moveonly') == 'Yes' )
	
	
	def addProfile(self):
		profName, ok = QtWidgets.QInputDialog.getText(self,
			self.tr("New Profile"), self.tr('Name:'))
		
		profName = str(profName)
		if ok and profName != '':
			conf = Configuration()
			profiles = conf.getProfileList()
			for p in profiles:
				if p == profName: return
			profiles.append(profName)
			conf.setProfileList(profiles)
			self.refreshProfiles()
			i = self.ui.comboProfiles.findText(profName)
			self.ui.comboProfiles.setCurrentIndex(i)
	
	
	def delCurrentProfile(self):
		i = self.ui.comboProfiles.currentIndex()
		currentProfile = str(self.ui.comboProfiles.currentText())
		if i == 0: return
		conf = Configuration()
		profiles = conf.getProfileList()
		profiles = [ p for p in profiles if p != currentProfile ]
		conf.setProfileList(profiles)
		self.refreshProfiles()
		self.ui.comboProfiles.setCurrentIndex(0)
	
	
	def wipeConfiguration(self):
		conf = Configuration()
		conf.wipe()
		msgbox = QtWidgets.QMessageBox(self)
		msgbox.setText(self.tr("The application will close. Please restart manually") )
		msgbox.setModal( True )
		ret = msgbox.exec_()
		self.mustQuit()
	
	
	def showHideSettings(self):
		self.ui.confContainer.setVisible(not self.ui.confContainer.isVisible())
		QtWidgets.QApplication.processEvents()
		if self.ui.confContainer.isVisible():
			self.ui.pushButtonSettings.setText(self.tr('Hide settings'))
			# Res¡ze to max
			self.resize(1000,1000)
		else:
			self.ui.pushButtonSettings.setText(self.tr('Show settings'))
			self.adjustSize()
	
	
	def checkMoveOnly(self,i):
		conf = Configuration()
		if self.sender().isChecked():
			conf.saveValue('moveonly','Yes')
			if self.cursor:
				self.cursor.noClicks = True
		else:
			conf.saveValue('moveonly','No')
			if self.cursor:
				self.cursor.noClicks = False
	
	
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
			
			msgbox = QtWidgets.QMessageBox( self )
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
			y = max_y * (1-old_div(float(p[1]),Wiimote.MAX_Y))
			quad.append(qt.QPointF(x,y))
		self.scene.addPolygon(quad)
		self.wiiScreen.setScene(self.scene)
		self.wiiScreen.show()
	
	
	def clearScreenGraphic(self):
		if self.wiiScreen.scene():
			self.scene.clear()


	def center(self):
		screen = QtWidgets.QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move(old_div((screen.width()-size.width()),2), old_div((screen.height()-size.height()),2))
		
		

	def updateButtons(self):
		if self.connected == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonLoadCal.setEnabled(0)
			#self.ui.frame_mouseControl.setEnabled(1)
			self.statusBar().showMessage("")
			return
		
		self.statusBar().showMessage(self.tr("Connected to ") + self.wii.addr)
		
		if self.calibrated == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(0)
			self.ui.pushButtonLoadCal.setEnabled(1)
			#self.ui.frame_mouseControl.setEnabled(1)
			return
		if self.active == False:
			self.ui.pushButtonConnect.setEnabled(1)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonActivate.setEnabled(1)
			self.ui.pushButtonLoadCal.setEnabled(1)
			#self.ui.frame_mouseControl.setEnabled(1)
			return
		else:
			self.ui.pushButtonConnect.setEnabled(0)
			self.ui.pushButtonCalibrate.setEnabled(1)
			self.ui.pushButtonLoadCal.setEnabled(0)
			self.ui.pushButtonActivate.setEnabled(1)
			#self.ui.frame_mouseControl.setEnabled(0)
	
	
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


	def makeBTNCallback(self):
		def func():
			# Simulate click to calibrate button
			self.ui.pushButtonCalibrate.click()
		
		return func

	

	def connectWii(self):
		if self.connected:
			self.disconnectDevice()
			return
		
		self.wii = Wiimote()
		pBar = PBarDlg(self)
		pBar.setModal( True )
		pBar.show()
		conf = Configuration()
		selectedMac = conf.getValueStr("selectedmac")
		pBar.reInit(selectedMac)
		pool = []
		while 1:
			thread = self.wii.createConnectThread(selectedMac,pool)
			thread.start()
			
			while not thread.wait(30):
				QtWidgets.QApplication.processEvents()
			
			if pBar.cancelled == True:
				if self.wii.isConnected():
					self.wii.close()
					
				self.wii = None
				pBar.close()
				return
			
			if selectedMac == '*' and len(pool) >= 1:
				if Configuration().getValueStr('nowaitdevices') == 'Yes':
					selectedMac = pool[0]
				else:
					pBar.inform(self.tr('Found ') + str(len(pool)) + self.tr(' Devices. Press to Choose'))

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
				
				self.wii.disable()
				self.wii.putCallbackBTN(self.makeBTNCallback())
				self.wii.putCallbackIR(None)
				self.wii.enable()
				
				# Start calibration if configuration says so
				conf = Configuration()
				if conf.getValueStr("autocalibration") == "Yes":
					if conf.getValueStr("automatrix") == "Yes":
						self.calibrateWiiFromSettings()
					else:
						self.calibrateWiiScreen()
				return
			
			if self.wii.error:
				self.wii = None
				msgbox = QtWidgets.QMessageBox( self )
				msgbox.setWindowTitle( self.tr('Error') )
				msgbox.setText( self.tr("Error. Check your bluetooth driver") )
				msgbox.setModal( True )
				ret = msgbox.exec_()
				pBar.close()
				return
			
			if pBar.choice:
				if len(pool) == 1:
					selectedMac = str(pool[0])
					pBar.reInit(selectedMac)
				else:
					item, ok = QtWidgets.QInputDialog.getItem(self,
						self.tr("Warning"), self.tr("Choose device"), pool, 0, False)
					if ok:
						selectedMac = str(item)
						pBar.reInit(selectedMac)
					else:
						pBar.close()
						return
			
			
			

	# doscreen: if doscreen is true, calibrate by manual pointing
	def calibrateWii(self,loadFromSettings=False):
		self.deactivateWii()		
		self.ui.label_utilization.setText(self.tr("Utilization: 0%"))
		self.clearScreenGraphic()
		
		self.calibrated = False
		self.active = False
		try:
			self.wii.state = Wiimote.NONCALIBRATED
			if loadFromSettings:
				# If calibration matrix can't be loaded, calibrate manually
				if not self.loadCalibration(self.wii):
					doCalibration(self,self.wii)
			else:
				doCalibration(self,self.wii)
			
			
			if self.wii.state == Wiimote.CALIBRATED:
				self.calibrated = True
				self.active = False
				self.drawScreenGraphic()
				self.updateButtons()
				self.ui.label_utilization.setText(self.tr("Utilization: ") + "%d%%" % (100.0*self.wii.utilization))
				self.saveCalibrationPars(self.wii)
				
				# Activate cursor after calibration (always)
				self.activateWii()
				return
		
		except CalibrationAbort:
			# Do nothing (user choice)
			pass
		
		except:
			print("Error during Calibration")
			traceback.print_exc(file=sys.stdout)
			self.updateButtons()
			msgbox = QtWidgets.QMessageBox( self )
			msgbox.setText( self.tr("Error during Calibration") )
			msgbox.setModal( True )
			ret = msgbox.exec_()
		
		# Installs button callback (for calling calibration)
		self.wii.disable()
		self.wii.putCallbackBTN(self.makeBTNCallback())
		self.wii.putCallbackIR(None)
		self.wii.enable()

	
	def calibrateWiiScreen(self):
		self.calibrateWii()
	
	
	def calibrateWiiFromSettings(self):
		self.calibrateWii(loadFromSettings=True)


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
			return True
		except:
			return False
		
	
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
			
			# Installs button callback (for calling calibration)
			self.wii.disable()
			self.wii.putCallbackBTN(self.makeBTNCallback())
			
			conf = Configuration()
			zones = [ conf.getValueStr(z) for z in ("zone1","zone2","zone3","zone4") ]
			self.cursor.setZones(zones)
			self.cursor.runThread()
			self.active = True
			self.pushButtonActivate.setText(self.tr("Deactivate"))
			self.updateButtons()
	
	
	# Exit callback
	def closeEvent(self,e):
		# Unity does not support qt systray anymore.
		# So, I'm putting the old code on hold
		
		#if self.mustquit:
			#self.disconnectDevice()
			#e.accept()
		#else:
			#msgbox = QtWidgets.QMessageBox(self)
			#msgbox.setText(self.tr("The application will remain active (systray).") + "\n" + \
				#self.tr("To quit, use file->quit menu") )
			#msgbox.setModal( True )
			#ret = msgbox.exec_()
			#self.showHide()
			#e.ignore()
		
		# Instead, we simply ask if the user wants to really quit.
		
		msgbox = QtWidgets.QMessageBox(self)
		msgbox.setText(self.tr("Are you sure you want to exit?") )
		msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
		msgbox.setModal( True )
		ret = msgbox.exec_()
		if ret == QtWidgets.QMessageBox.Ok:
			# Exit the application
			self.disconnectDevice()
			e.accept()
		else:
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
		self.stray = QtWidgets.QSystemTrayIcon()
		self.stray.setIcon(QtGui.QIcon(fname))

		self.stray.activated.connect(self.activate)
	
	def activate(self, reason):
		if reason == QtWidgets.QSystemTrayIcon.Trigger:
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
			fname = "/usr/share/qt5/translations/pywhiteboard_" + code + ".qm"
			trl.load(fname)
	return trl




# Checks that only one instance of python-whiteboard is running
import fcntl
fp = None
def checkSingle():
	lockfile = '/tmp/python-whiteboard.lock'
	global fp
	fp = open(lockfile, 'w')
	try:
		fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
		return True
	except IOError:
		return False





def main():
	app = QtWidgets.QApplication(sys.argv)
	t = getTranslator()
	app.installTranslator(t)
	mainWin = MainWindow()
	
	if checkSingle() == False:
		msgbox = QtWidgets.QMessageBox( mainWin )
		msgbox.setText( app.tr("Application already running") )
		msgbox.setModal( True )
		ret = msgbox.exec_()
		sys.exit()
	
	stray = SysTrayIcon("icon.xpm", mainWin)
	stray.show()
	mainWin.show()
	app.exec_()
