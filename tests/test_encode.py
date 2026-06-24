import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import gget.gget_encode as gget_encode
import pandas as pd
import requests
from gget.gget_encode import _files_to_df, _is_encode_accession, _search_row, encode

from .from_json import from_json

with open("./tests/fixtures/test_encode.json") as json_file:
    encode_dict = json.load(json_file)


class TestEncode(unittest.TestCase, metaclass=from_json(encode_dict, encode)):
    pass  # tests loaded from json


class _FakeResponse:
    """Minimal stand-in for a requests.Response used to test ENCODE parsing offline."""

    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


_EXPERIMENT_PAYLOAD = {
    "@type": ["Experiment", "Dataset", "Item"],
    "accession": "ENCSR000AKS",
    "files": [
        {
            "accession": "ENCFF000BXK",
            "file_format": "bam",
            "output_type": "alignments",
            "assembly": "GRCh38",
            "file_size": 123,
            "status": "released",
            "href": "/files/ENCFF000BXK/@@download/ENCFF000BXK.bam",
        },
        {
            "accession": "ENCFF000BXM",
            "file_format": "bigBed",
            "output_type": "peaks",
            "assembly": "hg19",
            "file_size": 456,
            "status": "released",
            "href": "/files/ENCFF000BXM/@@download/ENCFF000BXM.bigBed",
        },
    ],
}

_FILE_PAYLOAD = {
    "@type": ["File", "Item"],
    "accession": "ENCFF000BXK",
    "file_format": "bam",
    "output_type": "alignments",
    "assembly": "GRCh38",
    "file_size": 123,
    "status": "released",
    "href": "/files/ENCFF000BXK/@@download/ENCFF000BXK.bam",
}

_SEARCH_PAYLOAD = {
    "@graph": [
        {
            "accession": "ENCSR111AAA",
            "assay_title": "TF ChIP-seq",
            "biosample_summary": "Homo sapiens K562",
            "target": {"label": "CTCF"},
            "description": "desc",
            "status": "released",
            "lab": {"title": "Some Lab"},
        }
    ]
}


