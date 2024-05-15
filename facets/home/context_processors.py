def mycontext(request):
    globalvariables = {
        "sitename": "FACETS",
        "longname": "FACETS music collection exploration tool"
    }
    return {'globalvariables': globalvariables}
