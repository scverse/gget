import json
import unittest

from gget.gget_blast import blast

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_blast.json") as json_file:
    blast_dict = json.load(json_file)


class TestBlast(unittest.TestCase, metaclass=from_json(blast_dict, blast)):
    pass  # all tests are loaded from json
