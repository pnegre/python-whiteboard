# -*- coding: utf-8 -*-

import Xlib.display
import Xlib.ext.xtest
import time

import PyQt4.Qt as qt

from configuration import Configuration


def clock():
	return int(time.time()*1000)


class Filter:
	def __init__(self):
		self.data = []
		conf = Configuration()
		self.limit = int(conf.getValueStr("smoothing"))
	
	def update(self,p):
		self.data.append(p)
		if len(self.data) > self.limit:
			self.data.pop(0)
			
		n = len(self.data)
		res = [0,0]
		for p in self.data:
			res[0] += p[0]
			res[1] += p[1]
		res[0] /= n
		res[1] /= n
		return res

class Click:
	UP_TIMEOUT = 100
	
	def __init__(self,cursor):
		self.initialTime = clock()
		self.cursor = cursor
		self.cursor.mouse_down()
		
	
	def update(self,evt):
		t = clock()
		if evt:
			self.initialTime = clock()
			return True
		elif (t-self.initialTime) > Click.UP_TIMEOUT:
			self.cursor.mouse_up()
			return False
		return True


class FakeCursor:
	LEFT_BUTTON = 1
	MIDDLE_BUTTON = 2
	RIGHT_BUTTON = 3
	ONLY_MOVE = 4
	ZONE1, ZONE2, ZONE3, ZONE4 = range(4)
	
	def __init__(self,wii):
		self.display = Xlib.display.Display()
		self.screen = self.display.screen()
		self.wii = wii
		self.click = None
		self.filt = None
		self.clickType = FakeCursor.LEFT_BUTTON
		self.zones = {}
		self.mutex = qt.QMutex()
		self.mustFinish = False
		self.thread = None
	
	
	def setZone(self,zone,clickType):
		self.zones[zone] = clickType
	
	def setZones(self,actions):
		for z,a in zip((FakeCursor.ZONE1,FakeCursor.ZONE2,FakeCursor.ZONE3,FakeCursor.ZONE4),actions):
			if a == '2':
				self.setZone(z,FakeCursor.RIGHT_BUTTON)
			elif a == '0':
				self.setZone(z,FakeCursor.LEFT_BUTTON)
			elif a == '3':
				self.setZone(z,FakeCursor.MIDDLE_BUTTON)
			elif a == '1':
				self.setZone(z,FakeCursor.ONLY_MOVE)
			else:
				self.setZone(z,FakeCursor.LEFT_BUTTON)
	
	
	def move(self,pos):
		Xlib.ext.xtest.fake_input(self.display, Xlib.X.MotionNotify, x=pos[0], y=pos[1])
		self.display.sync()
	
	
	def mouse_down(self):
		button = self.clickType
		if button != FakeCursor.ONLY_MOVE:
			Xlib.ext.xtest.fake_input(self.display, Xlib.X.ButtonPress, button)
			self.display.sync()
	
	
	def mouse_up(self):
		button = self.clickType
		if button != FakeCursor.ONLY_MOVE:
			Xlib.ext.xtest.fake_input(self.display, Xlib.X.ButtonRelease, button)
			self.display.sync()
	
	
	# Returns True if point is within screen limits
	def checkLimits(self,pos):
		if pos[1] < 0:
			# Zone 1
			self.clickType = self.zones[FakeCursor.ZONE1]
			return False
		if pos[0] > self.screen['width_in_pixels']:
			# Zone 2
			self.clickType = self.zones[FakeCursor.ZONE2]
			return False
		if pos[1] > self.screen['height_in_pixels']:
			# Zone 3
			self.clickType = self.zones[FakeCursor.ZONE3]
			return False
		if pos[0] < 0:
			# Zone 4
			self.clickType = self.zones[FakeCursor.ZONE4]
			return False
		
		return True
	
	
	# This function fabricates the callback function that is to be
	# passed to the wiimote object. It's called every time that IR data
	# is available. It is necessary to do it this way because the callback
	# has to be aware of the cursor object.
	def makeCallback(self):
		def callback(q):
			self.mutex.lock()
			if self.checkLimits(q):
				if not self.filt:
					self.filt = Filter()
				p = self.filt.update(q)
				
				self.move(p)
				
				if not self.click:
					self.click = Click(self)
				else:
					self.click.update(True)
			self.mutex.unlock()
		
		return callback
	
	
	# This function creates the cursor thread. It makes the callback to the
	# thread and enables the wiimote device
	def runThread(self):
		def runFunc():
			while 1:
				qt.QThread.usleep(100)
				self.mutex.lock()
				if self.click and not self.click.update(False):
					self.click = None
					self.filt = None
					self.clickType = FakeCursor.LEFT_BUTTON
				if self.mustFinish:
					self.mutex.unlock()
					break
				self.mutex.unlock()
		
		from threads import CreateThreadClass
		
		self.mustFinish = False
		self.wii.setCallback(self.makeCallback())
		self.wii.enable()
		thread = CreateThreadClass(runFunc)
		self.thread = thread()
		self.thread.start()
	
	
	# Destroys the cursor thread and disables the wiimote device
	def finish(self):
		self.mutex.lock()
		self.mustFinish = True
		self.mutex.unlock()
		self.thread.wait()
		self.wii.disable()
		self.thread = None
		


