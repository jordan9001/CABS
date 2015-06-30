#!/usr/bin/python

import re
import subprocess
import os
import zipfile
import tarfile
from contextlib import closing
from shutil import copy2, copytree, rmtree
try:
    import curses
    tui = True
except:
    tui = False
#This is a installer creater, having the main directory downloaded, it can create a system according to your choosen settings.
#Is is for unix, but can create Windows installers
#It uses curses, to look cool
########### SETTINGS ############
class Settings(object):
    #Handles giving out settings, and keeping things consistant.
    s = (
                #Broker or Shared .conf
                ["Max_Clients", "60", "Maximum Client Connections", "The maximum number of client connections at one time.\nAfter that it will force others to wait.\nIf 'None' is specified, there will be no set maximum.", r"^((\d+)|(None))$"],
                ["Max_Agents", "120", "Maximum Agent Connections", "The maximum number of agent connections at one time.\nAfter that it will force others to wait.\nIf 'None' is specified, there will be no set maximum.", r"^((\d+)|(None))$"],
                ["Client_Port", "18181", "Client Port", "The port that the Broker will use to listen for Client connections.", r"^\d{3,5}$"],
                ["Agent_Port", "18182", "Agent Port", "The port that the Broker will use to listen for Agent connections.", r"^\d{3,5}$"],
                ["Use_Agents", "True", "Use Agents", "This should be True, it allows Agents to connect to the Server.", r"^((True)|(False))$"],
                ["SSL_Priv_Key", "privkey.pem", "Broker Private Key", "The Name of the Sever's Private Key for ssl authentication.\nIt should be 'None' or a filename ending in '.pem'\nIf this is set to 'None', then SSL will not be used.", r"^((\w+.pem)|(None))$"],
                ["SSL_Cert", "cacert.pem", "Broker Self-Signed Certificate", "The Name of the Sever's key certificates for ssl authentication.\nIt should be 'None' or a filename ending in '.pem'\nIf this is set to 'None', then SSL will not be used.", r"^((\w+.pem)|(None))$"],
                ["Database_Addr", "127.0.0.1", "MySQL Server Address", "The address of the MySQL server the Broker and Interface will use.\nIf the Broker and the Database will be installed on the same machine, keep the default.",r""],
                ["Database_Port", "3306", "MySQL Port", "The port number that the MySQL server runs on.", r"^\d{3,5}$"],
                ["Database_Usr", "CABS", "MySQL Username", "The username for the Broker to access the MySQL database.\nThis should be changed from the default value, and kept private.", r"^\w+$"],
                ["Database_Pass", "BACS", "MySQL Password", "The password for the Broker to access the MySQL password.\nThis should be changed from the default value, and kept private.", r"^.+$"],
                ["Database_Name", "test", "Database Name", "The CABS Database name on the MySQL server that the Broker will access.", r"^\w+$"],
                ["Reserve_Time", "360", "Machine Reserve Time", "The amount of time, that the Broker will keep a machine reserved.\nThis must be longer than the Agent's Interval, usually by 2 or 3 times.\nThis value is in seconds.", r"^\d{2,9}$"],
                ["Timeout_Time", "540", "Machine Timeout Time", "The time the Broker will wait until it marks a machine as inactive.\nThis must be longer that Reserve Time.\nThis is in seconds.", r"^\d{2,9}$"],
                ["Use_Blacklist", "True", "Use The Blacklist", "Refuse to connect with the addresses in the Blacklist.\n'True' or 'False'", r"^((True)|(False))$"],
                ["Auto_Blacklist", "False", "Automatically Blacklist", "Automatically add addresses to the Blacklist if too many connections per minute.", r"^((True)|(False))$"],
                ["Auto_Max", "300", "Maximum Connections per Minute", "Applies if Auto Blacklist is True.\nThe number of times in a minute an address can connect before being blacklisted.", r"^\d+$"],
                ["Auth_Server", "None", "Authentication Server", "An LDAP or Active Directory server address.\nIf 'None' is specified, then no authentication will be required.", r""],
                ["Auth_Prefix", "", "Distinguished Name prefix", "The prefix before the username inorder to build the DN.\nFor Active Directory you might want something like 'DOMAIN\\'\nFor LDAP you may want something like 'cn='", r""],
                ["Auth_Postfix", "", "Distinguished Name postfix", "The postfix after the username inorder to build the DN.\nFor Active Directory you might want something like '@mysite.org'\nFor LDAP you might want something like ',ou=accounts,dc=mysite,dc=org'", r""],
                ["Auth_Base", "None", "Request Base", "The Base for the LDAP or Active Directory request.\nUsually something like 'dc=mysite,dc=org'", r""],
                ["Auth_Usr_Attr", "None", "User Attribute", "The LDAP or Active Directory user attribute.", r""],
                ["Auth_Grp_Attr", "None", "Group Attribute", "The LDAP or Active Direcory group attribute.", r""],
                ["RGS_Ver_Min", "False", "RGS Minimum Version", "The earliest RGS version that can connect.\nIf you are not using RGS, put 'False'", r"^((False)|(\d+.\d+.\d+))$"],
                ["Verbose_Out", "False", "Output to Screen", "Output not only to the log, but also to stdout.", r"^((True)|(False))$"],
                ["Log_Amount", "3", "Verbosity Level", "The amount written out to the log database.\nA number from 0(none) to 4(highest).", r"^\d$"],
                ["Log_Keep", "600", "Log History Limit", "The number of Log items to keep in history after pruning.", r"^\d+"],
                ["Log_Time", "1800", "Log Prune Interval", "How long between deleting excess off of the Log, in seconds.", r"^\d+"],
                ["One_Connection", "True", "One Connection per Machine", "True if the machines with the Agents can only handle one remote connection.", r"^((True)|(False))$"],
                #Broker Installation
                ["#Broker_Distro", "Debian", "Linux Distribution", "If you are using this installer, you must use: Debian (or something close).", r"^Debian$"],
                ["#Create_SSL_Keys", "True", "Create a new SSL private key and certificate.", "If this is 'True', this script will create a new SSL private key and SSL certificate.\nNote, OpenSSL must be installed for this option.", r"^((True)|(False))$"],
                ["#Cou_Name", "US", "Country Name", "The Country name for the SSL certificate", r"^[^/]{,2}$"],
                ["#Org_Name", "", "Organization Name", "The Organization name for the SSL certificate", r"^[^/]*$"],
                ["#Com_Name", "CABS_Server", "The Server's Name", "The Common name for the SSL certificate, usually the server name.", r"^[^/]+$"],
                #Interface Installation
                ["Interface_Group", "", "Admin Group", "The LDAP or Active Directory group that can access the Interface\nThis should be the whole identifier line.\nSomething like: cn=group,ou=our groups,ou=departments,dc=example,dc=com", r""],
                ["Create_Server", "False", "Create New Apache Webserver", "Create a new apache2 webserver from script, installing all the proper components.\nIf this is False, the installer will just give you the Django application.\nIt is recommended you set up your own server.", r"^((True)|(False))$"],
                ["Interface_Distro", "Debian", "Linux Distribution", "If you are using this installer, you must use: Debian (or something close).", r"^Debian$"],
                ["Interface_Host_Addr", "", "Interface Host Addresses", "The allowed hosts (website names) for your Interface.\nSeparate addresses with a space\nPut * for all hosts (insecure).", r""],
                #Client or Shared .conf
                ["Host_Addr", "localhost", "Broker Address", "The network address for the Broker.", r""],
                ["Net_Domain", "", "The Network Domain", "The domain for your network.\nLeave this blank if your machines are on many networks.", r""],
                ["Command-Win", "", "Client Command", "The command that will be run by the client when it receives an address.\nIf use RGS is true, this does nothing.\nTo following variables are available: {user} {address} {password} and {port}\nExample: C:\PuTTY\putty.exe -ssh {user{@{address} -pw {password}\nThis can be changed during Client Install.", r""],
                ["Command-Lin", "", "Client Command", "The command that will be run by the client when it receives an address.\nIf use RGS is true, this does nothing.\nTo following variables are available: {user} {address} {password} and {port}\nExample: C:\PuTTY\putty.exe -ssh {user{@{address} -pw {password}\nThis can be changed during Client Install.", r""],
                ["RGS_Options", "True", "Use RGS", "Have CABS Client run an RGS connection.", r"^((True)|(False))$"],
                ["RGS_Location", "/opt/hpremote/rgreceiver/rgreceiver.sh", "The RGS executable fullpath", "This should be the full pathname to rgreceiver.sh or rgreceiver.exe\nThis only matters if Use RGS is True", r""],
                ["RGS_Version", "False", "Check RGS Version", "Have the Client send in the RGS version number to the Broker, to make sure it is up to date.", r"^((True)|(False))$"],
                #Agent .conf
                ["Interval", "120", "Heartbeat Interval", "How often the Agent reports to the Server in seconds.\nMust be less than Broker's Reserve_Time.", r"^\d+$"],
                ["Hostname", "None", "Fixed Hostname", "The Agent Machine's Hostname.\nIf 'None' then the hostname will be determined by the Agent.\nThis can be changed during Agent Install.", r""],
                #["Directory-Win", "\\Program Files\\CABS\\Agent\\", "Install Directory", "The Agent's default install directory.\nYou probably shouldn't change this.", r""],
                #["Directory-Lin", "/usr/lib/cabs/agent/", "Install Directory", "The Agent's default install directory.\nYou probably shouldn't change this.", r""],
            )
    def finds(self, var_name):
        for item in self.s:
            if item[0] == var_name:
                return item
        raise Exception

    def getSettings(self, which):
        #Returns settings in: settings( group( setting[var_name, default, tag, description, regex],),)
        if which == "Server":
            settings = (
                        (self.finds("#Broker_Distro"),self.finds("Max_Clients"),self.finds("Max_Agents"),self.finds("Client_Port"),self.finds("Agent_Port"),self.finds("SSL_Priv_Key"),self.finds("SSL_Cert"),self.finds("RGS_Ver_Min"),self.finds("Verbose_Out")),
                        
                        (self.finds("Database_Addr"),self.finds("Database_Port"),self.finds("Database_Usr"),self.finds("Database_Pass"),self.finds("Database_Name")),

                        (self.finds("Use_Agents"),self.finds("Reserve_Time"),self.finds("Timeout_Time"),self.finds("Use_Blacklist"),self.finds("Auto_Blacklist"),self.finds("Auto_Max"),self.finds("One_Connection")),

                        (self.finds("Auth_Server"),self.finds("Auth_Prefix"),self.finds("Auth_Postfix"),self.finds("Auth_Base"),self.finds("Auth_Usr_Attr"),self.finds("Auth_Grp_Attr")),
                        
                        (self.finds("Log_Amount"),self.finds("Log_Keep"),self.finds("Log_Time")),
                        
                        (self.finds("#Create_SSL_Keys"),self.finds("#Cou_Name"),self.finds("#Org_Name"),self.finds("#Com_Name")),
                        )
        elif which == "Interface":
            settings = (
                        (self.finds("Create_Server"),self.finds("Interface_Distro"),self.finds("Interface_Host_Addr"),self.finds("SSL_Priv_Key"),self.finds("SSL_Cert")),
                        
                        (self.finds("Database_Addr"),self.finds("Database_Port"),self.finds("Database_Usr"),self.finds("Database_Pass"),self.finds("Database_Name")),
                        
                        (self.finds("Auth_Server"),self.finds("Auth_Prefix"),self.finds("Auth_Postfix"),self.finds("Auth_Base"),self.finds("Auth_Usr_Attr"),self.finds("Auth_Grp_Attr"), self.finds("Interface_Group")),
                        )
        elif which == "Client_Windows":
            settings = (
                        (self.finds("Host_Addr"),self.finds("Net_Domain"),self.finds("Client_Port"),self.finds("SSL_Cert")),
                        
                        (self.finds("Command-Win"),self.finds("RGS_Options"),self.finds("RGS_Location"),self.finds("RGS_Version")),
                        )
        elif which == "Client_Linux":
            settings = (
                        (self.finds("Host_Addr"),self.finds("Net_Domain"),self.finds("Client_Port"),self.finds("SSL_Cert")),
                        
                        (self.finds("Command-Lin"),self.finds("RGS_Options"),self.finds("RGS_Location"),self.finds("RGS_Version")),
                        )
        elif which == "Agent_Windows":
            settings = (
                        (self.finds("SSL_Cert"),self.finds("Host_Addr"),self.finds("Agent_Port")),
                        
                        (self.finds("Interval"),self.finds("Hostname")),
                        )
        elif which == "Agent_Linux":
            settings = (
                        (self.finds("SSL_Cert"),self.finds("Host_Addr"),self.finds("Agent_Port")),
                        
                        (self.finds("Interval"),self.finds("Hostname")),
                        )
        else:
            raise Exception
        
        return settings
    
    def setSettings(self, changedItems):
        for item in changedItems:
            for original in self.s:
                if item[0] == original[0]:
                    original[1] = item[1]
    
    def createConf(self, choice):
        #create a string of the configuration
        settings = self.getSettings(choice)
        confstring = "##The settings file for CABS (Connection Automation/Brokerage System)\n#Automatically generated by CABS Installer\n"
        confstring +="#For the CABS {0}\n".format(choice)
        confstring +="#Syntax requires Variable_Name separated by from the value with ':\\t' (colon and a tab)\n"
        
        for group in settings:
            confstring += "\n### ### ###\n"
            for item in group:
                if item[0].startswith('#'):
                    continue
                confstring += "##{varname}\n".format(varname=item[2])
                for line in item[3].split('\n'):
                    confstring += "#{infoline}\n".format(infoline=line)
                var = item[0].split('-')[0]
                confstring += "{variable}:\t{value}\n\n".format(variable=var, value=item[1])
        return confstring

