import json
import unittest

from gget.gget_bgee import bgee

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_bgee.json") as json_file:
    bgee_dict = json.load(json_file)


class TestBgee(unittest.TestCase, metaclass=from_json(bgee_dict, bgee)):
    pass  # all tests are loaded from json
