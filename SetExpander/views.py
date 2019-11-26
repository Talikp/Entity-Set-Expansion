from django.shortcuts import render
from django.http import HttpResponse
from SetExpander.algorythm.WordSynsets import *


def main_page(request):
    return render(request, 'main_page.html', {})


def about(request):
    return render(request, 'about.html', {})


def search_result(request):

    entities = request.GET.get('entities', '')
    entities = entities.replace(" ", "")
    entities_list = entities.split(",")
    instances_list = []

    for entity in entities_list:
        word = WordSynsets(entity)
        instances_list.append(word)

    categories_mapping = find_commmon_categories(instances_list)
    categories_name_mapping = {}
    for id in categories_mapping:
        categories_name_mapping[get_name_from_ID(id)] = categories_mapping[id]
    name_list = list(categories_name_mapping.keys())
    active = name_list[0]

    print("---------------------------------------------------------")
    print(categories_name_mapping)
    return render(request, 'search_result.html', {'categories': categories_name_mapping, 'active': active, 'names' : name_list})
