import json
import os
import tempfile
import unittest
from unittest.mock import patch

import gget.gget_rummage as gget_rummage
import requests
from gget.gget_rummage import _clean_genes, rummagene, rummageo

from .from_json import from_json

# Load dictionaries containing arguments and expected results
with open("./tests/fixtures/test_rummagene.json") as json_file:
    rummagene_dict = json.load(json_file)

with open("./tests/fixtures/test_rummageo.json") as json_file:
    rummageo_dict = json.load(json_file)


class TestRummagene(unittest.TestCase, metaclass=from_json(rummagene_dict, rummagene)):
    pass  # tests loaded from json


class TestRummageo(unittest.TestCase, metaclass=from_json(rummageo_dict, rummageo)):
    pass  # tests loaded from json


class _FakeResponse:
    """Minimal stand-in for a requests.Response used to test parsing offline."""

    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


# Canned GraphQL payloads mirroring the live Rummagene / RummaGEO responses
_RUMMAGENE_PAYLOAD = {
    "data": {
        "currentBackground": {
            "enrich": {
                "totalCount": 2,
                "nodes": [
                    {
                        "pvalue": 1e-10,
                        "adjPvalue": 1e-8,
                        "oddsRatio": 500.0,
                        "nOverlap": 8,
                        "geneSets": {"nodes": [{"term": "PMC123-table1-up", "nGeneIds": 30}]},
                    },
                    {
                        "pvalue": 1e-5,
                        "adjPvalue": 1e-3,
                        "oddsRatio": 100.0,
                        "nOverlap": 5,
                        "geneSets": {"nodes": [{"term": "PMC456-table2-down", "nGeneIds": 40}]},
                    },
                ],
            }
        }
    }
}

_RUMMAGEO_PAYLOAD = {
    "data": {
        "currentBackground": {
            "enrich": {
                "totalCount": 1,
                "nodes": [
                    {
                        "pvalue": 2e-9,
                        "adjPvalue": 2e-7,
                        "oddsRatio": 400.0,
                        "nOverlap": 7,
                        "geneSet": {"term": "GSE123-2-vs-1-human up", "nGeneIds": 50, "species": "human"},
                    }
                ],
            }
        }
    }
}


class TestRummageParsing(unittest.TestCase):
    """Network-free tests of the shared enrichment parsing logic (issue #164)."""

    def test_clean_genes(self):
        self.assertEqual(_clean_genes("STAT1"), ["STAT1"])
        self.assertEqual(_clean_genes([" STAT1 ", "IRF1", "", None, "nan"]), ["STAT1", "IRF1"])
        with self.assertRaises(ValueError):
            _clean_genes([])

    @patch.object(gget_rummage.requests, "post")
    def test_rummagene_parsing(self, mock_post):
        mock_post.return_value = _FakeResponse(_RUMMAGENE_PAYLOAD)
        df = rummagene(["STAT1", "IRF1"], verbose=False)
        self.assertEqual(
            list(df.columns),
            ["rank", "term", "n_overlap", "n_genes_in_set", "odds_ratio", "pval", "adj_pval"],
        )
        self.assertEqual(df.shape[0], 2)
        self.assertEqual(df.iloc[0]["rank"], 1)
        self.assertEqual(df.iloc[0]["term"], "PMC123-table1-up")
        self.assertEqual(df.iloc[0]["n_overlap"], 8)

    @patch.object(gget_rummage.requests, "post")
    def test_rummagene_json_and_limit(self, mock_post):
        mock_post.return_value = _FakeResponse(_RUMMAGENE_PAYLOAD)
        result = rummagene(["STAT1"], limit=1, json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["term"], "PMC123-table1-up")

    @patch.object(gget_rummage.requests, "post")
    def test_rummageo_parsing(self, mock_post):
        mock_post.return_value = _FakeResponse(_RUMMAGEO_PAYLOAD)
        df = rummageo(["STAT1", "IRF1"], verbose=False)
        self.assertEqual(
            list(df.columns),
            ["rank", "term", "species", "n_overlap", "n_genes_in_set", "odds_ratio", "pval", "adj_pval"],
        )
        self.assertEqual(df.iloc[0]["species"], "human")
        self.assertEqual(df.iloc[0]["term"], "GSE123-2-vs-1-human up")

    @patch.object(gget_rummage.requests, "post")
    def test_no_results_returns_none(self, mock_post):
        empty = {"data": {"currentBackground": {"enrich": {"totalCount": 0, "nodes": []}}}}
        mock_post.return_value = _FakeResponse(empty)
        self.assertIsNone(rummagene(["STAT1"], verbose=False))

    @patch.object(gget_rummage.requests, "post")
    def test_graphql_error_raises(self, mock_post):
        mock_post.return_value = _FakeResponse({"errors": [{"message": "boom"}]})
        with self.assertRaises(RuntimeError):
            rummagene(["STAT1"], verbose=False)

    @patch.object(gget_rummage.requests, "post")
    def test_http_error_raises(self, mock_post):
        mock_post.return_value = _FakeResponse({}, ok=False, status_code=500)
        with self.assertRaises(RuntimeError):
            rummageo(["STAT1"], verbose=False)

    @patch.object(gget_rummage.requests, "post")
    def test_filter_term_and_verbose(self, mock_post):
        # Covers the filter_term variable branch and the verbose logging line.
        mock_post.return_value = _FakeResponse(_RUMMAGENE_PAYLOAD)
        rummagene(["STAT1"], filter_term="cancer", verbose=True)
        sent_variables = mock_post.call_args.kwargs["json"]["variables"]
        self.assertEqual(sent_variables["filterTerm"], "cancer")

    @patch.object(gget_rummage.requests, "post")
    def test_request_exception_raises(self, mock_post):
        # Covers the requests.RequestException -> RuntimeError branch.
        mock_post.side_effect = requests.exceptions.ConnectionError("no network")
        with self.assertRaises(RuntimeError):
            rummagene(["STAT1"], verbose=False)

    @patch.object(gget_rummage.requests, "post")
    def test_save_csv(self, mock_post):
        # Covers the save-to-CSV branch.
        mock_post.return_value = _FakeResponse(_RUMMAGENE_PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                rummagene(["STAT1"], save=True, verbose=False)
                self.assertTrue(os.path.exists("gget_rummagene_results.csv"))
            finally:
                os.chdir(cwd)

    @patch.object(gget_rummage.requests, "post")
    def test_save_json(self, mock_post):
        # Covers the json + save branch.
        mock_post.return_value = _FakeResponse(_RUMMAGENE_PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                result = rummagene(["STAT1"], save=True, json=True, verbose=False)
                self.assertIsInstance(result, list)
                self.assertTrue(os.path.exists("gget_rummagene_results.json"))
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
