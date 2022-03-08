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