########### INSTALL  ############
def Server(settingsobj):
    #The server installer script has to apt-get install python, python-twisted, python-ldap, python-mysqldb, pyOpenSSl
    #It also might have to install mysql
    base = os.path.dirname(os.path.realpath(__file__))
    path = base + "/Install_CABS_Broker"
    
    if not os.path.exists(path):
        os.makedirs(path)
    conf = settingsobj.createConf("Server")
    with open(path+"/CABS_server.conf", 'w') as f:
        f.write(conf)
    #this function makes the ca-certificates and priv key to go with it, and puts cacert in Shared
    if settingsobj.finds("#Create_SSL_Keys")[1] == 'True':
        makeKeys(base, path, settingsobj)
    else:
        #try to move the cacert from shared
        sslcert = settingsobj.finds("SSL_Cert")[1]
        if sslcert != "None" and  os.path.isfile(base+"/Source/Shared/"+sslcert):
            copy2(base+"/Source/Shared/"+sslcert, path+"/"+sslcert)
    #copy the script and the installer scripts
    copy2(base+"/Source/Broker/CABS_server.py",path+"/CABS_server.py")
    copy2(base+"/Source/Broker/build/installer.sh",path+"/installer.sh")
    copy2(base+"/Source/Broker/build/setupDatabase.py",path+"/setupDatabase.py")
    
    zipit(path, "CABS_Server")

