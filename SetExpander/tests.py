import json
import os
import xml.etree.ElementTree as ET
from unittest.mock import patch

from django.test import TestCase

from SetExpander.algorithm.WordSynsets import WordSynsets, Synset
from SetExpander.algorithm.functions import sparql_create_query_string, find_commmon_categories, compare_synsets, \
    find_common_categories, sparql_expand_parallel


class SPARQLWrapperMock(object):

    def __init__(self, mocked_data):
        self.data = mocked_data

    def setQuery(self, *args):
        pass

    def addParameter(self, *args):
        pass

    def query(self):
        print('query')
        return self

    def convert(self):
        return self

    def toxml(self):
        return self.data


def read_json_test_data(file_name):
    TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'test_files/' + file_name)
    json_file = open(TESTDATA_FILENAME, 'r')
    mock_data = json.load(json_file)
    json_file.close()
    return mock_data


def read_xml_test_data(file_name):
    TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'test_files/' + file_name)
    return ET.parse(TESTDATA_FILENAME).getroot()


class SetExpandTestCase(TestCase):

    def test_create_query_string(self):
        expected_str = """PREFIX rdfs: <http://babelnet.org/rdf/> 
SELECT ?expand ?entry WHERE {
    ?expand skos:broader <http://babelnet.org/rdf/s14129567n> . 
{ ?expand skos:related <http://babelnet.org/rdf/s00048043n> }
 UNION { ?expand skos:related <http://babelnet.org/rdf/s01713224n> } . 
    ?expand skos:exactMatch ?entry . 
    FILTER(strstarts(str(?entry), "http://dbpedia.org/resource/")) . 
} ORDER BY str(?expand) LIMIT 10"""
        address = "http://babelnet.org/rdf/s"
        category = 'bn:14129567n'
        synset1 = Synset(id="bn:00048043n", value=2183,
                         edges={'bn:00058449n', 'bn:14253335n', 'bn:14129567n', 'bn:01246770n'})
        synset2 = Synset(id='bn:01713224n', value=1898,
                         edges={'bn:00725358n', 'bn:00064652n', 'bn:14253335n', 'bn:01431715n', 'bn:00182120n',
                                'bn:03782293n', 'bn:00044037n', 'bn:01652181n', 'bn:01246770n', 'bn:14129567n'})
        actual_str = sparql_create_query_string(category, [synset1, synset2], address)
        self.assertEqual(actual_str, expected_str)

    def test_find_common_categories(self):
        wordsynset1 = WordSynsets('Java',
                                  {'bn:00020414n', 'bn:05285563n', 'bn:01246770n', 'bn:00789872n', 'bn:14253335n',
                                   'bn:00070724n',
                                   'bn:14831528n', 'bn:00000242n', 'bn:08978346n', 'bn:00002745n', 'bn:14129567n',
                                   'bn:00012195n',
                                   'bn:00077773n', 'bn:00054416n', 'bn:00020927n', 'bn:00047612n', 'bn:01636191n',
                                   'bn:00058449n',
                                   'bn:00010183n'}, [Synset('bn:00452580n', {'bn:05285563n', 'bn:00077773n'}, 112),
                                                     Synset('bn:03218702n', {'bn:00077773n', 'bn:00070724n'}, 535),
                                                     Synset('bn:00020414n', {'bn:00010183n', 'bn:00002745n'}, 3918),
                                                     Synset('bn:00551458n', {'bn:05285563n', 'bn:00077773n'}, 423),
                                                     Synset('bn:03241725n', {'bn:14831528n', 'bn:00054416n'}, 719),
                                                     Synset('bn:00048043n',
                                                            {'bn:00058449n', 'bn:14129567n', 'bn:01246770n',
                                                             'bn:14253335n'}, 2183),
                                                     Synset('bn:15275257n', {'bn:00789872n'}, 131),
                                                     Synset('bn:00048042n', {'bn:00047612n'}, 1918),
                                                     Synset('bn:03244714n', {'bn:08978346n', 'bn:00020927n'}, 619),
                                                     Synset('bn:03107993n', {'bn:00012195n'}, 1018),
                                                     Synset('bn:17140284n', {'bn:00020414n'}, 101),
                                                     Synset('bn:16083111n', {'bn:00000242n'}, 936),
                                                     Synset('bn:02367450n', {'bn:01636191n'}, 136)])

        wordsynset2 = WordSynsets('Python',
                                  {'bn:03411625n', 'bn:01246770n', 'bn:14253335n', 'bn:00025364n', 'bn:00725358n',
                                   'bn:00064652n',
                                   'bn:00056671n', 'bn:00016287n', 'bn:01237332n', 'bn:03342540n', 'bn:01431715n',
                                   'bn:03472731n',
                                   'bn:00059150n', 'bn:00021286n', 'bn:03782293n', 'bn:01652181n', 'bn:00056674n',
                                   'bn:00033346n',
                                   'bn:14129567n', 'bn:00067221n', 'bn:00041645n', 'bn:00044037n', 'bn:00055322n',
                                   'bn:00028582n',
                                   'bn:00076380n', 'bn:00544981n', 'bn:00076248n', 'bn:00182120n'},
                                  [Synset('bn:00279773n', {'bn:03472731n'}, 141),
                                   Synset('bn:02533602n', {'bn:00055322n'}, 383),
                                   Synset('bn:03489893n', {'bn:00076380n', 'bn:00544981n'}, 127),
                                   Synset('bn:02368767n', {'bn:00021286n'}, 109),
                                   Synset('bn:01253620n', {'bn:03342540n', 'bn:00016287n'}, 296),
                                   Synset('bn:00033346n', {'bn:00059150n', 'bn:00067221n', 'bn:00076248n'}, 654),
                                   Synset('bn:00065463n',
                                          {'bn:00056674n', 'bn:03411625n', 'bn:00025364n', 'bn:00041645n',
                                           'bn:00056671n',
                                           'bn:00028582n', 'bn:00059150n'}, 741), Synset('bn:01713224n',
                                                                                         {'bn:03782293n',
                                                                                          'bn:01246770n',
                                                                                          'bn:14129567n',
                                                                                          'bn:14253335n',
                                                                                          'bn:00725358n',
                                                                                          'bn:00064652n',
                                                                                          'bn:00044037n',
                                                                                          'bn:01431715n',
                                                                                          'bn:01652181n',
                                                                                          'bn:00182120n'}, 1898),
                                   Synset('bn:01157670n', set(), 1285),
                                   Synset('bn:03270061n', {'bn:00033346n', 'bn:00076248n'}, 610),
                                   Synset('bn:16032125n', {'bn:01237332n'}, 190)])

        word_list = [wordsynset1, wordsynset2]
        connection_mapping = {}
        connection_mapping['bn:14129567n'] = [
            Synset('bn:00048043n', {'bn:00058449n', 'bn:14129567n', 'bn:01246770n', 'bn:14253335n'}, 2183),
            Synset('bn:01713224n',
                   {'bn:03782293n', 'bn:01246770n', 'bn:14129567n', 'bn:14253335n', 'bn:00725358n', 'bn:00064652n',
                    'bn:00044037n', 'bn:01431715n', 'bn:01652181n', 'bn:00182120n'}, 1898)]
        connection_mapping['bn:01246770n'] = [
            Synset('bn:00048043n', {'bn:00058449n', 'bn:14129567n', 'bn:01246770n', 'bn:14253335n'}, 2183),
            Synset('bn:01713224n',
                   {'bn:03782293n', 'bn:01246770n', 'bn:14129567n', 'bn:14253335n', 'bn:00725358n', 'bn:00064652n',
                    'bn:00044037n', 'bn:01431715n', 'bn:01652181n', 'bn:00182120n'}, 1898)]
        connection_mapping['bn:14253335n'] = [
            Synset('bn:00048043n', {'bn:00058449n', 'bn:14129567n', 'bn:01246770n', 'bn:14253335n'}, 2183),
            Synset('bn:01713224n',
                   {'bn:03782293n', 'bn:01246770n', 'bn:14129567n', 'bn:14253335n', 'bn:00725358n', 'bn:00064652n',
                    'bn:00044037n', 'bn:01431715n', 'bn:01652181n', 'bn:00182120n'}, 1898)]

        categories = find_commmon_categories(word_list)
        self.assertEqual(connection_mapping, categories)

    @patch("SetExpander.algorithm.functions.SPARQLWrapper")
    def test_sparql_expand(self, mock_sparqlwrapper):
        item = 'bn:14253335n', [
            Synset('bn:00048043n', {'bn:00058449n', 'bn:14129567n', 'bn:01246770n', 'bn:14253335n'}, 2183),
            Synset('bn:01713224n',
                   {'bn:03782293n', 'bn:01246770n', 'bn:14129567n', 'bn:14253335n', 'bn:00725358n', 'bn:00064652n',
                    'bn:00044037n', 'bn:01431715n', 'bn:01652181n', 'bn:00182120n'}, 1898)]
        mock_sparqlwrapper.return_value = SPARQLWrapperMock(ET.tostring(read_xml_test_data('sparql_expand_response.xml')))
        actual = sparql_expand_parallel(item)

        self.assertEqual(actual[1], {'Smalltalk', 'Lua_(programming_language)', 'C_sharp_(programming_language)', 'Ruby_(programming_language)', 'Python_(programming_language)', 'Ceylon_(programming_language)'})

