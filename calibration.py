#!/usr/bin/python
# -*- coding: utf-8 -*-

#from wiimote import Wiimote
import pygame, os

SCR_WIDTH = 640
SCR_HEIGHT = 480


class SmallScreen():
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
		px = self.parentx/2 - 100 + pos[0]*self.dx/1024;
		py = self.parenty/2 + 100 - pos[1]*self.dy/768;
		pygame.draw.circle(self.surface, (255,255,255), (px,py), 2)
		


class Calibration:
	def __init__(self):
		pass
	
	def drawCross(self,pos):
		pygame.draw.line(self.screen, (255,255,255), (pos[0]-5,pos[1]), (pos[0]+5,pos[1]))
		pygame.draw.line(self.screen, (255,255,255), (pos[0],pos[1]-5), (pos[0],pos[1]+5)) 
		
	
	def doIt(self,wii):
		os.environ["SDL_VIDEO_CENTERED"] = "1"
		pygame.init()
		self.window = pygame.display.set_mode( (SCR_WIDTH, SCR_HEIGHT) )
		self.screen = pygame.display.get_surface()
		self.clock = pygame.time.Clock()

		smallScreen = SmallScreen(self.screen)
		
		p_wii = ((0,0), (0,0), (0,0), (0,0))
		p_screen = (
			(20,20),
			(self.screen.get_width()-20, 20),
			(self.screen.get_width()-20, self.screen.get_height()-20),
			(20, self.screen.get_height()-20),
		)
		
		while 1:
			k = pygame.key.get_pressed()
			if (k[pygame.K_RETURN]):
				break
			
			self.screen.fill((0,0,0))
			smallScreen.draw()
			
			wii.getMsgs()
			if wii.pos:
				print wii.pos
				smallScreen.drawPoint(wii.pos)
				wii.pos = None
			
			for p in p_screen:
				self.drawCross(p)
			
			pygame.display.flip()
		
		# Do calibration
		wii.calibrate(p_screen,p_wii)