def Interface(settingsobj):
    #split allowed hosts
    item = settingsobj.finds("Interface_Host_Addr")
    splitlist = item[1].split()
    formated = "'" + "', '".join(splitlist) + "'"
    item[1] = formated
    settingsobj.setSettings((item,))
    #Create the interface_install.conf
    base = os.path.dirname(os.path.realpath(__file__))
    path = base + "/Install_CABS_Interface"
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    conf = settingsobj.createConf("Interface")
    with open(path+"/interface_install.conf", 'w') as f:
        f.write(conf)
    #move the admin_tools and cabs_admin and installers
    copy2(base+"/Source/Interface/build/interface_install.sh", path+"/interface_install.sh")
    copy2(base+"/Source/Interface/build/createSettings.py", path+"/createSettings.py")
    copytree(base+"/Source/Interface/admin_tools/admin_tools/", path+"/admin_tools/")
    copytree(base+"/Source/Interface/admin_tools/cabs_admin/", path+"/cabs_admin/")
    #copy SSL keys
    sslcert = settingsobj.finds("SSL_Cert")[1]
    if sslcert != "None" and  os.path.isfile(base+"/Source/Shared/"+sslcert):
        copy2(base+"/Source/Shared/"+sslcert, path+"/"+sslcert)
    sslkey = settingsobj.finds("SSL_Priv_Key")[1]
    if sslkey != "None" and  os.path.isfile(base+"/Source/Shared/"+sslkey):
        copy2(base+"/Source/Shared/"+sslkey, path+"/"+sslkey)
    
    zipit(path, "CABS_Interface")

