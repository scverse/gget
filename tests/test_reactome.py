import json
import unittest
from unittest.mock import patch

import gget.gget_reactome as gget_reactome
import pandas as pd
from gget.gget_reactome import reactome

from .from_json import from_json

# Load dictionary containing arguments and expected results for the offline (deterministic)
# argument-validation tests.
with open("./tests/fixtures/test_reactome.json") as json_file:
    reactome_dict = json.load(json_file)

# Reactome content is updated quarterly, so the network tests below assert structural
# invariants (columns, identifier shape, presence of a stable well-known entry) rather than
# exact pathway lists, and skip themselves if the Reactome service is unreachable.


class TestReactome(unittest.TestCase, metaclass=from_json(reactome_dict, reactome)):
    def _maybe_skip(self, func, **kwargs):
        try:
            return func(**kwargs)
        except RuntimeError as e:  # network/transient upstream failure
            self.skipTest(f"Reactome service unreachable: {e}")

    def test_reactome_pathways_network(self):
        df = self._maybe_skip(reactome, query="P04637", resource="pathways", species="9606", verbose=False)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(list(df.columns), ["stable_id", "name", "species", "schema_class", "in_disease"])
        self.assertGreater(len(df), 0)
        # All stable IDs are Reactome identifiers, and the species filter is honored.
        self.assertTrue(df["stable_id"].str.startswith("R-").all())
        self.assertTrue((df["species"] == "Homo sapiens").all())

    def test_reactome_search_network(self):
        df = self._maybe_skip(reactome, query="TP53", resource="search", types="Pathway", verbose=False)
        self.assertEqual(list(df.columns), ["stable_id", "name", "type", "species", "reactome_id"])
        self.assertGreater(len(df), 0)
        # HTML highlight tags from the search endpoint must be stripped from names.
        self.assertFalse(df["name"].str.contains("<", regex=False).any())

    def test_reactome_entity_network(self):
        df = self._maybe_skip(reactome, query="R-HSA-6804754", resource="entity", verbose=False)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["stable_id"], "R-HSA-6804754")
        self.assertEqual(df.iloc[0]["schema_class"], "Pathway")

    def test_reactome_json_output_network(self):
        result = self._maybe_skip(
            reactome, query="P04637", resource="pathways", species="9606", json=True, verbose=False
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn("stable_id", result[0])

    def test_reactome_pathways_no_results_network(self):
        # An unmapped identifier yields an empty DataFrame (Reactome returns HTTP 404), not an error.
        df = self._maybe_skip(reactome, query="NOTAREALID", resource="pathways", verbose=False)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
        self.assertEqual(list(df.columns), ["stable_id", "name", "species", "schema_class", "in_disease"])


class TestReactomeOffline(unittest.TestCase):
    """Network-free tests of the Reactome parsing/branch logic (issue #114).

    All HTTP access goes through gget_reactome.http_json, which is mocked here.
    """

    def test_strip_html_passthrough(self):
        # Non-string values pass through unchanged.
        self.assertIsNone(gget_reactome._strip_html(None))
        self.assertEqual(gget_reactome._strip_html(123), 123)
        self.assertEqual(gget_reactome._strip_html("<span>TP53</span>"), "TP53")

    @patch.object(gget_reactome, "http_json")
    def test_pathways_parsing_verbose(self, mock_http):
        mock_http.return_value = [
            {
                "stId": "R-HSA-1",
                "displayName": "Pathway A",
                "speciesName": "Homo sapiens",
                "schemaClass": "Pathway",
                "isInDisease": False,
            }
        ]
        df = reactome("P04637", resource="pathways", species="Homo sapiens", verbose=True)
        self.assertEqual(df.iloc[0]["stable_id"], "R-HSA-1")
        self.assertEqual(df.iloc[0]["species"], "Homo sapiens")

    @patch.object(gget_reactome, "http_json")
    def test_pathways_404_returns_empty(self, mock_http):
        mock_http.side_effect = RuntimeError("Reactome returned HTTP 404")
        df = reactome("NOTREAL", resource="pathways", verbose=False)
        self.assertEqual(len(df), 0)

    @patch.object(gget_reactome, "http_json")
    def test_pathways_other_error_raises(self, mock_http):
        mock_http.side_effect = RuntimeError("Reactome returned HTTP 500")
        with self.assertRaises(RuntimeError):
            reactome("P04637", resource="pathways", verbose=False)

    @patch.object(gget_reactome, "http_json")
    def test_search_parsing_species_types_verbose(self, mock_http):
        mock_http.return_value = {
            "results": [
                {
                    "entries": [
                        {
                            "stId": "R-HSA-9",
                            "name": "<span class='highlighting'>TP53</span>",
                            "exactType": "Protein",
                            "species": ["Homo sapiens"],
                            "id": 12345,
                        }
                    ]
                }
            ]
        }
        df = reactome("TP53", resource="search", species="9606", types="Protein", verbose=True)
        self.assertEqual(df.iloc[0]["stable_id"], "R-HSA-9")
        self.assertEqual(df.iloc[0]["name"], "TP53")  # HTML stripped
        self.assertEqual(df.iloc[0]["species"], "Homo sapiens")  # list flattened

    @patch.object(gget_reactome, "http_json")
    def test_search_404_returns_empty(self, mock_http):
        mock_http.side_effect = RuntimeError("Reactome returned HTTP 404")
        df = reactome("zzzz", resource="search", verbose=False)
        self.assertEqual(len(df), 0)

    @patch.object(gget_reactome, "http_json")
    def test_search_other_error_raises(self, mock_http):
        mock_http.side_effect = RuntimeError("Reactome returned HTTP 503")
        with self.assertRaises(RuntimeError):
            reactome("TP53", resource="search", verbose=False)

    @patch.object(gget_reactome, "http_json")
    def test_entity_name_fallback_and_summation(self, mock_http):
        # displayName missing -> fall back to first of name list; summation HTML stripped.
        mock_http.return_value = {
            "stId": "R-HSA-6804754",
            "displayName": None,
            "name": ["Regulation of TP53 Activity"],
            "schemaClass": "Pathway",
            "speciesName": "Homo sapiens",
            "isInDisease": False,
            "summation": [{"text": "<p>Some <b>summary</b>.</p>"}],
        }
        result = reactome("R-HSA-6804754", resource="entity", json=True, verbose=True)
        self.assertEqual(result[0]["name"], "Regulation of TP53 Activity")
        self.assertEqual(result[0]["summation"], "Some summary.")

    @patch.object(gget_reactome, "http_json")
    def test_entity_404_raises_valueerror(self, mock_http):
        mock_http.side_effect = RuntimeError("Reactome returned HTTP 404")
        with self.assertRaises(ValueError):
            reactome("R-HSA-0", resource="entity", verbose=False)

    @patch.object(gget_reactome, "http_json")
    def test_entity_other_error_raises(self, mock_http):
        mock_http.side_effect = RuntimeError("Reactome returned HTTP 500")
        with self.assertRaises(RuntimeError):
            reactome("R-HSA-6804754", resource="entity", verbose=False)

    def test_invalid_resource_and_empty_query(self):
        with self.assertRaises(ValueError):
            reactome("TP53", resource="banana", verbose=False)
        with self.assertRaises(ValueError):
            reactome("   ", resource="pathways", verbose=False)


if __name__ == "__main__":
    unittest.main()
