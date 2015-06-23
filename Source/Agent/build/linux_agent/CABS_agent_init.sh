#!/bin/sh
#
# /etc/init.d/CABS_agent_init.sh
# 
# The agent that keeps in touch with the CABS broker service
# This is the redhat init.d script
#
# chkconfig: 345 93 01
# processname: CABS_Agent
# config: /usr/lib/CABS/CABS_agent.conf autoreload

#Get functions from functions library
. /etc/init.d/functions

PATHTOAGENT=/usr/lib/CABS/CABS_Agent

start() {
    if [ ! -f /var/lock/subsys/CABS_Agent ]; then
        echo -n "Starting CABS_Agent: "
        daemon $PATHTOAGENT
        ##create lockfile
        touch /var/lock/subsys/CABS_Agent
        success "Starting CABS_Agent"
    else
        echo -n "Lockfile exists already."
    fi
}

stop() {
    echo -n "Stopping CABS_Agent: "
    killproc CABS_Agent
    ##delete lockfile
    rm -f /var/lock/subsys/CABS_Agent
}


case "$1" in
    start)
        start
    ;;
    stop)
        stop
    ;;
    restart|reload)
        stop
        start
    ;;
    *)
        echo -n "Usage: $0 {start|stop|restart|reload}"
        exit 1
esac
exit 0
