import json
import unittest
from unittest.mock import patch

import pandas as pd
from gget.gget_archs4 import archs4

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_archs4.json") as json_file:
    archs4_dict = json.load(json_file)

# Columns gget returns for a tissue query -- the upstream 'color' column is dropped.
TISSUE_COLUMNS = ["id", "min", "q1", "median", "q3", "max"]


class TestArchs4(unittest.TestCase, metaclass=from_json(archs4_dict, archs4)):
    """Most tests are loaded from JSON. The live tissue-expression tests are defined in
    code because ARCHS4's row order and exact values drift over time; they assert the
    stable contract (columns incl. no 'color', quantile ordering, sorted by median) rather
    than pinning a full table snapshot. The check is gene-agnostic, so each test just reads
    its args from the JSON fixture -- no hardcoded gene to guard against."""

    def _assert_tissue_contract(self, df):
        self.assertGreater(len(df), 0, "ARCHS4 tissue query returned no rows")
        self.assertEqual(list(df.columns), TISSUE_COLUMNS)  # 'color' dropped; others present
        self.assertTrue((df["min"] <= df["q1"]).all())
        self.assertTrue((df["q1"] <= df["median"]).all())
        self.assertTrue((df["median"] <= df["q3"]).all())
        self.assertTrue((df["q3"] <= df["max"]).all())
        self.assertTrue(df["median"].is_monotonic_decreasing, "rows not sorted by median")

    def test_archs4_tissue(self):
        self._assert_tissue_contract(archs4(**archs4_dict["test_archs4_tissue"]["args"], verbose=False))

    def test_archs4_tissue_mouse(self):
        self._assert_tissue_contract(archs4(**archs4_dict["test_archs4_tissue_mouse"]["args"], verbose=False))

    def test_archs4_tissue_ensembl(self):
        self._assert_tissue_contract(archs4(**archs4_dict["test_archs4_tissue_ensembl"]["args"], verbose=False))

    def test_archs4_tissue_json(self):
        result = archs4(**archs4_dict["test_archs4_tissue_json"]["args"], verbose=False)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0, "ARCHS4 tissue JSON query returned no rows")
        self.assertEqual(list(result[0].keys()), TISSUE_COLUMNS)
        self._assert_tissue_contract(pd.DataFrame(result))


class _FakeResponse:
    def __init__(self, text):
        self.ok = True
        self.content = text.encode("utf-8")


class TestArchs4MissingColor(unittest.TestCase):
    """Network-free regression tests: ARCHS4 intermittently omits the 'color' column from
    the tissue-expression CSV. gget must not crash with a KeyError when it is absent
    (the 'color' column is dropped and never used)."""

    _CSV_WITH_COLOR = "id,min,q1,median,q3,max,color\nTissueA,0,1,5,9,10,#fff\nTissueB,0,2,8,12,15,#000\n"
    _CSV_NO_COLOR = "id,min,q1,median,q3,max\nTissueA,0,1,5,9,10\nTissueB,0,2,8,12,15\n"

    def test_tissue_missing_color_does_not_crash(self):
        with patch("gget.gget_archs4.requests.post", return_value=_FakeResponse(self._CSV_NO_COLOR)):
            df = archs4("STAT4", which="tissue", verbose=False)
        # Returns a valid, sorted data frame without a 'color' column (no KeyError).
        self.assertEqual(len(df), 2)
        self.assertNotIn("color", df.columns)
        self.assertEqual(df.iloc[0]["id"], "TissueB")  # sorted by median descending

    def test_tissue_with_color_still_dropped(self):
        with patch("gget.gget_archs4.requests.post", return_value=_FakeResponse(self._CSV_WITH_COLOR)):
            df = archs4("STAT4", which="tissue", verbose=False)
        self.assertEqual(len(df), 2)
        self.assertNotIn("color", df.columns)
        self.assertEqual(df.iloc[0]["id"], "TissueB")
