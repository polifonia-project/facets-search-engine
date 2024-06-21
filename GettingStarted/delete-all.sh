#! /bin/bash

URL="0.0.0.0:8000"
ES_URL="0.0.0.0:9201"

# clean

for index in chorals francoise inventions misc; do
	echo "deleting index ${index}"
	curl -X DELETE http://${ES_URL}/${index}
done
