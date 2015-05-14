#!/usr/bin/python
import wx
import socket, ssl
from ast import literal_eval

settings = {}
command_settings = []

ID_SAVE_BUTTON = wx.NewId()
ID_RESET_BUTTON = wx.NewId()
ID_SUBMIT_BUTTON = wx.NewId()

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
	if (not settings.get("Net_Domain")) or (settings.get("Net_Domain")=='None'):
		settings["Net_Domain"] = ""

def getPools(user,password):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((settings.get("Host_Addr"), int(settings.get("Client_Port"))))
 	content = "pr:{0}:{1}\r\n".format(user, password)
	#content = 'pr:cmguest47:rgst3st4u?\r\n'
	#content = 'pr:notauser:fakepass\r\n'
	if (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
		s_wrapped = s
	else:
		s_wrapped = ssl.wrap_socket(s, ca_certs=settings.get("SSL_Cert"), ssl_version=ssl.PROTOCOL_SSLv23)
	
	s_wrapped.sendall(content)
	pools = ""
	while True:
		chunk = s_wrapped.recv(1024)
		pools += chunk
		if chunk == '':
			break;
	poolsliterals = pools.split('\n')
	poolset = set()
	for literal in poolsliterals:
		poolset.add(literal_eval(literal))
	return poolset

def getMachine(user, password, pool):
	print settings.get("SSL_Cert")
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((settings.get("Host_Addr"), int(settings.get("Client_Port"))))
 	content = "pr:{0}:{1}:{2}\r\n".format(user, password, pool)
	#content = 'pr:cmguest47:rgst3st4u?:Main\r\n'
	#content = 'pr:notauser:fakepass:Main\r\n'
	if (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
		s_wrapped = s
	else:
		s_wrapped = ssl.wrap_socket(s, ca_certs=settings.get("SSL_Cert"), ssl_version=ssl.PROTOCOL_SSLv23)
	
	s_wrapped.sendall(content)
	machine = ""
	while True:
		chunk = s_wrapped.recv(1024)
		machine += chunk
		if chunk == '':
			break;
	return machine

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

#Settings start on RGS 7.1 manual page 92
class DisplayTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.Resolutions = [(800, 600), (1024, 768), (1152, 864), (1280, 768), (1280, 800), (1280, 960), (1280, 1024), (1360, 768), (1600, 1200), (1680, 1050), (1920, 1080), (1920, 1200), (1920, 1440), (2048, 1536), (2560, 1600)]
		self.getDisplayValues()
		self.InitUI()

	def InitUI(self):
		self.flexsizer = wx.FlexGridSizer(1, 2, 3, 3) #rows, cols, vgap, hgap
		self.flexsizer.AddGrowableCol(1,1)
		
		self.rez_label = wx.StaticText(self, wx.ID_ANY, "Screen Resolution:")
		self.rez_slider = wx.Slider(self, wx.ID_ANY, value=len(self.Resolutions) , minValue=0, maxValue=(len(self.Resolutions)-1), size=(-1,-1), style=wx.SL_HORIZONTAL)
		self.rez_choice = wx.TextCtrl(self, wx.ID_ANY, str(self.Resolutions[len(self.Resolutions)-1][0])+"x"+str(self.Resolutions[len(self.Resolutions)-1][1]), style=wx.TE_READONLY)
		self.rez_slider.Bind(wx.EVT_SCROLL, self.updateRezValue)
		self.rez_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.flexsizer.Add(self.rez_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)
		self.rez_sizer.Add(self.rez_slider, 1, wx.EXPAND)
		self.rez_sizer.Add(self.rez_choice, 0, wx.LEFT | wx.RIGHT, 6)
		self.flexsizer.Add(self.rez_sizer,1, wx.EXPAND)
		
		self.depth_label = wx.StaticText(self, wx.ID_ANY, "Color Depth:")
		self.depth_box = wx.ComboBox(self, wx.ID_ANY, "24-bit (High)", choices=["8-bit (Low)", "16-bit (Medium)", "24-bit (High)"], style=wx.CB_READONLY)
		self.flexsizer.Add(self.depth_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)
		self.flexsizer.Add(self.depth_box, 1, wx.EXPAND)
		
		self.imgqual_label = wx.StaticText(self, wx.ID_ANY, "Image Quality")
		self.imgqual_box = wx.SpinCtrl(self, wx.ID_ANY, "75", style=wx.SP_ARROW_KEYS, min=0, max=100, initial=75)
		self.flexsizer.Add(self.imgqual_label, 0 , wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)
		self.flexsizer.Add(self.imgqual_box, 1, wx.EXPAND)
		
		#self.chkbxsizer = wx.WrapSizer() #Need wxPython 2.9 or greater for this
		self.chkbxsizer = wx.GridSizer(2,2,3)
		self.chkfull = wx.CheckBox(self, wx.ID_ANY, "Fullscreen")
		self.chkbxsizer.Add(self.chkfull, 0, wx.EXPAND)	
		self.chkspan = wx.CheckBox(self, wx.ID_ANY, "Enable Spanning")
		self.chkbxsizer.Add(self.chkspan, 0, wx.EXPAND)
		self.chkmatch = wx.CheckBox(self, wx.ID_ANY, "Match Client Display")
		self.chkbxsizer.Add(self.chkmatch, 0, wx.EXPAND)
		self.chkborders = wx.CheckBox(self, wx.ID_ANY, "Borders")
		self.chkbxsizer.Add(self.chkborders, 0, wx.EXPAND)
		self.chksnap = wx.CheckBox(self, wx.ID_ANY, "Snap to Edge")
		self.chkbxsizer.Add(self.chksnap, 0, wx.EXPAND)
		self.chkconbar = wx.CheckBox(self, wx.ID_ANY, "Display Connection Bar in Fullscreen")
		self.chkbxsizer.Add(self.chkconbar, 0, wx.EXPAND)
		self.chkback = wx.CheckBox(self, wx.ID_ANY, "Show Desktop Background")
		self.chkbxsizer.Add(self.chkback, 0, wx.EXPAND)
		self.chkdrag = wx.CheckBox(self, wx.ID_ANY, "Show while Dragging")
		self.chkbxsizer.Add(self.chkdrag, 0, wx.EXPAND)
		self.chkani = wx.CheckBox(self, wx.ID_ANY, "Window/Menu Animations")
		self.chkbxsizer.Add(self.chkani, 0, wx.EXPAND)
		self.chkthemes = wx.CheckBox(self, wx.ID_ANY, "Show Themes")
		self.chkbxsizer.Add(self.chkthemes, 0, wx.EXPAND)
		self.chkcache = wx.CheckBox(self, wx.ID_ANY, "Cache Bitmaps")
		self.chkbxsizer.Add(self.chkcache, 0, wx.EXPAND)
		self.chkautosize = wx.CheckBox(self, wx.ID_ANY, "Autosizing")
		self.chkbxsizer.Add(self.chkautosize, 0, wx.EXPAND)
		self.chkcomposition = wx.CheckBox(self, wx.ID_ANY, "Desktop Composition")
		self.chkbxsizer.Add(self.chkcomposition, 0, wx.EXPAND)
		self.chksmoothing = wx.CheckBox(self, wx.ID_ANY, "Font Smoothing")
		self.chkbxsizer.Add(self.chksmoothing, 0, wx.EXPAND)
		
		self.Bind(wx.EVT_CHECKBOX, self.disableStuff)
		self.disableStuff(None)
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.flexsizer, 0, wx.EXPAND | wx.TOP, 6)
		self.sizer.Add(self.chkbxsizer, 0, wx.EXPAND)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
		

	def getDisplayValues(self):
		disp = wx.Display(0)
		self.dispCount = disp.GetCount()
		self.maxRez =  disp.GetClientArea()#max rez rectangle
		self.maxWidth = self.maxRez[2] - self.maxRez[0]
		self.maxHeight = self.maxRez[3] - self.maxRez[1]
		Rezolutions = []
		#now remove rezolutions above that
		for rez in self.Resolutions:
			if (rez[0] < self.maxWidth) and (rez[1] < self.maxHeight):
				Rezolutions.append(rez)
		self.Resolutions = Rezolutions
	
	def updateRezValue(self, e):
		self.rez_choice.ChangeValue(str(self.Resolutions[self.rez_slider.GetValue()][0])+"x"+str(self.Resolutions[self.rez_slider.GetValue()][1]))
	
	def disableStuff(self, e):
		#disable the things that you can't touch at the right times.
		self.chkspan.Enable(self.chkfull.IsChecked())
		self.chkborders.Enable(not self.chkfull.IsChecked())
		self.chksnap.Enable(not self.chkfull.IsChecked())
		#These I don't know when to enable, so they are all disabled for now
		self.chkconbar.Disable()
		self.chkback.Disable()
		self.chkdrag.Disable()
		self.chkani.Disable()
		self.chkthemes.Disable()
		self.chkcache.Disable()
		self.chkautosize.Disable()
		self.chkcomposition.Disable()
		self.chksmoothing.Disable()
		
		self.chkconbar.Hide()
		self.chkback.Hide()
		self.chkdrag.Hide()
		self.chkani.Hide()
		self.chkthemes.Hide()
		self.chkcache.Hide()
		self.chkautosize.Hide()
		self.chkcomposition.Hide()
		self.chksmoothing.Hide()
	
	def load(self, default):
		if(default):
			#load defaults
			self.rez_slider.SetValue(len(self.Resolutions)-1)
			self.updateRezValue(None)
			self.depth_box.SetSelection(2)
			self.imgqual_box.SetValue(75)
 			self.chkfull.SetValue(False)
			self.chkspan.SetValue(False)
			self.chkmatch.SetValue(False)
			self.chkborders.SetValue(False)
			self.chksnap.SetValue(False)
			self.chkconbar.SetValue(False)
			self.chkback.SetValue(False)
			self.chkdrag.SetValue(False)
			self.chkani.SetValue(False)
			self.chkthemes.SetValue(False)
			self.chkcache.SetValue(False)
			self.chkautosize.SetValue(False)
			self.chkcomposition.SetValue(False)
			self.chksmoothing.SetValue(False)
			self.disableStuff(None)
		else:
			#load from saved settings
			pass
		
class AudioTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.chkmute = wx.CheckBox(self, wx.ID_ANY, "Mute Audio")
		self.sizer.Add(self.chkmute, 0, wx.TOP, 6)
		
		self.qual_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.qual_label = wx.StaticText(self, wx.ID_ANY, "Audio Quality:")
		self.qual_choice = wx.ComboBox(self, wx.ID_ANY, "Medium", choices=["Low", "Medium", "High"], style=wx.CB_READONLY)
		self.qual_sizer.Add(self.qual_label, 0, wx.ALIGN_CENTER | wx.LEFT, 3)
		self.qual_sizer.Add(self.qual_choice, 1, wx.EXPAND)
		self.sizer.Add(self.qual_sizer, 0, wx.EXPAND)
		
		self.chkstereo = wx.CheckBox(self, wx.ID_ANY, "Stereo Sound")
		self.chkstereo.SetValue(True)
		self.sizer.Add(self.chkstereo, 0)
		
		self.chksessiononly = wx.CheckBox(self, wx.ID_ANY, "Sound for Active Session Only")
		self.sizer.Add(self.chksessiononly, 0)
		
		self.chkmic = wx.CheckBox(self, wx.ID_ANY, "Microphone")
		self.sizer.Add(self.chkmic, 0)
			
		self.Bind(wx.EVT_CHECKBOX, self.disableStuff)
		self.disableStuff(None)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)

	def disableStuff(self, e):
		self.qual_label.Enable(not self.chkmute.IsChecked())
		self.qual_choice.Enable(not self.chkmute.IsChecked())
		self.chkstereo.Enable(not self.chkmute.IsChecked())
		self.chksessiononly.Enable(not self.chkmute.IsChecked())
		self.chkmic.Enable(not self.chkmute.IsChecked())
	
	def load(self, default):
		if(default):
			#load defaults
			self.chkmute.SetValue(False)
			self.qual_choice.SetSelection(1)
			self.chkstereo.SetValue(True)
			self.chksessiononly.SetValue(False)
			self.chkmic.SetValue(False)
			self.disableStuff(None)
		else:
			#load from saved settings
			pass

class KeyboardTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.wincombo_label = wx.StaticText(self, wx.ID_ANY, "Special Windows key combinations should be handled:")
		self.sizer.Add(self.wincombo_label,0, wx.ALL, 6)
		
		self.wincombo_rb0 = wx.RadioButton(self, label="On the Remote Computer", style=wx.RB_GROUP)
		self.wincombo_rb1 = wx.RadioButton(self, label="On the Local Computer")
		self.wincombo_rb2 = wx.RadioButton(self, label="On the Remote Computer in Fullscreen")
		self.wincombo_rb2.SetValue(True)
		self.sizer.Add(self.wincombo_rb0, 0, wx.LEFT, 30)
		self.sizer.Add(self.wincombo_rb1, 0, wx.LEFT, 30)
		self.sizer.Add(self.wincombo_rb2, 0, wx.LEFT, 30)
		
		self.chkrepeat = wx.CheckBox(self, wx.ID_ANY, "Enable RGS Key Repeat")
		self.sizer.Add(self.chkrepeat, 0, wx.TOP, 6)
		
		self.disableStuff(None)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
	
	def disableStuff(self, e):
		self.wincombo_rb0.Enable(False)
		self.wincombo_rb1.Enable(False)
		self.wincombo_rb2.Enable(False)
		
	def load(self, default):
		if(default):
			#load defaults
			self.wincombo_rb2.SetValue(True)
			self.chkrepeat.SetValue(False)
			self.disableStuff(None)
		else:
			#load from saved settings
			pass

class DevicesTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.label = wx.StaticText(self, wx.ID_ANY, "Make the following Devices on this machine available:")
		self.sizer.Add(self.label, 0, wx.ALL, 6)
		
		self.chkdrives = wx.CheckBox(self, wx.ID_ANY, "Disk Drives")
		self.sizer.Add(self.chkdrives, 0, wx.LEFT, 30)
		self.chkprinters = wx.CheckBox(self, wx.ID_ANY, "Printers")
		self.sizer.Add(self.chkprinters, 0, wx.LEFT, 30)
		self.chkports = wx.CheckBox(self, wx.ID_ANY, "Serial Ports")
		self.sizer.Add(self.chkports, 0, wx.LEFT, 30)
		self.chkclip = wx.CheckBox(self, wx.ID_ANY, "Clipboard")
		self.sizer.Add(self.chkclip, 0, wx.LEFT, 30)
		self.chkclip.SetValue(True)
		self.chkcards = wx.CheckBox(self, wx.ID_ANY, "Smart Cards")
		self.sizer.Add(self.chkcards, 0, wx.LEFT, 30)
		self.chkusb = wx.CheckBox(self, wx.ID_ANY, "USB Devices")
		self.sizer.Add(self.chkusb, 0, wx.LEFT, 30)
		
		self.disableStuff(None)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
	
	def disableStuff(self, e):
		self.chkdrives.Enable(False)
		self.chkprinters.Enable(False)
		self.chkports.Enable(False)
		self.chkcards.Enable(False)

	def load(self, default):
		if(default):
			#load defaults
			self.chkdrives.SetValue(False)
			self.chkprinters.SetValue(False)
			self.chkports.SetValue(False)
			self.chkclip.SetValue(True)
			self.chkcards.SetValue(False)
			self.chkusb.SetValue(False)
			self.disableStuff(None)
		else:
			#load from saved settings
			pass

class TimersTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.def_rb = wx.RadioButton(self, label="Use Default Timeout Values", style=wx.RB_GROUP)
		self.cus_rb = wx.RadioButton(self, label="Use the Following Timeout Values (in seconds)")
		self.sizer.Add(self.def_rb, 0, wx.TOP, 6)
		self.sizer.Add(self.cus_rb, 0)
		
		self.cus_sizer = wx.FlexGridSizer(cols=2, vgap=3, hgap=3)
		self.error_label = wx.StaticText(self, wx.ID_ANY, "Error Timeout")
		self.error_box = wx.SpinCtrl(self, wx.ID_ANY, "0", style=wx.SP_ARROW_KEYS, min=0, max=60, initial=0)
		self.cus_sizer.Add(self.error_label, 0, wx.ALIGN_CENTER_VERTICAL)
		self.cus_sizer.Add(self.error_box, 1, wx.EXPAND)
		
		self.warn_label = wx.StaticText(self, wx.ID_ANY, "Warning Timeout")
		self.warn_box = wx.SpinCtrl(self, wx.ID_ANY, "0", style=wx.SP_ARROW_KEYS, min=0, max=60, initial=0)
		self.cus_sizer.Add(self.warn_label, 0, wx.ALIGN_CENTER_VERTICAL)
		self.cus_sizer.Add(self.warn_box, 1, wx.EXPAND)

		self.dialog_label = wx.StaticText(self, wx.ID_ANY, "Dialog Timeout")
		self.dialog_box = wx.SpinCtrl(self, wx.ID_ANY, "0", style=wx.SP_ARROW_KEYS, min=0, max=99, initial=0)
		self.cus_sizer.Add(self.dialog_label, 0, wx.ALIGN_CENTER_VERTICAL)
		self.cus_sizer.Add(self.dialog_box, 1, wx.EXPAND)
		
		self.cus_sizer.AddGrowableCol(1,1)
		self.sizer.Add(self.cus_sizer, 1, wx.EXPAND)
		
		self.Bind(wx.EVT_RADIOBUTTON, self.disableStuff)
		self.disableStuff(None)
		
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
	
	def disableStuff(self, e):
		self.error_label.Enable(self.cus_rb.GetValue())
		self.error_box.Enable(self.cus_rb.GetValue())
		self.warn_label.Enable(self.cus_rb.GetValue())
		self.warn_box.Enable(self.cus_rb.GetValue())
		self.dialog_label.Enable(self.cus_rb.GetValue())
		self.dialog_box.Enable(self.cus_rb.GetValue())

	def load(self, default):
		if(default):
			#load defaults
			self.def_rb.SetValue(True)
			self.error_box.SetValue(0)
			self.warn_box.SetValue(0)
			self.dialog_box.SetValue(0)
			self.disableStuff(None)
		else:
			#load from saved settings
			pass

