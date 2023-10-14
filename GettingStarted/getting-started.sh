#! /bin/bash

URL="0.0.0.0:8000"
ES_URL="0.0.0.0:9200"

# Index chorals
INDEX_NAME="chorals"
echo "Creating index ${INDEX_NAME}"
#curl -X PUT http://${URL}/rest/index/${INDEX_NAME}
curl -X PUT http://${ES_URL}/${INDEX_NAME}

NB_FILES=`ls ../data/chorals/*mei | wc -l`
N=1
for file in `ls ../data/chorals/*mei` 
do
  echo -e "\n$N/${NB_FILES}: $file"
  docid=`basename $file .mei | sed "s:\.:-:g"`
  curl -X PUT -H "Content-type: application/mei" http://${URL}/rest/index/${INDEX_NAME}/${docid}/ -d @${file}
  let "N+=1" 
done

#Index Misc
INDEX_NAME="misc"
echo -e "\nCreating index ${INDEX_NAME}"
#curl -X PUT http://${URL}/rest/index/${INDEX_NAME}
curl -X PUT http://${ES_URL}/${INDEX_NAME}

NB_FILES=`ls ../data/*xml ../data/*mei ../data/*krn | wc -l` 
N=1
for file in `ls ../data/*xml ../data/*mei ../data/*krn` 
do
  echo -e "\n$N/${NB_FILES}: $file"
  if [[ $file == *.mei ]]; then
    docid=`basename $file .mei | sed "s:\.:-:g"`
    curl -X PUT -H "Content-type: application/mei" http://${URL}/rest/index/${INDEX_NAME}/${docid}/ -d @${file}
  elif [[ $file == *.krn ]]; then
    docid=`basename $file .mei | sed "s:\.:-:g"`
    curl -X PUT -H "Content-type: application/krn" http://${URL}/rest/index/${INDEX_NAME}/${docid}/ --data-binary @${file}
  elif [[ $file == *.musicxml ]]; then
    docid=`basename $file .xml | sed "s:\.:-:g"`
    curl -X PUT -H "Content-type: application/musicxml" http://${URL}/rest/index/${INDEX_NAME}/${docid}/ --data-binary @${file}
  elif [[ $file == *.xml ]]; then
    docid=`basename $file .xml | sed "s:\.:-:g"`
    #echo $docid
    curl -X PUT -H "Content-type: application/xml" http://${URL}/rest/index/${INDEX_NAME}/${docid}/ -d @${file}
  fi
  let "N+=1" 
done

# Index francoise
INDEX_NAME="francoise"
echo -e "\n\nCreating index ${INDEX_NAME}"
#curl -X PUT http://${URL}/rest/index/${INDEX_NAME}
curl -X PUT http://${ES_URL}/${INDEX_NAME}

#NB_FILES=`unzip -t ../data/francoise.zip |grep -v "/.*/"|wc -l`
echo -e "\nimporting files from archive francoise.zip"
for file in `ls ../data/francoise.zip`
do
  curl -X PUT -H "Content-type: application/zip" http://${URL}/rest/index/${INDEX_NAME}/francoisezip/ --data-binary @${file}
done

echo -e"\nDone! You can now try FACETS at http://${URL}/!"
