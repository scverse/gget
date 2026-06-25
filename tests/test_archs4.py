import json
import unittest
from unittest.mock import patch

from gget.gget_archs4 import archs4

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_archs4.json") as json_file:
    archs4_dict = json.load(json_file)


class TestArchs4(unittest.TestCase, metaclass=from_json(archs4_dict, archs4)):
    pass  # all tests are loaded from json


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
