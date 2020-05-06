from multiprocessing import Pool

from django.shortcuts import render
from silk.profiling.profiler import silk_profile

from SetExpander.algorithm.WordSynsets import *
from SetExpander.algorithm.functions import sparql_expand_parallel, find_commmon_categories, get_name_from_ID


def main_page(request):
    return render(request, 'main_page.html', {})


def about(request):
    return render(request, 'about.html', {})


@silk_profile()
def search_result(request):
    entities = request.GET.get('entities', '')
    entities_list = entities.replace(" ", "").split(",")
    instances_list = []
    expansion_mapping = {}

    for entity in entities_list:
        # word = WordSynsets.from_http(entity)
        word = WordSynsets.from_sparql_json(entity)
        instances_list.append(word)

    categories_mapping = find_commmon_categories(instances_list)

    with Pool(4) as pool:
        expanded = pool.map(sparql_expand_parallel, categories_mapping.items())
        for id, founded in expanded:
            if founded:
                expansion_mapping[get_name_from_ID(id)] = founded

    # for id in categories_mapping:
    #     expanded = sparql_expand(id, entities_list, categories_mapping[id])
    #     if expanded:
    #         expansion_mapping[get_name_from_ID(id)] = expanded

    print(expansion_mapping)
    name_list = list(expansion_mapping.keys())
    active = None
    if len(name_list) > 0:
        active = name_list[0]

    return render(request, 'search_result.html',
                  {'categories': expansion_mapping, 'active': active, 'names': name_list, 'entries': entities_list})
