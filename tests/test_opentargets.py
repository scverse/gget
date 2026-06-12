import json
import unittest

from gget.gget_opentargets import opentargets

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_opentargets.json") as json_file:
    ot_dict = json.load(json_file)


class TestOpenTargets(unittest.TestCase, metaclass=from_json(ot_dict, opentargets)):
    pass  # all tests are loaded from json
