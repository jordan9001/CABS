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
		output = subprocess.check_output("w -h -s", shell=True)
		lines = output.split('\n')
		userlist = set()
		for line in lines:
			try:
				userlist.add(line.split()[0])
			except:
				pass
		print userlist

	elif sys.platform.startswith("win"):
		p = subprocess.Popen(["query","session"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output, err = p.communicate()
		userlist = set()
	else:
		#badbadnotgood
		#Unrecognized OS
	return

	tellServer(userlist)

def tellServer(userlist):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((settings.get("Host_Addr"), int(settings.get("Agent_Port"))))
		content = "ul"
		for user in userlist:
			content += ":{0}".format(user)
		if (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
			s_wrapped = s 
		else:
			s_wrapped = ssl.wrap_socket(s, ca_certs="/home/sherpa/CABS/cacert.pem", ssl_version=ssl.PROTOCOL_SSLv23)

		s_wrapped.sendall(content)		
	except Exception as e:
		print "Could not connect to {0}:{1} because {2}".format(settings.get("Host_Addr"), settings.get("Host_Port"), e)

def readConfigFile():
	#open the .conf file and return the variables as a dictionary
	global settings
	with open('CABS_client.conf', 'r') as f:
		for line in f:
			line = line.rstrip()
			if (not line.startswith('#')) and line:
				try:
					(key,val) = line.split(':\t',1)
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
		settings["SLL_Cert"] = None
	if not settings.get("Interval"):
		settings["Interval"] = 120

def main():
	readConfigFile()
	s = scheduler(time, sleep)
	#read config for time interval, in seconds
	while True:
		s.enter(settings.get("Interval"), 1, heartbeat, ())
		s.run()

if __name__ == "__main__":
	main()