class OtherTab(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()

	def InitUI(self):
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.savebttn = wx.Button(self, ID_SAVE_BUTTON, label="Save Settings")
		self.sizer.Add(self.savebttn, 0, wx.EXPAND)
		
		self.resetbttn = wx.Button(self, ID_RESET_BUTTON, label="Reset Defaults")
		self.sizer.Add(self.resetbttn, 0, wx.EXPAND)
		
		self.savebttn.Bind(wx.EVT_BUTTON, self.passOn)
		self.resetbttn.Bind(wx.EVT_BUTTON, self.passOn)
		
		self.domandserv = DomainAndServer(self)
		self.sizer.Add(self.domandserv, 0, wx.EXPAND | wx.ALL, 18)
		
		self.chkreconnect = wx.CheckBox(self, wx.ID_ANY, label="Reconnect on Lost Connection")
		self.sizer.Add(self.chkreconnect, 0)
		self.chkroles = wx.CheckBox(self, wx.ID_ANY, label="Show Public Roles")
		self.sizer.Add(self.chkroles, 0)
		self.chkroles.SetValue(True)		

		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)
	
	def passOn(self, e):
		e.Skip()

	def load(self, default):
		if(default):
			self.chkreconnect.SetValue(False)
			self.chkroles.SetValue(True)
			self.domandserv.domain.ChangeValue(settings.get("Net_Domain"))
			self.domandserv.server.ChangeValue(settings.get("Host_Addr"))
		else:
			#load from saved settings
			pass

