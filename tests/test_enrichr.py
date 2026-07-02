import json
import math
import os
import tempfile
import unittest
from unittest.mock import patch

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import requests

from .from_json import from_json

# Prevent matplotlib from opening windows
matplotlib.use("Agg")
import gget.gget_enrichr as gget_enrichr
from gget.gget_enrichr import enrichr, enrichr_libraries, enrichr_library

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

    def _live_library(self, **kwargs):
        """Call enrichr_library live, skipping (not failing) on transient network/Enrichr issues.

        A genuine network error, or Enrichr transiently returning a non-data response (e.g. a
        rate-limit/HTML page, which enrichr_library raises as RuntimeError), is treated as a skip
        so these live tests don't go red on upstream hiccups. The exact-count anchors below are
        stable because MSigDB_Hallmark_2020 is a frozen (2020) snapshot.
        """
        try:
            return enrichr_library(**kwargs)
        except requests.RequestException as e:
            self.skipTest(f"Network error reaching Enrichr: {e}")
        except RuntimeError as e:
            self.skipTest(f"Enrichr did not return library data (transient): {e}")

    def test_enrichr_library(self):
        td = enrichr_dict["test_enrichr_library"]
        df = self._live_library(**td["args"])
        self.assertListEqual(list(df.columns), ["gene_set", "gene"])
        self.assertEqual(df["gene_set"].nunique(), td["expected_n_sets"])

    def test_enrichr_library_gene_set(self):
        td = enrichr_dict["test_enrichr_library_gene_set"]
        df = self._live_library(**td["args"])
        self.assertEqual(set(df["gene_set"]), {td["args"]["gene_set"]})
        self.assertEqual(len(df), td["expected_n_genes"])

    def test_enrichr_library_json(self):
        td = enrichr_dict["test_enrichr_library_json"]
        result = self._live_library(**td["args"])
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), td["expected_n_sets"])

    def test_enrichr_library_bad(self):
        # A bad library name must raise RuntimeError; a real network error is a skip, not a failure.
        try:
            with self.assertRaises(RuntimeError):
                enrichr_library("NOT_A_LIBRARY_xyz", verbose=False)
        except requests.RequestException as e:
            self.skipTest(f"Network error reaching Enrichr: {e}")

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


class _FakeResponse:
    """Minimal stand-in for a requests.Response used to test enrichr_library offline."""

    def __init__(self, text, ok=True):
        self.text = text
        self.ok = ok


# A valid Enrichr gene-set-library text payload (tab-separated, with a blank line).
_LIBRARY_TEXT = "SET_A\t\tGENE1\tGENE2\tGENE3\n\nSET_B\tdescription\tGENE4\tGENE5\n"


