#!/usr/bin/python
#This is the test Agent for CABS

import socket, ssl
import sys
import subprocess
from sched import scheduler
from time import time, sleep

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
	else:
		#badbadnotgood
		#Unrecognized OS
		return

def main():
	s = scheduler(time, sleep)
	#read config for time interval, in seconds
	interval = 3
	
	while True:
		s.enter(interval, 1, heartbeat, ())
		s.run()

if __name__ == "__main__":
	main()
