import json
import unittest

from gget.gget_search import search

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_search.json") as json_file:
    search_dict = json.load(json_file)


class TestSearch(unittest.TestCase, metaclass=from_json(search_dict, search)):
    pass  # all tests are loaded from json
