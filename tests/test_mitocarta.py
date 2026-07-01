import json
import unittest

import pandas as pd
from gget.gget_mitocarta import _clean_df, mitocarta

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_mitocarta.json") as json_file:
    mitocarta_dict = json.load(json_file)


class TestMitocarta(unittest.TestCase, metaclass=from_json(mitocarta_dict, mitocarta)):
    # Error tests are generated from json; property tests are defined below.

    def test_mitocarta_human(self):
        test = "test_mitocarta_human"
        td = mitocarta_dict[test]
        df = mitocarta(**td["args"])
        self.assertEqual(len(df), td["expected_n_rows"])
        for col in td["expected_columns"]:
            self.assertIn(col, df.columns)
        # A well-known mitochondrial gene should be in the inventory
        self.assertIn("MT-CO1", set(df["Symbol"].astype(str)))

    def test_mitocarta_pathways(self):
        test = "test_mitocarta_pathways"
        td = mitocarta_dict[test]
        df = mitocarta(**td["args"])
        self.assertIn("MitoPathway", df.columns)
        self.assertGreaterEqual(len(df), td["expected_min_rows"])


class TestMitocartaClean(unittest.TestCase):
    """Network-free unit tests for the L2 tidy normalization (_clean_df)."""

    def test_pathways_drops_stray_column(self):
        # The 'C' sheet is read with a stray unlabeled integer-named leading column.
        raw = pd.DataFrame(
            {
                2: [7, 8],
                "MitoPathway": ["P1", "P2"],
                "MitoPathways Hierarchy": ["P1", "P1 > P2"],
                "Genes": ["AARS2, ALKBH1", "DNA2"],
            }
        )
        out = _clean_df(raw, "pathways")
        self.assertEqual(list(out.columns), ["MitoPathway", "MitoPathways Hierarchy", "Genes"])
        self.assertNotIn(2, out.columns)

    def test_pathways_genes_split_into_list(self):
        raw = pd.DataFrame({"MitoPathway": ["P1"], "Genes": ["AARS2, ALKBH1, ANGEL2"]})
        out = _clean_df(raw, "pathways")
        self.assertEqual(out.loc[0, "Genes"], ["AARS2", "ALKBH1", "ANGEL2"])

    def test_mitocarta_splits_pathways_and_synonyms(self):
        raw = pd.DataFrame(
            {
                "Symbol": ["CYC1"],
                "Synonyms": ["MC3DN6|UQCR4"],
                "MitoCarta3.0_MitoPathways": ["OXPHOS > Complex III | Metabolism > Heme"],
            }
        )
        out = _clean_df(raw, "mitocarta")
        self.assertEqual(out.loc[0, "Synonyms"], ["MC3DN6", "UQCR4"])
        self.assertEqual(
            out.loc[0, "MitoCarta3.0_MitoPathways"],
            ["OXPHOS > Complex III", "Metabolism > Heme"],
        )

    def test_missing_delimited_value_becomes_empty_list(self):
        raw = pd.DataFrame({"Symbol": ["X"], "Synonyms": [None]})
        out = _clean_df(raw, "mitocarta")
        self.assertEqual(out.loc[0, "Synonyms"], [])
