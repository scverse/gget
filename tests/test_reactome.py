import json
import unittest

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


if __name__ == "__main__":
    unittest.main()
