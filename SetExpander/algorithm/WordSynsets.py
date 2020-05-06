import time
import xml.etree.ElementTree as ET

import networkx as nx
import requests
from SPARQLWrapper import SPARQLWrapper
from django.conf import settings

from SetExpander.algorithm.SparqlJSONWrapper import SparqlJSONWrapper

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
    def from_sparql_json(cls, word, deep=1, named_entities_only=False):
        name = str(word)
        deep = min(deep, 5)
        deep = max(deep, 1)

        synset_type_subquery = """FILTER(
        ?synsetType="NE"
    ) ."""
        synset_type_subquery = synset_type_subquery if named_entities_only else ""
        categories_subquery = "?synset skos:broader ?X1 . "
        for level in range(2, deep + 1):
            categories_subquery += """
    ?X{} skos:broader ?X{} . """.format(level - 1, level)

        categories_subquery += """
    { ?A rdfs:label ?label. ?synset bn-lemon:synsetID ?B }
    UNION
    { ?synset bn-lemon:synsetID ?A . ?X1 bn-lemon:synsetID ?B }"""

        for level in range(2, deep + 1):
            categories_subquery += """
    UNION
    {{ ?X{} bn-lemon:synsetID ?A . ?X{} bn-lemon:synsetID ?B }}""".format(level - 1, level)

        query_string = """SELECT DISTINCT ?A ?B WHERE {{
    ?entries a lemon:LexicalEntry .
    ?entries lemon:sense ?sense .
    ?sense lemon:reference ?synset .
    ?synset a skos:Concept .
    ?entries rdfs:label ?label .
    ?synset bn-lemon:synsetType ?synsetType .
    FILTER(
        ?label="{}"@en ||
        ?label="{}"@en ||
        ?label="{}"@en
    ) .
    {}
    {}
}}""".format(name.capitalize(), name.lower(), name.upper(), synset_type_subquery, categories_subquery)
        sparql = SparqlJSONWrapper()
        json_data = sparql.query(query_string)
        synset_trees = WordSynsets.parse_json(json_data)
        all_edges = set()
        synsets = []
        for synset, tree in synset_trees.items():
            synsets.append(Synset(synset, tree, len(tree.nodes)))
            all_edges = all_edges | (tree.nodes - {synset})

        return WordSynsets(name, all_edges, synsets)

    @classmethod
    def parse_json(cls, json_data):
        ids = []
        G = nx.DiGraph()

        def extract_tree(G, root):
            tree = nx.DiGraph()
            tree.add_node(root, root=True)
            nodes = [root]
            visited = {root}
            while len(nodes) > 0:
                current_node = nodes.pop()
                for next_node in G.neighbors(current_node):
                    if next_node in visited:
                        continue
                    tree.add_edge(current_node, next_node)
                    nodes.append(next_node)
                    visited.add(next_node)
            return tree

        for result in json_data.get("results", {"bindings": []})["bindings"]:
            try:
                if result['A']['type'] == "uri":
                    ids.append(result['B']['value'])
                    G.add_node(result['B']['value'])
                else:
                    G.add_edge(result['A']['value'], result['B']['value'])
            except KeyError:
                continue
        result = {}
        for synset in ids:
            result[synset] = extract_tree(G, synset)
        return result

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
        return Synset(id, edges, value)

    def __str__(self):
        return "Synset('{}',{},{})".format(self.id, self.edges, self.value)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Synset):
            return self.id == o.id and self.edges == o.edges
        return False
