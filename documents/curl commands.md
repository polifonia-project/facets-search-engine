1. Create an index given index name:
curl -X PUT  http://localhost:8000/index_name/

2. Retrieve information of an index:
curl -X GET  http://localhost:8000/index_name/

3. Index a MEI format music score:
curl -X PUT -H "Content-type: application/mei" http://localhost:8000/index_name/doc_id/ -d @file_path

4. Get info of the music document:
curl -X GET  http://localhost:8000/index_name/doc_id/

5. Initiate a search under an index:
curl -X POST http://localhost:8000/index_name/_search -d @json_path

6. Delete an indexed document from ES:
curl -X DELETE http://localhost:9200/index_name/_doc/doc_id_that_you_want_delete


-----------------------------------------------------------------------------------------
Tutorial for indexing scores for pattern search with samples:

1. First create an index called "index":
curl -X PUT  http://localhost:8000/index/

2.1 Import the first music score "001.mei" from the folder "data":
curl -X PUT -H "Content-type:application/mei" http://localhost:8000/index/friuli001/ -d @data/friuli001.mei 

2.2(optional) Import more MEI score samples from the folder "data":
curl -X PUT -H "Content-type:application/mei" http://localhost:8000/index/terpsichore026/ -d @data/terpsichore026.mei

2.3(optional) Import a XML score from "data":
curl -X PUT -H "Content-type:application/xml" http://localhost:8000/index/couperin/ -d @data/couperin.xml

2.4(optional) Import a zip of score samples from "data":
curl -X PUT -H "Content-type:application/zip" http://localhost:8000/index/testzip/ --data-binary @data/test_zip.zip

2.5(optional) Import a kern score sample:
curl -X PUT -H "Content-type:application/krn" http://localhost:8000/index/danmark/ --data-binary @data/danmark1.krn

2.6(optional) Import an abc score sample:
curl -X PUT -H "Content-type:application/abc" http://localhost:8000/index/abctest/ --data-binary @data/test.abc

2.7(optional) Import a MusicXML score sample:
curl -X PUT -H "Content-type:application/musicxml" http://localhost:8000/index/testmxml/ --data-binary @data/Gas0301f.musicxml 
OR:
curl -X PUT -H "Content-type:application/vnd.recordare.musicxml+xml" 
					http://localhost:8000/index/testmxml/ -d @data/Gas0301f.musicxml

3. Use a defined query(search type: diatonic) in the folder "queries":
curl -X POST http://localhost:8000/index/_search -d @queries/test_dia1.json

3.2(optional) More samples for pattern search
Test the search engine with a mirror query
curl -X POST http://localhost:8000/index/_search -d @queries/test_mir1.json

Test chromatic search
curl -X POST http://localhost:8000/index/_search -d @queries/test_chr1.json

Test rhythmic search
curl -X POST http://localhost:8000/index/_search -d @queries/test_rhy2.json
