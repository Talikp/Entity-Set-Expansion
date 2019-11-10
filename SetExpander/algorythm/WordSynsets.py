from django.conf import settings
import requests

babelnet_url = "https://babelnet.io/v5/"


class WordSynsets:

    def __init__(self, word):
        self.name = str(word)
        self.ids = []

        params = {
            'lemma': self.name,
            'searchLang': 'EN',
            'key': settings.BABELNET_API_KEY
        }

        search_url = babelnet_url + "getSynsetIds"
        request = requests.get(search_url, params=params)

        for instance in request.json():
            self.ids.append(instance['id'])

        print("IDs:")
        print(self.ids)


def get_edges(id, weight=0):  #weight parameter might be usless since babelnet api doesn't return any information
    edges = {}

    params = {
        'id': id,
        'key': settings.BABELNET_API_KEY
    }

    search_url = babelnet_url + "getOutgoingEdges"
    request = requests.get(search_url, params=params)

    for edge in request.json():
        edges[edge['target']] = edge['weight']

    #next for each edge get_edges has to be performed untill connection is found

    print("Edges for ID " + id + " :")
    print(edges)
