import json
import os
import tempfile
import unittest
from unittest.mock import patch

import gget.gget_ucsc as gget_ucsc
import requests
from gget.gget_ucsc import _match_rows, _parse_position, ucsc

from .from_json import from_json

with open("./tests/fixtures/test_ucsc.json") as json_file:
    ucsc_dict = json.load(json_file)


class TestUcsc(unittest.TestCase, metaclass=from_json(ucsc_dict, ucsc)):
    pass  # tests loaded from json


class _FakeResponse:
    """Minimal stand-in for a requests.Response used to test parsing offline."""

    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


_SEARCH_PAYLOAD = {
    "genome": "hg38",
    "positionMatches": [
        {
            "trackName": "knownGene",
            "description": "GENCODE",
            "matches": [
                {
                    "position": "chr13:32315508-32400268",
                    "hgFindMatches": "ENST00000380152.8",
                    "posName": "BRCA2 (ENST00000380152.8)",
                    "description": "breast cancer type 2 susceptibility protein",
                }
            ],
        },
        {
            "trackName": "hgnc",
            "description": "HUGO Gene Nomenclature",
            "matches": [
                {
                    "position": "chr13:32315086-32400268",
                    "hgFindMatches": "HGNC%3A1101",
                    "posName": "BRCA2",
                    "description": None,
                }
            ],
        },
    ],
}


class TestUcscHelpers(unittest.TestCase):
    """Network-free tests of the UCSC helpers (issue #18)."""

    def test_parse_position(self):
        self.assertEqual(_parse_position("chr13:32315508-32400268"), ("chr13", 32315508, 32400268))
        self.assertEqual(_parse_position("chrX"), ("chrX", None, None))
        self.assertEqual(_parse_position(None), (None, None, None))

    def test_match_rows_decoding(self):
        rows = _match_rows(_SEARCH_PAYLOAD["positionMatches"][1])
        self.assertEqual(rows[0]["ucsc_id"], "HGNC:1101")  # URL-decoded
        self.assertEqual(rows[0]["track"], "hgnc")
        # description falls back to the group description when the match has none
        self.assertEqual(rows[0]["description"], "HUGO Gene Nomenclature")

    @patch.object(gget_ucsc.requests, "get")
    def test_search(self, mock_get):
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        df = ucsc("BRCA2", verbose=False)
        self.assertEqual(list(df.columns), gget_ucsc._COLUMNS)
        self.assertEqual(df.shape[0], 2)
        self.assertEqual(df.iloc[0]["ucsc_id"], "ENST00000380152.8")
        self.assertEqual(df.iloc[0]["chrom"], "chr13")
        self.assertEqual(df.iloc[0]["start"], 32315508)

    @patch.object(gget_ucsc.requests, "get")
    def test_track_filter(self, mock_get):
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        df = ucsc("BRCA2", track="knownGene", verbose=False)
        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df.iloc[0]["track"], "knownGene")

    @patch.object(gget_ucsc.requests, "get")
    def test_limit_and_json(self, mock_get):
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        result = ucsc("BRCA2", limit=1, json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch.object(gget_ucsc.requests, "get")
    def test_no_results_returns_none(self, mock_get):
        mock_get.return_value = _FakeResponse({"positionMatches": []})
        self.assertIsNone(ucsc("nonexistentxyz", verbose=False))

    @patch.object(gget_ucsc.requests, "get")
    def test_error_payload_raises(self, mock_get):
        mock_get.return_value = _FakeResponse({"error": "No such genome 'banana'"})
        with self.assertRaises(ValueError):
            ucsc("BRCA2", genome="banana", verbose=False)

    @patch.object(gget_ucsc.requests, "get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = _FakeResponse({}, ok=False, status_code=500)
        with self.assertRaises(RuntimeError):
            ucsc("BRCA2", verbose=False)

    def test_empty_search_term_raises(self):
        # Covers the empty/None search_term ValueError branch.
        with self.assertRaises(ValueError):
            ucsc("   ", verbose=False)

    def test_parse_position_no_range(self):
        # Covers the "chrom with colon but no range" branch of _parse_position.
        self.assertEqual(_parse_position("chr1:5000"), ("chr1", None, None))

    @patch.object(gget_ucsc.requests, "get")
    def test_search_verbose(self, mock_get):
        # Covers the verbose logging line.
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        df = ucsc("BRCA2", verbose=True)
        self.assertEqual(df.shape[0], 2)

    @patch.object(gget_ucsc.requests, "get")
    def test_request_exception_raises(self, mock_get):
        # Covers the requests.RequestException -> RuntimeError branch.
        mock_get.side_effect = requests.exceptions.ConnectionError("no network")
        with self.assertRaises(RuntimeError):
            ucsc("BRCA2", verbose=False)

    @patch.object(gget_ucsc.requests, "get")
    def test_save_csv_and_json(self, mock_get):
        # Covers the save-to-CSV and json+save branches.
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                ucsc("BRCA2", save=True, verbose=False)
                self.assertTrue(os.path.exists("gget_ucsc_results.csv"))
                ucsc("BRCA2", save=True, json=True, verbose=False)
                self.assertTrue(os.path.exists("gget_ucsc_results.json"))
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
