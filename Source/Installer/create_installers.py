#!/usr/bin/python

import re
import subprocess
import os
from shutil import copy2
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
                ["Max_Clients", "62", "Maximum Client Connections", "The maximum number of client connections at one time.\nAfter that it will force others to wait.\nIf 'None' is specified, there will be no set maximum.", r"^((\d+)|(None))$"],
                ["Client_Port", "18181", "Client Port", "The port that the Broker will use to listen for Client connections.", r"^\d{3,5}$"],
                ["Agent_Port", "18182", "Agent Port", "The port that the Broker will use to listen for Agent connections.", r"^\d{3,5}$"],
                ["Use_Agents", "True", "Use Agents", "This should be True, it allows Agents to connect to the Server.", r"^((True)|(False))$"],
                ["SSL_Priv_Key", "privkey.pem", "Broker Private Key", "The Name of the Sever's Private Key for ssl authentication.\nIt should be 'None' or a filename ending in '.pem'\nIf this is set to 'None', then SSL will not be used.", r"^((\w+.pem)|(None))$"],
                ["SSL_Cert", "cacert.pem", "Broker Self-Signed Certificate", "The Name of the Sever's key certificates for ssl authentication.\nIt should be 'None' or a filename ending in '.pem'\nIf this is set to 'None', then SSL will not be used.", r"^((\w+.pem)|(None))$"],
                ["Database_Addr", "127.0.0.1", "MySQL Server Address", "The address of the MySQL server the Broker and Interface will use.\nIf the Broker and the Database will be installed on the same machine, keep the default.",r""],
                ["Database_Port", "3306", "MySQL Port", "The port number that the MySQL server runs on.", r"^\d{3,5}$"],
                ["Database_Usr", "CABS", "MySQL Username", "The username for the Broker to access the MySQL database.\nThis should be changed from the default value, and kept private.", r"^\w+$"],
                ["Database_Pass", "BACS", "MySQL Password", "The password for the Broker to access the MySQL password.\nThis should be changed from the default value, and kept private.", r"^\w+$"],
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
                #Broker Installation
                ["Create_Database", "False", "Create a new Database on Broker Machine", "If this is 'True' then the Broker installer will create a database for it and the interface to use.", r"^((True)|(False))$"],
                ["Broker_Distro", "Debian", "Linux Distribution", "If you are using this installer, you must use: Debian (or something close).", r"^Debian$"],
                #Interface Installation
                ["Interface_Group", "", "Admin Group", "The LDAP or Active Directory group that can access the Interface", r""],
                ["Create_Server", "True", "Create New Apache Webserver", "Create a new apache2 webserver from script, installing all the proper components.\nIf this is False, the installer will just give you a Django application folder.", r"^((True)|(False))$"],
                ["Interface_Distro", "Debian", "Linux Distribution", "If you are using this installer, you must use: Debian (or something close).", r"^Debian$"],
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
                ["Directory", "/CABS/", "Install Directory", "The Agent's default install directory.\nThis can be changed during Agent Install.", r""],
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
                        (self.finds("Broker_Distro"),self.finds("Max_Clients"),self.finds("Client_Port"),self.finds("Agent_Port"),self.finds("SSL_Priv_Key"),self.finds("SSL_Cert"),self.finds("RGS_Ver_Min"),self.finds("Verbose_Out"),self.finds("Create_Database")),
                        
                        (self.finds("Database_Addr"),self.finds("Database_Port"),self.finds("Database_Usr"),self.finds("Database_Pass"),self.finds("Database_Name")),

                        (self.finds("Use_Agents"),self.finds("Reserve_Time"),self.finds("Timeout_Time"),self.finds("Use_Blacklist"),self.finds("Auto_Blacklist"),self.finds("Auto_Max")),

                        (self.finds("Auth_Server"),self.finds("Auth_Prefix"),self.finds("Auth_Postfix"),self.finds("Auth_Base"),self.finds("Auth_Usr_Attr"),self.finds("Auth_Grp_Attr")),
                        
                        (self.finds("Log_Amount"),self.finds("Log_Keep"),self.finds("Log_Time")),
                        )
        elif which == "Interface":
            settings = (
                        (self.finds("Create_Server"),self.finds("Interface_Distro")),
                        
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
                        (self.finds("Interval"),self.finds("Hostname"),self.finds("Directory")),
                        )
        elif which == "Agent_Linux":
            settings = (
                        (self.finds("Interval"),self.finds("Hostname"),self.finds("Directory")),
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
                confstring += "##{varname}\n".format(varname=item[2])
                for line in item[3].split('\n'):
                    confstring += "#{infoline}\n".format(infoline=line)
                confstring += "{variable}:\t{value}\n\n".format(variable=item[0], value=item[1])
        return confstring

########### INSTALL  ############
def Server(settingsobj):
    #The server installer script has to apt-get install python, python-twisted, python-ldap, python-mysqldb, pyOpenSSl
    #It also might have to install mysql
    #this function makes the ca-certificates and priv key to go with it, and puts cacert in Shared
    #openssl req -x509 -nodes -newkey res:2048 -keyout privkey.pen -out cacert.pem -days 24800
    pass

def Interface(settingsobj):
    #The Interface install script has to install django, and install apache, and set it all up, this is a tough one 
    pass

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
    #move the .exe, the .ico, the Header.png, the cacerts.pem
    copy2(base+"/Source/Client/build/win_client/CABS_client.exe", base+"/Install_CABS_Windows_Client/CABS_client.exe")
    copy2(base+"/Source/Client/build/win_client/Icon.ico", base+"/Install_CABS_Windows_Client/Icon.ico")
    copy2(base+"/Source/Client/Header.png", base+"/Install_CABS_Windows_Client/Header.png")
    sslcert = settingsobj.finds("SSL_Cert")[1]
    if sslcert != "None" and  os.path.isfile(base+"/Source/Shared/"+sslcert):
        copy2(base+"/Source/Shared/"+sslcert, base+"/Install_CABS_Windows_Client/"+sslcert)
    

def Client_Linux(settingsobj):
    #This function makes the .conf, and moves all teh stuff into a nice tar.bz with a install script, and a readme
    pass

def Agent_Windows(settingsobj):
    #This function makes the .conf, and moves all the stuff into a nice zipped file with an installer and a readme
    pass

def Agent_Linux(settingsobj):
    #This function makes the .conf, and moves all teh stuff into a nice tar.bz with a install script, and a readme
    pass

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
                return newvalue
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