def Client_Windows(settingsobj):
    #This function makes the .conf, and moves all the stuff into a nice zipped file with an installer and a readme
    #create directory
    base = os.path.dirname(os.path.realpath(__file__))
    path = base + "/Install_CABS_Windows_Client"
    
    if not os.path.exists(path):
        os.makedirs(path)
    #write .conf
    conf = settingsobj.createConf("Client_Windows")
    with open(path+"/CABS_client.conf", 'w') as f:
        f.write(conf)
    #move the installer and the cacerts.pem
    copy2(base+"/Source/Client/build/win_client/Install_CABS_Client.exe", path+"/Install_CABS_Client.exe")
    sslcert = settingsobj.finds("SSL_Cert")[1]
    if sslcert != "None" and  os.path.isfile(base+"/Source/Shared/"+sslcert):
        copy2(base+"/Source/Shared/"+sslcert, path+"/"+sslcert)
    
    zipit(path, "CABS_Windows_Client")

def Client_Linux(settingsobj):
    #This function makes the .conf, and moves all the stuff into a nice tar.bz with a install script, and a readme
    #create directory
    base = os.path.dirname(os.path.realpath(__file__))
    path = base + "/Install_CABS_Linux_Client"
    
    if not os.path.exists(path):
        os.makedirs(path)
    #write .conf
    conf = settingsobj.createConf("Client_Linux")
    with open(path+"/CABS_client.conf", 'w') as f:
        f.write(conf)
    #move the installer and the cacerts.pem
    copy2(base+"/Source/Client/build/linux_client/CABS_Client", path+"/CABS_Client")
    copy2(base+"/Source/Client/build/linux_client/install_client.sh", path+"/install_client.sh")
    copy2(base+"/Source/Client/Header.png", path+"/Header.png")
    copy2(base+"/Source/Client/Icon.png", path+"/Icon.png")
    sslcert = settingsobj.finds("SSL_Cert")[1]
    if sslcert != "None" and  os.path.isfile(base+"/Source/Shared/"+sslcert):
        copy2(base+"/Source/Shared/"+sslcert, path+"/"+sslcert)

    tarballit(path, "CABS_Linux_Client")

