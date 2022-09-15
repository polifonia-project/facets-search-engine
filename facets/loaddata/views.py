from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader

from lib.process import ScoreProcessing
from lib.search.IndexWrapper import IndexWrapper

from elasticsearch import Elasticsearch
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

try:
    host = getattr(settings, "ELASTIC_SEARCH", "localhost")["host"]
    es = Elasticsearch(hosts=[
        {'host': host, 'port': settings.ELASTIC_SEARCH["port"]},
        {'host': "FACETS-ES", 'port': 9200},
        {'host': "0.0.0.0", 'port': 9200}
    ])
except:
    print("\n\n******Error connecting to Elasticsearch, please check your if it is running.")

@csrf_exempt
def uploaddata(request):
    template = loader.get_template('loaddata/index.html')
    indices = es.indices.get_alias().keys()
    context = {"indices_names": indices}
    return HttpResponse(template.render(context, request))

@csrf_exempt
def processdata(request):

    template = loader.get_template('loaddata/loaded.html')

    if request.method == "POST":

        # In case the user wants to load more documents later
        indices = es.indices.get_alias().keys()

        # Load the music document
        try:
            uploadrequest = {}
            index_name = request.POST.get('indexname')
            templist = request.FILES["myfile"].name.split(".")
            doc_id = templist[0]
            real_format = templist[1]
            print("index_name, doc_id, format are", index_name, " ",doc_id, " ", real_format)

            uploadrequest["fileformat"] = request.POST.get('fileformat').lower()

            # Check the file format, make sure it is supported.
            allowed_formats = ["abc", "zip", "mei", "xml", "musicxml", "krn"]
            if real_format != uploadrequest["fileformat"]:
                # The real format is not selected format, it will cause problem. Return error page!
                if real_format in allowed_formats:
                    uploadrequest["fileformat"] = real_format
                    print("Wrong file format selected, but it was auto-corrected.")
                else:
                    template = loader.get_template('loaddata/loaderror.html')
                    context = {"indices_names": indices}
                    return HttpResponse(template.render(context, request))

            if real_format not in allowed_formats or (not request.FILES["myfile"]):
                # Not supported, return error page.
                template = loader.get_template('loaddata/loaderror.html')
                context = {"indices_names": indices}
                return HttpResponse(template.render(context, request))

            uploadedfile = request.FILES["myfile"]

            loadedfile = uploadedfile.read()
            
            # Now process and index the file

            if  uploadrequest["fileformat"] == "zip":
                """
                Bulk process and index all music documents from a zip file.
                in the case of loading a zip, "doc_id" from the curl command is just the name of zip file.
                It would not be saved on ES as id, but the name of each file would be considered as id of it.

                """
                try:
                    ScoreProcessing.load_and_process_zip(index_name, loadedfile)
                    context = {"indices_names": indices, "zip_id": doc_id, "index_name": index_name}
                    template = loader.get_template('loaddata/loaded.html')
                    return HttpResponse(template.render(context, request))
                except Exception as ex:
                    template = loader.get_template('loaddata/loaderror.html')
                    return template.render(request)
            else:
                if uploadrequest["fileformat"] != "midi":
                    # Avoid using utf to decode midi, it causes error
                    body_unicode = loadedfile.decode('utf')
                else:
                    # Not supported MIDI yet
                    template = loader.get_template('loaddata/loaderror.html')
                    context = {"indices_names": indices}
                    return HttpResponse(template.render(context, request))

                
                if uploadrequest["fileformat"] == "mei":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/mei" http://localhost:8000/index/index_name/lklk/ -d @data/friuli001.mei
                    In which "index" refers to index_name, and "lklk" refers to doc_id.
                    """
                    # Apply MEI -> Music21 converter
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mei", doc_id)
                
                elif uploadrequest["fileformat"] == "xml":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/xml"
                    http://localhost:8000/index/index_name/couperin/ -d @data/couperin.xml
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "xml", doc_id)
                
                elif uploadrequest["fileformat"]  == "musicxml":
                    """
                    Example 1:
                    curl -X PUT -H "Content-type:application/musicxml" 
                    http://localhost:8000/index/index_name/testmxml/ --data-binary @data/Gas0301f.musicxml 

                    Example 2: 
                    curl -X PUT -H "Content-type:application/vnd.recordare.musicxml+xml" 
                    http://localhost:8000/index/index_name/testmxml/ -d @data/Gas0301f.musicxml

                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "musicxml", doc_id)

                    """
                elif request.content_type == "application/vnd.recordare.musicxml":
                
                    #The recommended media type for a compressed MusicXML file(.mxl) is: application/vnd.recordare.musicxml
                    
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "mxl", doc_id)
                    """
                elif uploadrequest["fileformat"] == "krn":
                    """
                    Kern is not registered as a content type, thus use --data-binary!
                    Example:
                    curl -X PUT -H "Content-type:application/krn" http://localhost:8000/index/index_name/danmark/ --data-binary @data/danmark1.krn
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "krn", doc_id)

                elif uploadrequest["fileformat"] == "abc":
                    """
                    Example:
                    curl -X PUT -H "Content-type:application/abc" http://localhost:8000/index/index_name/abctest/ --data-binary @data/test.abc
                    """
                    m21_score, musicdoc = ScoreProcessing.load_score(index_name, body_unicode, "abc", doc_id)
                else:
                    # Otherwise, the format is not supported.
                    template = loader.get_template('loaddata/loaderror.html')
                    context = {"indices_names": indices}
                    return HttpResponse(template.render(context, request))


                # Process the current score, produce descriptors from MusicSummary
                descr_dict, encodedMS = ScoreProcessing.process_score(musicdoc, m21_score, doc_id)
                
                # Index the current musicdoc, including id, MusicSummary and descriptors
                index_wrapper = IndexWrapper(index_name) 
                index_wrapper.index_musicdoc(index_name, musicdoc, descr_dict, encodedMS)
                
                context = {"index_name": index_name, "musicdoc": musicdoc, "descr_dict": descr_dict, "encodedMS": encodedMS, "indices_names": indices}
                
                return HttpResponse(template.render(context, request))

        except Exception as ex:
            template = loader.get_template('loaddata/loaderror.html')
            context = {"indices_names": indices}
            return HttpResponse(template.render(context, request))
