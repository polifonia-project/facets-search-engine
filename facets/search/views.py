from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader

from elasticsearch import Elasticsearch

# Create your views here.

def index(request):
    template = loader.get_template('search/index.html')
    context = {}
    return HttpResponse(template.render(context, request))

@csrf_exempt
def results(request):
    # print("result view called")
    if request.method == 'POST':
        try:
            pattern = request.POST.get('pattern', False)
            mirror = request.POST.get('mirror', False)
            search_type = request.POST.get('searchtype', False)
            if pattern:
                print(pattern,mirror,search_type)
                results = {}
        except: 
            pass
    template = loader.get_template('search/results.html')
    context = {"pattern": pattern, "results": results}
    return HttpResponse(template.render(context, request))
