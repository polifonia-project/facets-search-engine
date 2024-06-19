def mycontext(request):
    globalvariables = {
        "sitename": "FACETS",
        "longname": "Polifonia — FACETS"
    }
    return {'globalvariables': globalvariables}
