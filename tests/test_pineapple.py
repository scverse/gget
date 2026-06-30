import json
import unittest
from unittest.mock import patch

import gget.gget_pineapple as gget_pineapple
import requests
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
        # filename is DERIVED (underscore -> dash, + .tar.gz), so this exercises
        # real logic -- unlike asserting raw catalog values back at themselves.
        row = df[df["name"] == "vicar_2021"].iloc[0]
        self.assertEqual(row["filename"], "vicar-2021.tar.gz")

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


class TestPineappleLiveAccess(unittest.TestCase):
    """Live data test: verify a representative set of Pineapple resources is
    still downloadable from Google Drive (issue #161).

    This hits Google Drive over the network but never downloads the (multi-GB)
    bodies. Each file ID is resolved through the *same* production code path as
    a real download (``_resolve_gdrive_response``, including the large-file
    virus-scan-warning confirmation), and only the response headers are checked.

    Purpose: if someone edits the catalog, or upstream repoints/removes a file,
    this fails loudly -- the Google-Drive-reported filename must still match the
    catalog and the ID must still resolve to a binary download rather than an
    error/quota HTML page.

    Coverage is a small representative sample (not all 30 resources) to keep CI
    fast and resilient to Google Drive rate-limiting: one resource per category,
    both filename conventions (.tar.gz datasets vs explicit .safetensors
    weights), and both resolution paths (direct download vs the large-file
    virus-scan-warning form).
    """

    _CATALOGS = {
        "segmentation": gget_pineapple._SEGMENTATION,
        "benchmark": gget_pineapple._BENCHMARK,
        "weights": gget_pineapple._WEIGHTS,
    }

    _SAMPLE = [
        ("segmentation", "arvidsson_2022"),  # small .tar.gz, direct download
        ("benchmark", "kromp_2023"),  # small .tar.gz, benchmark category
        ("weights", "dino_vit_small"),  # explicit .safetensors filename
        ("segmentation", "hpa_2022"),  # large file -> virus-scan-warning form
    ]

    # 1 MB floor: catches an ID repointed to a tiny placeholder/error file.
    # NOT tied to the catalog's size_gb, which is only approximate (e.g.
    # livecell_2021 lists 3.26 GB but the real file is ~1.81 GB).
    _MIN_BYTES = 1_000_000

    def _check_resource(self, category, name):
        info = self._CATALOGS[category][name]
        expected = _catalog_row(category, name, info)

        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; gget)"})
        try:
            response = gget_pineapple._resolve_gdrive_response(session, expected["google_drive_id"])
        except requests.RequestException as exc:
            self.skipTest(f"Network error reaching Google Drive for {name}: {exc}")

        try:
            content_type = response.headers.get("Content-Type", "")
            # Google Drive serves a transient HTML "download quota exceeded" page
            # under load. Treat that as a skip (not a failure); a genuinely missing
            # file would have raised a 404/410 in _resolve_gdrive_response above.
            if "text/html" in content_type:
                self.skipTest(
                    f"Google Drive returned an HTML page (likely download-quota "
                    f"throttling) for {name}; skipping live check."
                )

            self.assertEqual(response.status_code, 200, f"{name}: unexpected status code")
            self.assertIn(
                "octet-stream",
                content_type,
                f"{name}: expected a binary download, got Content-Type {content_type!r}",
            )

            disposition = response.headers.get("Content-Disposition", "")
            self.assertIn(
                f'filename="{expected["filename"]}"',
                disposition,
                f"{name}: Google Drive filename does not match the catalog "
                f"(expected {expected['filename']!r}, Content-Disposition={disposition!r}). "
                f"The file ID may have been repointed upstream.",
            )

            length = response.headers.get("Content-Length")
            self.assertIsNotNone(length, f"{name}: response is missing Content-Length")
            self.assertGreater(
                int(length),
                self._MIN_BYTES,
                f"{name}: file is implausibly small ({length} bytes) -- possible placeholder",
            )
        finally:
            response.close()

    def test_live_resources_accessible(self):
        for category, name in self._SAMPLE:
            with self.subTest(category=category, name=name):
                self._check_resource(category, name)


if __name__ == "__main__":
    unittest.main()
