#!/usr/bin/python

## CABS_Server.py
# This is the webserver that is at the center of the CABS system.
# It is asynchronous, and as such the callbacks and function flow can be a bit confusing
# The basic idea is that the HandleAgentFactory and HandleClienFactory make new HandleAgents and Handle Clients
# There is one per connection, and it processes all communication on that connection, without blocking


from twisted.internet.protocol import Factory, Protocol
from twisted.internet import ssl, reactor, endpoints, defer, task
from twisted.protocols.basic import LineOnlyReceiver
from twisted.protocols.policies import TimeoutMixin
from twisted.enterprise import adbapi
from twisted.names import client
from twisted.python import log

import ldap
import sys
import logging
import random
import os

from time import sleep

#global settings dictionary
settings = {}
#global database pool
dbpool = adbapi.ConnectionPool
#global blacklist set
blacklist = set()
#make a logger
logger=logging.getLogger()

random.seed()


## Handles each Agent connection
class HandleAgent(LineOnlyReceiver, TimeoutMixin):
    def __init__(self, factory):
        self.factory = factory
        #timeout after 9 seconds
        self.setTimeout(9)
    
    def connectionMade(self):
        self.agentAddr = self.transport.getPeer()
        logger.debug('Connection made with {0}'.format(self.agentAddr))
        self.factory.numConnections = self.factory.numConnections + 1   
        logger.debug('There are {0} Agent connections'.format(self.factory.numConnections))

    def connectionLost(self, reason):
        logger.debug('Connection lost with {0} due to {1}'.format(self.agentAddr,reason))
        self.factory.numConnections = self.factory.numConnections - 1       
        logger.debug('There are {0} Agent connections'.format(self.factory.numConnections))

    def lineLengthExceeded(self, line):
        logger.error('Agent at {0} exceeded the Line Length'.format(self.agentAddr))
        self.transport.abortConnection()

    def lineReceived(self, line):
        #types of reports = status report (sr) and status process report (spr)
        report = line.split(':')
        if report[0] == 'sr' or report[0] == 'spr':
            status = None
            if report[0] == 'spr':
                status = report.pop(1)
                if status.endswith('-1'):
                    status = status.rstrip('-1') + ' : Unknown'
                elif status.endswith('0'):
                    status = status.rstrip('0') + ' : Not Found'
                elif status.endswith('1'):
                    status = status.rstrip('1') + ' : Not Running'
                elif status.endswith('2'):
                    status = status.rstrip('2') + ' : Not Connected'
                elif status.endswith('3'):
                    status = status.rstrip('3') + ' : Okay'

                logger.debug("The process on {0} is {1}".format(report[1], status))

            logger.debug('There are {0} users on {1}'.format(len(report)-2, report[1]))
            #Mark the machine as active, and update timestamp
            querystring = "UPDATE machines SET active = True, last_heartbeat = NOW(), status = %s WHERE machine = %s"
            r1 = dbpool.runQuery(querystring, (status, report[1]))
            #confirm any users that reserved the machine if they are there, or unconfirm them if they are not
            #For now we don't support assigning multiple users per machine, so only one should be on at a time
            #but, if we do have multiple, let it be so
            #Try to write an entry under the first listed users name, if duplicate machine update the old entry to confirmed
            users = ''
            if len(report) > 2:
                for item in range(2, len(report)):
                    users += report[item] + ', '
                users = users[0:-2]
                logger.info("Machine {0} reports user {1}".format(report[1],users))
                regexstr = ''
                for item in range(2, len(report)):
                    regexstr += '(^'
                    regexstr += report[item]
                    regexstr += '$)|'
                regexstr = regexstr[0:-1]
                if settings.get("One_Connection") == 'True' or settings.get("One_Connection") == True:
                    querystring = "INSERT INTO current VALUES (%s, NULL, %s, True, NOW()) ON DUPLICATE KEY UPDATE confirmed = True, connecttime = Now(), user = %s"
                    r2 = dbpool.runQuery(querystring,(report[2],report[1],users))
                querystring = "UPDATE current SET confirmed = True, connecttime = Now() WHERE (machine = %s AND user REGEXP %s)"
                r2 = dbpool.runQuery(querystring,(report[1],regexstr))
            else:
                querystring = "DELETE FROM current WHERE machine = %s"
                r2 = dbpool.runQuery(querystring, (report[1],))

