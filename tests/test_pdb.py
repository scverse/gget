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

    def test_pdb_mmcif(self):
        # Explicit PDBx/mmCIF download returns a CIF document (starts with "data_<ID>")
        result = pdb("4ACQ", resource="mmcif")
        self.assertTrue(
            result.startswith("data_4ACQ"),
            "resource='mmcif' did not return a PDBx/mmCIF document.",
        )

    def test_pdb_legacy_fallback_to_mmcif(self):
        # Regression test for #177/#178: 6Q38 has no legacy PDB file, so a
        # resource='pdb' request must transparently fall back to PDBx/mmCIF.
        result = pdb("6Q38", resource="pdb")
        self.assertTrue(
            result.startswith("data_6Q38"),
            "resource='pdb' did not fall back to PDBx/mmCIF when the legacy PDB file is missing.",
        )

    def tearDown(self):
        super().tearDown()
        # Delete temporary result files
        for fname in ("4ACQ.pdb", "4ACQ.cif", "6Q38.cif"):
            try:
                os.remove(fname)
            except OSError:
                pass
