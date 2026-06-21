import json
import unittest

from gget.gget_elm import elm
from gget.gget_setup import setup as gget_setup

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_elm.json") as json_file:
    elm_dict = json.load(json_file)

gget_setup(module="elm")


class TestELM(unittest.TestCase):
    def test_elm_uniprot_id_in_elm(self):
        test = "test1"
        expected_result = elm_dict[test]["expected_result"]

        result1, result2 = elm(**elm_dict[test]["args"])
        result_to_test = result1.dropna(axis=1).values.tolist() + result2.dropna(axis=1).values.tolist()[15:20]

        self.assertListEqual(result_to_test, expected_result)

    def test_elm_uniprot_id_new(self):
        test = "test2"
        expected_result = elm_dict[test]["expected_result"]

        result1, result2 = elm(**elm_dict[test]["args"])
        result_to_test = result1.dropna(axis=1).values.tolist() + result2.dropna(axis=1).values.tolist()[15:20]

        self.assertListEqual(result_to_test, expected_result)

    def test_elm_uniprot_aminoacidseq(self):
        test = "test3"
        expected_result = elm_dict[test]["expected_result"]

        result1, result2 = elm(**elm_dict[test]["args"])
        result_to_test = result1.dropna(axis=1).values.tolist() + result2.dropna(axis=1).values.tolist()[15:20]

        self.assertListEqual(result_to_test, expected_result)
