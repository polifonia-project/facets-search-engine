from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from elasticsearch import Elasticsearch

# Create your views here.

def index(request):
    template = loader.get_template('search/index.html')
    context = {}
    return HttpResponse(template.render(context, request))

def results(request):
    # print("result view called")
    if request.method == 'POST':
        try:
            pattern = request.POST.get('pattern', False)
            if pattern:
                print(pattern)
                results = {}
                for i in range(10):
                    results[str(i)] = "res" + str(i+1)
        except TypeError:
            print("wrong input")
    template = loader.get_template('search/results.html')
    context = {"pattern": pattern, "results": results}
    return HttpResponse(template.render(context, request))
