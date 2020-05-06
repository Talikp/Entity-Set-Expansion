import requests
from django.conf import settings


class SparqlJSONWrapper:

    def __init__(self):
        self.address = "https://babelnet.org/sparql/"
        self.format = "application/sparql-results+json"
        self.key = settings.BABELNET_API_KEY

    def query(self, query_str):
        params = {
            'query': query_str,
            'key': self.key,
            'format': self.format
        }
        request = requests.get(self.address, params=params)
        if request.status_code == 200:
            return request.json()

        return {}
