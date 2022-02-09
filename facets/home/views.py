from django.shortcuts import render

from django.http import HttpResponse

def SearchView(request):
    return HttpResponse("FACETS")