#!/usr/bin/python
# -*- coding: utf-8 -*-

from numpy import matrix, linalg
import cwiid

class Wiimote:
	CALIBRATED, NONCALIBRATED = range(2)
	
	def __init__(self):
		self.wii = None
		self.pos = None
		self.state = Wiimote.NONCALIBRATED
	
	def bind(self):
		self.wii = cwiid.Wiimote()
		self.wii.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_IR
		self.wii.led = cwiid.LED1_ON
		self.wii.enable(cwiid.FLAG_MESG_IFC)
		self.wii.disable(cwiid.FLAG_NONBLOCK)
		self.wii.disable(cwiid.FLAG_CONTINUOUS)
	
	def close(self):
		self.wii.close()
	
	def getMsgs(self):
		msgs = self.wii.get_mesg()
		for m in msgs:
			if m:
				if m[0] == cwiid.MESG_IR:
					data = m[1][0]
					if data:
						self.pos = list(data['pos'])
	
	def getPos(self):
		if self.pos == None: return None
		p = list(self.pos)
		self.pos = None
		if self.state == Wiimote.NONCALIBRATED:
			return p
		if self.state == Wiimote.CALIBRATED:
			#DO STUFF
			return p
	
	def calibrate(p_screen, p_wii):
		l = []
		for i in range(0,4):
			l.append( [p_wii[i][0], p_wii[i][1], 1, 0, 0, 0, 
				(-p_screen[i][0] * p_wii[i][0]), 
				(-p_screen[i][0] * p_wii[i][1])] )
			l.append( [0, 0, 0, p_wii[i][0], p_wii[i][1], 1, 
				(-p_screen[i][1] * p_wii[i][0]), 
				(-p_screen[i][1] * p_wii[i][1])] )

		A = matrix(l)

		x = matrix( [
			[p_screen[0][0]],
			[p_screen[0][1]],
			[p_screen[1][0]],
			[p_screen[1][1]],
			[p_screen[2][0]],
			[p_screen[2][1]],
			[p_screen[3][0]],
			[p_screen[3][1]],
		])

		self.hCoefs = linalg.solve(A, x)
		self.state = CALIBRATED



