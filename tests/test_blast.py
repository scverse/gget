import json
import unittest

from gget.gget_blast import _build_entrez_query, blast

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_blast.json") as json_file:
    blast_dict = json.load(json_file)


class TestBlast(unittest.TestCase, metaclass=from_json(blast_dict, blast)):
    pass  # all tests are loaded from json


class TestBuildEntrezQuery(unittest.TestCase):
    """Network-free tests for the taxonomy/Entrez query builder (issue #71)."""

    def test_none(self):
        self.assertIsNone(_build_entrez_query())
        self.assertIsNone(_build_entrez_query(taxid=None, entrez_query=None))
        self.assertIsNone(_build_entrez_query(entrez_query="   "))

    def test_single_taxid_int(self):
        self.assertEqual(_build_entrez_query(taxid=9606), "txid9606[ORGN]")

    def test_single_taxid_str_and_prefix(self):
        self.assertEqual(_build_entrez_query(taxid="9606"), "txid9606[ORGN]")
        self.assertEqual(_build_entrez_query(taxid="txid9606"), "txid9606[ORGN]")
        self.assertEqual(_build_entrez_query(taxid="TXID9606"), "txid9606[ORGN]")

    def test_multiple_taxids_or(self):
        self.assertEqual(
            _build_entrez_query(taxid=[9606, "10090"]),
            "(txid9606[ORGN] OR txid10090[ORGN])",
        )

    def test_entrez_query_only(self):
        self.assertEqual(
            _build_entrez_query(entrez_query="Homo sapiens[ORGN]"),
            "Homo sapiens[ORGN]",
        )

    def test_taxid_and_entrez_query_combined(self):
        self.assertEqual(
            _build_entrez_query(taxid=9606, entrez_query="NOT predicted[Title]"),
            "txid9606[ORGN] AND NOT predicted[Title]",
        )

    def test_invalid_taxid_raises(self):
        with self.assertRaises(ValueError):
            _build_entrez_query(taxid="banana")
        with self.assertRaises(ValueError):
            _build_entrez_query(taxid=[9606, "banana"])
