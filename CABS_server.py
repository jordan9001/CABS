#!/usr/bin/python
from twisted.internet.protocol import Factory
from twisted.internet import ssl, reactor, endpoints, defer, task
from twisted.protocols.basic import LineOnlyReceiver
from twisted.enterprise import adbapi

import ldap

import logging
import random

#global settings dictionary
settings = {}
#global database pool
dbpool = adbapi.ConnectionPool
random.seed()


class HandleAgent(LineOnlyReceiver):
	def __init__(self, factory):
		self.factory = factory
	
	def connectionMade(self):
		self.agentAddr = self.transport.getPeer()
		logging.debug('Connection made with {0}'.format(self.agentAddr))
		self.factory.numConnections = self.factory.numConnections + 1	
		logging.debug('There are {0} Agent connections'.format(self.factory.numConnections))

	def connectionLost(self, reason):
		logging.debug('Connection lost with {0} due to {1}'.format(self.agentAddr,reason))
		self.factory.numConnections = self.factory.numConnections - 1		
		logging.debug('There are {0} Agent connections'.format(self.factory.numConnections))

	def lineLengthExceeded(self, line):
		logging.error('Agent at {0} exceeded the Line Length'.format(self.agentAddr))
		self.transport.loseConnection()

	def lineReceived(self, line):
		#types of reports = status report (sr) or login report (lr) or logoff report (fr)
		print "Received " + line #remove this line
		report = line.split(':')
		logging.debug('There are {0} users on {1}'.format(len(report)-2, report[1]))
		if report[0] == 'sr':
			#Mark the machine as active, and update timestamp
			querystring = "UPDATE machines SET active = True WHERE machine = %s"
			r1 = dbpool.runQuery(querystring, (report[1],))
			#confirm any users that reserved the machine if they are there, or unconfirm them if they are not
			#For now we don't support assigning multiple users per machine, so only one should be on at a time
			#but, if we do have multiple, let it be so
			#Try to write an entry under the first listed users name, if duplicate machine update the old entry to confirmed
			users = ''
			if len(report) > 2:
				for item in range(2, len(report)):
					users += report[item] + ', '
				users = users[0:-1]
				logging.debug("Machine {0} reports user {1}".format(report[1],users))
				querystring = "INSERT INTO current VALUES (%s, NULL, %s, True, NOW()) ON DUPLICATE KEY UPDATE confirmed = True"
				r2 = dbpool.runQuery(querystring,(report[2],report[1]))
			else:
				querystring = "DELETE FROM current WHERE machine = %s"
				r2 = dbpool.runQuery(querystring, (report[1],))


class HandleAgentFactory(Factory):
	
	def __init__(self):
		self.numConnections = 0
	
	def buildProtocol(self, addr):
		return HandleAgent(self)


