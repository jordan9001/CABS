from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from cabs_admin.models import Machines
from cabs_admin.models import Pools
from cabs_admin.models import Settings


def index(request):	
    context = {}
    return render(request, 'cabs_admin/index.html', context)

def machinesPage(request):
    machine_list = Machines.objects.using('cabs').all()
    context = {'section_name': 'Machines', 'machine_list': machine_list}
    return render(request, 'cabs_admin/machines.html', context)

def setMachines(request):
    try: 
        new_name = request.POST['name']
        new_machine = request.POST['machine']
        if (new_machine == '') or (new_name == ''):
            raise KeyError('This value cannot be empty')
    except:
        return HttpResponseRedirect(reverse('cabs_admin:machinesPage'))
    else:
        try:
            s = Machines.objects.using('cabs').get(machine=new_machine)
            s.name = new_name
        except:
            s = Machines(name=new_name, machine=new_machine, active=False, deactivated=False)
        s.save(using='cabs')
        return HttpResponseRedirect(reverse('cabs_admin:machinesPage'))

def toggleMachines(request):
    try:
        choosen_machine = request.POST['machine']
        s = Machines.objects.using('cabs').get(machine=choosen_machine)
        if 'rm' in request.POST:
            s.delete(using='cabs')
        else:
            if s.deactivated:
                s.deactivated = False;
            else:
                s.deactivated = True;
            s.save(using='cabs')
    except:
        return HttpResponseRedirect(reverse('cabs_admin:machinesPage'))
    else:
        return HttpResponseRedirect(reverse('cabs_admin:machinesPage'))

def poolsPage(request):
    pool_list = Pools.objects.using('cabs').all()
    context = {'section_name': 'Pools', 'pool_list': pool_list}
    return render(request, 'cabs_admin/pools.html', context)

def setPools(request):
    try:
        new_pool = request.POST['name']
        new_description = request.POST['description']
        new_secondary = request.POST['secondary']
        new_groups = request.POST['groups']
        if (new_pool == ''):
            raise KeyError('This value cannot be empty')
    except:
        return HttpResponseRedirect(reverse('cabs_admin:poolsPage'))
    else:
        try:
            s = Pools.objects.usint('cabs').get(name = new_pool)
            s.description = new_desc
            s.secondary = new_secondary
            s.groups = new_groups
        except:
            s = Pools(name=new_pool, description=new_description, secondary=new_secondary, groups=new_groups, deactivated=False)
        s.save(using='cabs')
        return HttpResponseRedirect(reverse('cabs_admin:poolsPage'))

def togglePools(request): 
    try:
        choosen_pool = request.POST['pool']
        s = Pools.objects.using('cabs').get(name=choosen_pool)
        if 'rm' in request.POST:
            s.delete(using='cabs')
        else:
            if s.deactivated:
                s.deactivated = False;
            else:
                s.deactivated = True;
            s.save(using='cabs')
    except:
        return HttpResponseRedirect(reverse('cabs_admin:poolsPage'))
    else:
        return HttpResponseRedirect(reverse('cabs_admin:poolsPage'))

def settingsPage(request):
    settings_list = Settings.objects.using('cabs').all()
    try:
        option_choosen = request.GET['setting']
    except:
        option_choosen = None
    context = {'section_name': 'Change Settings', 'settings_list': settings_list, 'option_choosen': option_choosen}
    return render(request, 'cabs_admin/settings.html', context)

def setSettings(request):
    try:
        new_value = request.POST['value']
        new_setting = request.POST['setting']
        if (new_value == '') and (not new_setting.endswith('fix')):
            raise KeyError('This value cannot be empty')
    except:
        return HttpResponseRedirect(reverse('cabs_admin:settingsPage'))
    else:
        try:
            s = Settings.objects.using('cabs').get(setting=new_setting)
            s.value = new_value
        except:
            s = Settings(setting=new_setting, value=new_value)
        s.save(using='cabs')
        return HttpResponseRedirect(reverse('cabs_admin:settingsPage'))

def rmSettings(request):
    try:
        choosen_setting = request.POST['setting']
        s = Settings.objects.using('cabs').get(setting=choosen_setting)
        s.delete(using='cabs')
    except:
        return HttpResponseRedirect(reverse('cabs_admin:settingsPage'))
    else:
        return HttpResponseRedirect(reverse('cabs_admin:settingsPage'))
