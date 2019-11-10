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
    print(entities_list[0])

    for entity in entities_list:

        instances_list.append(WordSynsets(entity))
        get_edges(instances_list[0].ids[0])

    return render(request, 'search_result.html', {'entities_list': entities_list})
