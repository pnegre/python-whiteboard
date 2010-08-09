# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
import PyQt4.Qt as qt


CONFIG_VERSION = 6


class Configuration:

	class __impl:
		""" Implementation of the singleton interface """
		
		def __init__(self):
			self.settings = QtCore.QSettings("pywhiteboard","pywhiteboard")
			
			self.defaults = {
				"fullscreen": "Yes",
				"selectedmac": '*',
				"zone1": "1",
				"zone2": "2",
				"zone3": "3",
				"zone4": "0",
				"autoconnect": "Yes",
				"autocalibration": "Yes",
				"sensitivity": "6",
				"smoothing": "5",
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
			for i,dct in enumerate(lst):
				self.settings.setArrayIndex(i)
				for k in dct.keys():
					self.settings.setValue(k,dct[k])
			self.settings.endArray()
		
		
		def readArray(self,name):
			n = self.settings.beginReadArray(name)
			result = []
			for i in range(0,n):
				self.settings.setArrayIndex(i)
				kys = self.settings.childKeys()
				d = dict()
				for k in kys:
					d[unicode(k)] = unicode(self.settings.value(k).toString())
				result.append(d)
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
		if conf.getValueStr("autocalibration") == "Yes":
			self.ui.check_autocalibration.setChecked(True)
		
		self.connect(self.ui.check_fullscreen,
			QtCore.SIGNAL("stateChanged(int)"), self.checkStateChanged)
		self.connect(self.ui.check_autoconnect,
			QtCore.SIGNAL("stateChanged(int)"), self.checkStateChanged)
		self.connect(self.ui.check_autocalibration,
			QtCore.SIGNAL("stateChanged(int)"), self.checkStateChanged)
		
		self.connect(self.ui.button_addDev,
			QtCore.SIGNAL("clicked()"), self.addDevice)
		self.connect(self.ui.button_remDev,
			QtCore.SIGNAL("clicked()"), self.removeDevice)
		
		self.setupMacTable()
		
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
		
		self.ui.slider_smoothing.setMinimum(1)
		self.ui.slider_smoothing.setMaximum(7)
		self.connect(self.ui.slider_smoothing,
			QtCore.SIGNAL("valueChanged(int)"), self.sliderSmMoved)
		smth = int(conf.getValueStr("smoothing"))
		self.ui.slider_smoothing.setValue(smth)
		
		self.checkButtons()
	
	
	def checkButtons(self):
		if self.wii == None:
			self.ui.button_addDev.setEnabled(False)
		else:
			self.ui.button_addDev.setEnabled(True)
	
	
	
	def setupMacTable(self):
		self.ui.tableMac.setColumnCount(2)
		self.ui.tableMac.setHorizontalHeaderLabels(['Address','Comment'])
		self.ui.tableMac.setSelectionMode(QtGui.QTableWidget.SingleSelection)
		self.ui.tableMac.setSelectionBehavior(QtGui.QTableWidget.SelectRows)
		self.refreshMacTable()
		header = self.ui.tableMac.horizontalHeader()
		header.setStretchLastSection(True)
		self.connect(self.ui.tableMac,
			QtCore.SIGNAL("cellClicked(int,int)"), self.macTableCellSelected)
	
	
	def macTableCellSelected(self,r,c):
		address = unicode(self.ui.tableMac.item(r,0).text())
		conf = Configuration()
		conf.saveValue('selectedmac',address)
	
	
	def refreshMacTable(self):
		while self.ui.tableMac.item(0,0):
			self.ui.tableMac.removeRow(0)
		
		self.ui.tableMac.insertRow(0)
		item = QtGui.QTableWidgetItem('*')
		self.ui.tableMac.setItem(0,0,item)
		item = QtGui.QTableWidgetItem(self.tr('All devices'))
		self.ui.tableMac.setItem(0,1,item)
		self.ui.tableMac.selectRow(0)
		conf = Configuration()
		lst = conf.readArray('maclist')
		for elem in lst:
			rc = self.ui.tableMac.rowCount()
			self.ui.tableMac.insertRow(rc)
			item = QtGui.QTableWidgetItem(elem['address'])
			self.ui.tableMac.setItem(rc,0,item)
			item = QtGui.QTableWidgetItem(elem['comment'])
			self.ui.tableMac.setItem(rc,1,item)
			selected = conf.getValueStr('selectedmac')
			if selected == elem['address']:
				self.ui.tableMac.selectRow(rc)
	
	
	
	
	def addDevice(self):
		if self.wii == None: return
		conf = Configuration()
		d = conf.readArray('maclist')
		address = self.wii.addr
		for item in d:
			if item['address'] == address: return
		
		comment, ok = QtGui.QInputDialog.getText(self,
			self.tr("Comment"), self.tr('Wii device description'))
		
		if ok:
			d.append( {'address': address, 'comment': comment} )
			conf.writeArray('maclist',d)
			self.refreshMacTable()
	
	
	def removeDevice(self):
		conf = Configuration()
		mlist = conf.readArray('maclist')
		for it in self.ui.tableMac.selectedItems():
			if it.column() == 0:
				address = it.text()
				mlist = [ elem for elem in mlist if elem['address'] != address ]
				conf.writeArray('maclist',mlist)
				self.refreshMacTable()
				conf.saveValue('selectedmac','*')
				return
	
	
	def sliderSmMoved(self,val):
		conf = Configuration()
		conf.saveValue("smoothing",str(val))
		self.ui.label_smoothing.setText(self.tr("Smoothing: ") + str(val))
	
	
	def sliderIrMoved(self, val):
		conf = Configuration()
		conf.saveValue("sensitivity",str(val))
		self.ui.label_sensitivity.setText(self.tr("IR Sensitivity: ") + str(val))
	
		
	def finish(self):
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
	
	def checkStateChanged(self,i):
		yesno = 'Yes'
		if i == 0: yesno = 'No'
		sender = self.sender()
		conf = Configuration()
		if sender == self.ui.check_fullscreen:
			conf.saveValue('fullscreen',yesno)
		if sender == self.ui.check_autoconnect:
			conf.saveValue('autoconnect',yesno)
		if sender == self.ui.check_autocalibration:
			conf.saveValue('autocalibration',yesno)
	
	
	def closeEvent(self,e):
		e.accept()



