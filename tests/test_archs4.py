import json
import unittest
from unittest.mock import patch

import pandas as pd
from gget.gget_archs4 import archs4

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_archs4.json") as json_file:
    archs4_dict = json.load(json_file)


class TestArchs4(unittest.TestCase, metaclass=from_json(archs4_dict, archs4)):
    """Most tests are loaded from JSON. Live ARCHS4 tissue-expression tests are
    defined in code because upstream row order and exact values can drift; these
    tests assert the stable contract instead of pinning a full table snapshot."""

    _TISSUE_COLUMNS = ["id", "min", "q1", "median", "q3", "max"]

    def _run(self, name, **overrides):
        args = {**archs4_dict[name]["args"], "verbose": False, **overrides}
        return archs4(**args)

    def _assert_tissue_df(self, df):
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0, "ARCHS4 tissue query returned no rows")
        self.assertEqual(list(df.columns), self._TISSUE_COLUMNS)
        self.assertNotIn("color", df.columns)

        for tissue_id in df["id"].dropna().head(50):
            self.assertTrue(str(tissue_id).strip(), "empty tissue id")

        numeric = df[["min", "q1", "median", "q3", "max"]]
        for col in numeric.columns:
            self.assertTrue(pd.api.types.is_numeric_dtype(numeric[col]), f"{col} is not numeric")
        self.assertTrue((numeric["min"] <= numeric["q1"]).all())
        self.assertTrue((numeric["q1"] <= numeric["median"]).all())
        self.assertTrue((numeric["median"] <= numeric["q3"]).all())
        self.assertTrue((numeric["q3"] <= numeric["max"]).all())
        self.assertTrue(df["median"].is_monotonic_decreasing, "tissue rows are not sorted by median")

    def _assert_tissue_json(self, result):
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0, "ARCHS4 tissue JSON query returned no rows")
        for row in result[:50]:
            self.assertEqual(list(row.keys()), self._TISSUE_COLUMNS)
        self._assert_tissue_df(pd.DataFrame(result))

    def test_archs4_tissue(self):
        self._assert_tissue_df(self._run("test_archs4_tissue"))

    def test_archs4_tissue_json(self):
        self._assert_tissue_json(self._run("test_archs4_tissue_json"))

    def test_archs4_tissue_mouse(self):
        self._assert_tissue_df(self._run("test_archs4_tissue_mouse"))

    def test_archs4_tissue_ensembl(self):
        self._assert_tissue_df(self._run("test_archs4_tissue_ensembl"))


class _FakeResponse:
    def __init__(self, text, ok=True):
        self.ok = ok
        self.content = text.encode("utf-8")


class TestArchs4MissingColor(unittest.TestCase):
    """Network-free regression tests: ARCHS4 intermittently omits the 'color' column
    from the tissue-expression CSV. gget must not crash with a KeyError in that case
    (the 'color' column is dropped and never used)."""

    _CSV_WITH_COLOR = "id,min,q1,median,q3,max,color\nTissueA,0,1,5,9,10,#fff\nTissueB,0,2,8,12,15,#000\n"
    _CSV_NO_COLOR = "id,min,q1,median,q3,max\nTissueA,0,1,5,9,10\nTissueB,0,2,8,12,15\n"

    def test_tissue_missing_color_does_not_crash(self):
        with patch("gget.gget_archs4.requests.post", return_value=_FakeResponse(self._CSV_NO_COLOR)):
            df = archs4("STAT4", which="tissue", verbose=False)
        # Returns a valid, sorted data frame without a 'color' column (no KeyError)
        self.assertEqual(len(df), 2)
        self.assertNotIn("color", df.columns)
        self.assertEqual(df.iloc[0]["id"], "TissueB")  # sorted by median descending

    def test_tissue_with_color_still_dropped(self):
        with patch("gget.gget_archs4.requests.post", return_value=_FakeResponse(self._CSV_WITH_COLOR)):
            df = archs4("STAT4", which="tissue", verbose=False)
        self.assertEqual(len(df), 2)
        self.assertNotIn("color", df.columns)
        self.assertEqual(df.iloc[0]["id"], "TissueB")