## Creates a HandleAgent for each connection
class HandleAgentFactory(Factory):
    
    def __init__(self):
        self.numConnections = 0
    
    def buildProtocol(self, addr):
        #Blacklist check here
        if addr.host in blacklist:
            logger.debug("Blacklisted address {0} tried to connect".format(addr.host))
            protocol = DoNothing()
            protocol.factory = self
            return protocol
        
        #limit connection number here
        if (settings.get("Max_Agents") is not None and settings.get("Max_Agents") != 'None') and (int(self.numConnections) >= int(settings.get("Max_Agents"))):
            logger.warning("Reached maximum Agent connections")
            protocol = DoNothing()
            protocol.factory = self
            return protocol
        return HandleAgent(self)

## Handles each Client Connection
class HandleClient(LineOnlyReceiver, TimeoutMixin):
    def __init__(self, factory):
        self.factory = factory
        self.setTimeout(9)#set timeout of 9 seconds
    
    def connectionMade(self):
        #if auto then add to blacklist
        self.clientAddr = self.transport.getPeer()
        logger.debug('Connection made with {0}'.format(self.clientAddr))
        self.factory.numConnections = self.factory.numConnections + 1
        logger.debug('There are {0} Client connections'.format(self.factory.numConnections))
    
    def connectionLost(self, reason):
        logger.debug('Connection lost with {0} due to {1}'.format(self.clientAddr,reason))
        self.factory.numConnections = self.factory.numConnections - 1
        logger.debug('There are {0} Client connections'.format(self.factory.numConnections))

    def lineLengthExceeded(self, line):
        logger.error('Client at {0} exceeded the Line Length'.format(self.clientAddr))
        self.transport.abortConnection()

    def lineReceived(self, line):
        #We can receieve 2 types of lines from a client, pool request (pr), machine request(mr)
        request = line.split(':')
        if request[0].startswith('pr'):
            if request[0].endswith('v') and settings.get('RGS_Ver_Min') != 'False':
                #check version
                print "###################################" + settings.get('RGS_Ver_Min')
                logger.debug('User {0} at {1} is using RGS {2}'.format(request[1], self.clientAddr, request[-1]))
                if request[-1] < settings.get('RGS_Ver_Min'):
                    self.transport.write("Err:Sorry, your RGS reciever is out of date, it should be at least {0}".format(settings.get('RGS_Ver_Min')))
                    self.transport.loseConnection()
            logger.info('User {0} requested pool info from {1}'.format(request[1],self.clientAddr))
            #authenticate_user
            #get pools for user
            try:
                self.getAuthLDAP(request[1],request[2]).addCallback(self.writePools)
            except:
                logger.debug("Could not get Pools")
                self.transport.write("Err:Could not authenticate to authentication server")
                self.transport.loseConnection()
        elif request[0] == 'mr':
            logger.info('User {0} requested a machine in pool {1} from {2}'.format(request[1],request[3],self.clientAddr))
            if (request[3] is not None) and (request[3] != ''):
                #check authentication and get machine for the user
                try:
                    deferredtouple = self.getAuthLDAP(request[1],request[2],request[3])
                    deferredtouple[0].addCallback(self.checkSeat,deferredtouple[1],request[1],request[3])
                except:
                    logger.debug("Could not get a machine")
                    self.transport.abortConnection()
                
    ## called after getAuthLDAP
    # Checks the return to see if the user had previously had a machine
    # then gives the user a new machine (or their old one) through writeMachine
    def checkSeat(self, previousmachine, deferredmachine, user, pool):
        #Give user machine
        if len(previousmachine) == 0:
            deferredmachine.addBoth(self.writeMachine, user, pool, False)
        else:
            self.writeMachine(previousmachine, user, pool, True)

    ## Writes a machine to the user, if none are availible, calls getSecondary
    def writeMachine(self, machines, user, pool, restored, secondary=False):
        if restored:
            stringmachine = random.choice(machines)[0]  
            logger.info("Restored machine {0} in pool {1} to {2}".format(stringmachine, pool, user))
            self.transport.write(stringmachine)
            self.transport.loseConnection()
            
        elif len(machines) == 0:
            #check secondary pools here
            if not secondary:
                self.getSecondary(pool).addBoth(self.getSecondaryMachines, user, pool)
            else:
                logger.info("Could not find an open machine in {0} or its secondaries".format(pool))
                self.transport.write("Err:Sorry, There are no open machines in {0}.".format(pool))
                self.transport.loseConnection()
        else:
            stringmachine = random.choice(machines)[0]  
            #write to database to reserve machine
            self.reserveMachine(user, pool, stringmachine).addBoth(self.verifyReserve, user, pool, stringmachine)
    
    ## Makes sure we can assign that machine, if all went well, we give them the machine
    # This is needed so we make sure we have set aside the machine before we give it to the Client
    def verifyReserve(self, error, user, pool, machine):
        #if we get an error, then we had a collision, so give them another machine
        if error:
            #don't send anything, client will try again a few times
            logger.warning("Tried to reserve machine {0} but was unable".format(machine))
            self.transport.write("Err:RETRY")
            self.transport.loseConnection()
        else:
            logger.info("Gave machine {0} in pool {1} to {2}".format(machine, pool, user))
            self.transport.write(machine)
            self.transport.loseConnection()

    ## Sends the SQL request to reserve the machine for the user
    def reserveMachine(self, user, pool, machine):
        opstring = "INSERT INTO current VALUES (%s, %s, %s, False, CURRENT_TIMESTAMP)"
        logger.debug("Reserving {0} in pool {1} for {2}".format(machine, pool, user))
        return dbpool.runQuery(opstring, (user, pool, machine))
    
    ## Sends the list of pools accesable to the user
    def writePools(self, listpools):
        logger.debug("Sending {0} to {1}".format(listpools, self.clientAddr))
        for item in listpools:
            self.transport.write(str(item))
            self.transport.write("\n")
        self.transport.loseConnection()
    
    ## Attempts to authenticate the user to the LDAP server via their username and password
    # Returns a touple of deffereds to getPreviousSession and getMachine
    def getAuthLDAP(self, user, password, requestedpool = None):
        auth = True
        groups = []
        pools = {}
        if (settings.get("Auth_Server") is None) or (settings.get("Auth_Server") == 'None'):
            #Don't try to authenticate, just give back the list of pools
            auth = False
        else:
            Server = settings.get("Auth_Server")
            if Server.startswith("AUTO"):
                logger.warning("A user tried to Authenticate before a LDAP server could be found")
                raise ReferenceError("No AUTO Authentication Server yet")
            if not Server.startswith("ldap"):
                Server = "ldap://" + Server
            DN = settings.get("Auth_Prefix") + user + settings.get("Auth_Postfix")
            Base = settings.get("Auth_Base")
            Scope = ldap.SCOPE_SUBTREE
            Attrs = [ settings.get("Auth_Grp_Attr") ]
            UsrAttr = settings.get("Auth_Usr_Attr")
            
            logger.debug("Attempting to Autenticate to {0} as {1}".format(Server, DN))
            
            try:
                if settings.get("Auth_Secure") == 'True':
                    if settings.get("Auth_Cert") != 'None' and settings.get("Auth_Cert") is not None:
                        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.get("Auth_Cert"))
                        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
                    else:
                        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                l = ldap.initialize(Server)
                l.set_option(ldap.OPT_REFERRALS,0)
                l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
                if settings.get("Auth_Secure") == 'True':
                    try:
                        l.start_tls_s()
                    except Exception as e:
                        logger.error("Could not start a TLS connection to the server at {0} with the certificate {1}".format(Server, settings.get("Auth_Cert")))
                        logger.debug("error = {0}".format(e))
                        return
                l.bind_s(DN, password, ldap.AUTH_SIMPLE)
                r = l.search(Base, Scope, UsrAttr + '=' + user, Attrs)
                result = l.result(r,9)      
                logger.debug("Sucessfully returned {0}".format(result))
                try:
                    l.unbind()
                except:
                    pass
            except:
                logger.warning("User {0} was unable to authenticate.".format(user))
                return
    
            #get user groups
            AttrsDict = result[1][0][1]
            for key in AttrsDict:
                for x in AttrsDict[key]:
                    #take only the substring after the first =, and before the comma
                    groups.append(x[x.find('=')+1:x.find(',')])
            logger.debug("User {0} belongs to {1}".format(user, groups))
        
        if requestedpool == None:
            #pool request, give list of user available
            return self.getPools(groups, auth)
        else:
            #machine request
            #returned touple of (deferred from getprevsession, deferred from getmachine)
            return (self.getPreviousSession(user,requestedpool), self.getMachine(groups, auth, requestedpool))
    
    ## Runs the SQL to see if the user already has a machine checked out
    def getPreviousSession(self, user, requestedpool):
        #only find a previous machine if it had been in the same pool, and confirmed
        querystring = "SELECT machine FROM current WHERE (user = %s AND name = %s AND confirmed = True)"
        return dbpool.runQuery(querystring, (user, requestedpool))
    
    ## Runs the SQL to get machines the user could use
    def getMachine(self, groups, auth, requestedpool):
        r = defer.Deferred
        if auth and (len(groups) > 0):
            regexstring = ""
            for group in groups:
                regexstring += "(.*"
                regexstring += group
                regexstring += ".*)|"
            regexstring = regexstring[0:-1]
            querystring = "SELECT machines.machine FROM machines INNER JOIN pools ON pools.name = machines.name WHERE ((machines.machine NOT IN (SELECT machine FROM current)) AND (active = True) AND (status = 'Okay') AND (pools.name = %s) AND (groups IS NULL OR groups REGEXP %s) AND (machines.deactivated = False) AND (pools.deactivated = False))"
            r = dbpool.runQuery(querystring, (requestedpool, regexstring))
        else:
            querystring = "SELECT machines.machine FROM machines INNER JOIN pools ON pools.name = machines.name WHERE ((machines.machine NOT IN (SELECT machine FROM current)) AND (active = True) AND (status = 'Okay') AND (pools.name = %s) AND (groups IS NULL) AND (machines.deactivated = False) AND (pools.deactivated = False))"
            r = dbpool.runQuery(querystring, (requestedpool,))
        return r
    
    ## finds a pools secondary pools
    def getSecondary(self, requestedpool):
        #get secondary pools for this pool
        querystring = "SELECT secondary FROM pools WHERE name=%s"
        return dbpool.runQuery(querystring, (requestedpool,))

    ## gets machines in a secondary pool
    def getSecondaryMachines(self, pools, user, originalpool):
        #parse secondary pools and do a machine request
        if pools[0][0] is not None:
            args = tuple(pools[0][0].split(','))
        else:
            args = None
        querystring = "SELECT machines.machine FROM machines INNER JOIN pools ON pools.name = machines.name WHERE ((machines.machine NOT IN (SELECT machine FROM current)) AND (active = True) AND (machines.deactivated = False) AND (pools.deactivated = False) AND ((pools.name = %s)"
        if args is not None:
            for pool in args:
                querystring += " OR (pools.name = %s)"
        querystring += "))"
        args = (originalpool,) + (args if args is not None else ())
        r = dbpool.runQuery(querystring, args)
        r.addBoth(self.writeMachine, user, originalpool, False, True)

    ## runs the SQL to see what pools the user can access
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
            r = dbpool.runQuery("SELECT name, description FROM pools WHERE (deactivated = False AND (groups IS NULL OR groups REGEXP %s))",(regexstring,))
        else:
            r = dbpool.runQuery("SELECT name, description FROM pools WHERE (groups IS NULL AND deactivated = False)")
        return r    

