#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys, re

import PyQt5.Qt as qt

from numpy import matrix, linalg
import bluetooth

import linuxWiimoteLib as wiLib
from configuration import Configuration
from threads import CreateThreadClass
import threading



def calculateArea(points):
    print(points)
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
    print(paral_A_area)
    print(paral_B_area)
    return result






class Wiimote:
    CALIBRATED, NONCALIBRATED = range(2)
    MAX_X = 1023
    MAX_Y = 768
    
    def __init__(self):
        self.wii = None
        self.error = False
        self.pos = None
        self.state = Wiimote.NONCALIBRATED
        self.calibrationPoints = []
        self.screenPoints = []
        self.utilization = 0.0
        self.funcIR = None
        self.funcBTN = None
        self.enableCallback = False
        self.lock = threading.Lock()
    
    
    def create_wiimote_callback(self):
        # Closure
        def wiimote_callback(px,py):
            self.lock.acquire()
            if self.enableCallback and self.funcIR is not None:
                self.lock.release()
                self.funcIR(self.getPos([px,py]))
            else:
                self.lock.release()
        
        return wiimote_callback
    
    
    def putCallbackIR(self,funcIR):
        self.funcIR = funcIR
    
    def putCallbackBTN(self,funcBTN):
        self.funcBTN = funcBTN
    
    
    def detectWiimotes(self):
        try:
            self.wiimotesDetected = []
            devices = bluetooth.discover_devices(duration=10, lookup_names=True)
            for device in devices:
                if re.match('.*nintendo.*', device[1].lower()):
                    self.wiimotesDetected.append(device)
            return
        
        except bluetooth.BluetoothError as errString:
            self.wii = None
            self.error = True
            return
    
    
    def bind(self, device):
        try:
            self.addr = str(device[0])
            self.wii = wiLib.Wiimote()
            self.wii.Connect(device)
            self.wii.SetRumble(True)
            qt.QThread.msleep(200)
            self.wii.SetRumble(False)
            self.wii.setIRCallBack(self.create_wiimote_callback())
            self.wii.activate_IR(int(Configuration().getValueStr("sensitivity")))
            self.wii.SetLEDs(True, False, False, False)
            self.error = False
            return
            
        except RuntimeError as errString:
            self.wii = None
            return
        
        except:
            self.wii = None
            self.error = True
            print("Unexpected error:", sys.exc_info()[0])
            raise
    
    def isConnected(self):
        if self.wii: return True
        return False
    
    def enable(self):
        self.lock.acquire()
        self.error = False
        self.wii.setIRSensitivity(int(Configuration().getValueStr("sensitivity")))
        self.enableCallback = True
        self.lock.release()
    
    def disable(self):
        self.lock.acquire()
        self.enableCallback = False
        self.lock.release()
    
    def close(self):
        self.disable()
        self.wii.Disconnect()
        self.wii = None
    
    def checkStatus(self):
        return True
        #if self.wii == None or self.error == True: return False
        #try:
            #self.wii.request_status()
            #return True
        #except:
            #return False
    
    def battery(self):
        return self.wii.WiimoteState.Battery 
    
    def getPos(self,p):
        if self.state == Wiimote.NONCALIBRATED:
            return p
        if self.state == Wiimote.CALIBRATED:
            return [
                (self.h11*p[0] + self.h12*p[1] + self.h13) / \
                (self.h31*p[0] + self.h32*p[1] + 1),
                (self.h21*p[0] + self.h22*p[1] + self.h23) / \
                (self.h31*p[0] + self.h32*p[1] + 1) ]
    
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
        self.h11 = self.hCoefs[0]
        self.h12 = self.hCoefs[1]
        self.h13 = self.hCoefs[2]
        self.h21 = self.hCoefs[3]
        self.h22 = self.hCoefs[4]
        self.h23 = self.hCoefs[5]
        self.h31 = self.hCoefs[6]
        self.h32 = self.hCoefs[7]
        
        self.calibrationPoints = list(p_wii)
        self.screenPoints = list(p_screen)
        self.state = Wiimote.CALIBRATED
        
        area_inside = calculateArea(self.calibrationPoints)
        total_area = Wiimote.MAX_X * Wiimote.MAX_Y
        self.utilization = float(area_inside)/float(total_area)
    
    
    def createConnectThread(self, selectedmac, pool):
        def func():         
            if selectedmac == '*':
                self.detectWiimotes()
                if len(self.wiimotesDetected) == 0:
                    return
                
                for p in self.wiimotesDetected:
                    if not p[0] in pool:
                        pool.append(p[0])
                
            else:
                mac = str(selectedmac)
                name = bluetooth.lookup_name(mac)
                self.bind([mac,name])
        
        thread = CreateThreadClass(func)
        return thread() 



