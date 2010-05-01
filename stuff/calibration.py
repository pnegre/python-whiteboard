#!/usr/bin/python
# -*- coding: utf-8 -*-

import pygame, os
import time
import wiimote

PI = 3.1416


def clock():
	return int(time.time()*1000)


class SandClock:
	READY, FIN1, FIN2 = range(3)
	
	def __init__(self,px,py):
		self.point = [0,0]
		self.px = px-20
		self.py = py-20
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
	
	def draw(self,screen,sms):
		if self.totalTicks:
			dgrs = 360*self.totalTicks/700
			pygame.draw.arc(screen, (255,0,0),
				pygame.Rect(self.px,self.py,40,40), 0, dgrs*3.14/180, 8)
			sms.drawPoint(self.point)

	
	def finished(self):
		return self.state == SandClock.FIN2
	
	def getPoint(self):
		return self.point



class SmallScreen:
	def __init__(self,screen):
		self.surface = screen
		self.parentx = screen.get_width();
		self.parenty = screen.get_height();
		self.dx = 200
		self.dy = 200
	
	def draw(self):
		pygame.draw.rect(self.surface, (255,255,255), 
			pygame.Rect(int(self.parentx/2-100), int(self.parenty/2-100),
			200, 200), 1)
	
	def drawPoint(self,pos):
		px = self.parentx/2 - 100 + pos[0]*self.dx/wiimote.Wiimote.MAX_X;
		py = self.parenty/2 + 100 - pos[1]*self.dy/wiimote.Wiimote.MAX_Y;
		pygame.draw.circle(self.surface, (255,255,255), (px,py), 2)
		


class Calibration:
	def __init__(self):
		pass
	
	def drawCross(self,pos):
		pygame.draw.line(self.screen, (255,255,255), (pos[0]-5,pos[1]), (pos[0]+5,pos[1]))
		pygame.draw.line(self.screen, (255,255,255), (pos[0],pos[1]-5), (pos[0],pos[1]+5)) 
	
	def drawBox(self, pos, filled=False):
		w = 1
		if filled: w = 0
			
		pygame.draw.rect(self.screen, (255,255,255), 
			pygame.Rect(pos[0]-5, pos[1]-5, 11, 11), w)
			
	
	def doIt(self,wii):
		os.environ["SDL_VIDEO_CENTERED"] = "1"
		pygame.init()
		self.window = pygame.display.set_mode( (0,0), pygame.FULLSCREEN | pygame.DOUBLEBUF )
		self.screen = pygame.display.get_surface()
		self.clock = pygame.time.Clock()

		smallScreen = SmallScreen(self.screen)
		
		p_wii = [(0,0), (0,0), (0,0), (0,0)]
		p_screen = (
			(20,20),
			(self.screen.get_width()-20, 20),
			(self.screen.get_width()-20, self.screen.get_height()-20),
			(20, self.screen.get_height()-20),
		)
		sandClock = SandClock(self.screen.get_width()/2, self.screen.get_height()/2)
		state = 0
		finish = False
		while not finish:
			for e in pygame.event.get():
				if e.type == pygame.KEYDOWN:
					if e.key == pygame.K_ESCAPE:
						finish = True
					if e.key == pygame.K_SPACE:
						state += 1
			
			if (state >= 4):
				break
			
			self.screen.fill((0,0,0))
			smallScreen.draw()
			sandClock.draw(self.screen,smallScreen)
			
			wii.getMsgs()
			wii_pos = wii.getPos()
			if wii_pos:
				#smallScreen.drawPoint(wii_pos)
				sandClock.update(wii_pos)
			else:
				sandClock.update(None)
			
			if sandClock.finished():
				p_wii[state] = sandClock.getPoint()
				state += 1
				sandClock.initialize()
				if (state >= 4):
					break
			
			for n,p in enumerate(p_screen):
				self.drawCross(p)
				if n<state:
					self.drawBox(p_screen[n], filled=True)
			
			self.drawBox(p_screen[state])
			
			pygame.display.flip()
		
		pygame.quit()
		
		# Do calibration
		if state >= 4:
			wii.calibrate(p_screen,p_wii)
		
		