class TestEncodeHelpers(unittest.TestCase):
    """Network-free tests of the ENCODE helpers (issue #151)."""

    def test_is_accession(self):
        self.assertTrue(_is_encode_accession("ENCSR000AKS"))
        self.assertTrue(_is_encode_accession("ENCFF000BXK"))
        self.assertFalse(_is_encode_accession("CTCF K562"))
        self.assertFalse(_is_encode_accession("chip-seq"))

    def test_files_to_df_and_filter(self):
        df = _files_to_df(_EXPERIMENT_PAYLOAD["files"])
        self.assertEqual(list(df.columns), gget_encode._FILE_COLUMNS)
        self.assertEqual(df.shape[0], 2)
        self.assertEqual(
            df.iloc[0]["url"], "https://www.encodeproject.org/files/ENCFF000BXK/@@download/ENCFF000BXK.bam"
        )
        # Filter by assembly
        df2 = _files_to_df(_EXPERIMENT_PAYLOAD["files"], assembly="GRCh38")
        self.assertEqual(df2.shape[0], 1)
        self.assertEqual(df2.iloc[0]["file_accession"], "ENCFF000BXK")
        # Filter by file_format
        df3 = _files_to_df(_EXPERIMENT_PAYLOAD["files"], file_format="bigBed")
        self.assertEqual(df3.shape[0], 1)
        self.assertEqual(df3.iloc[0]["file_format"], "bigBed")

    def test_search_row(self):
        row = _search_row(_SEARCH_PAYLOAD["@graph"][0])
        self.assertEqual(row["accession"], "ENCSR111AAA")
        self.assertEqual(row["target"], "CTCF")
        self.assertEqual(row["lab"], "Some Lab")

    @patch.object(gget_encode.requests, "get")
    def test_experiment_accession(self, mock_get):
        mock_get.return_value = _FakeResponse(_EXPERIMENT_PAYLOAD)
        df = encode("ENCSR000AKS", verbose=False)
        self.assertEqual(list(df.columns), gget_encode._FILE_COLUMNS)
        self.assertEqual(df.shape[0], 2)

    @patch.object(gget_encode.requests, "get")
    def test_file_accession(self, mock_get):
        mock_get.return_value = _FakeResponse(_FILE_PAYLOAD)
        df = encode("ENCFF000BXK", verbose=False)
        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df.iloc[0]["file_accession"], "ENCFF000BXK")

    @patch.object(gget_encode.requests, "get")
    def test_search_mode_json(self, mock_get):
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        result = encode("CTCF K562", json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["accession"], "ENCSR111AAA")
        self.assertEqual(result[0]["target"], "CTCF")

    @patch.object(gget_encode.requests, "get")
    def test_no_results_returns_none(self, mock_get):
        mock_get.return_value = _FakeResponse({"@graph": []})
        self.assertIsNone(encode("nonexistent term xyz", verbose=False))

    @patch.object(gget_encode.requests, "get")
    def test_http_error_raises(self, mock_get):
        mock_get.return_value = _FakeResponse({}, ok=False, status_code=500)
        with self.assertRaises(RuntimeError):
            encode("ENCSR000AKS", verbose=False)

    def test_empty_search_term_raises(self):
        # Covers the empty/None search_term ValueError branch.
        with self.assertRaises(ValueError):
            encode("   ", verbose=False)

    def test_files_to_df_output_type_filter(self):
        # Covers the output_type filter branch.
        df = _files_to_df(_EXPERIMENT_PAYLOAD["files"], output_type="peaks")
        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df.iloc[0]["output_type"], "peaks")

    @patch.object(gget_encode.requests, "get")
    def test_encode_get_request_exception(self, mock_get):
        # Covers the requests.RequestException -> RuntimeError branch in _encode_get.
        mock_get.side_effect = requests.exceptions.ConnectionError("no network")
        with self.assertRaises(RuntimeError):
            encode("ENCSR000AKS", verbose=False)

    @patch.object(gget_encode.requests, "get")
    def test_encode_get_404(self, mock_get):
        # Covers the 404 -> ValueError branch in _encode_get.
        mock_get.return_value = _FakeResponse({}, ok=False, status_code=404)
        with self.assertRaises(ValueError):
            encode("ENCSR000AKS", verbose=False)

    @patch.object(gget_encode.requests, "get")
    def test_generic_object_metadata(self, mock_get):
        # Covers the generic-object (non-File, no 'files') metadata branch.
        mock_get.return_value = _FakeResponse(
            {"@type": ["Biosample", "Item"], "accession": "ENCBS000AAA", "status": "released", "nested": {"x": 1}}
        )
        df = encode("ENCBS000AAA", verbose=False)
        self.assertEqual(df.iloc[0]["accession"], "ENCBS000AAA")

    @patch.object(gget_encode, "_download_files")
    @patch.object(gget_encode.requests, "get")
    def test_accession_download_and_verbose(self, mock_get, mock_dl):
        # Covers the verbose-logging line and the download branch (accession path).
        mock_get.return_value = _FakeResponse(_EXPERIMENT_PAYLOAD)
        encode("ENCSR000AKS", download=True, verbose=True)
        self.assertTrue(mock_dl.called)

    @patch.object(gget_encode.requests, "get")
    def test_search_verbose_and_download_warning(self, mock_get):
        # Covers the search-path verbose line and the download-not-supported warning.
        mock_get.return_value = _FakeResponse(_SEARCH_PAYLOAD)
        result = encode("CTCF K562", download=True, verbose=True)
        self.assertEqual(result.iloc[0]["accession"], "ENCSR111AAA")

    @patch.object(gget_encode.requests, "get")
    def test_save_csv_and_json(self, mock_get):
        # Covers the save-to-CSV and json+save branches.
        mock_get.return_value = _FakeResponse(_EXPERIMENT_PAYLOAD)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                encode("ENCSR000AKS", save=True, verbose=False)
                self.assertTrue(any(f.endswith(".csv") for f in os.listdir(".")))
                encode("ENCSR000AKS", save=True, json=True, verbose=False)
                self.assertTrue(any(f.endswith(".json") for f in os.listdir(".")))
            finally:
                os.chdir(cwd)

    def test_download_files_no_urls(self):
        # Covers the "no downloadable files" early-return branch.
        gget_encode._download_files(pd.DataFrame({"url": []}), "unused_dir")

    @patch.object(gget_encode.requests, "get")
    def test_download_files_writes_and_handles_error(self, mock_get):
        # Covers the streaming-download body and the per-file error branch.
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_get.return_value.__enter__.return_value = resp
        df = pd.DataFrame({"url": ["https://www.encodeproject.org/files/ENCFF000BXK/@@download/ENCFF000BXK.bam"]})
        with tempfile.TemporaryDirectory() as tmp:
            gget_encode._download_files(df, tmp, verbose=True)
            self.assertTrue(os.path.exists(os.path.join(tmp, "ENCFF000BXK.bam")))
            # Error branch: requests.get raises -> logged, not raised
            mock_get.side_effect = requests.exceptions.ConnectionError("boom")
            gget_encode._download_files(df, tmp, verbose=False)


if __name__ == "__main__":
    unittest.main()
