from django.shortcuts import render
from django.http import HttpResponse
from SetExpander.algorythm.WordSynsets import *
from pytictoc import TicToc


def main_page(request):
    return render(request, 'main_page.html', {})


def about(request):
    return render(request, 'about.html', {})


def search_result(request):

    entities = request.GET.get('entities', '')
    entities = entities.replace(" ", "")
    entities_list = entities.split(",")
    instances_list = []
    expansion_mapping = {}


    for entity in entities_list:
        # t1 = TicToc()
        # t1.tic()
        word = WordSynsets(entity)
        # t1.toc()
        # print(t1.elapsed)
        # print("Instances amount: " + str(len(word.ids)))
        instances_list.append(word)
    """
    t2 = TicToc()
    t2.tic()
    categories_mapping = find_commmon_categories(instances_list)
    t2.toc()
    print(t2.elapsed)
    print("Categories amount: " + str(len(categories_mapping)))
    categories_name_mapping = {}
    # for id in categories_mapping:
    #     categories_name_mapping[get_name_from_ID(id)] = categories_mapping[id]
    """
    categories_mapping = find_commmon_categories(instances_list)
    for id in categories_mapping:
        expanded = sparql_expand(id, entities_list, categories_mapping[id])
        if expanded:
            expansion_mapping[get_name_from_ID(id)] = expanded

    # name_list = list(categories_name_mapping.keys())
    name_list = list(expansion_mapping.keys())
    active = name_list[0]

    return render(request, 'search_result.html', {'categories': expansion_mapping, 'active': active, 'names': name_list, 'entries': entities_list})
