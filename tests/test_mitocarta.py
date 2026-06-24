import json
import unittest

from gget.gget_mitocarta import mitocarta

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_mitocarta.json") as json_file:
    mitocarta_dict = json.load(json_file)


class TestMitocarta(unittest.TestCase, metaclass=from_json(mitocarta_dict, mitocarta)):
    # Error tests are generated from json; property tests are defined below.

    def test_mitocarta_human(self):
        test = "test_mitocarta_human"
        td = mitocarta_dict[test]
        df = mitocarta(**td["args"])
        self.assertEqual(len(df), td["expected_n_rows"])
        for col in td["expected_columns"]:
            self.assertIn(col, df.columns)
        # A well-known mitochondrial gene should be in the inventory
        self.assertIn("MT-CO1", set(df["Symbol"].astype(str)))

    def test_mitocarta_pathways(self):
        test = "test_mitocarta_pathways"
        td = mitocarta_dict[test]
        df = mitocarta(**td["args"])
        self.assertIn("MitoPathway", df.columns)
        self.assertGreaterEqual(len(df), td["expected_min_rows"])
