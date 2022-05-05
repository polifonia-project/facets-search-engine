def mycontext(request):
    globalvariables = {
        "sitename": "MuSEEK",
        "longname": "MuSEEK search engine"
    }
    return {'globalvariables': globalvariables}
