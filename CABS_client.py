#!/usr/bin/python
#This is the test Client for CABS

import socket, ssl
import time

def readConfigFile():
	#testing
	settings = {}
	settings["Host_Addr"] = "localhost"
	settings["Host_Port"] = "18181"
	return settings

def main():
	#read config file
	settings = {}
	settings = readConfigFile()
	
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((settings.get("Host_Addr"), int(settings.get("Host_Port"))))
		s_wrapped = ssl.wrap_socket(s, ca_certs="/home/sherpa/CABS/cacert.pem", ssl_version=ssl.PROTOCOL_SSLv23)
		content = 'pr:cmguest47:rgst3st4u?\r\n'
		#content = 'pr:notauser:fakepass\r\n'
		s_wrapped.sendall(content)
		pools = ""
		while True:
			chunk = s_wrapped.recv(4096)
			pools += chunk
			if chunk == '':
				break;
		print pools
		s.close()

		ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ss.connect((settings.get("Host_Addr"), int(settings.get("Host_Port"))))
		ss_wrapped = ssl.wrap_socket(ss, ca_certs="/home/sherpa/CABS/cacert.pem", ssl_version=ssl.PROTOCOL_SSLv23)
		content = 'mr:cmguest47:rgst3st4u?:Main\r\n'
		#content = 'mr:notauser:fakepass:Main\r\n'
		ss_wrapped.sendall(content)
		machine = ""
		while True:
			chunk = ss_wrapped.recv(4096)
			machine += chunk
			if chunk == '':
				break;
		print machine
		ss.close()	

	except Exception as e:
		print "Could not connect to {0}:{1} because {2}".format(settings.get("Host_Addr"), settings.get("Host_Port"), e)


if __name__ == "__main__":
	main()
