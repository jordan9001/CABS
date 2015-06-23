#!/bin/bash
#This is for Red Hat based systems

if [ "$1" = "-h" ]; then
    echo "This script installs the CABS Linux Client to <directory>"
    exit 0
fi

if [[ $EUID -ne 0 ]]; then
    echo "This scrpt must be run as root"
    exit 0
fi

SRCDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

DIR="/usr/lib/CABS/"

mkdir -m 775 -p $DIR

#copy the files
cp $SRCDIR/CABS_Agent $DIR/CABS_Agent
cp $SRCDIR/CABS_agent.conf $DIR/CABS_agent.conf
cp $SRCDIR/*.pem $DIR/
cp $SRCDIR/CABS_agent_init.sh /etc/init.d/CABS_agent_init.sh

#add the init script
chkconfig --add --levels 345


