import filecmp
import json
import os
import unittest

from gget.gget_pdb import pdb

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_pdb.json") as json_file:
    pdb_dict = json.load(json_file)


class TestPDB(unittest.TestCase):
    def test_pdb_assembly(self):
        test = "test1"
        expected_result = pdb_dict[test]["expected_result"]
        result_to_test = pdb(**pdb_dict[test]["args"])

        self.assertEqual(result_to_test, expected_result)

    # def test_pdb_branched_entity(self):
    #     test = "test2"
    #     expected_result = pdb_dict[test]["expected_result"]
    #     result_to_test = pdb(**pdb_dict[test]["args"])

    #     self.assertEqual(result_to_test, expected_result)

    # def test_pdb_nonpolymer_entity(self):
    #     test = "test3"
    #     expected_result = pdb_dict[test]["expected_result"]
    #     result_to_test = pdb(**pdb_dict[test]["args"])

    #     self.assertEqual(result_to_test, expected_result)

    # def test_pdb_uniprot(self):
    #     test = "test4"
    #     expected_result = pdb_dict[test]["expected_result"]
    #     result_to_test = pdb(**pdb_dict[test]["args"])

    #     self.assertListEqual(result_to_test, expected_result)

    # def test_pdb_branched_entity_instance(self):
    #     test = "test5"
    #     expected_result = pdb_dict[test]["expected_result"]
    #     result_to_test = pdb(**pdb_dict[test]["args"])

    #     self.assertEqual(result_to_test, expected_result)

    # def test_pdb_nonpolymer_entity_instance(self):
    #     test = "test6"
    #     expected_result = pdb_dict[test]["expected_result"]
    #     result_to_test = pdb(**pdb_dict[test]["args"])

    #     self.assertEqual(result_to_test, expected_result)

    # def test_pdb_npolymer_entity_instance(self):
    #     test = "test7"
    #     expected_result = pdb_dict[test]["expected_result"]
    #     result_to_test = pdb(**pdb_dict[test]["args"])

    #     self.assertEqual(result_to_test, expected_result)

    # def test_pdb_entry(self):
    #     test = "test8"
    #     expected_result = pdb_dict[test]["expected_result"]
    #     result_to_test = pdb(**pdb_dict[test]["args"])

    #     self.assertEqual(result_to_test, expected_result)

    def test_pdb_pdb(self):
        test = "test9"
        pdb(**pdb_dict[test]["args"])

        # Expected result
        ref_path = pdb_dict[test]["expected_result"]
        self.assertTrue(
            filecmp.cmp("4ACQ.pdb", ref_path, shallow=False),
            "The reference and fetched PDB are not the same.",
        )

    def tearDown(self):
        super().tearDown()
        # Delete temporary result file
        try:
            os.remove("4ACQ.pdb")
        except OSError:
            pass