def Agent_Windows(settingsobj):
    #This function makes the .conf, and moves all the stuff into a nice zipped file with an installer and a readme
    #create directory
    base = os.path.dirname(os.path.realpath(__file__))
    path = base + "/Install_CABS_Windows_Agent"
    
    if not os.path.exists(path):
        os.makedirs(path)
    #write .conf
    conf = settingsobj.createConf("Agent_Windows")
    with open(path+"/CABS_agent.conf", 'w') as f:
        f.write(conf)
    #move the installer and the cacerts.pem
    copy2(base+"/Source/Agent/build/win_agent/Install_CABS_Agent.exe", path+"/Install_CABS_Agent.exe")
    copy2(base+"/Source/Agent/build/win_agent/win_agent_createtask.xml", path+"/win_agent_createtask.xml")
    sslcert = settingsobj.finds("SSL_Cert")[1]
    if sslcert != "None" and  os.path.isfile(base+"/Source/Shared/"+sslcert):
        copy2(base+"/Source/Shared/"+sslcert, path+"/"+sslcert)

    zipit(path, "CABS_Windows_Agent")

def Agent_Linux(settingsobj):
    #This function makes the .conf, and moves all the stuff into a nice tar.bz with a install script, and a readme
    #create directory
    base = os.path.dirname(os.path.realpath(__file__))
    path = base + "/Install_CABS_Linux_Agent"
    
    if not os.path.exists(path):
        os.makedirs(path)
    #write .conf
    conf = settingsobj.createConf("Agent_Linux")
    with open(path+"/CABS_agent.conf", 'w') as f:
        f.write(conf)
    #move the installer and the cacerts.pem
    copy2(base+"/Source/Agent/build/linux_agent/cabsagentd", path+"/cabsagentd")
    copy2(base+"/Source/Agent/build/linux_agent/install_agent.sh", path+"/install_agent.sh")
    copy2(base+"/Source/Agent/build/linux_agent/cabsagent", path+"/cabsagent")
    sslcert = settingsobj.finds("SSL_Cert")[1]
    if sslcert != "None" and  os.path.isfile(base+"/Source/Shared/"+sslcert):
        copy2(base+"/Source/Shared/"+sslcert, path+"/"+sslcert)
    
    tarballit(path, "CABS_Linux_Agent")

