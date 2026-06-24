import json
import os
import tempfile
import unittest
from unittest.mock import patch

import gget.gget_ref as gget_ref
from gget.gget_ref import assembly_report, ref

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_ref.json") as json_file:
    ref_dict = json.load(json_file)


class TestRef(unittest.TestCase, metaclass=from_json(ref_dict, ref)):
    pass  # all tests are loaded from json


class _FakeResp:
    """Minimal stand-in for a requests.Response used to test assembly_report offline."""

    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


# A parent-directory listing containing the assembly's folder, and a minimal
# tab-delimited assembly report (with a comment header and a blank line).
_PARENT_HTML = '<html><body><a href="GCF_000001405.40_GRCh38.p14/">GCF_000001405.40_GRCh38.p14/</a></body></html>'
_REPORT_TEXT = (
    "# Assembly name:  GRCh38.p14\n"
    "# Sequence-Name\tSequence-Role\tGenBank-Accn\tRefSeq-Accn\tUCSC-style-name\n"
    "1\tassembled-molecule\tCM000663.2\tNC_000001.11\tchr1\n"
    "\n"
)


class TestAssemblyReportOffline(unittest.TestCase):
    """Network-free tests of assembly_report and the ref() delegation (issue #179)."""

    def test_invalid_accession_raises(self):
        with self.assertRaises(ValueError):
            assembly_report("not-an-accession", verbose=False)

    @patch.object(gget_ref.requests, "get")
    def test_parse_verbose_json_and_save(self, mock_get):
        # Happy path: verbose log, blank-line skip, parsing, then json/save/csv branches.
        mock_get.side_effect = [_FakeResp(_PARENT_HTML), _FakeResp(_REPORT_TEXT)]
        df = assembly_report("GCF_000001405.40", verbose=True)
        self.assertEqual(list(df["Sequence-Name"]), ["1"])
        self.assertEqual(df.iloc[0]["UCSC-style-name"], "chr1")

        mock_get.side_effect = [_FakeResp(_PARENT_HTML), _FakeResp(_REPORT_TEXT)]
        result = assembly_report("GCF_000001405.40", json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["RefSeq-Accn"], "NC_000001.11")

        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                mock_get.side_effect = [_FakeResp(_PARENT_HTML), _FakeResp(_REPORT_TEXT)]
                assembly_report("GCF_000001405.40", save=True, verbose=False)
                self.assertTrue(os.path.exists("GCF_000001405.40_assembly_report.csv"))
                mock_get.side_effect = [_FakeResp(_PARENT_HTML), _FakeResp(_REPORT_TEXT)]
                assembly_report("GCF_000001405.40", json=True, save=True, verbose=False)
                self.assertTrue(os.path.exists("GCF_000001405.40_assembly_report.json"))
            finally:
                os.chdir(cwd)

    @patch.object(gget_ref.requests, "get")
    def test_parent_dir_non_200_raises(self, mock_get):
        mock_get.return_value = _FakeResp("", status_code=404)
        with self.assertRaises(RuntimeError):
            assembly_report("GCF_000001405.40", verbose=False)

    @patch.object(gget_ref.requests, "get")
    def test_no_folder_found_raises(self, mock_get):
        mock_get.return_value = _FakeResp("<html>no matching links</html>", status_code=200)
        with self.assertRaises(RuntimeError):
            assembly_report("GCF_000001405.40", verbose=False)

    @patch.object(gget_ref.requests, "get")
    def test_report_non_200_raises(self, mock_get):
        mock_get.side_effect = [_FakeResp(_PARENT_HTML), _FakeResp("", status_code=500)]
        with self.assertRaises(RuntimeError):
            assembly_report("GCF_000001405.40", verbose=False)

    @patch.object(gget_ref.requests, "get")
    def test_report_missing_header_raises(self, mock_get):
        # No "# Sequence-Name" header line -> columns stay None -> RuntimeError.
        mock_get.side_effect = [_FakeResp(_PARENT_HTML), _FakeResp("# only comments\nfoo\tbar\n")]
        with self.assertRaises(RuntimeError):
            assembly_report("GCF_000001405.40", verbose=False)

    def test_ref_assembly_report_requires_species(self):
        with self.assertRaises(ValueError):
            ref(None, assembly_report=True, verbose=False)

    @patch.object(gget_ref, "_assembly_report_fn")
    def test_ref_delegates_to_assembly_report(self, mock_fn):
        mock_fn.return_value = "DELEGATED"
        self.assertEqual(ref("GCF_000001405.40", assembly_report=True, verbose=False), "DELEGATED")
        mock_fn.assert_called_once()
