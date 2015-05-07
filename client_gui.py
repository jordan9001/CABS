#!/usr/bin/python
import wx
import socket, ssl

settings = {}

def readConfigFile():
	global settings
        with open('CABS_client.conf', 'r') as f:
                for line in f:
                        line = line.strip()
                        if (not line.startswith('#')) and line:
                                try:
                                        (key,val) = line.split(':\t',1)
                                except:
                                        print "Warning : Check .conf syntax"
                                        try:
                                                (key,val) = line.split(None,1)
                                                key = key[:-1]
                                        except:
                                                key = line
                                                val = ''
                                settings[key] = val
                f.close()
        #insert default settings for all not specified
        if not settings.get("Host_Addr"):
                settings["Host_Addr"] = 'localhost'
        if not settings.get("Client_Port"):
                settings["Client_Port"] = 18181
        if not settings.get("SSL_Cert"):
                settings["SSL_Cert"] = None
	if not settings.get("Command"):
		settings["Command"] = None
	if not settings.get("RGS_Options"):
		settings["RGS_Options"] = False
	if not settings.get("RGS_Location"):
		settings["RGS_Location"] = None

class MainPage(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()
	
	def InitUI(self):
		self.user_label = wx.StaticText(self, wx.ID_ANY, "Username : ", size=(80,-1))
		self.pass_label = wx.StaticText(self, wx.ID_ANY, "Password : ", size=(80,-1))
		self.username = wx.TextCtrl(self, style=wx.TE_LEFT, size=(120,30))
		self.password = wx.TextCtrl(self, style=wx.TE_PASSWORD, size = (120,30))
		
		self.user_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.user_sizer.Add(self.user_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 15)
		self.user_sizer.Add(self.username, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.RIGHT, 15)
		
		self.pass_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.pass_sizer.Add(self.pass_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 15)
		self.pass_sizer.Add(self.password, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.RIGHT, 15)
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.user_sizer, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, 6)
		self.sizer.Add(self.pass_sizer, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER, 6)

		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)

class DisplayTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.label = wx.StaticText(self, wx.ID_ANY, "Display Options")

class AudioTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.label = wx.StaticText(self, wx.ID_ANY, "Audio Options")

class KeyboardTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.label = wx.StaticText(self, wx.ID_ANY, "Keyboard Options")

class DevicesTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.label = wx.StaticText(self, wx.ID_ANY, "Devices Options")

class TimersTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.label = wx.StaticText(self, wx.ID_ANY, "Timers Options")

class OtherTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.label = wx.StaticText(self, wx.ID_ANY, "Other Options")


class SettingsRGS(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()
	
	def InitUI(self):
		p = wx.Panel(self)
		notebook = wx.Notebook(p)
		tab1 = DisplayTab(notebook)
		tab2 = AudioTab(notebook)
		tab3 = KeyboardTab(notebook)
		tab4 = DevicesTab(notebook)
		tab5 = TimersTab(notebook)
		tab6 = OtherTab(notebook)
		notebook.AddPage(tab1, "Display")
		notebook.AddPage(tab2, "Audio")
		notebook.AddPage(tab3, "Keyboard")
		notebook.AddPage(tab4, "Devices")
		notebook.AddPage(tab5, "Timers")
		notebook.AddPage(tab6, "Other")
			
		user_label = wx.StaticText(self, wx.ID_ANY, "Username : ", size=(80,-1))
		pass_label = wx.StaticText(self, wx.ID_ANY, "Password : ", size=(80,-1))
		
		sizer.Add(notebook, 1, wx.EXPAND)
		sizer.Add(user_label)
		sizer.Add(pass_label)
		
		p.SetSizer(sizer)
		p.SetAutoLayout(1)

class MainWindow(wx.Frame):
	def __init__(self, parent):
		#wx.Frame.__init__(self, parent, title="CABS", size=(-1,-1), style = wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)
		wx.Frame.__init__(self, parent, title="CABS", size=(450,-1))
		self.CreateStatusBar()
		
		self.InitUI()
		self.Center()
		self.Show()
		
		
	def InitUI(self):
		
		p = wx.Panel(self)
		headerimage = wx.Image('Header.png', wx.BITMAP_TYPE_ANY)
		header = wx.StaticBitmap(p, wx.ID_ANY, wx.BitmapFromImage(headerimage))
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(header, 0, wx.BOTTOM, 0)	
		self.sizer.Add(MainPage(p), 0, wx.EXPAND)
		if settings.get("RGS_Options") == 'True':
			#Build button
			show_settings = wx.CheckBox(p, wx.ID_ANY, "Options")
			show_settings.Bind(wx.EVT_CHECKBOX, self.toggleOptions)
			self.sizer.Add(show_settings, 0)
			#Build Settings tabs
			self.notebook = wx.Notebook(p)
			
			tab1 = DisplayTab(self.notebook)
			tab2 = AudioTab(self.notebook)
			tab3 = KeyboardTab(self.notebook)
			tab4 = DevicesTab(self.notebook)
			tab5 = TimersTab(self.notebook)
			tab6 = OtherTab(self.notebook)
			
			self.notebook.AddPage(tab1, "Display")
			self.notebook.AddPage(tab2, "Audio")
			self.notebook.AddPage(tab3, "Keyboard")
			self.notebook.AddPage(tab4, "Devices")
			self.notebook.AddPage(tab5, "Timers")
			self.notebook.AddPage(tab6, "Other")
			
			self.notebook.Hide()	
			self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 3)
		
		p.SetSizer(self.sizer)
		p.SetAutoLayout(1)
		self.sizer.Fit(self)
	
	def toggleOptions(self, e):
		if self.notebook.IsShown():
			self.notebook.Hide()
			self.SetSize((-1,-1))
			self.sizer.Fit(self)
		else:
			self.notebook.Show()
			self.SetSize((-1,-1))
			self.sizer.Fit(self)

def main():
	readConfigFile()	
	
	app = wx.App(False)
	MainWindow(None).Show()
	
	app.MainLoop()

if __name__ == "__main__":
        main()