########### HELPER #############

def tarballit(path, name):
    with closing(tarfile.open(name+'.tar.bz2', "w:bz2")) as f:
        f.add(path, arcname=os.path.basename(path))
    rmtree(path, True)

def zipit(path, name):
    base_size = os.path.dirname(os.path.realpath(__file__)).count('/')
    
    #create zip
    zipdir = zipfile.ZipFile(name+'.zip', 'w', zipfile.ZIP_STORED)
    #add the stuff
    for root, dirs, files in os.walk(path):
        for item in files:
            fullpath = os.path.join(root,item)
            shortpath = fullpath[fullpath.replace('/', ' ', base_size).find('/')+1:]
            zipdir.write(fullpath, shortpath)
    zipdir.close()
    #remove the original directory
    rmtree(path, True)

def makeKeys(base, path, settingsobj):
    privkey = settingsobj.finds("SSL_Priv_Key")[1]
    cacert = settingsobj.finds("SSL_Cert")[1]
    if privkey == "None" or cacert == "None":
        return
    couname = settingsobj.finds("#Cou_Name")[1]
    orgname = settingsobj.finds("#Org_Name")[1]
    comname = settingsobj.finds("#Com_Name")[1]
    subjstring = ""
    if couname:
        subjstring += "/C="+couname
    if orgname:
        subjstring += "/O="+orgname
    subjstring += "/CN="+comname
    #openssl req -x509 -nodes -newkey rsa:2048 -keyout privkey.pem -out cacert.pem -days 24800 -subj "/C=<Country Name>/ST=<State>/L=<Locality Name>/O=<Organization Name>/CN=<Common Name>"
    command = ["openssl", "req", "-x509", "-nodes", "-newkey", "rsa:2048", "-keyout", privkey, "-out", cacert, "-days", "24800", "-subj", subjstring]
    p = subprocess.Popen(command, cwd=path)
    (out,err) = p.communicate() #block until finished
    copy2(path+"/"+cacert, base+"/Source/Shared/"+cacert)
    copy2(path+"/"+privkey, base+"/Source/Shared/"+privkey)
 
def cleanup(settingsobj):
    #delete shared cacert
    base = os.path.dirname(os.path.realpath(__file__))
    #sslcert = settingsobj.finds("SSL_Cert")[1]
    #nevermind, it is better to leave it for multiple sessions
    #os.remove(base+"/Source/Shared/"+sslcert)

########### TUI PAGES ###########

def settings_screen(choice, settingsobj):
    #read default settings
    settingsgroups = settingsobj.getSettings(choice)
    pos = 1
    group = 0
    changedsettings = ()
    while(group < len(settingsgroups)):
        settings = settingsgroups[group]
        createSettingsScreen(choice.upper(), pos, settings)
        stdscr.refresh()
        c = stdscr.getch()
        #serve up a group of settings
        if c == curses.KEY_UP:
            if pos > 0:
                pos = pos - 1
            else:
                pos = len(settings)
        elif c == curses.KEY_DOWN:
            if pos < len(settings):
                pos = pos + 1
            else:
                pos = 0
        elif c == curses.KEY_ENTER or c == ord(' ') or c == 10 or c == 11 or c == 13:
            if pos < len(settings):
                settingsgroups[group][pos][1] = editSetting(settingsgroups[group][pos])
                changedsettings = changedsettings + (settingsgroups[group][pos],)
            elif pos == len(settings):
                pos = 0;
                group = group + 1
    #return settings to Settings class and your are done!
    settingsobj.setSettings(changedsettings)

