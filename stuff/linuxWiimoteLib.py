# LICENSE:         MIT (X11) License which follows:
#
# Copyright (c) 2008 Stephane Duchesneau
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Modified by Pere Negre and Pietro Pilolli
#

import threading
import time
import bluetooth

def old_div(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a // b
    else:
        return a / b

def i2bs(val):
	lst = []
	while val:
		lst.append(val&0xff)
		val = val >> 8
	lst.reverse()
	return lst

class WiimoteState(object):
    Battery = None
    
    class ButtonState(object):
        A = False
        B = False
        Down = False
        Home = False
        Left = False
        Minus = False
        One = False
        Plus = False
        Right = False
        Two = False
        Up = False

    class IRState(object):
        RawX1 = 0
        RawX2 = 0
        RawX3 = 0
        RawX4 = 0
        
        RawY1 = 0
        RawY2 = 0
        RawY3 = 0
        RawY4 = 0
        
        Found1 = 0
        Found2 = 0
        Found3 = 0
        Found4 = 0
        
        Size1 = 0
        Size2 = 0
        Size3 = 0
        Size4 = 0
        
        X1 = X2 = X3 = X4 = 0.0
        Y1 = Y2 = Y3 = Y4 = 0.0
        
        #Mode = None
        MidX = 0
        MidY = 0
        RawMidX = 0
        RawMidY = 0 

    class LEDState(object):
        LED1 = False
        LED2 = False
        LED3 = False
        LED4 = False
	
class Parser(object):
	""" Sets the values contained in a signal """
	A = 0x0008
	B = 0x0004
	Down = 0x0400
	Home = 0x0080
	Left = 0x0100
	Minus = 0x0010
	One = 0x0002
	Plus = 0x1000
	Right = 0x0200
	Two = 0x0001
	Up = 0x0800
	
	def parseButtons(self,signal, ButtonState): #signal is 16bit long intl
		ButtonState.A = bool(signal&self.A)
		ButtonState.B = bool(signal&self.B)
		ButtonState.Down = bool(signal&self.Down)
		ButtonState.Home = bool(signal&self.Home)
		ButtonState.Left = bool(signal&self.Left)
		ButtonState.Minus = bool(signal&self.Minus)
		ButtonState.One = bool(signal&self.One)
		ButtonState.Plus = bool(signal&self.Plus)
		ButtonState.Right = bool(signal&self.Right)
		ButtonState.Two = bool(signal&self.Two)
		ButtonState.Up = bool(signal&self.Up)
	
	def parseIR(self,signal,irstate):
		irstate.RawX1 = signal[0] + ((signal[2] & 0x30) >>4 << 8)
		irstate.RawY1 = signal[1] + (signal[2] >> 6 << 8)
		irstate.Size1 = signal[2] & 0x0f
		if irstate.RawY1 == 1023: irstate.Found1 = False
		else: irstate.Found1 = True
		
		irstate.RawX2 = signal[3] + ((signal[5] & 0x30) >>4 << 8)
		irstate.RawY2 = signal[4] + (signal[5] >> 6 << 8)
		irstate.Size2 = signal[5] & 0x0f
		if irstate.RawY2 == 1023: irstate.Found2 = False
		else: irstate.Found2 = True
		
		irstate.RawX3 = signal[6] + ((signal[8] & 0x30) >>4 << 8)
		irstate.RawY3 = signal[7] + (signal[8] >> 6 << 8)
		irstate.Size3 = signal[8] & 0x0f
		if irstate.RawY3 == 1023: irstate.Found3 = False
		else: irstate.Found3 = True
		
		irstate.RawX4 = signal[9] + ((signal[11] & 0x30) >>4 << 8)
		irstate.RawY4 = signal[10] + (signal[11] >> 6 << 8)
		irstate.Size4 = signal[11] & 0x0f
		if irstate.RawY4 == 1023: irstate.Found4 = False
		else: irstate.Found4 = True
		
		if irstate.Found1:
			if irstate.Found2: 
				irstate.RawMidX = old_div((irstate.RawX1 + irstate.RawX2), 2)
				irstate.RawMidY = old_div((irstate.RawY1 + irstate.RawY2), 2)
			else:
				irstate.RawMidX = irstate.RawX1
				irstate.RawMidY = irstate.RawY1
			irstate.MidX = old_div(float(irstate.RawMidX), 1024)
			irstate.MidY = old_div(float(irstate.RawMidY), 768)
		else: irstate.MidX = irstate.MidY = 0
		

class Setter(object): 
	"""The opposite from the Parser class: returns the signal needed to set the values in the wiimote"""
	LED1 = 0x10
	LED2 = 0x20
	LED3 = 0x40
	LED4 = 0x80
	
	def SetLEDs(self,ledstate):
		signal = 0
		if ledstate.LED1: signal += self.LED1
		if ledstate.LED2: signal += self.LED2
		if ledstate.LED3: signal += self.LED3
		if ledstate.LED4: signal += self.LED4
		return signal
				
		
class InputReport(object):
    Buttons = 2 #2 to 8 not implemented yet !!! only IR is implemented
    Status = 4
    ReadData = 5
    ButtonsExtension = 6
    
class Wiimote(threading.Thread):
	state = None
	running = False
	WiimoteState = WiimoteState
	InputReport = InputReport
	

	def __init__(self):
		threading.Thread.__init__(self)
		self.parser = Parser()
		self.setter = Setter()
		self.IRCallback = None
		
	def Connect(self, device):
		self.bd_addr = device[0]
		self.name = device[1]
		self.controlsocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
		self.controlsocket.connect((self.bd_addr,17))
		self.datasocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
		self.datasocket.connect((self.bd_addr,19))
		self.sendsocket = self.controlsocket
		self.CMD_SET_REPORT = 0x52
		
		if self.name == "Nintendo RVL-CNT-01-TR":
			self.CMD_SET_REPORT = 0xa2 
			self.sendsocket = self.datasocket
		
		try:
			self.datasocket.settimeout(1)
		except NotImplementedError:
			print("socket timeout not implemented with this bluetooth module")
		
		print("Connected to ", self.bd_addr)
		self._get_battery_status()
		self.start() #start this thread
		return True
		
	def char_to_binary_string(self,ascii):
		bin = []

		while (ascii > 0):
			if (ascii & 1) == 1:
				bin.append("1")
			else:
				bin.append("0")
			ascii = ascii >> 1

		bin.reverse()
		binary = "".join(bin)
		zerofix = (8 - len(binary)) * '0'

		return zerofix + binary
	
	def SetLEDs(self, led1,led2,led3,led4):
		self.WiimoteState.LEDState.LED1 = led1
		self.WiimoteState.LEDState.LED2 = led2
		self.WiimoteState.LEDState.LED3 = led3
		self.WiimoteState.LEDState.LED4 = led4
		
		self._send_data((0x11,self.setter.SetLEDs(self.WiimoteState.LEDState)))


	def run(self):
		print("starting")
		self.running = True
		while self.running:
			try:
				x= bytearray(self.datasocket.recv(32))
			except bluetooth.BluetoothError:
				continue
			self.state = ""
			for each in x[:17]:
				self.state += self.char_to_binary_string(each) + " "
			if len(x) >= 4:
				self.parser.parseButtons((x[2]<<8) + x[3], self.WiimoteState.ButtonState)
			if len(x) >= 19: 
				self.parser.parseIR(x[7:19],self.WiimoteState.IRState)
				self.doIRCallback()
			
		self.datasocket.close()
		self.controlsocket.close()
		print("Bluetooth socket closed succesfully.")
		self.Dispose()
		print("stopping")
	
	def Dispose(self):
		self.Disconnect()
		
	def Disconnect(self):
		self.running = False
		self.WiimoteState.Battery = None
		
	def join(self):#will be called last...
		self.Dispose()
		
	def _send_data(self,data):
		bin_data = bytearray()
		bin_data.append(self.CMD_SET_REPORT)
		for each in data:
			bin_data.append(each)
		self.sendsocket.send(bytes(bin_data))
	
	def _write_to_mem(self, address, value):
		val = i2bs(value)
		val_len=len(val)
		val += [0]*(16-val_len)
		msg = [0x16] + i2bs(address) + [val_len] +val
		self._send_data(msg)
	
	def SetRumble(self,on):
		if on: self._send_data((0x11,0x01)) 
		else: self._send_data((0x11,0x00)) 
	
	def activate_IR(self, sens=6):
		self._send_data(i2bs(0x120033)) #mode IR
		self._send_data(i2bs(0x1304))#enable transmission
		self._send_data(i2bs(0x1a04))#enable transmission
		
		self.setIRSensitivity(sens)
	
	def setIRSensitivity(self, n):
		if n < 1 or n > 6:
			return
		
		self._write_to_mem(0x04b00030,0x08)
		time.sleep(0.1)
		
		if n == 1:
			self._write_to_mem(0x04b00000,0x0200007101006400fe)
			time.sleep(0.1)
			self._write_to_mem(0x04b0001a,0xfd05)
		elif n == 2:
			self._write_to_mem(0x04b00000,0x0200007101009600b4)
			time.sleep(0.1)
			self._write_to_mem(0x04b0001a,0xb304)
		elif n == 3:
			self._write_to_mem(0x04b00000,0x020000710100aa0064)
			time.sleep(0.1)
			self._write_to_mem(0x04b0001a,0x6303)
		elif n == 4:
			self._write_to_mem(0x04b00000,0x020000710100c80036)
			time.sleep(0.1)
			self._write_to_mem(0x04b0001a,0x3503)
		elif n == 5:
			self._write_to_mem(0x04b00000,0x070000710100720020)
			time.sleep(0.1)
			self._write_to_mem(0x04b0001a,0x1f03)
		# MAX
		elif n == 6:
			self._write_to_mem(0x04b00000,0x000000000000900041)
			time.sleep(0.1)
			self._write_to_mem(0x04b0001a,0x4000)
		
		time.sleep(0.1)
		self._write_to_mem(0x04b00033,0x33)
	
	def _get_battery_status(self):
		self._send_data((0x15,0x00))
		self.running2 = True
		while self.running2:
			try:
				x = bytearray(self.datasocket.recv(32))
			except bluetooth.BluetoothError:
				continue
			self.state = ""
			if len(x) >= 7:
				self.running2 = False
				battery_level = float(x[7])
		self.WiimoteState.Battery = battery_level / 208.
	
	
	def setIRCallBack(self, func):
		self.IRCallback = func
	
	def doIRCallback(self):
		if self.IRCallback == None: return
		irstate = self.WiimoteState.IRState
		
		if irstate.Found1:
			self.IRCallback(irstate.RawX1, irstate.RawY1)
		elif irstate.Found2:
			self.IRCallback(irstate.RawX2, irstate.RawY2)
		elif irstate.Found3:
			self.IRCallback(irstate.RawX3, irstate.RawY3)
		elif irstate.Found4:
			self.IRCallback(irstate.RawX4, irstate.RawY4)


if __name__ == "__main__":
	wiimote = Wiimote()
	print("Press 1 and 2 on wiimote (or SYNC on wiimote plus) to make it discoverable")
	wiimote.Connect()
	wiimote.activate_IR()
	while 1:
		time.sleep(0.1)
		#print wiimote.state
		print(wiimote.WiimoteState.ButtonState.A, wiimote.WiimoteState.ButtonState.B, wiimote.WiimoteState.ButtonState.Up, wiimote.WiimoteState.ButtonState.Down, wiimote.WiimoteState.ButtonState.Left, wiimote.WiimoteState.ButtonState.Right, wiimote.WiimoteState.ButtonState.Minus, wiimote.WiimoteState.ButtonState.Plus, wiimote.WiimoteState.ButtonState.Home, wiimote.WiimoteState.ButtonState.One, wiimote.WiimoteState.ButtonState.Two, wiimote.WiimoteState.IRState.RawX1, wiimote.WiimoteState.IRState.RawY1, wiimote.WiimoteState.IRState.Size1, wiimote.WiimoteState.IRState.RawX2, wiimote.WiimoteState.IRState.RawY2, wiimote.WiimoteState.IRState.Size2)
		#print wiimote.IRState.Found1	


