import json
import unittest

from gget.gget_blat import blat

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_blat.json") as json_file:
    blat_dict = json.load(json_file)


class TestBlat(unittest.TestCase, metaclass=from_json(blat_dict, blat)):
    pass  # all tests are loaded from json