#class PauseAndStoreTransport(Protocol):
#   def makeConnection(self, transport):
#       transport.pauseProducting()
#       self.factory.addPausedTransport(self, transport)

## A place to direct blacklisted addresses, or if we have too many connections at once
class DoNothing(Protocol):
    def makeConnection(self, transport):
        transport.abortConnection()

## creates a HandleClient for each Client connection
class HandleClientFactory(Factory):
    
    def __init__(self):
        self.numConnections = 0
        self.transports = []
    
    def buildProtocol(self, addr):
        #Blacklist check here
        if addr.host in blacklist:
            logger.debug("Blacklisted address {0} tried to connect".format(addr.host))
            protocol = DoNothing()
            protocol.factory = self
            return protocol
        
        #limit connection number here
        if (settings.get("Max_Clients") is not None and settings.get("Max_Clients") != 'None') and (int(self.numConnections) >= int(settings.get("Max_Clients"))):
            logger.warning("Reached maximum Client connections")
            protocol = DoNothing()
            protocol.factory = self
            return protocol
        return HandleClient(self)

##This might not be needed in this case, I might implement it later if it helps speed.
##For now, let's just let Clients try to reconnect a few times after a few seconds
#   def addPausedTransport(originalProtocol, transport):
#       self.transports.append((originalProtocol,transport))
#   
#   def oneConnectionDisconnected(self): 
#       if (settings.get("Max_Clients") is not None and settings.get("Max_Clients") != 'None') and (int(self.numConnections) < int(settings.get("Max_Clients"))):
#           originalProtocol, transport = self.transports.pop(0)
#           newProtocol = self.buildProtocol(address)
#
#           originalProtocol.dataReceived = newProtocol.dataReceived
#           originalProtocol.connectionLost = newProtocol.connectionLost
#           
#           newProtocol.makeConnection(transport)
#           transport.resumeProducing()

