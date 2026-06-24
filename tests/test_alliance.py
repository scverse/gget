import json
import os
import tempfile
import unittest
from unittest.mock import patch

import gget.gget_alliance as gget_alliance
import requests
from gget.gget_alliance import _gene_row, _is_gene_id, _search_row, alliance

from .from_json import from_json

with open("./tests/fixtures/test_alliance.json") as json_file:
    alliance_dict = json.load(json_file)


class TestAlliance(unittest.TestCase, metaclass=from_json(alliance_dict, alliance)):
    pass  # tests loaded from json


class _FakeResponse:
    """Minimal stand-in for a requests.Response used to test parsing offline."""

    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


_GENE_PAYLOAD = {
    "category": "gene_summary",
    "gene": {
        "primaryExternalId": "HGNC:1101",
        "geneSymbol": {"displayText": "BRCA2", "formatText": "BRCA2"},
        "geneFullName": {"displayText": "BRCA2 DNA repair associated"},
        "geneType": {"name": "protein_coding_gene"},
        "geneSynonyms": [{"displayText": "FAD"}, {"displayText": "FACD"}],
        "taxon": {"curie": "NCBITaxon:9606", "name": "Homo sapiens"},
        "dataProvider": {"abbreviation": "RGD"},
    },
}

_SEARCH_PAYLOAD = {
    "results": [
        {
            "id": "HGNC:1101",
            "symbol": "BRCA2",
            "name": "BRCA2 DNA repair associated",
            "species": "Homo sapiens",
            "category": "gene_search_result",
            "soTermName": "protein_coding_gene",
        },
        {
            "id": "MGI:109337",
            "symbol": "Brca2",
            "name": "breast cancer 2",
            "species": "Mus musculus",
            "category": "gene_search_result",
            "soTermName": "protein_coding_gene",
        },
    ]
}


class TestAllianceHelpers(unittest.TestCase):
    """Network-free tests of the Alliance helpers (issue #162)."""

    def test_is_gene_id(self):
        self.assertTrue(_is_gene_id("HGNC:1101"))
        self.assertTrue(_is_gene_id("MGI:109337"))
        self.assertTrue(_is_gene_id("rgd:2219"))
        self.assertFalse(_is_gene_id("brca2"))
        self.assertFalse(_is_gene_id("breast cancer"))

    def test_gene_row(self):
        row = _gene_row(_GENE_PAYLOAD["gene"])
        self.assertEqual(row["id"], "HGNC:1101")
        self.assertEqual(row["symbol"], "BRCA2")
        self.assertEqual(row["name"], "BRCA2 DNA repair associated")
        self.assertEqual(row["species"], "Homo sapiens")
        self.assertEqual(row["taxon"], "NCBITaxon:9606")
        self.assertEqual(row["gene_type"], "protein_coding_gene")
        self.assertEqual(row["synonyms"], ["FAD", "FACD"])
        self.assertEqual(row["data_provider"], "RGD")

    def test_search_row(self):
        row = _search_row(_SEARCH_PAYLOAD["results"][0])
        self.assertEqual(row["id"], "HGNC:1101")
        self.assertEqual(row["symbol"], "BRCA2")
        self.assertEqual(row["species"], "Homo sapiens")

    @patch.object(gget_alliance.requests, "get")
    def test_gene_id_mode(self, mock_get):
        mock_get.return_value = _FakeResponse(_GENE_PAYLOAD)
        df = alliance("HGNC:1101", verbose=False)
        self.assertEqual(list(df.columns), gget_alliance._GENE_COLUMNS)
        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df.iloc[0]["symbol"], "BRCA2")

    @patch.object(gget_alliance.requests, "get")
    def test_search_mode_json(self, mock_get):
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        result = alliance("brca2", json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "HGNC:1101")

    @patch.object(gget_alliance.requests, "get")
    def test_category_mapping(self, mock_get):
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        alliance("brca2", category="gene", verbose=False)
        # Confirm the friendly category was mapped to the API value
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["category"], "gene_search_result")

    @patch.object(gget_alliance.requests, "get")
    def test_no_results_returns_none(self, mock_get):
        mock_get.return_value = _FakeResponse({"results": []})
        self.assertIsNone(alliance("nonexistent xyz", verbose=False))

    @patch.object(gget_alliance.requests, "get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = _FakeResponse({}, ok=False, status_code=500)
        with self.assertRaises(RuntimeError):
            alliance("brca2", verbose=False)

    def test_empty_search_term_raises(self):
        # Covers the empty/None search_term ValueError branch.
        with self.assertRaises(ValueError):
            alliance("  ", verbose=False)

    def test_text_passthrough(self):
        # Covers the non-dict passthrough branch of _text.
        self.assertEqual(gget_alliance._text("plain"), "plain")
        self.assertIsNone(gget_alliance._text(None))

    @patch.object(gget_alliance.requests, "get")
    def test_request_exception_raises(self, mock_get):
        # Covers the requests.RequestException -> RuntimeError branch in _alliance_get.
        mock_get.side_effect = requests.exceptions.ConnectionError("no network")
        with self.assertRaises(RuntimeError):
            alliance("brca2", verbose=False)

    @patch.object(gget_alliance.requests, "get")
    def test_404_raises(self, mock_get):
        # Covers the 404 -> ValueError branch in _alliance_get.
        mock_get.return_value = _FakeResponse({}, ok=False, status_code=404)
        with self.assertRaises(ValueError):
            alliance("HGNC:1101", verbose=False)

    @patch.object(gget_alliance.requests, "get")
    def test_gene_not_found_verbose(self, mock_get):
        # Covers the gene-path verbose log and the "no gene found" branch.
        mock_get.return_value = _FakeResponse({"gene": None})
        self.assertIsNone(alliance("HGNC:9999", verbose=True))

    @patch.object(gget_alliance.requests, "get")
    def test_search_verbose(self, mock_get):
        # Covers the search-path verbose log line.
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        df = alliance("brca2", verbose=True)
        self.assertEqual(df.shape[0], 2)

    @patch.object(gget_alliance.requests, "get")
    def test_save_csv_and_json(self, mock_get):
        # Covers the save-to-CSV and json+save branches.
        mock_get.return_value = _FakeResponse(_GENE_PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                alliance("HGNC:1101", save=True, verbose=False)
                self.assertTrue(any(f.endswith(".csv") for f in os.listdir(".")))
                alliance("HGNC:1101", save=True, json=True, verbose=False)
                self.assertTrue(any(f.endswith(".json") for f in os.listdir(".")))
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