def editSetting(setting):
    pos = 0
    regex_error = False
    linepos = 0
    size = stdscr.getmaxyx()
    value = setting[1]
    newvalue = ""
    
    while(True):
        createSettingsScreen(setting[2], pos)
        y = 3
        for line in setting[3].split('\n'):
            stdscr.addstr(y, 3, line)
            y = y+1
        y = y+1
        stdscr.addstr(y, 6, "NEW VALUE : ", curses.color_pair(3) if (pos==0) else curses.color_pair(2))
        stdscr.addstr(y, 18, " "*((size[1]-18)-3), curses.color_pair(2))
        stdscr.addstr(y, 19, (newvalue if (newvalue != "") else value), curses.color_pair(2) if (regex_error == False) else curses.color_pair(4))
        if regex_error:
            stdscr.addstr(y+1, 19, "This is not a valid value", curses.color_pair(1))
        else:
            stdscr.addstr(y+1, (size[1]/2)-2, " OK ", curses.color_pair(3) if (1==pos) else curses.color_pair(0))
        stdscr.addstr(y+2, (size[1]/2)-4, " CANCEL ", curses.color_pair(3) if (2==pos) else curses.color_pair(0))
        if newvalue != "":
            stdscr.addstr(y, linepos+19, newvalue[linepos:linepos+1], curses.color_pair(0))
        #input
        stdscr.refresh()
        curses.echo()
        c = stdscr.getch(y,linepos+19)
        curses.noecho()
        
        if c == curses.KEY_ENTER or c == 10 or c == 11 or c == 13 or (c == ord(' ') and pos != 0):
            if pos == 1 and not regex_error:
                return newvalue.encode('string_escape')
            if pos == 0:
                pos = 1
            else:
                break
        elif c == curses.KEY_UP:
            if pos > 0:
                pos = pos -1
            else:
                pos = 2
        elif c == curses.KEY_DOWN:
            if pos == 2:
                pos = 0
            else:
                pos = pos +1
        elif c == curses.KEY_RIGHT:
            if linepos < len(newvalue):
                linepos = linepos + 1
        elif c== curses.KEY_LEFT:
            if linepos > 0:
                linepos = linepos - 1        
        elif c == curses.KEY_BACKSPACE or c == 8:
            newvalue = newvalue[:-1]
            p = re.compile(setting[4])
            m = p.match( newvalue )
            if m:
                regex_error = False
            else:
                regex_error = True
        else:
            p = re.compile(setting[4])
            try:
                newvalue = newvalue[:linepos] + chr(c) + newvalue[linepos:]
                linepos = linepos + 1
                m = p.match( newvalue )
                if m:
                    regex_error = False
                else:
                    regex_error = True
            except:
                pass

    return value

def createSettingsScreen(title, pos=1, settingsgroup=None):
    title = " "+title+" "
    stdscr.clear()
    size = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(3))
    stdscr.border(' ',' ',' ',' ',' ',' ',' ',' ')
    stdscr.addstr(2, (size[1]/2)-(len(title)/2), title)
    stdscr.attroff(curses.color_pair(3))
    if settingsgroup is not None:
        #show the list in a scrollable style, with selected one in middle
        ytop = 2
        ybottom = size[0]-3
        ctr = size[0]/2
        y = 0
        #show selected lines
        for item in range(0, len(settingsgroup)):
            y = (ctr - ((pos - item)*3))
            if (y < ytop) or (y > ybottom):
                continue
            else:
                if item == pos:
                    stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, 3, settingsgroup[item][2] + ":")
                stdscr.addstr(y +1, 6, settingsgroup[item][1])
                if item == pos:
                    stdscr.attroff(curses.color_pair(3)) 
        #add ok
        if ctr - ((pos - len(settingsgroup))*3) < ybottom:
            stdscr.addstr(y+3, (size[1]/2)-2, " OK ", curses.color_pair(3) if (len(settingsgroup)==pos) else curses.color_pair(0))
    

