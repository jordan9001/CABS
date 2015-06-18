#!/bin/bash

#run as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root."
    exit
fi

#get script dir
SRCDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#install apache and python
apt-get install -y apache2
apt-get install -y python
apt-get install -y python-pip python-virtualenv
apt-get install python-mysqldb libmysqlclient18 libmysqlclient-dev
sudo apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev

#create an environment and a project
cd /var/www/
mkdir CABS_interface
cd CABS_interface
virtualenv env
source env/bin/activate
pip install django
pip install python-ldap
pip install django_auth_ldap
pip install 
django-admin.py startproject admin_tools .

#configure apache
echo "" > /etc/apache2/mods-enabled/python.load
apt-get install libapache2-mod-wsgi
awk '/VirtualHost \*:80/ { print > ".tempconf"; print "\tWSGIDaemonProcess CABS_interface python-path=/var/www/CABS_interface:/var/www/CABS_interface/env/lib/python2.7/site-packages" >> ".tempconf"; print "\tWSGIProcessGroup CABS_interface" >> ".tempconf"; print "\tWSGIScriptAlias / /var/www/CABS_interface/admin_tools/wsgi.py" >> ".tempconf"; next} {print >> ".tempconf"} 1' /etc/apache2/sites-enabled/000-default.conf
cp .tempconf /etc/apache2/sites-enabled/000-default.conf
rm .tempconf

#remove previous settings and stuff, and any .sqlite3
rm -r admin_tools
rm *.sqlite*

#copy over the stuff we have
cp -r $SRCDIR/admin_tools ./admin_tools
cp -r $SRCDIR/cabs_admin ./cabs_admin

#create the settings file
python $SRCDIR/createSettings.py
cp $SRCDIR/settings.py ./admin_tools/settings.py

#run all migrations
./manage.py makemigrations
./manage.py migrate

service apache2 restart

deactivate
exit
