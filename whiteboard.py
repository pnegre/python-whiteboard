#!/usr/bin/python
# -*- coding: utf-8 -*-

from wiimote import Wiimote
from calibration import Calibration
from cursor import FakeCursor

wii = Wiimote()
wii.bind()
calibration = Calibration()
calibration.doIt(wii)
curs = FakeCursor(wii)
while(1):
	wii.getMsgs()
	curs.update()