from django.shortcuts import render
from django.conf import settings
import requests
from django.http import HttpResponse


def main_page(request):
    return render(request, 'main_page.html', {})

def about(request):
    return render(request, 'about.html', {})

def search_result(request):
    entities = request.GET.get('entities', '')
    entities = entities.replace(" ", "")
    entities_list = entities.split(",")
    print(entities_list[0])
    for entity in entities_list:

        search_url = 'https://babelnet.io/v5/getSenses'

        params = {
            'lemma' : str(entity),
            'searchLang' : 'EN',
            'key' : settings.BABELNET_API_KEY
        }

        r = requests.get(search_url, params=params)
        print(r.json())
    return render(request, 'search_result.html', {'entities_list': entities_list})