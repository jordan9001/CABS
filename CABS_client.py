#!/usr/bin/python
#This is the test Client for CABS

import socket, ssl

settings = {}

def readConfigFile():
        #open the .conf file and return the variables as a dictionary
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

def main():
	#read config file
	readConfigFile()
	
	try:
		print settings.get("SSL_Cert")
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((settings.get("Host_Addr"), int(settings.get("Client_Port"))))
		content = 'pr:cmguest47:rgst3st4u?\r\n'
		#content = 'pr:notauser:fakepass\r\n'
		if (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
			s_wrapped = s
		else:
			s_wrapped = ssl.wrap_socket(s, ca_certs=settings.get("SSL_Cert"), ssl_version=ssl.PROTOCOL_SSLv23)
		
		s_wrapped.sendall(content)
		pools = ""
		while True:
			chunk = s_wrapped.recv(4096)
			pools += chunk
			if chunk == '':
				break;
		print pools
		
		ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ss.connect((settings.get("Host_Addr"), int(settings.get("Client_Port"))))
		content = 'mr:cmguest47:rgst3st4u?:Main\r\n'
		#content = 'mr:notauser:fakepass:Main\r\n'	
		if (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
			ss_wrapped = ss
		else:
			ss_wrapped = ssl.wrap_socket(ss, ca_certs=settings.get("SSL_Cert"), ssl_version=ssl.PROTOCOL_SSLv23)
		
		ss_wrapped.sendall(content)
		machine = ""
		while True:
			chunk = ss_wrapped.recv(4096)
			machine += chunk
			if chunk == '':
				break;
		print machine
		
	except Exception as e:
		print "Could not connect to {0}:{1} because {2}".format(settings.get("Host_Addr"), settings.get("Host_Port"), e)


if __name__ == "__main__":
	main()
