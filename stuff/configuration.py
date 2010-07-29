# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt


CONFIG_VERSION = 4


class Configuration:

	class __impl:
		""" Implementation of the singleton interface """
		
		def __init__(self):
			self.settings = QtCore.QSettings("pywhiteboard","pywhiteboard")
			
			self.defaults = {
				"fullscreen": "Yes",
				"selectedmac": '*',
				"zone1": "2",
				"zone2": "2",
				"zone3": "2",
				"zone4": "2",
				"autoconnect": "No",
				"autoactivate": "No",
				"autocalibration": "No",
				"sensitivity": "6",
			}
			
			version = self.getValueStr("version")
			if version == '' or int(version) < CONFIG_VERSION:
				self.settings.clear()
				self.saveValue("version",str(CONFIG_VERSION))
			
			self.activeGroup = None
			self.setGroup("default")
			
		
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
		
		
		def setGroup(self,name):
			if self.activeGroup:
				self.settings.endGroup(self.activeGroup)
			self.activeGroup = name
			self.settings.beginGroup(name)


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
		super(ConfigDialog, self).__init__(parent)
		self.ui = uic.loadUi("configuration.ui",self)
		
		self.wii = wii
		
		conf = Configuration()
		if conf.getValueStr("fullscreen") == "Yes":
			self.ui.check_fullscreen.setChecked(True)
		if conf.getValueStr("autoconnect") == "Yes":
			self.ui.check_autoconnect.setChecked(True)
		if conf.getValueStr("autoactivate") == "Yes":
			self.ui.check_autoactivate.setChecked(True)
		if conf.getValueStr("autocalibration") == "Yes":
			self.ui.check_autocalibration.setChecked(True)		
		
		self.connect(self.ui.button_OK,
			QtCore.SIGNAL("clicked()"), self.finish)
		
		self.connect(self.ui.button_addDev,
			QtCore.SIGNAL("clicked()"), self.addDevice)
		self.connect(self.ui.button_remDev,
			QtCore.SIGNAL("clicked()"), self.removeDevice)
		
		item = QtGui.QListWidgetItem(self.tr("All Devices"))
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
			QtCore.SIGNAL("currentIndexChanged(int)"), self.changeCombo)
		self.connect(self.ui.combo2,
			QtCore.SIGNAL("currentIndexChanged(int)"), self.changeCombo)
		self.connect(self.ui.combo3,
			QtCore.SIGNAL("currentIndexChanged(int)"), self.changeCombo)
		self.connect(self.ui.combo4,
			QtCore.SIGNAL("currentIndexChanged(int)"), self.changeCombo)
		self.updateCombos()
		
		self.ui.slider_ir.setMinimum(2)
		self.ui.slider_ir.setMaximum(6)
		self.connect(self.ui.slider_ir,
			QtCore.SIGNAL("valueChanged(int)"), self.sliderIrMoved)
		sens = int(conf.getValueStr("sensitivity"))
		self.ui.slider_ir.setValue(sens)
	
	
	def sliderIrMoved(self, val):
		conf = Configuration()
		conf.saveValue("sensitivity",str(val))
	
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
		
		if self.ui.check_autocalibration.isChecked():
			conf.saveValue("autocalibration","Yes")
		else:
			conf.saveValue("autocalibration","No")
		
		mlist = []
		for i in range(1,self.ui.macListWidget.count()):
			item = self.ui.macListWidget.item(i)
			t = item.text()
			mlist.append(t)
		
		conf.writeArray("macs",mlist)
		
		slist = self.ui.macListWidget.selectedItems()
		for item in slist:
			mac = item.text()
			if ':' in mac:
				conf.saveValue("selectedmac",mac)
			else:
				conf.saveValue("selectedmac",'*')
			break
		
		self.close()
	
	
	def updateCombos(self):
		conf = Configuration()
		for combo,zone in [(self.ui.combo1,"zone1"), (self.ui.combo2,"zone2"), (self.ui.combo3,"zone3"), (self.ui.combo4,"zone4")]:
			ind = int(conf.getValueStr(zone))
			combo.setCurrentIndex(ind)

	def changeCombo(self,i):
		sender = self.sender()
		conf = Configuration()
		if sender == self.ui.combo1:
			conf.saveValue("zone1",str(i))
		elif sender == self.ui.combo2:
			conf.saveValue("zone2",str(i))
		elif sender == self.ui.combo3:
			conf.saveValue("zone3",str(i))
		elif sender == self.ui.combo4:
			conf.saveValue("zone4",str(i))
	
	
	def closeEvent(self,e):
		e.accept()