class HandleClient(LineOnlyReceiver):
	def __init__(self, factory):
		self.factory = factory
	
	def connectionMade(self):
		self.clientAddr = self.transport.getPeer()
		logging.debug('Connection made with {0}'.format(self.clientAddr))
		self.factory.numConnections = self.factory.numConnections + 1
		logging.debug('There are {0} Client connections'.format(self.factory.numConnections))
	
	def connectionLost(self, reason):
		logging.debug('Connection lost with {0} due to {1}'.format(self.clientAddr,reason))
		self.factory.numConnections = self.factory.numConnections - 1		
		logging.debug('There are {0} Client connections'.format(self.factory.numConnections))

	def lineLengthExceeded(self, line):
		logging.error('Client at {0} exceeded the Line Length'.format(self.clientAddr))
		self.transport.loseConnection()

	def lineReceived(self, line):
		#warning, this logging line will write out passwords in the log
		#logging.debug('{0} sent : {1}'.format(self.clientAddr, line))
		
		#We can receieve 2 types of lines from a client, pool request (pr), machine request(mr)
		request = line.split(':')
		if request[0] == 'pr':
			logging.info('User {0} requested pool info from {1}'.format(request[1],self.clientAddr))
			#authenticate_user
			#get pools for user
			try:
				self.getAuthLDAP(request[1],request[2]).addCallback(self.writePools)
			except:
				logging.debug("Could not get Pools")
				self.transport.loseConnection()
		elif request[0] == 'mr':
			logging.info('User {0} requested a machine in pool {1} from {2}'.format(request[1],request[3],self.clientAddr))
			#check authentication
			#get machine for the user
			try:
				deferredtouple = self.getAuthLDAP(request[1],request[2],request[3])
				deferredtouple[0].addCallback(self.checkSeat,deferredtouple[1],request[1],request[3])
			except:
				logging.debug("Could not get a machine")
				self.transport.loseConnection()
				

	def checkSeat(self, previousmachine, deferredmachine, user, pool):
		#Give user machine
		if len(previousmachine) == 0:
			deferredmachine.addCallback(self.writeMachine, user, pool, False)
		else:
			self.writeMachine(previousmachine, user, pool, True)

	def writeMachine(self, machines, user, pool, restored):
		if len(machines) == 0:
			self.transport.write("Err:No Availible Machines")
			self.transport.loseConnection()
		else:
			stringmachine = random.choice(machines)[0]	
			if not restored:
				#write to database to reserve machine
				self.reserveMachine(user, pool, stringmachine).addBoth(self.verifyReserve, user, pool, stringmachine)
			else:
				logging.info("Restored machine {0} in pool {1} to {2}".format(stringmachine, pool, user))
				self.transport.write(stringmachine)
				self.transport.loseConnection()

	def verifyReserve(self, error, user, pool, machine):
		#if we get an error, then we had a collision, so give them another machine
		if error:
			#don't send anything, client will try again a few times
			logging.warning("Tried to reserve machine {0} but was unable".format(machine))
			self.transport.loseConnection()
		else:
			logging.info("Gave machine {0} in pool {1} to {2}".format(machine, pool, user))
			self.transport.write(machine)
			self.transport.loseConnection()

	def reserveMachine(self, user, pool, machine):
		opstring = "INSERT INTO current VALUES (%s, %s, %s, False, CURRENT_TIMESTAMP)"
		logging.debug("Reserving {0} in pool {1} for {2}".format(machine, pool, user))
		return dbpool.runQuery(opstring, (user, pool, machine))

	def writePools(self, listpools):
		logging.debug("Sending {0} to {1}".format(listpools, self.clientAddr))
		for item in listpools:
			self.transport.write(str(item))
			self.transport.write("\n")
		self.transport.loseConnection()
	
	def getAuthLDAP(self, user, password, requestedpool = None):
		auth = True
		groups = []
		pools = {}
		if (settings.get("Auth_Server") is None) or (settings.get("Auth_Server") == 'None'):
			#Don't try to authenticate, just give back the list of pools
			auth = False
		else:
			Server = "ldap://" + settings.get("Auth_Server")
			DN = settings.get("Auth_Prefix") + user + settings.get("Auth_Postfix")
			Base = settings.get("Auth_Base")
			Scope = ldap.SCOPE_SUBTREE
			Attrs = [ settings.get("Auth_Grp_Attr") ]
			UsrAttr = settings.get("Auth_Usr_Attr")
			
			logging.debug("Attempting to Autenticate to {0} as {1}".format(Server, DN))
			
			try:
				l = ldap.initialize(Server)
				l.set_option(ldap.OPT_REFERRALS,0)
				l.bind(DN, password, ldap.AUTH_SIMPLE)
				r = l.search(Base, Scope, UsrAttr + '=' + user, Attrs)
				result = l.result(r,9)		
				logging.debug("Sucessfully returned {0}".format(result))
			except:
				logging.warning("User {0} was unable to authenticate.".format(user))
				return
	
			#get user groups
			AttrsDict = result[1][0][1]
			for key in AttrsDict:
				for x in AttrsDict[key]:
					#take only the substring after the first =, and before the comma
					groups.append(x[x.find('=')+1:x.find(',')])
			logging.debug("User {0} belongs to {1}".format(user, groups))
		
		if requestedpool == None:
			#pool request, give list of user available
			return self.getPools(groups, auth)
		else:
			#machine request
			#returned touple of (deferred from getprevsession, deferred from getmachine)
			return (self.getPreviousSession(user,requestedpool), self.getMachine(groups, auth, requestedpool))
	
	def getPreviousSession(self, user, requestedpool):
		querystring = "SELECT machine FROM current WHERE (user = %s AND name = %s)"
		return dbpool.runQuery(querystring, (user, requestedpool))
	
	def getMachine(self, groups, auth, requestedpool):
		r = defer.Deferred
		if auth and (len(groups) > 0):
			regexstring = ""
			for group in groups:
				regexstring += "(.*"
				regexstring += group
				regexstring += ".*)|"
			regexstring = regexstring[0:-1]
			querystring = "SELECT machines.machine FROM machines INNER JOIN pools ON pools.name = machines.name WHERE ((machines.machine NOT IN (SELECT machine FROM current)) AND (active = True) AND (pools.name = %s) AND (groups IS NULL OR groups REGEXP %s))"
			r = dbpool.runQuery(querystring, (requestedpool, regexstring))
		else:
			querystring = "SELECT machines.machine FROM machines INNER JOIN pools ON pools.name = machines.name WHERE ((machines.machine NOT IN (SELECT machine FROM current)) AND (active = True) AND (pools.name = %s) AND (groups IS NULL))"
			r = dbpool.runQuery(querystring, (requestedpool,))
		return r
	
		
	def getPools(self, groups, auth):
		poolset = set()
		r = defer.Deferred
		if auth and (len(groups) > 0):
			regexstring = ""
			for group in groups:
				regexstring += "(.*"
				regexstring += group
				regexstring += ".*)|"
			regexstring = regexstring[0:-1]
			r = dbpool.runQuery("SELECT name, description FROM pools WHERE (groups IS NULL OR groups REGEXP %s)",(regexstring,))
		else:
			r = dbpool.runQuery("SELECT name, description FROM pools WHERE groups IS NULL")
		return r	

