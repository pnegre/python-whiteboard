# -*- coding: utf-8 -*-

import sys,time

import wiimote

from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt




def clock():
	return int(time.time()*1000)


class SandClock:
	READY, FIN1, FIN2 = range(3)
	
	def __init__(self,scene,px,py):
		self.scene = scene
		self.elipse = scene.addEllipse(px-30,py-30,60,60,
			qt.QPen(QtCore.Qt.black, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin),
			qt.QBrush(QtCore.Qt.red))
		self.elipse.setVisible(False)
		self.initialize()
	
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
				if delta > 150:
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
		else:
			self.elipse.setVisible(False)

	
	def finished(self):
		return self.state == SandClock.FIN2
	
	def getPoint(self):
		return self.point



class SmallScreen:
	def __init__(self,scx,scy,scene):
		self.scene = scene
		self.parentx = scx
		self.parenty = scy
		self.dx = 200
		self.dy = 200
		self.square = scene.addRect(qt.QRectF(scx/2-100,scy/2-100,200,200))
		self.point = scene.addRect(qt.QRectF(self.parentx/2-2,self.parenty/2-2,4,4))
	
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
	


class CalibrateDialog2(QtGui.QDialog):
	def __init__(self,parent,wii):
		QtGui.QWidget.__init__(self,parent)
		self.wii = wii
		self.ui = uic.loadUi("calibration2.ui",self)
		
		screenGeom = QtGui.QDesktopWidget().screenGeometry()
		wdt = screenGeom.width()-2
		hgt = screenGeom.height()-2
		
		viewport = [ self.ui.graphicsView.maximumViewportSize().width(), 
			self.ui.graphicsView.maximumViewportSize().height() 
		]
		
		self.scene = qt.QGraphicsScene()
		self.scene.setSceneRect(0,0, viewport[0], viewport[1])
		self.ui.graphicsView.setScene(self.scene)
		
		self.smallScreen = SmallScreen(viewport[0], viewport[1], self.scene)
		self.sandclock = SandClock(self.scene,viewport[0]/2,viewport[1]/2)
		
		self.realCalibrationPoints = [
			[0,0], [wdt,0], [wdt,hgt], [0,hgt]
		]
		
		self.wiiPoints = []
		self.textMessages = [ "TOP-LEFT", "TOP-RIGHT", "BOTTOM-RIGHT", "BOTTOM-LEFT" ]
		
		self.ui.label.setText(self.textMessages.pop(0))
		
		self.connect(self.ui.but_cancel,
			QtCore.SIGNAL("clicked()"), self.close)
		
		self.shcut1 = QtGui.QShortcut(self)
		self.shcut1.setKey("Esc")
		self.connect(self.shcut1, QtCore.SIGNAL("activated()"), self.close)
		
		self.timer = qt.QTimer(self)
		self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.doWork)
		self.timer.start()
	
	
	def doWork(self):
		self.wii.getMsgs()
		wii_pos = self.wii.getPos()
		if wii_pos:
			self.smallScreen.drawPoint(wii_pos)
			self.sandclock.update(wii_pos)
			self.sandclock.draw()
		else:
			self.sandclock.update(None)
			self.sandclock.draw()
		
		if self.sandclock.finished():
			self.wiiPoints.append(self.sandclock.getPoint())
			self.sandclock.initialize()
			if len(self.wiiPoints) == 4:
				self.close()
				return
			self.ui.label.setText(self.textMessages.pop(0))
	
	
	def closeEvent(self,e):
		#self.disconnect(self.timer, QtCore.SIGNAL("timeout()"), self.doWork)
		e.accept()