class TestEnrichrLibraryOffline(unittest.TestCase):
    """Network-free tests of enrichr_library parsing/branches (issue #139)."""

    def test_invalid_species_raises(self):
        with self.assertRaises(ValueError):
            enrichr_library("MSigDB_Hallmark_2020", species="martian", verbose=False)

    @patch.object(gget_enrichr.requests, "get")
    def test_parse_verbose(self, mock_get):
        # Covers verbose logging, the blank-line skip, and full parsing.
        mock_get.return_value = _FakeResponse(_LIBRARY_TEXT)
        df = enrichr_library("MSigDB_Hallmark_2020", verbose=True)
        self.assertEqual(list(df.columns), ["gene_set", "gene"])
        self.assertEqual(set(df["gene_set"]), {"SET_A", "SET_B"})
        self.assertEqual(df.shape[0], 5)

    @patch.object(gget_enrichr.requests, "get")
    def test_bad_library_html_raises(self, mock_get):
        # Enrichr returns an HTML page for unknown library names.
        mock_get.return_value = _FakeResponse("<html>HTTP Status 404</html>")
        with self.assertRaises(RuntimeError):
            enrichr_library("DoesNotExist", verbose=False)

    @patch.object(gget_enrichr.requests, "get")
    def test_empty_library_raises(self, mock_get):
        # A response whose sets contain no member genes is treated as empty.
        mock_get.return_value = _FakeResponse("SET_A\tdescription\n")
        with self.assertRaises(RuntimeError):
            enrichr_library("EmptyLib", verbose=False)

    @patch.object(gget_enrichr.requests, "get")
    def test_gene_set_filter(self, mock_get):
        mock_get.return_value = _FakeResponse(_LIBRARY_TEXT)
        df = enrichr_library("MSigDB_Hallmark_2020", gene_set="SET_A", verbose=False)
        self.assertEqual(set(df["gene_set"]), {"SET_A"})

    @patch.object(gget_enrichr.requests, "get")
    def test_gene_set_not_found_raises(self, mock_get):
        mock_get.return_value = _FakeResponse(_LIBRARY_TEXT)
        with self.assertRaises(ValueError):
            enrichr_library("MSigDB_Hallmark_2020", gene_set="NOPE", verbose=False)

    @patch.object(gget_enrichr.requests, "get")
    def test_json_and_save(self, mock_get):
        # Covers the json return, json+save, and CSV save branches.
        mock_get.return_value = _FakeResponse(_LIBRARY_TEXT)
        result = enrichr_library("MSigDB_Hallmark_2020", json=True, verbose=False)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["SET_A"], ["GENE1", "GENE2", "GENE3"])
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                enrichr_library("MSigDB_Hallmark_2020", save=True, verbose=False)
                self.assertTrue(any(f.endswith(".csv") for f in os.listdir(".")))
                enrichr_library("MSigDB_Hallmark_2020", json=True, save=True, verbose=False)
                self.assertTrue(any(f.endswith(".json") for f in os.listdir(".")))
            finally:
                os.chdir(cwd)

    @patch.object(gget_enrichr.requests, "get")
    def test_descriptions(self, mock_get):
        # descriptions=True keeps the (often empty) description field.
        mock_get.return_value = _FakeResponse(_LIBRARY_TEXT)
        df = enrichr_library("MSigDB_Hallmark_2020", descriptions=True, verbose=False)
        self.assertEqual(list(df.columns), ["gene_set", "description", "gene"])
        self.assertEqual(df[df["gene_set"] == "SET_B"]["description"].iloc[0], "description")
        self.assertEqual(df[df["gene_set"] == "SET_A"]["description"].iloc[0], "")
        # json + descriptions -> {set: {"description", "genes"}}
        result = enrichr_library("MSigDB_Hallmark_2020", descriptions=True, json=True, verbose=False)
        self.assertEqual(result["SET_B"], {"description": "description", "genes": ["GENE4", "GENE5"]})


class _FakeJsonResponse:
    """Minimal stand-in for a requests.Response returning JSON (for enrichr_libraries)."""

    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


_STATS_PAYLOAD = {
    "statistics": [
        {"libraryName": "MSigDB_Hallmark_2020", "numTerms": 50, "geneCoverage": 4383, "genesPerTerm": 146},
        {"libraryName": "KEGG_2021_Human", "numTerms": 300, "geneCoverage": 8000, "genesPerTerm": 90},
        {"libraryName": "MSigDB_Computational", "numTerms": 858, "geneCoverage": 10061, "genesPerTerm": 106},
    ]
}


class TestEnrichrLibrariesOffline(unittest.TestCase):
    """Network-free tests of enrichr_libraries (library discovery, issue #139)."""

    def test_invalid_species_raises(self):
        with self.assertRaises(ValueError):
            enrichr_libraries(species="martian", verbose=False)

    @patch.object(gget_enrichr.requests, "get")
    def test_list_columns_and_sort(self, mock_get):
        mock_get.return_value = _FakeJsonResponse(_STATS_PAYLOAD)
        df = enrichr_libraries(verbose=True)
        self.assertEqual(list(df.columns), ["library", "num_terms", "gene_coverage", "genes_per_term"])
        # Sorted case-insensitively by library name
        self.assertEqual(list(df["library"]), ["KEGG_2021_Human", "MSigDB_Computational", "MSigDB_Hallmark_2020"])

    @patch.object(gget_enrichr.requests, "get")
    def test_filter_case_insensitive(self, mock_get):
        mock_get.return_value = _FakeJsonResponse(_STATS_PAYLOAD)
        df = enrichr_libraries(filter="msigdb", verbose=False)
        self.assertEqual(set(df["library"]), {"MSigDB_Hallmark_2020", "MSigDB_Computational"})

    @patch.object(gget_enrichr.requests, "get")
    def test_json_return(self, mock_get):
        mock_get.return_value = _FakeJsonResponse(_STATS_PAYLOAD)
        result = enrichr_libraries(filter="Hallmark", json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["library"], "MSigDB_Hallmark_2020")

    @patch.object(gget_enrichr.requests, "get")
    def test_bad_status_raises(self, mock_get):
        mock_get.return_value = _FakeJsonResponse({}, ok=False, status_code=503)
        with self.assertRaises(RuntimeError):
            enrichr_libraries(verbose=False)
