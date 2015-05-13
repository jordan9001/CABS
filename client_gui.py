#!/usr/bin/python
import wx
import socket, ssl
from ast import literal_eval

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
		self.sizer = wx.FlexGridSizer(1, 3, 3, 3) #rows, cols, vgap, hgap
		self.rez_label = wx.StaticText(self, wx.ID_ANY, "Screen Resolution:")
		self.rez_slider = wx.Slider(self, wx.ID_ANY, value=len(self.Resolutions) , minValue=0, maxValue=len(self.Resolutions), size=(200,-1), style=wx.SL_HORIZONTAL)
		self.rez_choice = wx.TextCtrl(self, wx.ID_ANY, str(self.Resolutions[len(self.Resolutions)-1][0])+"x"+str(self.Resolutions[len(self.Resolutions)-1][1]), style=wx.TE_READONLY)
		self.sizer.Add(self.rez_label, 0)
		self.sizer.Add(self.rez_slider, 1, wx.EXPAND)
		self.sizer.Add(self.rez_choice, 0)
		#self.sizer.AddGrowableCol(1,1)
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
		print self.maxWidth, self.maxHeight
		print self.Resolutions

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
		#self.sizer.Fit(self)
	
	def toggleOptions(self, e):
		if self.notebook.IsShown():
			self.notebook.Hide()	
			self.sizer.Fit(self)
			self.SetSize((450,-1))
		else:
			self.notebook.Show()
			self.sizer.Fit(self)
			self.SetSize((450,-1))

def main():
	readConfigFile()	
	
	app = wx.App(False)
	MainWindow(None).Show()
	
	app.MainLoop()

if __name__ == "__main__":
        main()
