#! /bin/bash

curl -X DELETE http://localhost:9200/inventions 
#curl -X DELETE http://localhost:9200/francoise
#curl -X DELETE http://localhost:9200/bach
#curl -X DELETE http://localhost:9200/palestrina
#curl -X DELETE http://localhost:9200/chorals
#curl -X DELETE http://localhost:9200/essen-schubert
#curl -X DELETE http://localhost:9200/misc

#echo "**** INVENTIONS ****"
#curl -X PUT http://localhost:8000/rest/index/inventions/ ; curl -X PUT -H "Content-type:application/zip" http://localhost:8000/rest/index/inventions/foo/ --data-binary @/home/raph/Encadrement/These/TiangeZhu/facets-search-engine/data/data_to_use/inventions.zip


#echo "**** francoise ****"
#curl -X PUT http://localhost:8000/rest/index/francoise/ ; curl -X PUT -H "Content-type:application/zip" http://localhost:8000/rest/index/francoise/foo/ --data-binary @/home/raph/Encadrement/These/TiangeZhu/facets-search-engine/data/data_to_use/francoise.zip
