# -*- coding: utf-8 -*-

import sys,time

import wiimote

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import PyQt5.Qt as qt

from configuration import Configuration


class CalibrationAbort(Exception):
	pass

def old_div(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a // b
    else:
        return a / b

def clock():
	return int(time.time()*1000)


class SandClock(object):
	READY, FIN1, FIN2 = list(range(3))

	def __init__(self,scene,px,py,radius=30):
		self.scene = scene
		self.radius = radius
		self.elipse = None
		self.circle = None
		self.setCenter(px,py)
		self.initialize()


	def setCenter(self,x,y):
		if self.elipse:
			self.scene.removeItem(self.elipse)
			self.scene.removeItem(self.circle)

		self.elipse = self.scene.addEllipse(x-old_div(self.radius,2), y-old_div(self.radius,2), self.radius, self.radius,
			qt.QPen(QtCore.Qt.red, 1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin),
			qt.QBrush(QtCore.Qt.red))
		self.circle = self.scene.addEllipse(x-old_div(self.radius,2), y-old_div(self.radius,2), self.radius, self.radius,
			qt.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
		self.elipse.setVisible(False)
		self.circle.setVisible(True)
		self.scene.update() 


	def initialize(self):
		self.totalTicks = 0
		self.lastTick = 0
		self.state = SandClock.READY

	def update(self,p):
		t = clock()
		delta = 0
		if self.lastTick != 0: delta = t - self.lastTick
		if p == None:
			if delta > 100:
				if self.state == SandClock.FIN1:
					self.state = SandClock.FIN2
				if delta > 250:
					self.initialize()
			return
		self.point = list(p)
		self.lastTick = t
		if self.totalTicks < 700:
			self.totalTicks += delta
		else:
			self.state = SandClock.FIN1

	def draw(self):
		if self.totalTicks:
			self.elipse.setVisible(True)
			dgrs = 5760*self.totalTicks/700
			self.elipse.setSpanAngle(dgrs)
			self.scene.update()
		else:
			self.elipse.setVisible(False)
			self.scene.update()

	def finished(self):
		return self.state == SandClock.FIN2

	def getPoint(self):
		return self.point



class SmallScreen(object):
	def __init__(self,scx,scy,scene):
		self.scene = scene
		self.parentx = scx
		self.parenty = scy
		self.dx = 200
		self.dy = 200
		self.square = scene.addRect(qt.QRectF(old_div(scx,2)-100,old_div(scy,2)-100,200,200))
		self.point = scene.addRect(qt.QRectF(old_div(self.parentx,2)-2,old_div(self.parenty,2)-2,4,4))
	def drawPoint(self,pos):
		px = -100 + pos[0]*self.dx/wiimote.Wiimote.MAX_X-2
		py = 100 - pos[1]*self.dy/wiimote.Wiimote.MAX_Y-2
		self.point.setPos(px,py)



def crossPoly(x,y):
	pol = QtGui.QPolygonF()
	pol.append(qt.QPointF(x,y))
	pol.append(qt.QPointF(x-5,y-5))
	pol.append(qt.QPointF(x,y))
	pol.append(qt.QPointF(x+5,y+5))
	pol.append(qt.QPointF(x,y))
	pol.append(qt.QPointF(x-5,y+5))
	pol.append(qt.QPointF(x,y))
	pol.append(qt.QPointF(x+5,y-5))
	return pol



class CalibrateDialog2(QtWidgets.QDialog):
	wiiCallback = QtCore.pyqtSignal(int, int)

	def __init__(self,parent,wii):
		QtWidgets.QWidget.__init__(self,parent)
		self.wii = wii
		self.ui = uic.loadUi("calibration2.ui",self)

		screenGeom = QtWidgets.QDesktopWidget().screenGeometry()
		wdt = screenGeom.width()-2
		hgt = screenGeom.height()-2

		viewport = [ self.ui.graphicsView.maximumViewportSize().width(), 
			self.ui.graphicsView.maximumViewportSize().height() 
		]

		self.scene = qt.QGraphicsScene()
		self.scene.setSceneRect(0,0, viewport[0], viewport[1])
		self.ui.graphicsView.setScene(self.scene)

		self.smallScreen = SmallScreen(viewport[0], viewport[1], self.scene)
		self.sandclock = SandClock(self.scene,old_div(viewport[0],2),old_div(viewport[1],2))

		self.CalibrationPoints = [
			[0,0], [wdt,0], [wdt,hgt], [0,hgt]
		]
		self.wiiPoints = []
		self.textMessages = [ 
			self.tr("TOP-LEFT"), 
			self.tr("TOP-RIGHT"), 
			self.tr("BOTTOM-RIGHT"), 
			self.tr("BOTTOM-LEFT") ]

		self.ui.label.setText(self.textMessages.pop(0))

		self.ui.but_cancel.clicked.connect(self.close)

		self.shcut1 = QtWidgets.QShortcut(self)
		self.shcut1.setKey("Esc")
		self.shcut1.activated.connect(self.close)

		self.mutex = qt.QMutex()

		self.wii.disable()
		self.wii.putCallbackIR(self.makeWiiCallback())
		self.wii.enable()

		self.timer = qt.QTimer(self)
		self.timer.setInterval(70)
		self.timer.timeout.connect(self.doWork)
		self.timer.start()

		self.wiiCallback.connect(self._wiiCallback)

	@QtCore.pyqtSlot(int, int)
	def _wiiCallback(self, pos0, pos1):
		pos = [pos0, pos1]
		self.mutex.lock()
		self.smallScreen.drawPoint(pos)
		self.sandclock.update(pos)
		self.sandclock.draw()
		# Restart the timer
		self.timer.start()
		self.mutex.unlock()

	def makeWiiCallback(self):
		def callback(pos):
			self.wiiCallback.emit(pos[0], pos[1])
		return callback

	def doWork(self):
		self.mutex.lock()
		self.sandclock.update(None)
		self.sandclock.draw()

		if self.sandclock.finished():
			self.wiiPoints.append(self.sandclock.getPoint())
			self.sandclock.initialize()
			if len(self.wiiPoints) == 4:
				self.mutex.unlock()
				self.close()
				return
			self.ui.label.setText(self.textMessages.pop(0))

		self.mutex.unlock()

	def closeEvent(self,e):
		self.timer.stop()
		self.wii.disable()
		e.accept()




class CalibrateDialog(QtWidgets.QDialog):
	wiiCallback = QtCore.pyqtSignal(int, int)

	def __init__(self,parent,wii):
		screenGeom = QtWidgets.QDesktopWidget().screenGeometry()
		self.wdt = screenGeom.width()
		self.hgt = screenGeom.height()

		# Thanks, Pietro Pilolli!!
		QtWidgets.QWidget.__init__(self, parent,
			QtCore.Qt.FramelessWindowHint | 
			QtCore.Qt.WindowStaysOnTopHint  | 
			QtCore.Qt.X11BypassWindowManagerHint )
		self.setGeometry(0, 0, self.wdt, self.hgt)

		self.wii = wii
		self.setContentsMargins(0,0,0,0)

		sh = QtWidgets.QShortcut(self)
		sh.setKey("Esc")
		sh.activated.connect(self.close)

		sh = QtWidgets.QShortcut(self)
		sh.setKey("Down")
		sh.activated.connect(self.decCrosses)

		sh = QtWidgets.QShortcut(self)
		sh.setKey("Up")
		sh.activated.connect(self.incCrosses)

		self.scene = qt.QGraphicsScene()
		self.scene.setSceneRect(0,0, self.wdt, self.hgt)
		self.gv = QtWidgets.QGraphicsView()
		self.gv.setScene(self.scene)
		self.gv.setStyleSheet( "QGraphicsView { border-style: none; }" )
		self.layout = QtWidgets.QVBoxLayout()
		self.layout.setContentsMargins(0,0,0,0)
		self.layout.setSpacing(0)
		self.layout.addWidget(self.gv)
		self.setLayout(self.layout)

		self.CalibrationPoints = [
			[40,40], [self.wdt-40,40], [self.wdt-40,self.hgt-40], [40,self.hgt-40]
		]
		self.clock = clock()
		self.mutex = qt.QMutex()
		self.updateCalibrationPoints(0)

		self.wii.putCallbackIR(self.makeWiiCallback())
		self.wii.enable()

		self.timer = qt.QTimer(self)
		self.timer.setInterval(70)
		self.timer.timeout.connect(self.doWork)
		self.timer.start()

		self.wiiCallback.connect(self._wiiCallback)


	def decCrosses(self):
		if self.CalibrationPoints[0][0] < 350:
			self.updateCalibrationPoints(10)

	def incCrosses(self):
		if self.CalibrationPoints[0][0] > 40: 
			self.updateCalibrationPoints(-10)

	def updateCalibrationPoints(self,delta=0):
		self.mutex.lock()
		self.scene.clear()
		self.marks = []
		self.wiiPoints = []
		self.CalibrationPoints[0][0] += delta
		self.CalibrationPoints[1][0] -= delta
		self.CalibrationPoints[2][0] -= delta
		self.CalibrationPoints[3][0] += delta
		self.CalibrationPoints[0][1] += delta
		self.CalibrationPoints[1][1] += delta
		self.CalibrationPoints[2][1] -= delta
		self.CalibrationPoints[3][1] -= delta
		for p in self.CalibrationPoints:
			self.scene.addPolygon(crossPoly(*p))
			m = self.scene.addRect(p[0]-5,p[1]-5,10,10,
				qt.QPen(QtCore.Qt.red, 2, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
			m.setVisible(False)
			self.marks.append([m, p])
			self.scene.update()

		self.smallScreen = SmallScreen(self.wdt,self.hgt,self.scene)
		self.sandclock = SandClock(self.scene,*self.marks[0][1])
		txt = self.scene.addSimpleText(self.tr("Push UP/DOWN to alter the crosses' position"))
		txt.setPos(old_div(self.wdt,2) - old_div(txt.boundingRect().width(),2), 40)
		self.mutex.unlock()

	@QtCore.pyqtSlot(int, int)
	def _wiiCallback(self, pos0, pos1):
		pos = [pos0, pos1]
		self.mutex.lock()
		self.smallScreen.drawPoint(pos)
		self.sandclock.update(pos)
		self.sandclock.draw()
		# Restart the timer
		self.timer.start()
		self.mutex.unlock()

	def makeWiiCallback(self):
		k = [0]
		def callback(pos):
			t = clock()
			if (t-k[0]) < 30: return
			self.wiiCallback.emit(pos[0], pos[1])
			k[0] = t
		return callback

	def doWork(self):
		self.mutex.lock()
		self.sandclock.update(None)
		self.sandclock.draw()

		if len(self.marks):
			m = self.marks[0][0]
			c = clock() - self.clock
			if c >= 300:
				if m.isVisible(): m.setVisible(False)
				else: m.setVisible(True)
				self.clock = clock()

		if self.sandclock.finished():
			self.wiiPoints.append(self.sandclock.getPoint())
			self.marks.pop(0)[0].setVisible(True)
			if len(self.wiiPoints) == 4:
				self.mutex.unlock()
				self.close()
				return
			self.sandclock.initialize()
			self.sandclock.setCenter(*self.marks[0][1])

		self.mutex.unlock()


	def closeEvent(self,e):
		self.timer.stop()
		self.wii.disable()
		e.accept()


def doCalibration(parent,wii):
	conf = Configuration()
	wii.disable()
	wii.putCallbackBTN(None)

	if conf.getValueStr("fullscreen") == "Yes":
		dialog = CalibrateDialog(parent,wii)
		dialog.showFullScreen()
		dialog.grabKeyboard()
		dialog.exec_()
		dialog.releaseKeyboard()
	else:
		dialog = CalibrateDialog2(parent,wii)
		dialog.exec_()

	if len(dialog.wiiPoints) == 4:
		wii.calibrate(dialog.CalibrationPoints,dialog.wiiPoints)
	else:
		raise CalibrationAbort()

