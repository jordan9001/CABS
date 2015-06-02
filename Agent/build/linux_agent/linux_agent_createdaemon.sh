#!/bin/sh
#
# /etc/init.d/CABSagent
# 
# The agent that keeps in touch with the CABS broker service
# This is the redhat init.d script
#
# chkconfig: 345 93 01
# processname: CABS_agentd
# config: /usr/lib/CABS/CABS_agent.conf autoreload

#Get functions from functions library
. /etc/init.d/functions

PATHTOAGENT=/usr/lib/CABS/CABS_agentd

start() {
    if [ ! -f /var/lock/subsys/CABS_agent ]; then
        echo -n "Starting CABS_agent: "
        daemon $PATHTOAGENT
        ##create lockfile
        touch /var/lock/subsys/CABS_agent
        success "Starting CABS_agent"
    else
        echo -n "Lockfile exists already."
    fi
}

stop() {
    echo -n "Stopping CABS_agent: "
    killproc CABS_agent
    ##delete lockfile
    rm -f /var/lock/subsys/CABS_agent
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
