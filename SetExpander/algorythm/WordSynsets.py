from django.conf import settings
import requests
import copy

babelnet_url = "https://babelnet.io/v5/"


class WordSynsets:

    def __init__(self, word):
        self.name = str(word)
        self.all_edges = set([])
        self.ids = []

        params = {
            'lemma': self.name,
            'searchLang': 'EN',
            'key': settings.BABELNET_API_KEY
        }

        search_url = babelnet_url + "getSynsetIds"
        request = requests.get(search_url, params=params)

        for instance in request.json():
            synset = Synset(instance['id'])
            if synset.value >= 100:
                self.ids.append(synset)
                self.all_edges = self.all_edges | synset.edges

        print("IDs:")
        print(self.ids)


class Synset:

    def __init__(self, id):
        self.id = id
        self.edges = set([])
        self.value = 0

        params = {
            'id': self.id,
            'key': settings.BABELNET_API_KEY
        }

        search_url = babelnet_url + "getOutgoingEdges"
        request = requests.get(search_url, params=params)

        self.value = len(request.json())

        for edge in request.json():
            if edge["pointer"]["shortName"] != "related":  # == "is-a":
                self.edges.add(edge["target"])

    def __str__(self):
        return self.id

            # if edge["pointer"]["shortName"] == "related":
            #     if related_count >= 3:  # limit 'related' relations to the most important ones
            #         continue
            #     related_count += 1
            # self.edges.add(edge["target"])

        # next for each edge get_edges has to be performed until connection is found


def find_commmon_categories(word_list):
    common = copy.copy(word_list[0].all_edges)
    for i in range(1,len(word_list)):
        common = common & word_list[i].all_edges

    connection_mapping = {}
    for category in common:
        connected_synsets = []
        for word in word_list:
            id_containing = None
            for id in word.ids:
                if category in id.edges:
                    if id_containing == None:
                        id_containing = id
                    else:
                        if id_containing.value < id.value:
                            id_containing = id.value
            connected_synsets.append(id_containing)
        connection_mapping[category] = connected_synsets
    return connection_mapping







def get_name_from_ID(id):

    params = {
        'id': id,
        'key': settings.BABELNET_API_KEY
    }

    search_url = babelnet_url + "getSynset"
    request = requests.get(search_url, params=params)
    name = request.json()["mainSense"].replace("_", " ").capitalize()
    #name = name.split("#")[0]
    return name

def get_edges_from_ID(id):

    edges = set([])
    params = {
        'id': id,
        'key': settings.BABELNET_API_KEY
    }

    search_url = babelnet_url + "getOutgoingEdges"
    request = requests.get(search_url, params=params)

    for edge in request.json():
        if edge["pointer"]["shortName"] == "is-a":
            edges.add(edge["target"])

    return edges

def get_edges_from_ID_list(ids):

    edges = set([])
    for id in ids:

        params = {
            'id': id,
            'key': settings.BABELNET_API_KEY
        }

        search_url = babelnet_url + "getOutgoingEdges"
        request = requests.get(search_url, params=params)

        for edge in request.json():
            if edge["pointer"]["shortName"] == "is-a":
                edges.add(edge["target"])

    return edges
