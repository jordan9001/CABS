#!/usr/bin/python
#This is the test Agent for CABS

import socket, ssl
import sys
import subprocess
from sched import scheduler
from time import time, sleep

settings = {}

def heartbeat():
	if sys.platform.startswith("linux"):
		p = subprocess.Popen(["w", "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output, err = p.communicate()
		#output = subprocess.check_output("w -h", shell=True) #only works on python 2.7
		lines = output.split('\n')
		userlist = set()
		for line in lines:
			try:
				userlist.add(line.split()[0])
			except:
				pass
		print userlist

	elif sys.platform.startswith("win"):
		p = subprocess.Popen(settings.get("C:/Users/Administrator/Desktop/PsLoggedon.exe -x", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True)
		output, err = p.communicate()
		userlist = set()
		for line in output.split('\r\n'):
			if line.startswith(' '):
				userline = line.split("\\")[-1]
				userlist.add(line.strip())
	else:
		#badbadnotgood
		#Unrecognized OS
		pass
		return

	tellServer(userlist)

def tellServer(userlist):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((settings.get("Host_Addr"), int(settings.get("Agent_Port"))))
		content = "sr:" + settings.get("Hostname")
		for user in userlist:
			content += ":{0}".format(user)
		content += "\r\n"
		if (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
			s_wrapped = s 
		else:
			s_wrapped = ssl.wrap_socket(s, ca_certs=settings.get("SSL_Cert"), ssl_version=ssl.PROTOCOL_SSLv23)
		
		s_wrapped.sendall(content)		
	except Exception as e:
		print "Could not connect to {0}:{1} because {2}".format(settings.get("Host_Addr"), settings.get("Agent_Port"), e)

def readConfigFile():
	#open the .conf file and return the variables as a dictionary
	global settings
	with open('CABS_agent.conf', 'r') as f:
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
	if not settings.get("Agent_Port"):
		settings["Agent_Port"] = 18181
	if not settings.get("SSL_Cert"):
		settings["SSL_Cert"] = None
	if not settings.get("Interval"):
		settings["Interval"] = 120
	if not settings.get("Con_Type"):
		settings["Con_Type"] = None
	if not settings.get("Hostname"):
		settings["Hostname"] = None

	if (settings.get("Hostname") is None) or (settings.get("Hostname") == 'None'):
		#If we want a fqdn we can use socket.gethostbyaddr(socket.gethostname())[0]
		settings["Hostname"] = socket.gethostname()

def main():
	readConfigFile()
	s = scheduler(time, sleep)
	#read config for time interval, in seconds
	print "Starting. Pulsing every {0} seconds.".format(settings.get("Interval"))
	while True:
		s.enter(int(settings.get("Interval")), 1, heartbeat, ())
		s.run()

if __name__ == "__main__":
	main()
