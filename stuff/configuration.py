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
				"alternate_fullscreen": "No",
			}
		
		def saveValue(self,name,value):
			self.settings.setValue(name,QtCore.QVariant(value))

		
		def getValueStr(self,name):
			v = self.settings.value(name).toString()
			if v != '': return v
			if v == '' and name in self.defaults.keys():
				return self.defaults[name]
			else: return ''
		



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
	def __init__(self,parent):
		QtGui.QWidget.__init__(self,parent)
		self.ui = uic.loadUi("configuration.ui",self)
		
		conf = Configuration()
		if conf.getValueStr("fullscreen") == "Yes":
			self.ui.check_fullscreen.setChecked(True)
		if conf.getValueStr("alternate_fullscreen") == "Yes":
			self.ui.check_altfullscreen.setChecked(True)
		
		self.connect(self.ui.button_OK,
			QtCore.SIGNAL("clicked()"), self.finish)
		
		
	def finish(self):
		conf = Configuration()
		
		if self.ui.check_altfullscreen.isChecked():
			conf.saveValue("alternate_fullscreen","Yes")
		else:
			conf.saveValue("alternate_fullscreen","No")
		
		if self.ui.check_fullscreen.isChecked():
			conf.saveValue("fullscreen","Yes")
		else:
			conf.saveValue("fullscreen","No")
		
		self.close()
	
	
	
	def closeEvent(self,e):
		e.accept()



