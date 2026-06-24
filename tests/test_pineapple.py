import json
import unittest
from unittest.mock import patch

import gget.gget_pineapple as gget_pineapple
from gget.gget_pineapple import (
    _catalog_row,
    _parse_gdrive_form,
    _resource_filename,
    pineapple,
)

from .from_json import from_json

with open("./tests/fixtures/test_pineapple.json") as json_file:
    pineapple_dict = json.load(json_file)


class TestPineapple(unittest.TestCase, metaclass=from_json(pineapple_dict, pineapple)):
    pass  # tests loaded from json


class TestPineappleHelpers(unittest.TestCase):
    """Network-free tests of the Pineapple catalog/helpers (issue #161)."""

    def test_list_segmentation(self):
        df = pineapple(verbose=False)
        self.assertEqual(list(df.columns), gget_pineapple._COLUMNS)
        self.assertEqual(df.shape[0], len(gget_pineapple._SEGMENTATION))
        self.assertIn("vicar_2021", set(df["name"]))
        row = df[df["name"] == "vicar_2021"].iloc[0]
        self.assertEqual(row["google_drive_id"], "12tJOlIHZPFqp8GLek_jV__Uhhgsa530_")
        self.assertEqual(row["filename"], "vicar-2021.tar.gz")
        self.assertEqual(row["license"], "CC BY 4.0")

    def test_list_weights(self):
        df = pineapple(category="weights", verbose=False)
        self.assertEqual(df.shape[0], len(gget_pineapple._WEIGHTS))
        row = df[df["name"] == "dino_vit_small"].iloc[0]
        self.assertEqual(row["filename"], "dinov2_vits14_imagenet.safetensors")

    def test_single_entry_json(self):
        result = pineapple("vicar_2021", json=True, verbose=False)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "vicar_2021")

    def test_resource_filename(self):
        self.assertEqual(
            _resource_filename("segmentation", "vicar_2021", gget_pineapple._SEGMENTATION["vicar_2021"]),
            "vicar-2021.tar.gz",
        )
        self.assertEqual(
            _resource_filename("weights", "dino_vit_small", gget_pineapple._WEIGHTS["dino_vit_small"]),
            "dinov2_vits14_imagenet.safetensors",
        )

    def test_catalog_row_types(self):
        row = _catalog_row("benchmark", "runtime", gget_pineapple._BENCHMARK["runtime"])
        self.assertEqual(row["category"], "benchmark")
        self.assertIsInstance(row["size_gb"], float)

    def test_parse_gdrive_form(self):
        html = (
            '<html><body><form id="download-form" action="https://drive.usercontent.google.com/download">'
            '<input type="hidden" name="id" value="ABC123">'
            '<input type="hidden" name="confirm" value="t">'
            '<input type="hidden" name="uuid" value="xyz"></form></body></html>'
        )
        action, params = _parse_gdrive_form(html)
        self.assertEqual(action, "https://drive.usercontent.google.com/download")
        self.assertEqual(params, {"id": "ABC123", "confirm": "t", "uuid": "xyz"})

    def test_parse_gdrive_form_absent(self):
        action, params = _parse_gdrive_form("<html><body>direct download</body></html>")
        self.assertIsNone(action)
        self.assertEqual(params, {})

    @patch.object(gget_pineapple, "_download_from_gdrive")
    def test_download_invokes_gdrive(self, mock_dl):
        df = pineapple("vicar_2021", download=True, out_dir="/tmp/pineapple_test_dir", verbose=False)
        self.assertTrue(mock_dl.called)
        args, _ = mock_dl.call_args
        # Called with the correct Google Drive file ID and destination path
        self.assertEqual(args[0], "12tJOlIHZPFqp8GLek_jV__Uhhgsa530_")
        self.assertTrue(args[1].endswith("vicar-2021.tar.gz"))
        self.assertEqual(df.iloc[0]["name"], "vicar_2021")


if __name__ == "__main__":
    unittest.main()
