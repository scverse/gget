import json
import unittest

from gget.gget_diamond import diamond

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_diamond.json") as json_file:
    diamond_dict = json.load(json_file)


class TestDiamond(unittest.TestCase, metaclass=from_json(diamond_dict, diamond)):
    pass  # all tests are loaded from JSON
