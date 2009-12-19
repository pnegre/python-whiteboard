#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from calibration import Calibration
from cursor import FakeCursor

wii = Wiimote()
wii.bind()
calibration = Calibration()
calibration.doIt(wii)
curs = FakeCursor()
while(1):
	wii.getMsgs()
	p = wii.getPos()
	if p:
		print p
		curs.move(p)