## Checks the machines table for inactive machines, and sets them as so
# Called periodically
def checkMachines():
    logger.debug("Checking Machines")
    #check for inactive machines
    if (settings.get("Timeout_time") is not None) or (settings.get("Timeout_time") != 'None'):
        querystring = "UPDATE machines SET active = False, status = NULL WHERE last_heartbeat < DATE_SUB(NOW(), INTERVAL %s SECOND)"
        r1 = dbpool.runQuery(querystring, (settings.get("Timeout_Time"),))
    
    #check for reserved machines without confirmation
    #querystring = "DELETE FROM current WHERE (confirmed = False AND connecttime < DATE_SUB(NOW(), INTERVAL %s SECOND))"
    querystring = "DELETE FROM current WHERE (connecttime < DATE_SUB(NOW(), INTERVAL %s SECOND))"
    r2 = dbpool.runQuery(querystring, (settings.get("Reserve_Time"),))

## Gets the blacklist from the database, and updates is
def cacheBlacklist():
    logger.debug("Cacheing the Blacklist")
    querystring = "SELECT blacklist.address FROM blacklist LEFT JOIN whitelist ON blacklist.address = whitelist.address WHERE (banned = True AND whitelist.address IS NULL)"
    r = dbpool.runQuery(querystring)
    r.addBoth(setBlacklist)

