from django.shortcuts import render

from cabs_admin.models import Machines



def index(request):	
	context = {}
	return render(request, 'cabs_admin/index.html', context)
