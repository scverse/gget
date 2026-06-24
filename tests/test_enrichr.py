import json
import math
import unittest

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from .from_json import from_json

# Prevent matplotlib from opening windows
matplotlib.use("Agg")
from gget.gget_enrichr import enrichr, enrichr_library

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_enrichr.json") as json_file:
    enrichr_dict = json.load(json_file)


class TestEnrichr(unittest.TestCase, metaclass=from_json(enrichr_dict, enrichr)):
    pass  # Note: some tests are generated from json

    def test_enrichr_bad_gene(self):
        test = "test_enrichr_bad_gene"
        df = enrichr(**enrichr_dict[test]["args"])

        self.assertTrue(df.empty, "Invalid gene result is not empty data frame.")

    def test_enrichr_background(self):
        test = "test_enrichr_background"
        expected_result = enrichr_dict[test]["expected_result"]
        result_to_test = enrichr(**enrichr_dict[test]["args"])
        # If result is a DataFrame, convert to list
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = result_to_test.values.tolist()[:20]
            result_to_test = [[x if x != math.inf else "inf" for x in i] for i in result_to_test]

        self.assertListEqual(result_to_test, expected_result)

    def test_enrichr_background_ensembl(self):
        test = "test_enrichr_background_ensembl"
        expected_result = enrichr_dict[test]["expected_result"]
        result_to_test = enrichr(**enrichr_dict[test]["args"])
        # If result is a DataFrame, convert to list
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = result_to_test.values.tolist()
            result_to_test = [[x if x != math.inf else "inf" for x in i] for i in result_to_test]

        self.assertListEqual(result_to_test, expected_result)

    def test_enrichr_library(self):
        test = "test_enrichr_library"
        td = enrichr_dict[test]
        df = enrichr_library(**td["args"])
        self.assertListEqual(list(df.columns), ["gene_set", "gene"])
        self.assertEqual(df["gene_set"].nunique(), td["expected_n_sets"])

    def test_enrichr_library_gene_set(self):
        test = "test_enrichr_library_gene_set"
        td = enrichr_dict[test]
        df = enrichr_library(**td["args"])
        self.assertEqual(set(df["gene_set"]), {td["args"]["gene_set"]})
        self.assertEqual(len(df), td["expected_n_genes"])

    def test_enrichr_library_json(self):
        test = "test_enrichr_library_json"
        td = enrichr_dict[test]
        result = enrichr_library(**td["args"])
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), td["expected_n_sets"])

    def test_enrichr_library_bad(self):
        with self.assertRaises(RuntimeError):
            enrichr_library("NOT_A_LIBRARY_xyz", verbose=False)

    def test_enrichr_plot(self):
        # Number of plots before running enrichr plot
        num_figures_before = plt.gcf().number
        enrichr(
            [
                "AIMP1",
                "MFHAS1",
                "BFAR",
                "FUNDC1",
                "AIMP2",
                "ASF1A",
                "FUNDC2",
                "TRMT112",
                "MTHFD2L",
            ],
            database="transcription",
            plot=True,
        )
        # Number of plots after running enrichr plot
        num_figures_after = plt.gcf().number

        self.assertGreater(
            num_figures_after,
            num_figures_before,
            "No matplotlib plt object was created.",
        )
