# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt

from cursor import FakeCursor


CONFIG_VERSION = 2


class Configuration:

	class __impl:
		""" Implementation of the singleton interface """
		
		def __init__(self):
			self.settings = QtCore.QSettings("pywhiteboard","pywhiteboard")
			
			self.defaults = {
				"fullscreen": "Yes",
				"selectedmac": "All Devices",
				"delayloop": "10",
				"zone1": "Left Click",
				"zone2": "Left Click",
				"zone3": "Left Click",
				"zone4": "Left Click",
				"autoconnect": "No",
				"autoactivate": "No",
			}
			
			version = self.getValueStr("version")
			if version == '' or int(version) < CONFIG_VERSION:
				self.settings.clear()
				self.saveValue("version",str(CONFIG_VERSION))
			
		
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
		if conf.getValueStr("autoconnect") == "Yes":
			self.ui.check_autoconnect.setChecked(True)
		if conf.getValueStr("autoactivate") == "Yes":
			self.ui.check_autoactivate.setChecked(True)
		
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
		
		pixmap = QtGui.QPixmap("screen.png")
		self.areasScene = QtGui.QGraphicsScene()
		self.areasScene.addPixmap(pixmap)
		self.screenAreas.setScene(self.areasScene)
		self.screenAreas.show()
		
		self.connect(self.ui.combo1,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo1)
		self.connect(self.ui.combo2,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo2)
		self.connect(self.ui.combo3,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo3)
		self.connect(self.ui.combo4,
			QtCore.SIGNAL("currentIndexChanged(const QString)"), self.changeCombo4)
		self.updateCombos()
	
	
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
		
		if self.ui.check_autoconnect.isChecked():
			conf.saveValue("autoconnect","Yes")
		else:
			conf.saveValue("autoconnect","No")
		
		if self.ui.check_autoactivate.isChecked():
			conf.saveValue("autoactivate","Yes")
		else:
			conf.saveValue("autoactivate","No")
		
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
	
	
	def updateCombos(self):
		conf = Configuration()
		for combo,zone in [(self.ui.combo1,"zone1"), (self.ui.combo2,"zone2"), (self.ui.combo3,"zone3"), (self.ui.combo4,"zone4")]:
			text = conf.getValueStr(zone)
			ind = combo.findText(text,QtCore.Qt.MatchContains)
			combo.setCurrentIndex(ind)


	def changeCombo1(self,text):
		conf = Configuration()
		conf.saveValue("zone1",text)
	
	def changeCombo2(self,text):
		conf = Configuration()
		conf.saveValue("zone2",text)
	
	def changeCombo3(self,text):
		conf = Configuration()
		conf.saveValue("zone3",text)
	
	def changeCombo4(self,text):
		conf = Configuration()
		conf.saveValue("zone4",text)
	
	
	
	def closeEvent(self,e):
		e.accept()



