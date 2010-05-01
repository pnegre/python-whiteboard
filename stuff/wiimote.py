#!/usr/bin/python
# -*- coding: utf-8 -*-

from numpy import matrix, linalg
import cwiid



def calculateArea(points):
	print points
	p1 = points[0]
	p2 = points[1]
	p3 = points[2]
	p4 = points[3]

	vb = [p2[0]-p1[0], p2[1]-p1[1]]
	va = [p4[0]-p1[0], p4[1]-p1[1]]

	paral_A_area = va[0]*vb[1] - va[1]*vb[0]

	va = [p2[0]-p3[0], p2[1]-p3[1]]
	vb = [p4[0]-p3[0], p4[1]-p3[1]]

	paral_B_area = va[0]*vb[1] - va[1]*vb[0]

	result = float(paral_A_area)/2 + float(paral_B_area)/2
	print paral_A_area
	print paral_B_area
	return result




class Wiimote:
	CALIBRATED, NONCALIBRATED = range(2)
	MAX_X = 1024
	MAX_Y = 768
	
	def __init__(self):
		self.wii = None
		self.pos = None
		self.state = Wiimote.NONCALIBRATED
		self.calibrationPoints = []
		self.utilization = 0.0
	
	def bind(self):
		try:
			self.wii = cwiid.Wiimote()
			self.wii.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_IR
			self.wii.led = cwiid.LED1_ON
			self.wii.enable(cwiid.FLAG_MESG_IFC)
			self.wii.enable(cwiid.FLAG_NONBLOCK)
			self.wii.enable(cwiid.FLAG_CONTINUOUS)
			return True
		except:
			return False
	
	def close(self):
		self.wii.close()
	
	def battery(self):
		return float(self.wii.state['battery']) / float(cwiid.BATTERY_MAX)
	
	def getMsgs(self):
		msgs = self.wii.get_mesg()
		if msgs:
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
			pp = [0,0]
			pp[0] = (self.h11*p[0] + self.h12*p[1] + self.h13) / \
				(self.h31*p[0] + self.h32*p[1] + 1)
			pp[1] = (self.h21*p[0] + self.h22*p[1] + self.h23) / \
				(self.h31*p[0] + self.h32*p[1] + 1)
			return pp
	
	def calibrate(self, p_screen, p_wii):
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
		print self.hCoefs
		self.h11 = self.hCoefs[0]
		self.h12 = self.hCoefs[1]
		self.h13 = self.hCoefs[2]
		self.h21 = self.hCoefs[3]
		self.h22 = self.hCoefs[4]
		self.h23 = self.hCoefs[5]
		self.h31 = self.hCoefs[6]
		self.h32 = self.hCoefs[7]
		
		self.calibrationPoints = list(p_wii)
		self.state = Wiimote.CALIBRATED
		
		area_inside = calculateArea(self.calibrationPoints)
		total_area = Wiimote.MAX_X * Wiimote.MAX_Y
		self.utilization = float(area_inside)/float(total_area)
		print self.utilization



