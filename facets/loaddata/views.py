from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.
def loaddataIndex(request):
    template = loader.get_template('loaddata/index.html')
    context = {}
    return HttpResponse(template.render(context, request))
