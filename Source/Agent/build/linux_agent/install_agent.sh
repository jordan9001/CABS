#!/bin/bash
#This is for Red Hat based systems

if [ "$1" = "-h" ]; then
    echo "usage: $0 <directory>"
    echo "This script installs the CABS Linux Client to <directory>"
    exit 0
fi

SRCDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

if [ -z "$1" ]; then
    read -p "Install Directory : " DIR
else
    DIR=$1
fi

mkdir -m 775 -p $DIR

#copy the files

#add the init script
#chconfig --add --levels 345


