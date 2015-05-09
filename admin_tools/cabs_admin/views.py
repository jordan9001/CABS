from django.shortcuts import render

from cabs_admin.models import Machines
from cabs_admin.models import Pools


def index(request):	
    context = {}
    return render(request, 'cabs_admin/index.html', context)

def machinesPage(request):
    machine_list = Machines.objects.using('cabs').all()
    context = {'section_name': 'Machines', 'machine_list': machine_list}
    return render(request, 'cabs_admin/machines.html', context)

def poolsPage(request):
    pool_list = Pools.objects.using('cabs').all()
    context = {'section_name': 'Pools', 'pool_list' : pool_list}
    return render(request, 'cabs_admin/pools.html', context)
