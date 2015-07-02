#!/usr/bin/python
import os
import random
import string

settings = {}

def readConfigFile():
    #open the .conf file and return the variables as a dictionary
    global settings
    filelocation = os.path.dirname(os.path.abspath(__file__)) + '/interface_install.conf'
    with open(filelocation, 'r') as f:
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
                settings[key] = val 
        f.close()

def generateKey():
    chars = string.ascii_uppercase + string.lowercase + string.digits + "!=%-+^"
    return ''.join(random.SystemRandom().choice(chars) for _ in range(50))

def createDjangoSettings():
    key = generateKey()
    output_string = ""
    output_string += """
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '{security_key}'
""".format(security_key=key)

    output_string += """
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'stream_to_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django_auth_ldap': {
            'handlers': ['stream_to_console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
"""

    output_string += """
ALLOWED_HOSTS = [{host_list}]

SESSION_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SECURE = True

# Django-auth-ldap
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
)
import ldap
from django_auth_ldap.config import LDAPSearch, MemberDNGroupType
""".format(host_list=settings.get("Interface_Host_Addr"))
    if settings.get("Auth_Secure") == 'True':
        output_string += """
#LDAP over TLS
AUTH_LDAP_GLOBAL_OPTIONS = {
"""
        if settings.get("Auth_Cert") != 'None' and settings.get("Auth_Cert") is not None:
            output_string += """
    ldap.OPT_X_TLS_CACERTFILE: "/var/www/CABS_interface/{auth_cert}",
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_DEMAND,
""".format(settings.get("Auth_Cert"))
        else:
            output_string += """
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
"""
        output_string += """
}
AUTH_LDAP_START_TLS = True
"""

    output_string += """
AUTH_LDAP_USER_DN_TEMPLATE = "{auth_prefix}%(user)s{auth_postfix}"
AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = True
AUTH_LDAP_SERVER_URI = "ldap://{auth_server}"
""".format(auth_prefix=settings.get("Auth_Prefix"), auth_postfix=settings.get("Auth_Postfix"), auth_server=settings.get("Auth_Server"))

    output_string += """
AUTH_LDAP_CONNECTION_OPTIONS = {
    ldap.OPT_REFERRALS: 0,
}
"""

    output_string += """
AUTH_LDAP_USER_SEARCH = LDAPSearch("{auth_base}", ldap.SCOPE_SUBTREE, "({auth_user_attr}=%(user)s)")

AUTH_LDAP_GROUP_TYPE = MemberDNGroupType('member')
AUTH_LDAP_GROUP_SEARCH = LDAPSearch('{auth_base}', ldap.SCOPE_SUBTREE)
AUTH_LDAP_REQUIRE_GROUP = "{auth_allowed_group}"
""".format(auth_base=settings.get("Auth_Base"), auth_user_attr=settings.get("Auth_Usr_Attr"), auth_allowed_group=settings.get("Interface_Group"))

    output_string += """
LOGIN_URL = "cabs_admin:index"
LOGIN_REDIRECT_URL = 'cabs_admin:index'

# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cabs_admin'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'admin_tools.urls'

WSGI_APPLICATION = 'admin_tools.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'djangoweb',
"""

    output_string += """
            'USER': '{db_user}',
            'PASSWORD': '{db_password}',
            'HOST': '{db_host}',
            'PORT': '{db_port}',
""".format(db_user=settings.get("Database_Usr"), db_password=settings.get("Database_Pass"), db_host=settings.get("Database_Addr"), db_port=settings.get("Database_Port"))

    output_string += """
    },
    'cabs': {
        'ENGINE':'django.db.backends.mysql',
"""

    output_string += """
        'NAME': '{db_name}',
            'USER': '{db_user}',
            'PASSWORD': '{db_password}',
            'HOST': '{db_host}',
            'PORT': '{db_port}',
""".format(db_name=settings.get("Database_Name"), db_user=settings.get("Database_Usr"), db_password=settings.get("Database_Pass"), db_host=settings.get("Database_Addr"), db_port=settings.get("Database_Port"))
   
    output_string += """
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = '/var/www/CABS_interface/static/'
STATIC_URL = '/static/'

#A patch to make django-auth-ldap work with Active Directory with direct bind
from django_auth_ldap import backend

def monkey(self, password):
    if self.dn is None:
        raise self.AuthenticationFailed("failed to map the username to a DN.")
    try:
        sticky = self.settings.BIND_AS_AUTHENTICATING_USER
        self._bind_as(self.dn, password, sticky=sticky)
        #MonkeyPatch:
        if sticky and self.settings.USER_SEARCH:
            self._search_for_user_dn()
        #Patched
    except ldap.INVALID_CREDENTIALS:
        raise self.AuthenticationFailed("user DN/password rejected by LDAP server.")

backend._LDAPUser._authenticate_user_dn = monkey
""" 
    
    #output to settings
    base = os.path.dirname(os.path.realpath(__file__))
    with open(base+"/settings.py", 'w') as f:
        f.write(output_string)
    
def createApacheSettings():
    output_string = ""
    output_string += """
<VirtualHost *:80>
    RewriteEngine On
    RewriteCond %{SERVER_PORT} !^443$
    RewriteRule (.*) https://cabs.et.byu.edu/$1 [QSA,NC,R,L]
    
    #WSGIDaemonProcess CABS_interface python-path=/var/www/CABS_interface:/var/www/CABS_interface/env/lib/python2.7/site-packages
    #WSGIProcessGroup CABS_interface
    #WSGIScriptAlias / /var/www/CABS_interface/admin_tools/wsgi.py

    #DocumentRoot /var/www/html

    #ErrorLog ${APACHE_LOG_DIR}/error.log
    #CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>

<VirtualHost *:443>
    WSGIDaemonProcess CABS_interface python-path=/var/www/CABS_interface:/var/www/CABS_interface/env/lib/python2.7/site-packages
    WSGIProcessGroup CABS_interface
    WSGIScriptAlias / /var/www/CABS_interface/admin_tools/wsgi.py
    
    SSLEngine On
"""

    output_string += """
    SSLCertificateKeyFile /var/www/CABS_interface/{privkey}
    SSLCertificateFile /var/www/CABS_interface/{cert}
""".format(privkey=settings.get("SSL_Priv_Key"), cert=settings.get("SSL_Cert"))

    output_string += """
    
    DocumentRoot /var/www/html

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
"""
    #output to 000-default.conf
    base = os.path.dirname(os.path.realpath(__file__))
    with open(base+"/000-default.conf", 'w') as f:
        f.write(output_string)

def main():
    readConfigFile()
    createDjangoSettings()
    createApacheSettings()

if __name__== "__main__":
    main()
