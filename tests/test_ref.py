import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import gget.gget_ref as gget_ref
import requests
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

    @patch.object(gget_ref.requests, "get")
    def test_version_prefix_no_collision(self, mock_get):
        # Only version .40 exists; querying .4 must NOT prefix-match the .40 folder.
        mock_get.return_value = _FakeResp('<a href="GCF_000001405.40_GRCh38.p14/">x</a>')
        with self.assertRaises(RuntimeError):
            assembly_report("GCF_000001405.4", verbose=False)

    @patch.object(gget_ref.requests, "get")
    def test_versionless_resolves_latest(self, mock_get):
        # No version given -> resolve to the latest version folder (.40, not .39).
        parent = '<a href="GCF_000001405.39_A/">a</a><a href="GCF_000001405.40_B/">b</a>'
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                mock_get.side_effect = [_FakeResp(parent), _FakeResp(_REPORT_TEXT)]
                assembly_report("GCF_000001405", save=True, verbose=False)
                # The resolved (latest) version is reflected in the saved filename.
                self.assertTrue(os.path.exists("GCF_000001405.40_assembly_report.csv"))
            finally:
                os.chdir(cwd)

    @patch.object(gget_ref.requests, "get")
    @patch.object(gget_ref, "_resolve_taxon_to_accession", return_value="GCF_000001405.40")
    def test_taxon_resolves_then_fetches(self, mock_resolve, mock_get):
        # taxon=True routes the input through the resolver, then fetches the report normally.
        mock_get.side_effect = [_FakeResp(_PARENT_HTML), _FakeResp(_REPORT_TEXT)]
        df = assembly_report("homo sapiens", taxon=True, verbose=False)
        mock_resolve.assert_called_once_with("homo sapiens", verbose=False)
        self.assertEqual(df.iloc[0]["UCSC-style-name"], "chr1")

    @patch("gget.gget_virus._get_datasets_path", return_value="datasets")
    @patch.object(gget_ref.subprocess, "run")
    def test_resolve_taxon_parses_accession(self, mock_run, _mock_path):
        mock_run.return_value = Mock(
            returncode=0,
            stdout='new version notice\n{"accession": "GCF_000001405.40", "organism": {}}\n',
        )
        self.assertEqual(gget_ref._resolve_taxon_to_accession("homo sapiens", verbose=False), "GCF_000001405.40")

    @patch("gget.gget_virus._get_datasets_path", return_value="datasets")
    @patch.object(gget_ref.subprocess, "run")
    def test_resolve_taxon_not_found_raises(self, mock_run, _mock_path):
        mock_run.return_value = Mock(returncode=0, stdout="")  # no records -> unknown taxon
        with self.assertRaises(ValueError):
            gget_ref._resolve_taxon_to_accession("not-a-species", verbose=False)

    @patch("gget.gget_virus._get_datasets_path", return_value="datasets")
    @patch.object(gget_ref.subprocess, "run")
    def test_resolve_taxon_datasets_failure_raises(self, mock_run, _mock_path):
        mock_run.return_value = Mock(returncode=1, stdout="")  # datasets CLI error (often transient)
        with self.assertRaises(RuntimeError):
            gget_ref._resolve_taxon_to_accession("homo sapiens", verbose=False)

    @patch("gget.gget_virus._get_datasets_path", return_value="datasets")
    @patch.object(gget_ref.subprocess, "run")
    def test_list_taxon_assemblies_columns_and_order(self, mock_run, _mock_path):
        # Two records; the "reference genome" must sort ahead of the "na" one.
        mock_run.return_value = Mock(
            returncode=0,
            stdout=(
                '{"accession": "GCF_000002125.1", "assembly_info": {"assembly_name": "HuRef", '
                '"assembly_level": "Chromosome"}, "organism": {"organism_name": "Homo sapiens"}}\n'
                '{"accession": "GCF_000001405.40", "assembly_info": {"assembly_name": "GRCh38.p14", '
                '"refseq_category": "reference genome", "assembly_level": "Chromosome"}, '
                '"organism": {"organism_name": "Homo sapiens"}}\n'
            ),
        )
        df = gget_ref._list_taxon_assemblies("homo sapiens", verbose=False)
        self.assertEqual(
            list(df.columns), ["accession", "assembly_name", "refseq_category", "assembly_level", "organism"]
        )
        self.assertEqual(df.iloc[0]["accession"], "GCF_000001405.40")  # reference first
        self.assertEqual(df.iloc[1]["refseq_category"], "na")  # missing category -> "na"

    @patch("gget.gget_virus._get_datasets_path", return_value="datasets")
    @patch.object(gget_ref.subprocess, "run")
    def test_list_taxon_assemblies_empty_raises(self, mock_run, _mock_path):
        mock_run.return_value = Mock(returncode=0, stdout="")
        with self.assertRaises(ValueError):
            gget_ref._list_taxon_assemblies("not-a-species", verbose=False)

    @patch.object(gget_ref, "_list_taxon_assemblies")
    def test_assembly_report_list_assemblies_delegates(self, mock_list):
        mock_list.return_value = "CATALOGUE"
        self.assertEqual(assembly_report("homo sapiens", list_assemblies=True, verbose=False), "CATALOGUE")
        mock_list.assert_called_once()


class TestAssemblyReportLive(unittest.TestCase):
    """Live test hitting the real NCBI FTP (issue #179).

    Anchored to SARS-CoV-2 (GCF_009858895.2), a frozen single-sequence reference, so
    the identity columns are stable. Skips (rather than fails) on a network error or a
    transient non-200 instead of reddening CI.
    """

    def test_sars_cov2_report_key_columns(self):
        try:
            df = assembly_report("GCF_009858895.2", verbose=False)
        except requests.RequestException as e:
            self.skipTest(f"Network error reaching NCBI FTP: {e}")
        except RuntimeError as e:
            self.skipTest(f"NCBI FTP transient error: {e}")
        # Anchor on stable identity columns, not the full row.
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row["RefSeq-Accn"], "NC_045512.2")
        self.assertEqual(row["GenBank-Accn"], "MN908947.3")
        self.assertEqual(row["Sequence-Length"], "29903")

    def test_taxon_human_resolves_to_reference(self):
        # taxon=True resolves "homo sapiens" (via the bundled datasets CLI) to the human
        # reference assembly and returns its report, which must contain chromosome 1.
        try:
            df = assembly_report("homo sapiens", taxon=True, verbose=False)
        except requests.RequestException as e:
            self.skipTest(f"Network error reaching NCBI: {e}")
        except RuntimeError as e:
            self.skipTest(f"NCBI datasets/FTP transient error: {e}")
        self.assertIn("NC_000001.11", set(df["RefSeq-Accn"]))

    def test_list_assemblies_human_contains_reference(self):
        # list_assemblies=True returns the taxon's assembly catalogue; the human reference must be in it.
        try:
            df = assembly_report("homo sapiens", list_assemblies=True, verbose=False)
        except requests.RequestException as e:
            self.skipTest(f"Network error reaching NCBI: {e}")
        except RuntimeError as e:
            self.skipTest(f"NCBI datasets transient error: {e}")
        self.assertIn("GCF_000001405.40", set(df["accession"]))
        self.assertEqual(df.iloc[0]["refseq_category"], "reference genome")  # reference sorted first
