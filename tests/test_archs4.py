import json
import unittest

from gget.gget_archs4 import archs4

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_archs4.json") as json_file:
    archs4_dict = json.load(json_file)


class TestArchs4(unittest.TestCase, metaclass=from_json(archs4_dict, archs4)):
    pass  # all tests are loaded from json
