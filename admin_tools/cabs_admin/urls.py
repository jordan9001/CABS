from django.conf.urls import patterns, url

from cabs_admin import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^machines/$', views.machinesPage, name='machinesPage'),
    url(r'^pools/$', views.poolsPage, name='poolsPage'),
)
