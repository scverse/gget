import json
import unittest

from gget.gget_ref import ref

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_ref.json") as json_file:
    ref_dict = json.load(json_file)


class TestRef(unittest.TestCase, metaclass=from_json(ref_dict, ref)):
    pass  # all tests are loaded from json
