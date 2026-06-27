import json
import unittest
from unittest.mock import patch

import pandas as pd
from gget.gget_opentargets import opentargets

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_opentargets.json") as json_file:
    ot_dict = json.load(json_file)


class TestOpenTargets(unittest.TestCase, metaclass=from_json(ot_dict, opentargets)):
    pass  # all tests are loaded from json


# Sample of the current OpenTargets `baselineExpression.rows` response shape.
_BASELINE_EXPRESSION_ROWS = [
    {
        "tissueBiosample": {"biosampleId": "UBERON_0000007", "biosampleName": "pituitary gland"},
        "celltypeBiosample": None,
        "median": 0.066891,
        "min": 0.0,
        "q1": 0.028268,
        "q3": 0.142208,
        "max": 1.69407,
        "unit": "TPM",
        "datasourceId": "gtex",
        "datatypeId": "bulk rna-seq",
    },
    {
        "tissueBiosample": {"biosampleId": "UBERON_0002107", "biosampleName": "liver"},
        "celltypeBiosample": None,
        "median": 2.5,
        "min": 0.1,
        "q1": 1.0,
        "q3": 3.0,
        "max": 8.0,
        "unit": "TPM",
        "datasourceId": "gtex",
        "datatypeId": "bulk rna-seq",
    },
]


def _baseline_expression_response(rows):
    return {"data": {"target": {"baselineExpression": {"rows": rows}}}}


class TestOpenTargetsExpressionMocked(unittest.TestCase):
    """Network-free tests for the expression resource after OpenTargets moved baseline
    expression from the (now-empty) `expressions` field to `baselineExpression.rows`.

    The previous live, exact-match fixtures `test_opentargets_expression` and
    `test_opentargets_expression_no_limit` asserted the old per-tissue RNA shape
    (`tissue.id`, `rna.zscore`, ...) which no longer exists upstream; they were
    removed from tests/fixtures/test_opentargets.json and replaced by these
    deterministic mocked tests."""

    def test_expression_parses_baseline_rows(self):
        with patch(
            "gget.gget_opentargets.http_json",
            return_value=_baseline_expression_response(_BASELINE_EXPRESSION_ROWS),
        ):
            df = opentargets("ENSG00000169194", resource="expression", verbose=False)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        # Flattened biosample + summary-statistic columns are present
        self.assertIn("tissueBiosample.biosampleId", df.columns)
        self.assertIn("median", df.columns)
        self.assertIn("unit", df.columns)
        self.assertEqual(df.iloc[0]["tissueBiosample.biosampleId"], "UBERON_0000007")

    def test_expression_limit(self):
        with patch(
            "gget.gget_opentargets.http_json",
            return_value=_baseline_expression_response(_BASELINE_EXPRESSION_ROWS),
        ):
            df = opentargets("ENSG00000169194", resource="expression", limit=1, verbose=False)
        self.assertEqual(len(df), 1)

    def test_expression_json(self):
        with patch(
            "gget.gget_opentargets.http_json",
            return_value=_baseline_expression_response(_BASELINE_EXPRESSION_ROWS),
        ):
            result = opentargets("ENSG00000169194", resource="expression", json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_expression_empty_is_graceful(self):
        with patch(
            "gget.gget_opentargets.http_json",
            return_value=_baseline_expression_response([]),
        ):
            df = opentargets("ENSG00000169194", resource="expression", verbose=False)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