class HandleClientFactory(Factory):
	
	def __init__(self):
		self.numConnections = 0
	
	def buildProtocol(self, addr):
		return HandleClient(self)

def checkMachines():
	logging.debug("Checking Machines")
	#check for inactive machines
	querystring = "UPDATE machines SET active = False  WHERE last_heartbeat < DATE_SUB(NOW(), INTERVAL %s SECOND)"
	r1 = dbpool.runQuery(querystring, (settings.get("Timeout_Time"),))
	
	#check for reserved machines without confirmation
	querystring = "DELETE FROM current WHERE (confirmed = False AND connecttime < DATE_SUB(NOW(), INTERVAL %s SECOND))"
	r2 = dbpool.runQuery(querystring, (settings.get("Reserve_Time"),))

def readConfigFile():
	#open the .conf file and return the variables as a dictionary
	global settings
	with open('CABS_server.conf', 'r') as f:
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
	if not settings.get("Client_Port"):
		settings["Client_Port"] = 18181
	if not settings.get("Agent_Port"):
		settings["Agent_Port"] = 18182
	if not settings.get("Use_Agents"):
		settings["User_Agents"] = 'True'
	if not settings.get("Database_Addr"):
		settings["Database_Addr"] = "127.0.0.1"
	if not settings.get("Database_Port"):
		settings["Database_Port"] = 3306
	if not settings.get("Database_Usr"):
		settings["Database_Usr"] = "CABS"
	if not settings.get("Database_Pass"):
		settings["Database_Pass"] = "BACS"
	if not settings.get("Database_Name"):
		settings["Database_Name"] = "test"
	if not settings.get("Reserve_Time"):
		settings["Reserve_Time"] = 360
	if not settings.get("Timeout_Time"):
		settings["Timeout_Time"] = 540
	if not settings.get("Log_File"):
		settings["Log_File"] = None
	if not settings.get("Log_Level"):
		settings["Log_Level"] = 3
	if not settings.get("Auth_Server"):
		settings["Auth_Server"] = None
	if not settings.get("Auth_Prefix"):
		settings["Auth_Prefix"] = ''
	if not settings.get("Auth_Postfix"):
		settings["Auth_Postfix"] = ''
	if not settings.get("Auth_Base"):
		settings["Auth_Base"] = None
	if not settings.get("Auth_Usr_Attr"):
		settings["Auth_Usr_Attr"] = None
	if not settings.get("Auth_Grp_Attr"):
		settings["Auth_Grp_Attr"] = None
	if not settings.get("SSL_Priv_Key"):
		settings["SSL_Priv_Key"] = None
	if not settings.get("SSL_Cert"):
		settings["SSL_Cert"] = None



