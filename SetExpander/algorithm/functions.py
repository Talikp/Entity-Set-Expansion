import time
from xml.etree import ElementTree as ET

import requests
from SPARQLWrapper import SPARQLWrapper
from django.conf import settings

from SetExpander.algorithm.WordSynsets import timing, babelnet_url, Synset, SparqlJSONWrapper


def sparql_create_query_string(category, source_ids):
    address = "http://babelnet.org/rdf/s"

    query_string = """PREFIX rdfs: <http://babelnet.org/rdf/> 
SELECT ?expand ?entry WHERE {{
    ?expand skos:broader <{}{}> . 
""".format(address, category.split(":")[1])

    query_string += "\n UNION ".join(
        map(lambda synset: "{ ?expand skos:related <" + address + synset.id.split(":")[1] + "> }", source_ids))
    query_string += """ . 
    ?expand skos:exactMatch ?entry . 
    FILTER(strstarts(str(?entry), "http://dbpedia.org/resource/")) . 
} ORDER BY str(?expand) LIMIT 10"""

    return query_string


@timing
def sparql_expand(category, entries, source_ids):
    instances = set([])
    address = "http://babelnet.org/rdf/s"
    limit = len(entries) + 100
    # ?relations, (count(?relations) as ?rel)     ORDER BY DESC(?rel)

    query_string = sparql_create_query_string(category, source_ids)

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
    time1 = time.time()

    category, source_ids = category_item
    instances = set([])
    query_string = sparql_create_query_string(category, source_ids)

    spaqrl = SparqlJSONWrapper()
    json_data = spaqrl.query(query_string)
    entry_prefix = "http://dbpedia.org/resource/"

    for result in json_data.get("results", {"bindings": []})["bindings"]:
        try:
            entry_name = result['entry']['value']
            if entry_name is not None and entry_name.startswith(entry_prefix):
                instances.add(entry_name.strip(entry_prefix).capitalize())

        except KeyError:
            continue

    time2 = time.time()
    if settings.MEASURE_TIME:
        print('{:s} function took {:.3f} ms'.format("sparql_expand_parallel", (time2 - time1) * 1000.0))

    if "results" not in json_data:
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
            for id in word.synsets:
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
def find_common_categories(word_list):
    synsets = list(map(lambda word: word.synsets, word_list))
    from itertools import product
    commmons = set()
    for combination in product(*synsets):
        commmons.add(compare_synsets(combination))

    return list(commmons)


def compare_synsets(synsets):
    if len(synsets) == 0:
        return None

    commons = set(synsets[0].edges.nodes)
    for synset in synsets:
        if len(commons) == 0:
            return None
        commons = commons & synset.edges.nodes
    if len(commons) == 0:
        return None
    commons = list(commons)
    lowest_category = commons[0]
    lowest_category_depth = synsets[0].edges.nodes[lowest_category]['depth']
    for common in commons:
        if synsets[0].edges.nodes[common]['depth'] < lowest_category_depth:
            lowest_category = common
            lowest_category_depth = synsets[0].edges.nodes[common]['depth']

    return lowest_category


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