## Sets the blacklist variable, given data from the Database
def setBlacklist(data):
    global blacklist
    blacklist = set()
    logger.debug("Blacklist:")
    for item in data:
        blacklist.add(item[0])
        logger.debug(item[0])

## Chooses a LDAP/Active Directory server
def setAuthServer(results):
    results = results[0]
    if not results[0].payload.target:
        logger.error("Could not find LDAP server from AUTO")
    else:
        logger.debug("Found AUTO authentication servers : {0}".format(', '.join(str(x.payload.target) for x in results)))
        logger.info("Using LDAP server {0}".format(str(results[0].payload.target)))
        settings["Auth_Server"] = str(results[0].payload.target)

## Does a DNS service request for an LDAP service
def getAuthServer():
    logger.debug("Getting LDAP server from AUTO")
    domain = settings.get("Auth_Auto").replace('AUTO', '', 1)
    domain = '_ldap._tcp' + domain
    resolver = client.Resolver('/etc/resolv.conf')
    d = resolver.lookupService(domain)
    d.addCallback(setAuthServer)

## Reads the configuration file
def readConfigFile():
    #open the .conf file and return the variables as a dictionary
    global settings
    filelocation = os.path.dirname(os.path.abspath(__file__)) + "/CABS_server.conf"
    with open(filelocation, 'r') as f:
        for line in f:
            line = line.strip()
            if (not line.startswith('#')) and line:
                try:
                    (key,val) = line.split(':\t',1)
                except:
                    print "Warning : Check .conf syntax for {0}".format(line)
                    try:
                        (key,val) = line.split(None,1)
                        key = key[:-1]
                    except:
                        key = line
                        key = key.strip()
                        key = key[:-1]
                        val = ''
                settings[key] = val
        f.close()
    
    #insert default settings for all not specified
    if not settings.get("Max_Clients"):
        settings["Max_Clients"] = '62'
    if not settings.get("Max_Agents"):
        settings["Max_Agents"] = '120'
    if not settings.get("Client_Port"):
        settings["Client_Port"] = '18181'
    if not settings.get("Agent_Port"):
        settings["Agent_Port"] = '18182'
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
        settings["Reserve_Time"] = '360'
    if not settings.get("Timeout_Time"):
        settings["Timeout_Time"] = '540'
    if not settings.get("Use_Blacklist"):
        settings["Use_Blacklist"] = 'False'
    if not settings.get("Auto_Blacklist"):
        settings["Auto_Blacklist"] = 'False'
    if not settings.get("Auto_Max"):
        settings["Auto_Max"] = '300'
    if not settings.get("Auth_Server"):
        settings["Auth_Server"] = 'None'
    if not settings.get("Auth_Prefix"):
        settings["Auth_Prefix"] = ''
    if not settings.get("Auth_Postfix"):
        settings["Auth_Postfix"] = ''
    if not settings.get("Auth_Base"):
        settings["Auth_Base"] = 'None'
    if not settings.get("Auth_Usr_Attr"):
        settings["Auth_Usr_Attr"] = 'None'
    if not settings.get("Auth_Grp_Attr"):
        settings["Auth_Grp_Attr"] = 'None'
    if not settings.get("Auth_Secure"):
        settings["Auth_Secure"] = 'False'
    if not settings.get("Auth_Cert"):
        settings["Auth_Cert"] = 'None'
    if not settings.get("SSL_Priv_Key"):
        settings["SSL_Priv_Key"] = 'None'
    if not settings.get("SSL_Cert"):
        settings["SSL_Cert"] = 'None'
    if not settings.get("RGS_Ver_Min"):
        settings["RGS_Ver_Min"] = 'False'
    if not settings.get("Verbose_Out"):
        settings["Verbose_Out"] = 'False'
    if not settings.get("Log_Amount"):
        settings["Log_Amount"] = '4'
    if not settings.get("Log_Keep"):
        settings["Log_Keep"] = '500'
    if not settings.get("Log_Time"):
        settings["Log_Time"] = '1800'
    if not settings.get("One_Connection"):
        settings["One_Connection"] = 'True'

