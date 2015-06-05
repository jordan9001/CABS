#!/usr/bin/python

import re
try:
    import curses
    tui = True
except:
    tui = False
#This is a installer creater, having the main directory downloaded, it can create a system according to your choosen settings.
#Is is for unix, but can create Windows installers
#It uses curses, to look cool

########### PACKAGE #############

########### TUI PAGES ###########
def settings_screen(choice):
    #read default settings
    settingsgroups = ((["Group1Setting 1", "value1", "G1Tag1", "Must say \"Jordan is Awesome\"", r"^Jordan is Awesome$"],["Group2Setting 2", "value2", "G1Tag2", "Any whole number", r"^\d$"]),(["Group2Setting 1", "value1", "G2Tag1", "No space", r"^\w*$"],["Group2Setting 2", "value2", "G2Tag2", "Explination2", "*"]))
    initial = True
    pos = 1
    group = 0
    while(group < len(settingsgroups)):
        if not initial:
            settings = settingsgroups[group]
        else:
            settings = None
        createSettingsScreen(choice.upper(), initial, pos, settings)
        stdscr.refresh()
        c = stdscr.getch()
        if initial:
            #check if they want to use all the defaults
            if c == curses.KEY_DOWN or c == curses.KEY_UP:
                pos = 1 if (pos==0) else 0
            elif c == curses.KEY_ENTER or c == ord(' ') or c == 10 or c == 11 or c == 13:
                if pos==1:
                    pos = 0;
                    initial = False
                else:
                    break;
        else:
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
                elif pos == len(settings):
                    group = group + 1
    
    #queue package to be made for choice
                

def editSetting(setting):
    pos = 0
    regex_error = False
    linepos = 0
    size = stdscr.getmaxyx()
    value = setting[1]
    newvalue = ""
    
    while(True):
        createSettingsScreen(setting[2], False, pos)
        y = 2
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

def createSettingsScreen(title, initial, pos=1, settingsgroup=None):
    title = " "+title+" "
    stdscr.clear()
    size = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(3))
    stdscr.border(' ',' ',' ',' ',' ',' ',' ',' ')
    stdscr.addstr(2, (size[1]/2)-(len(title)/2), title)
    stdscr.attroff(curses.color_pair(3))
    if initial:
        stdscr.addstr((size[0]/2)-1, (size[1]/2)-13, "Use Default Configuration?")
        stdscr.addstr((size[0]/2), (size[1]/2)-7, " USE DEFAULTS ", curses.color_pair(3) if (0==pos) else curses.color_pair(0))
        stdscr.addstr((size[0]/2)+1, (size[1]/2)-7, " SET SETTINGS ", curses.color_pair(3) if (1==pos) else curses.color_pair(0))
    elif settingsgroup is not None:
        #show the list in a scrollable style, with selected one in middle
        ytop = 2
        ybottom = size[0]-6
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
        options = (["Server", False], ["Interface", False], ["Client-Windows", False], ["Client-Linux", False], ["Agent-Windows", False], ["Agent-Linux", False])
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

def setTitle():
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
    for function in options:
        if function[1]:
            settings_screen(function[0])

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
        setTitle()
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
