# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt


class Configuration:

	class __impl:
		""" Implementation of the singleton interface """
		
		def __init__(self):
			self.settings = QtCore.QSettings("pywhiteboard","pywhiteboard")
			self.defaults = {
				"fullscreen": "Yes",
				"selectedmac": "All Devices",
				"delayloop": "10",
			}
		
		def saveValue(self,name,value):
			self.settings.setValue(name,QtCore.QVariant(value))

		
		def getValueStr(self,name):
			v = self.settings.value(name).toString()
			if v != '': return v
			if v == '' and name in self.defaults.keys():
				return self.defaults[name]
			else: return ''
		
		
		def writeArray(self,name,lst):
			self.settings.beginWriteArray(name)
			for i,mac in enumerate(lst):
				self.settings.setArrayIndex(i)
				self.settings.setValue("item",mac)
			self.settings.endArray()
		
		
		def readArray(self,name):
			n = self.settings.beginReadArray(name)
			result = []
			for i in range(0,n):
				self.settings.setArrayIndex(i)
				result.append(self.settings.value("item").toString())
			self.settings.endArray()
			return result



	# storage for the instance reference
	__instance = None

	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if Configuration.__instance is None:
			# Create and remember instance
			Configuration.__instance = Configuration.__impl()

		# Store instance reference as the only member in the handle
		self.__dict__['_Configuration__instance'] = Configuration.__instance

	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)



class ConfigDialog(QtGui.QDialog):

	def __init__(self, parent, wii=None):
		QtGui.QWidget.__init__(self,parent)
		self.ui = uic.loadUi("configuration.ui",self)
		
		self.wii = wii
		
		conf = Configuration()
		if conf.getValueStr("fullscreen") == "Yes":
			self.ui.check_fullscreen.setChecked(True)
		
		self.ui.slider_delayloop.setMinimum(5)
		self.ui.slider_delayloop.setMaximum(50)
		self.connect(self.ui.slider_delayloop,
			QtCore.SIGNAL("valueChanged(int)"), self.sliderMoved)
		delayloop = int(conf.getValueStr("delayloop"))
		self.ui.slider_delayloop.setValue(delayloop)
		
		
		self.connect(self.ui.button_OK,
			QtCore.SIGNAL("clicked()"), self.finish)
		
		self.connect(self.ui.button_addDev,
			QtCore.SIGNAL("clicked()"), self.addDevice)
		self.connect(self.ui.button_remDev,
			QtCore.SIGNAL("clicked()"), self.removeDevice)
		
		item = QtGui.QListWidgetItem("All Devices")
		self.ui.macListWidget.addItem(item)
		self.ui.macListWidget.setItemSelected(item,True)
		selectedmac = conf.getValueStr("selectedmac")
		
		macs = conf.readArray("macs")
		for m in macs:
			item = QtGui.QListWidgetItem(m)
			self.ui.macListWidget.addItem(item)
			if m == selectedmac:
				self.ui.macListWidget.setItemSelected(item,True)
		
		
		if self.wii == None:
			self.ui.button_addDev.setEnabled(False)
	
	
	def sliderMoved(self,newVal):
		self.ui.label_delayloop.setText(str(newVal))
	
	def addDevice(self):
		if self.wii == None: return
		
		address = self.wii.addr
		f = self.ui.macListWidget.findItems(address, QtCore.Qt.MatchContains)
		if len(f) != 0:
			return
		
		item = QtGui.QListWidgetItem(address)
		self.ui.macListWidget.addItem(item)
	
	
	def removeDevice(self):
		slist = self.ui.macListWidget.selectedItems()
		for item in slist:
			row = self.ui.macListWidget.row(item)
			if row != 0:
				self.ui.macListWidget.takeItem(row)
		
		
	def finish(self):
		conf = Configuration()
		
		if self.ui.check_fullscreen.isChecked():
			conf.saveValue("fullscreen","Yes")
		else:
			conf.saveValue("fullscreen","No")
		
		mlist = []
		for i in range(0,self.ui.macListWidget.count()):
			item = self.ui.macListWidget.item(i)
			t = item.text()
			if t != "All Devices":
				mlist.append(t)
		
		conf.writeArray("macs",mlist)
		
		slist = self.ui.macListWidget.selectedItems()
		for item in slist:
			mac = item.text()
			conf.saveValue("selectedmac",mac)
			break
		
		delayloop = self.ui.slider_delayloop.value()
		conf.saveValue("delayloop",str(delayloop))
		
		self.close()
	
	
	
	def closeEvent(self,e):
		e.accept()



