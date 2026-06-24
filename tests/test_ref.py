import json
import os
import tempfile
import unittest
from unittest.mock import patch

import gget.gget_ref as gget_ref
from gget.gget_ref import ref

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_ref.json") as json_file:
    ref_dict = json.load(json_file)


class TestRef(unittest.TestCase, metaclass=from_json(ref_dict, ref)):
    pass  # all tests are loaded from json


class _FakeResp:
    """Minimal stand-in for a requests.Response used to test GENCODE helpers offline."""

    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


class TestGencodeRefOffline(unittest.TestCase):
    """Network-free tests of the GENCODE reference helpers (issue #73)."""

    @patch.object(gget_ref.requests, "get")
    def test_find_latest_human(self, mock_get):
        mock_get.return_value = _FakeResp('<a href="release_45/">a</a><a href="release_46/">b</a>')
        self.assertEqual(gget_ref._find_latest_gencode_release("human"), "46")

    @patch.object(gget_ref.requests, "get")
    def test_find_latest_mouse(self, mock_get):
        mock_get.return_value = _FakeResp('<a href="release_M34/">a</a><a href="release_M35/">b</a>')
        self.assertEqual(gget_ref._find_latest_gencode_release("mouse"), "M35")

    @patch.object(gget_ref.requests, "get")
    def test_find_latest_bad_status(self, mock_get):
        mock_get.return_value = _FakeResp("", status_code=500)
        with self.assertRaises(RuntimeError):
            gget_ref._find_latest_gencode_release("human")

    @patch.object(gget_ref.requests, "get")
    def test_find_latest_human_no_releases(self, mock_get):
        mock_get.return_value = _FakeResp('<a href="other/">a</a>')
        with self.assertRaises(RuntimeError):
            gget_ref._find_latest_gencode_release("human")

    @patch.object(gget_ref.requests, "get")
    def test_find_latest_mouse_no_releases(self, mock_get):
        # A non-"M" release listing yields no mouse release numbers.
        mock_get.return_value = _FakeResp('<a href="release_46/">a</a>')
        with self.assertRaises(RuntimeError):
            gget_ref._find_latest_gencode_release("mouse")

    def test_gencode_bad_species(self):
        with self.assertRaises(ValueError):
            gget_ref._gencode_ref("zebrafish", "gtf", 46, False, False, False)

    def test_gencode_which_all_conflict(self):
        with self.assertRaises(ValueError):
            gget_ref._gencode_ref("human", ["gtf", "all"], 46, False, False, False)

    def test_gencode_bad_which_cds(self):
        # 'cds' is unsupported by GENCODE and triggers the extra-hint ValueError.
        with self.assertRaises(ValueError):
            gget_ref._gencode_ref("human", ["cds"], 46, False, False, False)

    @patch.object(gget_ref, "find_FTP_link")
    def test_gencode_all_verbose_link_found(self, mock_ftp):
        mock_ftp.return_value = ("gencode.v46.annotation.gtf.gz", "01-Jan-2024 12:00", "1.2G")
        result = gget_ref._gencode_ref("human", "all", 46, False, False, True)
        self.assertIn("human", result)
        self.assertTrue(any(v["ftp"] for v in result["human"].values()))

    @patch.object(gget_ref, "find_FTP_link")
    def test_gencode_link_not_found(self, mock_ftp):
        mock_ftp.return_value = (None, None, None)
        result = gget_ref._gencode_ref("mouse", "gtf", 35, False, False, False)
        self.assertIn("mouse", result)
        self.assertEqual(next(iter(result["mouse"].values()))["ftp"], "")

    @patch.object(gget_ref, "find_FTP_link")
    def test_gencode_ftp_and_save(self, mock_ftp):
        mock_ftp.return_value = ("f.gtf.gz", "01-Jan-2024 12:00", "1G")
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                urls = gget_ref._gencode_ref("human", "gtf", 46, True, True, False)  # ftp + save
                self.assertIsInstance(urls, list)
                self.assertTrue(os.path.exists("gget_ref_results.txt"))
                gget_ref._gencode_ref("human", "gtf", 46, False, True, False)  # json save
                self.assertTrue(os.path.exists("gget_ref_results.json"))
            finally:
                os.chdir(cwd)

    @patch.object(gget_ref, "_find_latest_gencode_release")
    @patch.object(gget_ref, "find_FTP_link")
    def test_gencode_release_none_resolves_latest(self, mock_ftp, mock_rel):
        mock_rel.return_value = "46"
        mock_ftp.return_value = ("f.gtf.gz", "01-Jan-2024 12:00", "1G")
        gget_ref._gencode_ref("human", "gtf", None, False, False, False)
        mock_rel.assert_called_once()

    def test_ref_bad_source(self):
        with self.assertRaises(ValueError):
            ref("human", source="banana", verbose=False)

    def test_ref_gencode_requires_species(self):
        with self.assertRaises(ValueError):
            ref(None, source="gencode", verbose=False)

    @patch.object(gget_ref, "_gencode_ref")
    def test_ref_delegates_to_gencode(self, mock_gencode):
        mock_gencode.return_value = {"human": {}}
        result = ref("human", source="gencode", verbose=False)
        self.assertEqual(result, {"human": {}})
        mock_gencode.assert_called_once()
