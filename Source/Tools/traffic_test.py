#!/usr/bin/python
import socket, ssl
import os
import struct
import random
import sys
import string
import threading
from os.path import isfile


settings = {}

def splash():
    print"""
           _______ _______ ______  _______              
           |       |_____| |_____] |______              
           |_____  |     | |_____] ______|              
                                                        
 ______   ______ _______ _______ _     _ _______  ______
 |_____] |_____/ |______ |_____| |____/  |______ |_____/
 |_____] |    \_ |______ |     | |    \_ |______ |    \_
                                                        
"""

def hitServer():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((settings.get("Host"), int(settings.get("Port"))))
    except Exception as e:
        print "Error:", e
    else:
        if settings.get("Evil_Close") == 'True':
            linger = 1
            lingertime = 0
            s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', linger, lingertime))
        if not settings.get("Message"):
            name = "".join( [random.choice(string.letters) for i in range(int(settings.get("Rand_Length")))] )
            paswd = "".join( [random.choice(string.letters) for i in range(int(settings.get("Rand_Length")))] )
            content = "pr:{0}:{1}".format(name, paswd)
        else:
            content = settings.get("Message")
        if settings.get("No_Return") != 'True':
            content += '\r\n'
        if (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
            s_wrapped = s
        else:
            s_wrapped = ssl.wrap_socket(s, ca_certs=settings.get("SSL_Cert"), ssl_version=ssl.PROTOCOL_SSLv23)
        s_wrapped.sendall(content)
        s_wrapped.close()

def printUsage(extend=False):
    print "Usage : "+sys.argv[0]+" -h host [-p port] [-v] [-s /path/to/cert.pem] [-r] [-e] [-n (#tries | loop)] [-t #threads] [(-m msg) | (-l msg_length)]"
    if extend:
        print "  -h host           : the CABS Broker Server"
        print "  -p port           : the CABS Broker Port for Clients or Agents"
        print "  -s /to/cert.pem   : the path to the CABS Broker certificate.pem"
        print "  -r                : don't add a valid return at the end of the message"
        print "  -e                : disconnect evily, with no FIN packet"
        print "  -n (#tries | loop): the number of requests to send, or loop until Ctrl-C"
        print "  -t #threads       : the number of threads for making requests"
        print "  -m msg            : the message to send, otherwise a random user name and password will be sent in a pool request"
        print "  -l msg_length     : the length of the random username and password"
    else:
        print "      : "+sys.argv[0]+" -? for extra info"
    sys.exit()

def getArgs():
    global settings
    #read command line arguments
    option = None
    for i in range(1,len(sys.argv)):
        if option is not None:
            if sys.argv[i].startswith('-'):
                printUsage()
            settings[option] = sys.argv[i]
            option = None
        else:
            if sys.argv[i] in ['-?', '?', '--help', '-help']:
                printUsage(True)
            if sys.argv[i] in ['-h', '--host', '-host']:
                option = "Host"
            elif sys.argv[i] in ['-v', '--verbose', '-verbose']:
                settings["Verbose"] = 'True'
            elif sys.argv[i] in ['-p', '--port', '-port']:
                option = "Port"
            elif sys.argv[i] in ['-s', '--ssl_cert', '--ssl', '-ssl']:
                option = "SSL_Cert"
            elif sys.argv[i] in ['-r', '--return', '-return']:
                settings["No_Return"] = 'True'
            elif sys.argv[i] in ['-e', '--evil', '-evil']:
                settings["Evil_Close"] = 'True'
            elif sys.argv[i] in ['-m', '--msg', '-msg', '--message', '-message']:
                option = "Message"
            elif sys.argv[i] in ['-l', '--length', '-length', '--msg_length']:
                option = "Rand_Length"
            elif sys.argv[i] in ['-n', '--tries', '-tries', '--number', '-number']:
                option = "Number"
            elif sys.argv[i] in ['-t', '--threads', '-threads']:
                option = "Threads"

    #fill in defaults or fail
    if not settings.get("Host"):
        printUsage()
    if not settings.get("Port"):
        settings["Port"] = "18181"
    if not settings.get("Rand_Length"):
        settings["Rand_Length"] = "30"
    if not settings.get("Number"):
        settings["Number"] = "300"
    if not settings.get("Threads"):
        settings["Threads"] = 1

def runHit():
    if settings.get("Number") == 'loop':
        while True:
            hitServer()
    else:
        for i in range(int(settings.get("Number"))):
            hitServer()

def gucci_main():
    getArgs()
    splash()
    
    if int(settings.get("Threads")) > 1:
        threads = []
        for i in range(int(settings.get("Threads"))):
            t=threading.Thread(target=runHit)
            if settings.get("Number") == 'loop':
                t.daemon = True
            threads.append(t)
            t.start()
        if settings.get("Number") == 'loop':
            input("Running... Press Enter to end")
    else:
        runHit()
    

if __name__ == "__main__":
        gucci_main()



