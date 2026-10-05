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


class TestInfoExpandFallback(unittest.TestCase):
    """Network-free tests for the Ensembl lookup/id 'expand' handling.

    Ensembl rejects 'expand' for exon and translation IDs and fails the whole batch
    (HTTP 400/500) when one is included.
    """

    def test_exon_and_translation_ids_detected(self):
        from gget.gget_info import _is_exon_or_translation_id

        for exon_or_translation in [
            "ENSE00001234567",
            "ENSTGUEE00000179311",
            "ENSP00000354587",
            "ENSMUSP00000000001.2",
        ]:
            self.assertTrue(_is_exon_or_translation_id(exon_or_translation), exon_or_translation)
        for other in [
            "ENSG00000187272",
            "EnsMUSG00000000001",
            "ENST00000254072.7",
            "ENSPPYG00000000001",
            "WBGene00000001",
        ]:
            self.assertFalse(_is_exon_or_translation_id(other), other)

    def test_batch_failure_falls_back_to_single_ids(self):
        from unittest.mock import patch

        from gget.gget_info import _lookup_with_expand

        def fake_post(server, endpoint, query):
            if len(query["ids"]) > 1 or query["ids"] == ["BAD"]:
                raise RuntimeError("500")
            return {query["ids"][0]: {"id": query["ids"][0]}}

        with patch("gget.gget_info.post_query", side_effect=fake_post) as mock_post:
            result = _lookup_with_expand("s/", "lookup/id/", ["G1", "BAD", "G2"])

        self.assertEqual(set(result), {"G1", "G2"})
        # one batch attempt + one request per ID, all with expand
        self.assertEqual(mock_post.call_count, 4)
        self.assertTrue(all(c.args[2]["expand"] for c in mock_post.call_args_list))

    def test_info_queries_exons_without_expand(self):
        from unittest.mock import patch

        queries = []

        def fake_post(server, endpoint, query):
            queries.append(query)
            return {
                i: {"id": i, "version": 1, "object_type": "Exon", "species": "taeniopygia_guttata"}
                for i in query["ids"]
            }

        with patch("gget.gget_info.post_query", side_effect=fake_post):
            info("ENSTGUEE00000179311", ncbi=False, uniprot=False, pdb=False, verbose=False)

        self.assertEqual(queries, [{"ids": ["ENSTGUEE00000179311"]}])