def main():
	#Read the settings
	readConfigFile() 
	
	#create database pool
	global dbpool
	dbpool = adbapi.ConnectionPool(
			"MySQLdb",
			db=settings.get("Database_Name"),
			port=int(settings.get("Database_Port")),
			user=settings.get("Database_Usr"),
			passwd=settings.get("Database_Pass"),
			host=settings.get("Database_Addr"),
			cp_reconnect=True
		)
	
	#set logging
	loglevel = settings.get("Log_Level")
	if loglevel <= 0:
		loglevel = logging.CRITICAL
		#For our purposes, CRITICAL means no logging
	elif loglevel == 1:
		loglevel = logging.ERROR
	elif loglevel == 2:
		loglevel = logging.WARNING
	elif loglevel == 3:
		loglevel = logging.INFO
	elif loglevel >= 4:
		loglevel = logging.DEBUG

	if (settings.get("Log_File") is None) or (settings.get("Log_File") == 'None'):
		logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=loglevel)
	else:
		logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', filename=settings.get("Log_File"), level=loglevel)
	logging.debug("Server Settings:")
	for key in settings:
		logging.debug("{0} = {1}".format(key, settings.get(key)))

	#Create Listening Servers
	if (settings.get("SSL_Priv_Key") is None) or (settings.get("SSL_Priv_Key") == 'None') or (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
		serverstring = "tcp:" + str(settings.get("Client_Port"))	
		endpoints.serverFromString(reactor, serverstring).listen(HandleClientFactory())
	else:
		serverstring = "ssl:" + str(settings.get("Client_Port")) + ":privateKey=" + settings.get("SSL_Priv_Key") + ":certKey=" + settings.get("SSL_Cert")
		endpoints.serverFromString(reactor, serverstring).listen(HandleClientFactory())

	logging.info("Starting Client Server {0}".format(serverstring))
	
	if (settings.get("Use_Agents") == 'True'):
		#Use Agents, so start the listening server
		if (settings.get("SSL_Priv_Key") is None) or (settings.get("SSL_Priv_Key") == 'None') or (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
			agentserverstring = "tcp:" + str(settings.get("Agent_Port"))	
			endpoints.serverFromString(reactor, agentserverstring).listen(HandleAgentFactory())
		else:
			agentserverstring = "ssl:" + str(settings.get("Agent_Port")) + ":privateKey=" + settings.get("SSL_Priv_Key") + ":certKey=" + settings.get("SSL_Cert")
			endpoints.serverFromString(reactor, agentserverstring).listen(HandleAgentFactory())
	
		logging.info("Starting Agent Server {0}".format(agentserverstring))
		#Check Machine status every 1/2 Reserve_Time
		checkup = task.LoopingCall(checkMachines)
		checkup.start( int(settings.get("Reserve_Time"))/2 )

	
	#Start Everything
	reactor.run()


if __name__ == "__main__":
	main()