## gets additional settings overrides from the Database
def readDatabaseSettings():
    #This needs to be a "blocked" call to ensure order, it can't be asynchronous.
    querystring = "SELECT * FROM settings"
    con = dbpool.connect()
    cursor = con.cursor()
    cursor.execute(querystring)
    data = cursor.fetchall()

    global settings
    for rule in data:
        settings[str(rule[0])] = rule[1]
    
    cursor.close()
    dbpool.disconnect(con)

    con = dbpool.connect()
    cursor = con.cursor()
    querystring = "UPDATE settings SET applied = True"
    cursor.execute(querystring)
    data = cursor.fetchall()
    cursor.close()
    con.commit()
    dbpool.disconnect(con)

## See if we need to restart because Database settings have changed
def checkSettingsChanged():
    querystring = "select COUNT(*) FROM settings WHERE (applied = False OR applied IS NULL)"
    r = dbpool.runQuery(querystring)
    r.addBoth(getSettingsChanged)

## Sees the result from checkSettingsChanged, and acts accordingly
def getSettingsChanged(data):
    if int(data[0][0]) > 0:
        logger.error("Interface settings had changed... Restarting the Server")
        reactor.stop()
        #should probably sleep here for a few seconds?
        os.execv(__file__, sys.argv)

## A logging.Handler class for writing out log to the Database
class MySQLHandler(logging.Handler):
    #This is our logger to the Database, it will handle out logger calls
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        querystring = "INSERT INTO log VALUES(NOW(), %s, %s, DEFAULT)"
        r = dbpool.runQuery(querystring, (str(record.getMessage()), record.levelname))

