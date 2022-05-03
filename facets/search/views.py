from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.

def index(request):
    template = loader.get_template('search/index.html')
    context = {}
    return HttpResponse(template.render(context, request))

def results(request):
    print("result view called")
    if request.method == 'POST':
        try:
            pattern = request.POST['pattern']
        except TypeError:
            print("wrong input")
        print(pattern)
    if pattern:
        result = DummyPattern(pattern=pattern)
    template = loader.get_template('search/results.html')
    context = {"pattern": pattern, "result": result}
    return HttpResponse(template.render(context, request))
