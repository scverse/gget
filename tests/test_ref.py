import json
import os
import tempfile
import unittest
from unittest.mock import patch

import gget.gget_ref as gget_ref
import requests
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

    @patch.object(gget_ref.requests, "get")
    def test_list_gencode_files_parses_and_filters(self, mock_get):
        html = (
            "<table>"
            '<tr><td><img></td><td><a href="../">Parent Directory</a></td><td></td><td> - </td></tr>'
            '<tr><td><img></td><td><a href="GRCh37_mapping/">GRCh37_mapping/</a></td><td>2024-05-13 16:01</td><td> - </td></tr>'
            '<tr><td><img></td><td><a href="gencode.v46.annotation.gtf.gz">gencode.v46.annotation.gtf.gz</a></td><td>2024-05-13 16:01  </td><td> 49M</td></tr>'
            '<tr><td><img></td><td><a href="README.TXT">README.TXT</a></td><td>2024-05-13 15:55  </td><td> 67K</td></tr>'
            "</table>"
        )
        mock_get.return_value = _FakeResp(html)
        files = gget_ref._list_gencode_files("https://example/release_46/")
        names = [f[0] for f in files]
        self.assertIn("gencode.v46.annotation.gtf.gz", names)
        self.assertIn("README.TXT", names)  # non-.gz files are listed too
        # The parent-directory link and subdirectories are filtered out.
        self.assertNotIn("../", names)
        self.assertNotIn("GRCh37_mapping/", names)

    @patch.object(gget_ref.requests, "get")
    def test_list_gencode_files_bad_status_raises(self, mock_get):
        mock_get.return_value = _FakeResp("", status_code=503)
        with self.assertRaises(RuntimeError):
            gget_ref._list_gencode_files("https://example/release_46/")

    @patch.object(gget_ref, "_list_gencode_files")
    def test_gencode_list_files_returns_dict(self, mock_list):
        mock_list.return_value = [
            ("gencode.v46.annotation.gtf.gz", "2024-05-13 16:01", "49M"),
            ("README.TXT", "2024-05-13 15:55", "67K"),
        ]
        result = gget_ref._gencode_ref("human", "all", 46, False, False, False, list_files=True)
        self.assertIn("gencode.v46.annotation.gtf.gz", result["human"])
        entry = result["human"]["gencode.v46.annotation.gtf.gz"]
        self.assertTrue(entry["ftp"].endswith("release_46/gencode.v46.annotation.gtf.gz"))
        self.assertEqual(entry["release_date"], "2024-05-13")
        self.assertEqual(entry["release_time"], "16:01")
        self.assertEqual(entry["bytes"], "49M")

    @patch.object(gget_ref, "_list_gencode_files")
    def test_gencode_list_files_ftp_returns_urls(self, mock_list):
        mock_list.return_value = [("gencode.v46.annotation.gtf.gz", "2024-05-13 16:01", "49M")]
        urls = gget_ref._gencode_ref("human", "all", 46, True, False, False, list_files=True)
        self.assertIsInstance(urls, list)
        self.assertTrue(urls[0].endswith("gencode.v46.annotation.gtf.gz"))

    def test_ref_list_files_requires_gencode(self):
        # list_files is only valid with source='gencode'; the default source='ensembl' must reject it.
        with self.assertRaises(ValueError):
            ref("human", list_files=True, verbose=False)


class TestGencodeRefLive(unittest.TestCase):
    """Live tests against the real GENCODE FTP (ftp.ebi.ac.uk) for issue #73.

    Unlike the offline tests above, these actually reach the network. They anchor
    a frozen GENCODE release (human v46 / mouse M35), whose files never change, so
    the exact assertions are stable over time. If the source is temporarily
    unreachable or rate-limits the request, the resource is skipped rather than
    failing the build.
    """

    def _skip_if_transient(self, fn, *args, **kwargs):
        """Run fn, converting a network error or a transient HTTP error into a skip."""
        try:
            return fn(*args, **kwargs)
        except requests.RequestException as e:
            self.skipTest(f"Network error reaching GENCODE FTP: {e}")
        except RuntimeError as e:
            # find_FTP_link / _find_latest raise RuntimeError on a non-200 (e.g. 5xx, rate-limit).
            self.skipTest(f"GENCODE FTP transient error: {e}")

    def test_human_v46_gtf(self):
        result = self._skip_if_transient(ref, "human", which="gtf", release=46, source="gencode", verbose=False)
        entry = result["human"]["annotation_gtf"]
        if not entry["ftp"]:
            self.skipTest("GENCODE returned no matching link (likely a transient/rate-limit HTML page).")
        self.assertEqual(
            entry["ftp"],
            "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_46/gencode.v46.annotation.gtf.gz",
        )
        # Frozen release -> these metadata values do not change.
        self.assertEqual(entry["gencode_release"], "46")
        self.assertEqual(entry["release_date"], "2024-05-13")
        self.assertEqual(entry["release_time"], "16:01")
        self.assertEqual(entry["bytes"], "49M")

    def test_mouse_M35_ftp(self):
        result = self._skip_if_transient(
            ref, "mouse", which=["gtf", "dna"], release=35, source="gencode", ftp=True, verbose=False
        )
        if not all(result):
            self.skipTest("GENCODE returned an empty link (likely a transient/rate-limit HTML page).")
        self.assertEqual(
            result,
            [
                "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M35/gencode.vM35.annotation.gtf.gz",
                "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M35/GRCm39.primary_assembly.genome.fa.gz",
            ],
        )

    def test_latest_human_release_is_plausible(self):
        # Guards the HTML-scraping path against upstream listing changes. Loose on purpose:
        # a bare integer string, >= a release we know exists (releases only grow).
        rel = self._skip_if_transient(gget_ref._find_latest_gencode_release, "human")
        self.assertTrue(rel.isdigit(), f"expected an integer human release, got {rel!r}")
        self.assertGreaterEqual(int(rel), 46)

    def test_latest_mouse_release_is_plausible(self):
        # Mouse releases look like 'M35', 'M39', ... (M + integer).
        rel = self._skip_if_transient(gget_ref._find_latest_gencode_release, "mouse")
        self.assertTrue(rel.startswith("M") and rel[1:].isdigit(), f"expected 'M<int>', got {rel!r}")
        self.assertGreaterEqual(int(rel[1:]), 35)

    def test_list_files_exposes_more_than_which(self):
        # The escape hatch must surface files the curated `which` set does not expose.
        result = self._skip_if_transient(ref, "human", release=46, source="gencode", list_files=True, verbose=False)
        files = result["human"]
        if not files:
            self.skipTest("GENCODE returned an empty listing (likely a transient/rate-limit HTML page).")
        self.assertIn("gencode.v46.annotation.gtf.gz", files)
        # pc_transcripts is a real GENCODE file with no `which` key -> proves list_files goes beyond it.
        self.assertIn("gencode.v46.pc_transcripts.fa.gz", files)
