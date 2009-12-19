#!/usr/bin/python
# -*- coding: utf-8 -*-

#from wiimote import Wiimote
import pygame, os


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
			
			wii.getMsgs()
			wii_pos = wii.getPos()
			if wii_pos:
				smallScreen.drawPoint(wii_pos)
				p_wii[state] = list(wii_pos)
			
			for n,p in enumerate(p_screen):
				self.drawCross(p)
				if n<state:
					self.drawBox(p_screen[n], filled=True)
			
			self.drawBox(p_screen[state])
			
			pygame.display.flip()
		
		# Do calibration
		wii.calibrate(p_screen,p_wii)
		pygame.quit()


