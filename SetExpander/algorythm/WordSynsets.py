from django.conf import settings
import requests
import copy
from SPARQLWrapper import SPARQLWrapper, JSON, XML
from xml.dom import minidom
import time

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

        # print("IDs:")
        # for i in self.ids:
        #     print(str(i))
        # print("---------------------------------------------------")

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
            if edge["pointer"]["shortName"] == "is-a" and edge["target"][-1] == 'n':  # edge["pointer"]["shortName"] != "related" and edge["pointer"]["shortName"] != "color"
                self.edges.add(edge["target"])
                # print(edge["pointer"]["shortName"])

    def __str__(self):
        return self.id

def sparql_expand(category, entries, source_ids):
    instances = set([])
    address = "http://babelnet.org/rdf/s"
    limit = len(entries) + 100
    # ?relations, (count(?relations) as ?rel)     ORDER BY DESC(?rel)

    query_string = "PREFIX rdfs: <http://babelnet.org/rdf/> SELECT ?expand WHERE { ?expand skos:broader <" + address + category.split(":")[1] + "> . "
    for i in range(len(source_ids)):
        query_string += "{ ?expand skos:related <" + address + source_ids[i].id.split(":")[1] + "> }"
        if i != len(source_ids)-1:
            query_string += " UNION "

    query_string += " } ORDER BY str(?expand)"

    sparql = SPARQLWrapper("https://babelnet.org/sparql/")
    sparql.setQuery(query_string)  #LIMIT " + str(limit))
    sparql.addParameter("key", settings.BABELNET_API_KEY)

    results = sparql.query().convert()
    results = results.toxml()

    xmldoc = minidom.parseString(results)
    itemlist = xmldoc.getElementsByTagName('binding')


    # print(results)
    if len(itemlist) == 0:
        return None

    for s in itemlist:
        if s.attributes['name'].value != "expand":
            continue
        instance = s.getElementsByTagName("uri")[0].firstChild.data
        if instance.startswith(address):
            instance = "bn:" + instance[len(address):]
            if len(instances) < 6:
                name = get_name_from_ID(instance)
                if name.lower() not in entries and instance not in source_ids and len(name) > 0: #and " " not in name:
                    instances.add(name.capitalize())
            else:
                break

    return instances

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
                            id_containing = id
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
    json = request.json()
    name = ""
    if "mainSense" in json:
        name = json["mainSense"]
    elif "senses" in json and len(json["senses"]) > 0:
        name = json["senses"][0]["properties"]["simpleLemma"]
    else:
        print("Other instance")
    name = name.replace("_", " ")
    name = name.split("#")[0]
    return name


"""
def get_edges_from_ID(id):

    edges = set([])
    params = {
        'id': id,
        'targetLang': 'EN',
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
    
    #expand using API
def expand(category, source_ids):
    instances = set([])

    params = {
        'id': category,
        'key': settings.BABELNET_API_KEY
    }

    search_url = babelnet_url + "getOutgoingEdges"
    request = requests.get(search_url, params=params)
    print(request.json())
    for edge in request.json():
        if len(instances) > 5:
            break
        if edge["pointer"]["shortName"] != "related":#"has-kind" and edge["target"] not in instances:
            instances.add(edge["target"])
            print(edge["pointer"]["shortName"])
    return instances
"""
