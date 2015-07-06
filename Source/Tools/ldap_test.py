#!/usr/bin/python
import ldap
import sys
import os
import time
from getpass import getpass

#global settings dictionary
settings = {}
def getAuthLDAP(user, password):
    Server = settings.get("Auth_Server")
    if not Server.startswith("ldap"):
        Server = "ldap://" + Server
    DN = settings.get("Auth_Prefix") + user + settings.get("Auth_Postfix")
    Base = settings.get("Auth_Base")
    Scope = ldap.SCOPE_SUBTREE
    Attrs = [ settings.get("Auth_Grp_Attr") ]
    UsrAttr = settings.get("Auth_Usr_Attr")
    
    print "Attempting to Autenticate to {0} as {1}".format(Server, DN)
    try:
        if settings.get("Auth_Secure") == 'True':
            if settings.get("Auth_Cert") != 'None' and settings.get("Auth_Cert") is not None:
                print "Using checking against certificate {0} for authentication over TLS".format(settings.get("Auth_Cert"))
                ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, settings.get("Auth_Cert"))
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
                
            else:
                print "Using to authenticate over TLS with no certificate check"
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        l = ldap.initialize(Server, trace_level=(1 if settings.get("Verbose")=='True' else 0))
        l.set_option(ldap.OPT_REFERRALS,0)
        l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        if settings.get("Auth_Secure") == 'True':
            try:
                l.start_tls_s()
            except Exception as e:
                print e
                print "Could not start a TLS connection."
                return
        l.bind_s(DN, password, ldap.AUTH_SIMPLE)
        r = l.search(Base, Scope, UsrAttr + '=' + user, Attrs)
        result = l.result(r,9)      
        print "Sucessfully returned {0}".format(result)
        try:
            l.unbind()
        except:
            pass
    except:
        print "User {0} was unable to authenticate to {1}".format(user, Server)
        return
    #get user groups
    groups = []
    AttrsDict = result[1][0][1]
    for key in AttrsDict:
        for x in AttrsDict[key]:
            #take only the substring after the first =, and before the comma
            groups.append(x[x.find('=')+1:x.find(',')])
    print "User {0} belongs to {1}".format(user, groups)

def splash():
    print "CABS LDAP and Active Directory authentication test\n"

def readConfigFile(filepath):
    #only write if it isn't there already
    global settings
    if not os.path.isfile(filepath):
        print filepath, "is not a file."
        printUsage()
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if (not line.startswith('#')) and line:
                    try:
                        (key,val) = line.split(':\t',1)
                    except:
                        try:
                            (key,val) = line.split(None,1)
                            key = key[:-1]
                        except:
                            key = line
                            key = key.strip()
                            key = key[:-1]
                            val = ''
                    settings.setdefault(key, val)
            f.close()
    except:
        print "Could not open {0}".format(filepath)
        printUsage()

def printUsage(extend=False):
    print "Usage : "+sys.argv[0]+" -u user [-p | -P password] [-f file.conf] [-s -c certfile.pem] [-h host] [-b prefix] [-a postfix] [-x base] [-r user-attribute] [-g group-attribute] [-v]"
    if extend:
        print "  -u username        : the user to authenticate"
        print "  -p                 : prompt for a password"
        print "  -P password        : use password to authenticate the user"
        print "  -f file.conf       : read settings from file.conf, instead of the command line"
        print "  -s                 : attempt to secure the connection with TLS (requires -c)"
        print "  -c certfile.pem    : use certfile.pem as the certificate for the server"
        print "  -h host            : the server's address"
        print "  -b prefix          : a prefix before username to make the DN"
        print "  -a postfix         : a postfix after username to make the DN"
        print "  -x base            : the search base for the request"
        print "  -r user-attribute  : the user attribute"
        print "  -g group-attribute : the member of group attribute"
        print "  -v                 : extra output"
    else:
        print "      : "+sys.argv[0]+" -? for extra info"
    sys.exit()

def setServer(results):
    results = results[0]
    if results[0].payload.target:
        print "Found Servers : ", (', '.join(str(x.payload.target) for x in results))
        print "Using : ", results[0].payload.target
        settings["Auth_Server"] = str(results[0].payload.target)
    else:
        reactor.stop()
        print "Could not find an LDAP server"
        sys.exit()

def stopReactor(_):
    reactor.stop()

def serverLookup(domain):
    global reactor
    try:
        from twisted.names import client
        from twisted.internet import reactor
    except:
        print "AUTO server lookup not supported without Twisted-Python"
        sys.exit()

    domain = domain.replace('AUTO', '', 1)
    domain = '_ldap._tcp' + domain
    resolver = client.Resolver('/etc/resolv.conf')
    d = resolver.lookupService(domain)
    d.addCallback(setServer)
    d.addBoth(stopReactor)
    reactor.run()

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
            elif sys.argv[i] in ['-u', '--user']:
                option = "User"
            elif sys.argv[i] in ['-p', '--prompt', '--pass']:
                settings["Password"] = getpass("Password : ")
            elif sys.argv[i] in ['-P', '--password']:
                option = "Password"
            elif sys.argv[i] in ['-f', '--conf', '--file']:
                option = "Config_File"
            elif sys.argv[i] in ['-s', '--secure']:
                settings["Auth_Secure"] = 'True'
            elif sys.argv[i] in ['-c', '--cert-file', '--cert']:
                option = "Auth_Cert"
            elif sys.argv[i] in ['-h', '--host', '--server']:
                option = "Auth_Server"
            elif sys.argv[i] in ['-b', '--before', '--prefix', '--pre']:
                option = "Auth_Prefix"
            elif sys.argv[i] in ['-a', '--after', '--postfix', '--post']:
                option = "Auth_Postfix"
            elif sys.argv[i] in ['-x', '--base']:
                option = "Auth_Base"
            elif sys.argv[i] in ['-r', '--user-attribute', '--usr-attr', '--user-attr', '--attr']:
                option = "Auth_Usr_Attr"
            elif sys.argv[i] in ['-g', '--group-attribute', '--grp-attr', '--group-attr', '--group', '--grp']:
                option = "Auth_Grp_Attr"
            elif sys.argv[i] in ['-v', '--verbose']:
                settings["Verbose"] = 'True'

    if settings.get("Config_File") is not None:
        readConfigFile(settings.get("Config_File"))
    
    #fill in defaults or fail
    if not settings.get("User"):
        print "Valid username required"
        printUsage()
    if not settings.get("Password"):
        settings["Password"] = ""
    if not settings.get("Auth_Server"):
        print "Valid authentication server required"
        printUsage()
    elif settings.get("Auth_Server").startswith('AUTO'):
        serverLookup(settings.get("Auth_Server"))
    if not settings.get("Auth_Prefix"):
        settings["Auth_Prefix"] = ''
    if not settings.get("Auth_Postfix"):
        settings["Auth_Postfix"] = ''
    if not settings.get("Auth_Base"):
        print "Authenticatin Base required."
        printUsage()
    if not settings.get("Auth_Usr_Attr"):
        settings["Auth_Usr_Attr"] = 'cn'
    if not settings.get("Auth_Grp_Attr"):
        settings["Auth_Grp_Attr"] = 'memberOf'

def main():
    splash()
    getArgs()
    if settings.get("Verbose") == 'True':
        print "Settings : "
        for item in settings:
            if item != "Password":
                print "  {0} = {1}".format(item, settings.get(item))
            else:
                print "  {0} = ******".format(item)
    getAuthLDAP(settings.get("User"), settings.get("Password"))

if __name__ == "__main__":
    main()