def header(y_in=1):
    size = stdscr.getmaxyx()
    if size[0] > 16 and size[1] > 26:
        for y in range(y_in,y_in+5):
            for x in range(1,size[1]-2):
                if (x+(2*y))%4 == 0:
                    stdscr.addstr(y, x, "  ", curses.color_pair(3))    
        stdscr.addstr(y_in, (size[1]/2)-13, "    ________   ___  ____  ", curses.color_pair(3))
        y_in = y_in + 1
        stdscr.addstr(y_in, (size[1]/2)-13, "   / ___/ _ | / _ )/ __/  ", curses.color_pair(3)) 
        y_in = y_in + 1
        stdscr.addstr(y_in, (size[1]/2)-13, "  / /__/ __ |/ _  |\ \    ", curses.color_pair(3))
        y_in = y_in + 1
        stdscr.addstr(y_in, (size[1]/2)-13, "  \___/_/ |_/____/___/    ", curses.color_pair(3))
        y_in = y_in + 1
        stdscr.addstr(y_in, (size[1]/2)-13, "                          ", curses.color_pair(3))
        y_in = y_in + 1
    else:
        pass
    return y_in

def title_screen(pos=0,options=None):
    stdscr.clear()
    size = stdscr.getmaxyx()
    y = header(1)
    
    if not options:
        options = (["Server", False], ["Interface", False], ["Client_Windows", False], ["Client_Linux", False], ["Agent_Windows", False], ["Agent_Linux", False])
    stdscr.addstr(y, 1, "Choose which installers to create")
    y = y+1
    stdscr.addstr(y, 1, "(UP/DOWN for navigation, ENTER/SPACE to select)")
    y = y+1
    posstart = y
    for line in options:
        stdscr.addstr(y, 3, ("[+] " if line[1] else "[ ] ")+ line[0], curses.color_pair(3) if ((y-posstart)==pos) else curses.color_pair(0))
        y = y+1
    stdscr.addstr(y, (size[1]/2)-2, " OK ", curses.color_pair(3) if ((y-posstart)==pos) else curses.color_pair(0))
    y = y+1
    stdscr.addstr(y, (size[1]/2)-4, " CANCEL ", curses.color_pair(3) if ((y-posstart)==pos) else curses.color_pair(0))
    stdscr.refresh()
    return options

def endscreen():
    stdscr.clear()
    createSettingsScreen("Done")
    stdscr.getch()

def runInterface():
    pos = 0;
    options = None
    while(True):
        options = title_screen(pos, options)
        c = stdscr.getch()
        if c == curses.KEY_UP:
            if pos > 0:
                pos = pos - 1
            else:
                pos = len(options)+1
        elif c == curses.KEY_DOWN:
            if pos <= len(options):
                pos = pos + 1
            else:
                pos = 0
        elif c == curses.KEY_ENTER or c == ord(' ') or c == 10 or c == 11 or c == 13:
            if pos < len(options):
                options[pos][1] = False if options[pos][1] else True
            elif pos == len(options):
                break
            elif pos == len(options)+1:
                return
    #set settings for all the to be made packages
    settingsobj = Settings()
    for function in options:
        if function[1]:
            settings_screen(function[0], settingsobj)
    #now run the packager/installer creater for each
    for ifunction in options:
        if ifunction[1]:
            globals()[ifunction[0]](settingsobj)
    cleanup(settingsobj)
    endscreen()

def start(screen):
    global stdscr
    stdscr = screen
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    curses.curs_set(0)

def close():
    curses.curs_set(1)
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

def main_tui(screen):
    start(screen)
    error = False
    try:    
        #set color scheme
        curses.init_pair(4,1,7)#pair 4 is red on white (input error)
        curses.init_pair(3,0,3)#pair 3 is black on yellow (highlight/decoration)
        curses.init_pair(2,0,7)#pair 2 is black on white (text input)
        curses.init_pair(1,1,0)#pair 1 is red on black (warning/error)
        runInterface()
    except Exception as e:
        close()
        error = True
        print e
    
    if not error:
        close()

def main():
    pass

if __name__== "__main__":
    if tui:
        curses.wrapper(main_tui)
    else:
        main()
