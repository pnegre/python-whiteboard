# -*- coding: utf-8 -*-

import Xlib.display
import Xlib.ext.xtest

class FakeCursor:
	def __init__(self):
		self.display = Xlib.display.Display()
		self.screen = self.display.screen()
		self.root = self.screen.root
	
	def move(self,pos):
		self.root.warp_pointer(pos[0],pos[1])
		self.display.sync()
		#Xlib.ext.xtest.fake_input(self.display, Xlib.X.
	
	#button= 1 left, 2 middle, 3 right
	def mouse_down(self,button):
		Xlib.ext.xtest.fake_input(self.display, Xlib.X.ButtonPress, button)
		self.display.sync()
	
	def mouse_up(self,button):
		Xlib.ext.xtest.fake_input(self.display, Xlib.X.ButtonRelease, button)
		self.display.sync()