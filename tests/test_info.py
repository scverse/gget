# import unittest.mock
import json
import unittest

import pandas as pd

# import time
from gget.gget_info import info

from .from_json import do_call, from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_info.json") as json_file:
    info_dict = json.load(json_file)

# Sleep time in seconds (wait [sleep_time] seconds between server requests to avoid 502 errors for WB and FB IDs)
# sleep_time = 15


_TEST_INFO_GENE_COLUMNS = [
    "ensembl_id",
    "uniprot_id",
    "ncbi_gene_id",
    "species",
    "assembly_name",
    "primary_gene_name",
    "ensembl_gene_name",
    "synonyms",
    "protein_names",
    "ensembl_description",
    "uniprot_description",
    "ncbi_description",
    "subcellular_localisation",
    "object_type",
    "biotype",
    "canonical_transcript",
    "seq_region_name",
    "strand",
    "start",
    "end",
    "all_transcripts",
    "transcript_biotypes",
    "transcript_names",
    "transcript_strands",
    "transcript_starts",
    "transcript_ends",
]

_BEST_EFFORT_INFO_COLUMNS = [
    "uniprot_id",
    "ncbi_gene_id",
    "synonyms",
    "protein_names",
    "uniprot_description",
    "ncbi_description",
    "subcellular_localisation",
]


def _assert_info_gene_core(name, td, func):
    def assert_info_gene_core(self: unittest.TestCase):
        test = name
        expected_result = pd.DataFrame(td[test]["expected_result"], columns=_TEST_INFO_GENE_COLUMNS)
        result_to_test = do_call(func, td[test]["args"])

        self.assertIsInstance(result_to_test, pd.DataFrame)

        result_to_test = result_to_test.dropna(axis=1)
        missing_columns = [col for col in expected_result.columns if col not in result_to_test.columns]
        missing_core_columns = [col for col in missing_columns if col not in _BEST_EFFORT_INFO_COLUMNS]

        self.assertEqual(missing_core_columns, [])

        expected_result = expected_result.drop(columns=missing_columns)

        pd.testing.assert_frame_equal(
            result_to_test.reset_index(drop=True),
            expected_result.reset_index(drop=True),
            check_dtype=False,
        )

    return assert_info_gene_core


class TestInfo(
    unittest.TestCase,
    metaclass=from_json(info_dict, info, {"assert_info_gene_core": _assert_info_gene_core}),
):
    pass  # all tests are loaded from json


# # todo convert to json loading once wormbase & flybase IDs are fixed. At that point, the json test framework will need a way to handle the ANY values
# class TestInfo(unittest.TestCase):
#     maxDiff = None

#     def test_info_WB_transcript(self):
#         test = "test2"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         time.sleep(sleep_time)
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     # def test_info_FB_gene(self):
#     #     test = "test3"
#     #     expected_result = info_dict[test]["expected_result"]
#     #     result_to_test = info(**info_dict[test]["args"])
#     #     time.sleep(sleep_time)
#     #     # If result is a DataFrame, convert to list
#     #     if isinstance(result_to_test, pd.DataFrame):
#     #         result_to_test = result_to_test.dropna(axis=1).values.tolist()

#     #     self.assertListEqual(result_to_test, expected_result)

#     def test_info_gene(self):
#         test = "test4"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     def test_info_transcript(self):
#         test = "test6"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     def test_info_mix(self):
#         test = "test7"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     def test_info_exon(self):
#         test = "test8"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     # def test_info_pdb(self):
#     #     test = "test9"
#     #     expected_result = info_dict[test]["expected_result"]
#     #     result_to_test = info(**info_dict[test]["args"])
#     #     # If result is a DataFrame, convert to list
#     #     if isinstance(result_to_test, pd.DataFrame):
#     #         result_to_test = result_to_test.dropna(axis=1).values.tolist()

#     #     self.assertListEqual(result_to_test, expected_result)

#     def test_info_ncbifalse_uniprottrue(self):
#         test = "test10"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     def test_info_ncbitrue_uniprotfalse(self):
#         test = "test11"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     def test_info_ncbifalse_uniprotfalse(self):
#         test = "test12"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)

#     # def test_info_ensembl_only(self):
#     #     test = "test13"
#     #     expected_result = info_dict[test]["expected_result"]
#     #     result_to_test = info(**info_dict[test]["args"])
#     #     # If result is a DataFrame, convert to list
#     #     if isinstance(result_to_test, pd.DataFrame):
#     #         result_to_test = result_to_test.dropna(axis=1).values.tolist()

#     #     self.assertListEqual(result_to_test, expected_result)

#     def test_info_bad_id(self):
#         test = "none_test1"
#         result_to_test = info(**info_dict[test]["args"])
#         self.assertIsNone(result_to_test, "Invalid argument return is not None.")

#     # # Expected result not part of the unittest dictionary because of the unittest.mock.ANY entries
#     # def test_info_WB_gene(self):
#     #     test = "test1"
#     #     result_to_test = info(**info_dict[test]["args"])
#     #     # If result is a DataFrame, convert to list
#     #     if isinstance(result_to_test, pd.DataFrame):
#     #         result_to_test = result_to_test.dropna(axis=1).values.tolist()

#     #     expected_result = [
#     #         [
#     #             "WBGene00043981",
#     #             "Q5WRS0",
#     #             "caenorhabditis_elegans",
#     #             "WBcel235",
#     #             "aaim-1",
#     #             "T14E8.4",
#     #             [],
#     #             "Protein aaim-1",
#     #             "Uncharacterized protein [Source:NCBI gene;Acc:3565421]",
#     #             "(Microbial infection) Promotes infection by microsporidian pathogens such as N.parisii in the early larval stages of development (PubMed:34994689). Involved in ensuring the proper orientation and location of the spore proteins of N.parisii during intestinal cell invasion (PubMed:34994689) Plays a role in promoting resistance to bacterial pathogens such as P.aeruginosa by inhibiting bacterial intestinal colonization",
#     #             ["Secreted"],
#     #             "Gene",
#     #             "protein_coding",
#     #             "T14E8.4.1.",
#     #             "X",
#     #             -1,
#     #             6559466,
#     #             6562428,
#     #             ["T14E8.4.1"],
#     #             ["protein_coding"],
#     #             [unittest.mock.ANY],
#     #             [-1],
#     #             [6559466],
#     #             [6562428],
#     #         ]
#     #     ]

#     #     self.assertListEqual(result_to_test, expected_result)

#     def test_info_gene_list_non_model(self):
#         test = "test5"
#         expected_result = info_dict[test]["expected_result"]
#         result_to_test = info(**info_dict[test]["args"])
#         # If result is a DataFrame, convert to list
#         if isinstance(result_to_test, pd.DataFrame):
#             result_to_test = result_to_test.dropna(axis=1).values.tolist()

#         self.assertListEqual(result_to_test, expected_result)