class CalibrateDialog(QtGui.QDialog):
	def __init__(self,parent,wii):
		QtGui.QWidget.__init__(self,parent,QtCore.Qt.FramelessWindowHint)
		self.wii = wii
		self.setFixedSize(QtGui.QDesktopWidget().size())
		self.setContentsMargins(0,0,0,0)
		self.setWindowState(QtCore.Qt.WindowActive | QtCore.Qt.WindowFullScreen)

		sh = QtGui.QShortcut(self)
		sh.setKey("Esc")
		self.connect(sh, 
			QtCore.SIGNAL("activated()"), self.close)
		
		sh = QtGui.QShortcut(self)
		sh.setKey("Down")
		self.connect(sh, 
			QtCore.SIGNAL("activated()"), self.decCrosses)
		
		sh = QtGui.QShortcut(self)
		sh.setKey("Up")
		self.connect(sh, 
			QtCore.SIGNAL("activated()"), self.incCrosses)
		
		screenGeom = QtGui.QDesktopWidget().screenGeometry()
		self.wdt = screenGeom.width()-2
		self.hgt = screenGeom.height()-2
		
		self.scene = qt.QGraphicsScene()
		self.gv = QtGui.QGraphicsView()
		self.gv.setScene(self.scene)
		self.gv.setStyleSheet( "QGraphicsView { border-style: none; }" )
		self.layout = QtGui.QVBoxLayout()
		self.layout.setMargin(0)
		self.layout.setSpacing(0)
		self.layout.addWidget(self.gv)
		self.setLayout(self.layout)
		
		self.CalibrationPoints = [
			[20,20], [self.wdt-20,20], [self.wdt-20,self.hgt-20], [20,self.hgt-20]
		]
		
		self.updateCalibrationPoints(0)
		
		self.clock = clock()
		
		self.timer = qt.QTimer(self)
		self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.doWork)
		self.timer.start()


	def decCrosses(self):
		if self.CalibrationPoints[0][0] < 350:
			self.updateCalibrationPoints(10)
	
	def incCrosses(self):
		if self.CalibrationPoints[0][0] > 15: 
			self.updateCalibrationPoints(-10)
	
	def updateCalibrationPoints(self,delta=0):
		self.scene.clear()
		self.marks = []
		self.wiiPoints = []
		self.realCalibrationPoints = []
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
			self.marks.append(m)
			self.realCalibrationPoints.append([p[0],p[1]])
		
		self.smallScreen = SmallScreen(self.wdt,self.hgt,self.scene)
		self.sandclock = SandClock(self.scene,self.wdt/2,self.hgt/2)
		txt = self.scene.addSimpleText("Push UP/DOWN to alter the crosses' position")
		txt.setPos(self.wdt/2 - txt.boundingRect().width()/2, 40)
			

	def doWork(self):
		self.wii.getMsgs()
		wii_pos = self.wii.getPos()
		if wii_pos:
			self.smallScreen.drawPoint(wii_pos)
			self.sandclock.update(wii_pos)
			self.sandclock.draw()
		else:
			self.sandclock.update(None)
			self.sandclock.draw()
		
		if self.sandclock.finished():
			self.wiiPoints.append(self.sandclock.getPoint())
			self.marks.pop(0).setVisible(True)
			self.sandclock.initialize()
			if len(self.wiiPoints) == 4:
				self.close()
				return
				
		if len(self.marks):
			m = self.marks[0]
			c = clock() - self.clock
			if c >= 300:
				if m.isVisible(): m.setVisible(False)
				else: m.setVisible(True)
				self.clock = clock()
	
	
	def closeEvent(self,e):
		#self.disconnect(self.timer, QtCore.SIGNAL("timeout()"), self.doWork)
		e.accept()
	

def doCalibration(parent,wii,fullscreen):
	dialog = None
	if fullscreen:
		dialog = CalibrateDialog(parent,wii)
	else:
		dialog = CalibrateDialog2(parent,wii)
	
	dialog.show()
	dialog.exec_()
	print "C"
	if len(dialog.wiiPoints) == 4:
		print dialog.realCalibrationPoints
		print dialog.wiiPoints
		wii.calibrate(dialog.realCalibrationPoints,dialog.wiiPoints)

