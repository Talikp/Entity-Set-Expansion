from django.conf import settings
import requests
import copy
from SPARQLWrapper import SPARQLWrapper, JSON, XML
from xml.dom import minidom
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

    @timing
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
        query_string = 'SELECT DISTINCT ?synset ?broader WHERE {{ ?entries a lemon:LexicalEntry . ?entries lemon:sense ?sense . ?sense lemon:reference ?synset . ?entries rdfs:label "{}"@en . ?synset a skos:Concept .  ?synset skos:broader ?broader }}'.format(name)

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


def sparql_create_query_string(category, source_ids, address):
    query_string = "PREFIX rdfs: <http://babelnet.org/rdf/> SELECT ?expand ?entry WHERE { ?expand skos:broader <" + address + \
                   category.split(":")[1] + "> . "
    query_string += " UNION ".join(
        map(lambda synset: "{ ?expand skos:related <" + address + synset.id.split(":")[1] + "> }", source_ids))
    query_string += r' . ?expand skos:exactMatch ?entry . FILTER(strstarts(str(?entry), "http://dbpedia.org/resource/")) .'
    query_string += " } ORDER BY str(?expand) LIMIT 10"
    return query_string


@timing
def sparql_expand(category, entries, source_ids):
    instances = set([])
    address = "http://babelnet.org/rdf/s"
    limit = len(entries) + 100
    # ?relations, (count(?relations) as ?rel)     ORDER BY DESC(?rel)

    query_string = sparql_create_query_string(category, source_ids, address)

    sparql = SPARQLWrapper("https://babelnet.org/sparql/")
    sparql.setQuery(query_string)  # LIMIT " + str(limit))
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
                if name.lower() not in entries and instance not in source_ids and len(name) > 0:  # and " " not in name:
                    instances.add(name.capitalize())
            else:
                break

    return instances

def sparql_expand_parallel(category_item):
    category, source_ids = category_item
    instances = set([])
    address = "http://babelnet.org/rdf/s"
    query_string = sparql_create_query_string(category, source_ids, address)

    sparql = SPARQLWrapper("https://babelnet.org/sparql/")
    sparql.setQuery(query_string)  # LIMIT " + str(limit))
    sparql.addParameter("key", settings.BABELNET_API_KEY)
    results = sparql.query().convert()
    results = results.toxml()

    root = ET.fromstring(results)

    entry_prefix = "http://dbpedia.org/resource/"

    namespace = "{http://www.w3.org/2005/sparql-results#}"
    for result in root.find(namespace + "results"):
        entry = result.find(namespace + "binding[@name='entry']")
        # expand = result.find(namespace + "binding[@name='expand']")
        entry_name = entry.find(namespace + "uri")
        if entry_name is not None and entry_name.text.startswith(entry_prefix):
            instances.add(entry_name.text.strip(entry_prefix).capitalize())

    if root.find(namespace + "results") is None:
        return category, None

    return category, instances


@timing
def find_commmon_categories(word_list):
    common = set.intersection(*map(lambda word: word.all_edges, word_list))

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


@timing
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
