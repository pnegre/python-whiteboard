# -*- coding: utf-8 -*-

import PyQt4.Qt as qt


def initGlobals():
	global mutex
	mutex = qt.QMutex()
	global wii
	wii = None
	global mutexWiiRun
	mutexWiiRun = None
	global cursor
	cursor = None
	global threadWii
	threadWii = None