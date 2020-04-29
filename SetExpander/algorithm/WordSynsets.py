from django.conf import settings
import requests
from SPARQLWrapper import SPARQLWrapper
import time
import xml.etree.ElementTree as ET

babelnet_url = "https://babelnet.io/v5/"


def timing(f):
    def wrap(*args):
        if not settings.MEASURE_TIME:
            return f(*args)
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print('{:s} function took {:.3f} ms'.format(f.__name__, (time2 - time1) * 1000.0))

        return ret

    return wrap


class WordSynsets:

    def __init__(self, name, all_edges, ids):
        self.name = str(name)
        self.all_edges = all_edges
        self.ids = ids

    @classmethod
    @timing
    def from_http(cls, word):
        name = str(word)
        all_edges = set([])
        ids = []

        params = {
            'lemma': name,
            'searchLang': 'EN',
            'key': settings.BABELNET_API_KEY
        }

        search_url = babelnet_url + "getSynsetIds"
        request = requests.get(search_url, params=params)

        for instance in request.json():
            synset = Synset.from_id(instance['id'])
            if synset.value >= 100:
                ids.append(synset)
                all_edges = all_edges | synset.edges

        return WordSynsets(name, all_edges, ids)

    @classmethod
    @timing
    def from_sparql(cls, word):
        name = str(word)
        query_string = """SELECT DISTINCT ?synset ?broader WHERE {{ 
    ?entries a lemon:LexicalEntry . 
    ?entries lemon:sense ?sense . 
    ?sense lemon:reference ?synset . 
    ?entries rdfs:label "{}"@en . 
    ?synset a skos:Concept .  
    ?synset skos:broader ?broader 
}}""".format(name)

        sparql = SPARQLWrapper("https://babelnet.org/sparql/")
        sparql.setQuery(query_string)
        sparql.addParameter("key", settings.BABELNET_API_KEY)

        results = sparql.query().convert()
        results = results.toxml()
        xmldoc = ET.fromstring(results)
        return WordSynsets.parse_xml(name, xmldoc)

    @classmethod
    @timing
    def parse_xml(cls, name, xml):
        all_edges = set()
        ids = []
        result_aggregator = {}
        get_id = lambda value: "bn:" + value.replace("http://babelnet.org/rdf/s", "")

        namespace = "{http://www.w3.org/2005/sparql-results#}"
        for result in xml.find(namespace + "results"):
            synset = result.findall("*")[0].find("*").text
            cat = result.findall("*")[1].find("*").text
            synset_id = get_id(synset)
            synset_cat = get_id(cat)

            if synset_id in result_aggregator:
                result_aggregator[synset_id].add(synset_cat)
            else:
                result_aggregator[synset_id] = {synset_cat}

        for synset_id, synset_edges in result_aggregator.items():
            ids.append(Synset(id=synset_id, edges=synset_edges, value=len(synset_edges)))
            all_edges = all_edges | synset_edges

        return WordSynsets(name, all_edges, ids)

    def __str__(self):
        result = "WordSynsets('{}',{},".format(self.name, self.all_edges)
        synsets = ",".join(map(Synset.__str__, self.ids))
        result += "[{:s}])".format(synsets)

        return result

    def __eq__(self, o: object) -> bool:
        if isinstance(o, WordSynsets):
            return self.name == o.name and self.all_edges == o.all_edges and self.ids == o.ids
        return False


class Synset:

    def __init__(self, id, edges, value):
        self.id = id
        self.edges = edges
        self.value = value

    @classmethod
    def from_id(cls, id):
        edges = set([])

        params = {
            'id': id,
            'key': settings.BABELNET_API_KEY
        }

        search_url = babelnet_url + "getOutgoingEdges"
        request = requests.get(search_url, params=params)

        value = len(request.json())

        for edge in request.json():
            if edge["pointer"]["shortName"] == "is-a" and edge["target"][-1] == 'n':  # edge["pointer"]["shortName"] != "related" and edge["pointer"]["shortName"] != "color"
                edges.add(edge["target"])
                # print(edge["pointer"]["shortName"])
        return Synset(id, edges, value)

    def __str__(self):
        return "Synset('{}',{},{})".format(self.id, self.edges, self.value)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Synset):
            return self.id == o.id and self.edges == o.edges
        return False


