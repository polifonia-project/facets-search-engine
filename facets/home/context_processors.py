def mycontext(request):
    globalvariables = {
        "sitename": "FACETS",
        "longname": "FACETS search engine"
    }
    return {'globalvariables': globalvariables}