class WordSynsetsTestCase(TestCase):

    @patch("SetExpander.algorithm.SparqlJSONWrapper.SparqlJSONWrapper.query")
    def test_wordsynsets_from_json(self, mock_query):
        mock_query.return_value = read_json_test_data('word_sparql_graph_small.json')
        word = WordSynsets.from_sparql_json("java", 4, True)
        query = """SELECT DISTINCT ?A ?B WHERE {
    ?entries a lemon:LexicalEntry .
    ?entries lemon:sense ?sense .
    ?sense lemon:reference ?synset .
    ?synset a skos:Concept .
    ?entries rdfs:label ?label .
    ?synset bn-lemon:synsetType ?synsetType .
    FILTER(
        ?label="Java"@en ||
        ?label="java"@en ||
        ?label="JAVA"@en
    ) .
    FILTER(
        ?synsetType="NE"
    ) .
    ?synset skos:broader ?X1 . 
    ?X1 skos:broader ?X2 . 
    ?X2 skos:broader ?X3 . 
    ?X3 skos:broader ?X4 . 
    { ?A rdfs:label ?label. ?synset bn-lemon:synsetID ?B }
    UNION
    { ?synset bn-lemon:synsetID ?A . ?X1 bn-lemon:synsetID ?B }
    UNION
    { ?X1 bn-lemon:synsetID ?A . ?X2 bn-lemon:synsetID ?B }
    UNION
    { ?X2 bn-lemon:synsetID ?A . ?X3 bn-lemon:synsetID ?B }
    UNION
    { ?X3 bn-lemon:synsetID ?A . ?X4 bn-lemon:synsetID ?B }
}"""
        mock_query.assert_called_with(query)

    def test_wordsynsets_from_xml(self):
        root = read_xml_test_data('word_sparql_small.xml')
        java_word = WordSynsets.parse_xml("Java", root)
        expected = WordSynsets("Java", {'bn:00054416n', 'bn:00054417n', 'bn:00012195n'},
                               [Synset('bn:03107993n', {'bn:00012195n'}, 1),
                                Synset('bn:03241725n',
                                       {'bn:00054416n', 'bn:00054417n'}, 2)])
        self.assertEqual(expected, java_word)

    def mock_wordsynsets(self, mock_query, file_name):
        mock_query.return_value = read_json_test_data(file_name)
        return WordSynsets.from_sparql_json(file_name, 4, True)

    @patch("SetExpander.algorithm.SparqlJSONWrapper.SparqlJSONWrapper.query")
    def test_find_common(self, mock_query):
        java = self.mock_wordsynsets(mock_query, 'word_java.json')
        python = self.mock_wordsynsets(mock_query, 'word_python.json')
        result = find_common_categories([java, python])
