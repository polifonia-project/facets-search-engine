import requests
import arrow
from requests.structures import CaseInsensitiveDict

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhZGFjYjZmZmRkZmE1YTc5MGQ1NTZhZDNiZWY4NGZiMSIsImp0aSI6IjU4YjYxMmRkMDhmYWVkNWQ3NzY0ZjY0NGM0YjZmMDg5OTUzMWMxYjYyZTMyMzZjZTdiOWMxN2ZkNGEyNjhmOGQwNThmYzY5MDk2ODE2NmVkIiwiaWF0IjoxNjc3MjMxMjA0LjkwMDIzNiwibmJmIjoxNjc3MjMxMjA0LjkwMDIzOSwiZXhwIjozMzIzNDE0MDAwNC44OTU1NDIsInN1YiI6IjcyMDk3MTAwIiwiaXNzIjoiaHR0cHM6Ly9tZXRhLndpa2ltZWRpYS5vcmciLCJyYXRlbGltaXQiOnsicmVxdWVzdHNfcGVyX3VuaXQiOjUwMDAsInVuaXQiOiJIT1VSIn0sInNjb3BlcyI6WyJiYXNpYyIsImhpZ2h2b2x1bWUiXX0.nOaoFjEYDYGzu8-mMTMADWCRHOqbKVtGR00AJbW_US_ITi0Xd6uLsTxP48pcwB6qWhU0NjLy4Bg4HOsYsdIjsJ2_m7ZIUWBGWSQm6INGSE6G5NwnBMs7gD-FUSwAs7gRlO0OXYa8mCwsLz5fVzIbtoNRTghNKMOVE9YoTjH_ph2tXnnqvBd9OXbxEBzlI40ew0_O0pUprh5-4ySyL4oL0EBsBIUnOjdh622e8ZxbtfvH4QwVaRgn-aHgeLRet4BZ5wl4fj0XVGnppre5QRIJMGkPMT2yJeT0c5d4ycud76y6ig9UrNfG39ivmKNKsLfDCKadjyYvgTUmg2bA8GbPj8b8smIX7aDAgpvP_zph7OEiZVp-KTdameqzfpdYGV81U_7iRF9Pq_NnxJIwU6-4v_ZgJUcTAq8AqlnfM__DlaG5TXz6V2KN6Oa1aefdq33CCRqpa6xPHesHQmeSXVZAo2EikKLuyDSunIkko_y20eE29fWVh-7_KSbLHkM9u4AgvRmabJsp2lcOi0JAqbIoDBMqrpYQW0rs2CGepNcAmRvRE7XDg71hOqO-imsmg6DyEgtiDSpZZXBrI7yVGbdiwE03yEZ6IM3EgFX0-emrc1BPNzGQ0TFjalxdDiJMg-PtqEvJ8umoiCIYJbAFjnnsQ81VdzQd7sEa68LEgdPEbyg"

headers["Authorization"] = token

search_url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&language=en&format=json&search="

composers = ["Mozart","François Couperin", "Josquin des prés"]
composersid = {}

class WikiComposer:
    """
        Composer information extracted from wikidata
    """
    
    def __init__(self, composer_name) :
        self.name = composer_name
        self.info = {}
        self.info = self.get_composer_info(composer_name)
        return
        
    def get_composer_info(self,composer_name):
        info = {}
        c = composer_name
        # retrieving wikidata entity string
        url = search_url+c
        searchres = requests.get(url, headers=headers)
        data = searchres.json()
        cid = data["search"][0]["id"]
        composersid[c] = cid
        # print("wikidata id for {name} is: {id}".format(name=c,id=cid))

        entity = cid

        statements_url = "https://www.wikidata.org/w/rest.php/wikibase/v0/entities/items/"+entity+"/statements"
        label_url = "https://www.wikidata.org/w/rest.php/wikibase/v0/entities/items/"+entity+"/labels"

        labels = requests.get(label_url, headers=headers)
        jsonlab = labels.json()

        statements = requests.get(statements_url, headers=headers)
        jsondata = statements.json()

        name = jsonlab["en"]

        dob = jsondata["P569"][0]["value"]["content"]["time"]
        dod = jsondata["P570"][0]["value"]["content"]["time"]

        dob_arrow = arrow.get(dob[1:]) # there's a + in front of dates
        dob_str = dob_arrow.format('YYYY-MM-DD')

        dod_arrow = arrow.get(dod[1:]) # there's a + in front of dates
        dod_str = dod_arrow.format('YYYY-MM-DD')

        # print(name+" was born on " + dob + " and he died on "+ dod + ". ")

        info["dob"] = dob_str
        info["dod"] = dod_str

        return info