## Makes sure the log doesn't grow too big, removes execess
def pruneLog():
    querystring = "DELETE FROM log WHERE id <= (SELECT id FROM (SELECT id FROM log ORDER BY id DESC LIMIT 1 OFFSET %s)foo )"
    r = dbpool.runQuery(querystring, (int(settings.get("Log_Keep")),))

## Starts the logging
def setLogging():
    global logger
    loglevel = int(settings.get("Log_Amount"))
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
    logger.setLevel(loglevel)
    
    if settings.get("Verbose_Out") == 'True':
        logger.addHandler(logging.StreamHandler(sys.stdout))
    
    logger.addHandler(MySQLHandler())
    
    logger.info("Server Settings:")
    for key in settings:
        if not key.endswith("Pass"):
            logger.info("{0} = {1}".format(key, settings.get(key)))

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
    
    
    #get override settings from the database, then start logger
    readDatabaseSettings()
    #SetLogging
    setLogging()
    
    #Create Client Listening Server
    if (settings.get("SSL_Priv_Key") is None) or (settings.get("SSL_Priv_Key") == 'None') or (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
        serverstring = "tcp:" + str(settings.get("Client_Port"))    
        endpoints.serverFromString(reactor, serverstring).listen(HandleClientFactory())
    else:
        serverstring = "ssl:" + str(settings.get("Client_Port")) + ":privateKey=" + settings.get("SSL_Priv_Key") + ":certKey=" + settings.get("SSL_Cert")
        endpoints.serverFromString(reactor, serverstring).listen(HandleClientFactory())

    logger.warning("Starting Client Server {0}".format(serverstring))
    
    #Set up Agents listening
    if (settings.get("Use_Agents") == 'True'):
        #Use Agents, so start the listening server
        if (settings.get("SSL_Priv_Key") is None) or (settings.get("SSL_Priv_Key") == 'None') or (settings.get("SSL_Cert") is None) or (settings.get("SSL_Cert") == 'None'):
            agentserverstring = "tcp:" + str(settings.get("Agent_Port"))    
            endpoints.serverFromString(reactor, agentserverstring).listen(HandleAgentFactory())
        else:
            agentserverstring = "ssl:" + str(settings.get("Agent_Port")) + ":privateKey=" + settings.get("SSL_Priv_Key") + ":certKey=" + settings.get("SSL_Cert")
            endpoints.serverFromString(reactor, agentserverstring).listen(HandleAgentFactory())
    
        logger.warning("Starting Agent Server {0}".format(agentserverstring))
        #Check Machine status every 1/2 Reserve_Time
        checkup = task.LoopingCall(checkMachines)
        checkup.start( int(settings.get("Reserve_Time"))/2 )
    else:
        #this to do so things kinda work without agents
        querystring = "UPDATE machines SET active = True, status = 'Okay'"
        r1 = dbpool.runQuery(querystring)
    
    #resolve LDAP server
    if settings.get("Auth_Server").startswith("AUTO"):
        settings["Auth_Auto"] = settings.get("Auth_Server")
        resolveldap = task.LoopingCall(getAuthServer)
        #Get the LDAP server every 2 hours
        resolveldap.start(7200)

    #Start Blacklist cacheing
    if settings.get("Use_Blacklist") == 'True':
        getblacklist = task.LoopingCall(cacheBlacklist)
        #refresh blacklist every 15 minutes
        getblacklist.start(900)
    #Start Pruning log
    if int(settings.get("Log_Amount")) != 0:
        prune = task.LoopingCall(pruneLog)
        prune.start(int(settings.get("Log_Time")))

    #Check the online settings every 9 minutes, and restart if they changed
    checksettingschange = task.LoopingCall(checkSettingsChanged)
    checksettingschange.start(540)

    #Start Everything
    reactor.run()


if __name__ == "__main__":
    main()


