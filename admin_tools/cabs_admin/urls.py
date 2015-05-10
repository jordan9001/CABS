from django.conf.urls import patterns, url

from cabs_admin import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^machines/$', views.machinesPage, name='machinesPage'),
    url(r'^machines/submit/$', views.setMachines, name='setMachines'),
    url(r'^machines/toggle/$', views.toggleMachines, name='toggleMachines'),
    url(r'^pools/$', views.poolsPage, name='poolsPage'),
    url(r'^pools/submit/$', views.setPools, name='setPools'),
    url(r'^pools/toggle/$', views.togglePools, name='togglePools'),
    url(r'^settings/$', views.settingsPage, name='settingsPage'),
    url(r'^settings/submit/$', views.setSettings, name='setSettings'),
    url(r'^settings/rm/$', views.rmSettings, name='rmSettings'),
)
