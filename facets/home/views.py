from django.shortcuts import render

from django.http import HttpResponse

def index(request):
    template = loader.get_template('home/index.html')
    context = {}
    return HttpResponse(template.render(context, request))


# def LoadDataView(request):
    # return HttpResponse("Load a single music score or zip, with instruction displayed")

# def OverviewDataView(request):
    # return HttpResponse("Overview of data currently available for search")

# def MusicDocView(request):
    # return HttpResponse("Display music doc without search result")

# def SearchView(request):
    # return HttpResponse("Search with keyboard, abc text etc")

# """
# def MainView(request):
    # return HttpResponse("A combo of SearchView and LoadDataView?")
# """
# def SearchResultView(request):
    # return HttpResponse("Display search result and perhaps kibana analysis")

# def HighlightMusicDocView(request):
    # return HttpResponse("Display music doc with highlighted search result")