class DomainAndServer(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		self.InitUI()
	def InitUI(self):
		self.domain_label = wx.StaticText(self, wx.ID_ANY, "Domain : ", size=(90,-1))
		self.server_label = wx.StaticText(self, wx.ID_ANY, "CABS Server : ", size=(90,-1))
		self.domain = wx.TextCtrl(self, value=settings.get("Net_Domain"), style=wx.TE_LEFT, size=(-1,30))
		self.server = wx.TextCtrl(self, value=settings.get("Host_Addr"), style=wx.TE_LEFT, size = (-1,30))
		
		self.sizer = wx.FlexGridSizer(cols=2, vgap=3, hgap=3)
		self.sizer.Add(self.domain_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 6)
		self.sizer.Add(self.domain, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.RIGHT, 6)
		
		self.sizer.Add(self.server_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.LEFT, 6)
		self.sizer.Add(self.server, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.RIGHT, 6)
		
		self.sizer.AddGrowableCol(1,1)
		self.SetSizer(self.sizer)
		self.SetAutoLayout(1)

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
		self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)	
		self.button_submit = wx.Button(p, ID_SUBMIT_BUTTON, "Connect")
		self.button_submit.Bind(wx.EVT_BUTTON, self.handleSettings)
		self.button_sizer.Add(self.button_submit, 1, wx.EXPAND | wx.ALL, 9)
		
		if settings.get("RGS_Options") == 'True':
			#Build button
			button_settings = wx.Button(p, wx.ID_ANY, "RGS Options")
			button_settings.Bind(wx.EVT_BUTTON, self.toggleOptions)
			self.button_sizer.Add(button_settings, 1, wx.ALL, 9)
			self.sizer.Add(self.button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT , 92)
			#Build Settings tabs
			self.notebook = wx.Notebook(p)
			
			self.tab1 = DisplayTab(self.notebook)
			self.tab2 = AudioTab(self.notebook)
			self.tab3 = KeyboardTab(self.notebook)
			self.tab4 = DevicesTab(self.notebook)
			self.tab5 = TimersTab(self.notebook)
			self.tab6 = OtherTab(self.notebook)
			
			self.notebook.AddPage(self.tab1, "Display")
			self.notebook.AddPage(self.tab2, "Audio")
			self.notebook.AddPage(self.tab3, "Keyboard")
			self.notebook.AddPage(self.tab4, "Devices")
			self.notebook.AddPage(self.tab5, "Timers")
			self.notebook.AddPage(self.tab6, "Other")
				
			self.Bind(wx.EVT_BUTTON, self.handleSettings)
		else:	
			button_settings = wx.Button(p, wx.ID_ANY, "Options")
			button_settings.Bind(wx.EVT_BUTTON, self.toggleOptions)
			self.button_sizer.Add(button_settings, 1, wx.ALL, 9)
			self.sizer.Add(self.button_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 92)
			
			self.notebook = DomainAndServer(p)
		
		self.notebook.Hide()	
		self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 3)
		
		p.SetSizer(self.sizer)
		p.SetAutoLayout(1)
		self.sizer.Fit(self)
		self.SetSize((450,-1))
	
	def toggleOptions(self, e):
		if self.notebook.IsShown():
			self.notebook.Hide()	
			self.sizer.Fit(self)
			self.SetSize((450,-1))
		else:
			self.notebook.Show()
			self.sizer.Fit(self)
			self.SetSize((450,-1))
	
	def handleSettings(self, e):
		if e.GetId() == ID_SUBMIT_BUTTON:
			#do a Pool Request
			pass
		elif e.GetId() == ID_SAVE_BUTTON:
			#save settings, which will be loaded automatically at the start with load(false), once we get it goin
			pass
		elif e.GetId() == ID_RESET_BUTTON:
			#We reset to default settings
			self.tab1.load(True)
			self.tab2.load(True)
			self.tab3.load(True)
			self.tab4.load(True)
			self.tab5.load(True)
			self.tab6.load(True)

def main():
	readConfigFile()	
	
	app = wx.App(False)
	MainWindow(None).Show()
	
	app.MainLoop()

if __name__ == "__main__":
        main()
