# -*- coding: utf-8 -*-

import Xlib.display
import Xlib.ext.xtest
import time

def clock():
	return int(time.time()*1000)


class Filter:
	def __init__(self):
		self.data = []
	
	def update(self,p):
		self.data.append(p)
		if len(self.data)>5:
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
	def __init__(self,cursor):
		self.initialTime = clock()
		self.cursor = cursor
		self.cursor.mouse_down()
		
	
	def update(self,evt):
		t = clock()
		if evt:
			self.initialTime = clock()
			return True
		elif (t-self.initialTime)>100:
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
		self.root = self.screen.root
		self.wii = wii
		self.click = None
		self.filt = None
		self.clickType = FakeCursor.LEFT_BUTTON
		self.zones = {}
	
	
	def setZone(self,zone,clickType):
		self.zones[zone] = clickType
	
	
	def move(self,pos):
		#self.root.warp_pointer(pos[0],pos[1])
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
	
	
	def update(self):
		if self.wii.pos:
			q = self.wii.getPos()
			if self.checkLimits(q):
				if not self.filt:
					self.filt = Filter()
				p = self.filt.update(q)
				
				self.move(p)
				
				if not self.click:
						self.click = Click(self)
				else:
					self.click.update(True)
		
		elif self.click and not self.click.update(False):
			self.click = None
			self.filt = None
			self.clickType = FakeCursor.LEFT_BUTTON
	
	
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


