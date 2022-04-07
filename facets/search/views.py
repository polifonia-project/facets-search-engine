from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.

def index(request):
    template = loader.get_template('search/index.html')
    context = {}
    return HttpResponse(template.render(context, request))

def post_new(request):
    # form = PostForm()
    # return render(request, 'search/index.html', {'form': form})
    return render(request, 'search/index.html', {})
