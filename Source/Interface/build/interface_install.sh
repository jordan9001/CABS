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
apt-get install -y python-mysqldb libmysqlclient18 libmysqlclient-dev
apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev

#create an environment and a project
cd /var/www/
mkdir CABS_interface
cd CABS_interface
virtualenv env
source env/bin/activate
pip install django
pip install python-ldap
pip install django_auth_ldap
pip install MySQL-python
django-admin.py startproject admin_tools .

#configure apache
echo "" > /etc/apache2/mods-enabled/python.load
apt-get install -y libapache2-mod-wsgi

#remove previous settings and stuff, and any .sqlite3
rm -r admin_tools
rm *.sqlite*

#copy over the stuff we have
cp -r $SRCDIR/admin_tools ./admin_tools
cp -r $SRCDIR/cabs_admin ./cabs_admin

#create the settings files
python $SRCDIR/createSettings.py
cp $SRCDIR/settings.py ./admin_tools/settings.py

mv /etc/apache2/sites-enabled/000-default.conf /etc/apache2/sites-enabled/000-default.conf.old
cp $SRCDIR/000-default.conf.old /etc/apache2/sites-enabled/000-default.conf.old
cp $SRCDIR/*.pem ./

#run all migrations
./manage.py makemigrations
./manage.py migrate

#enable https only
a2enmod rewrite
a2enmod ssl

service apache2 restart

deactivate
exit
