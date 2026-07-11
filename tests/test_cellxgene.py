import importlib.util
import json
import unittest

from gget.gget_cellxgene import SUPPORTED_SPECIES, cellxgene

# cellxgene-census has no wheels for some newer Python versions (e.g. 3.14, via
# its tiledbsoma dependency). The live integration tests below need it, so they
# skip when it is unavailable; the validation tests do not need it (the species
# allowlist check raises before the optional dependency is imported) and always run.
_HAS_CELLXGENE_CENSUS = importlib.util.find_spec("cellxgene_census") is not None

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_cellxgene.json") as json_file:
    cellxgene_dict = json.load(json_file)


def repr_dict(adata):
    """Convert the items/structure of an AnnData object to a dictionary."""
    d = {}
    for attr in (
        "n_obs",
        "n_vars",
        "obs",
        "var",
        "uns",
        "obsm",
        "varm",
        "layers",
        "obsp",
        "varp",
    ):
        got_attr = getattr(adata, attr)
        if isinstance(got_attr, int):
            d[attr] = got_attr
        else:
            # Ignore None keys: some cellxgene-census versions return an AnnData
            # whose `.layers` exposes a spurious `None` key, which is not a
            # meaningful (named) element and would otherwise break the structural
            # comparison in test_cellxgene_adata (issue #265).
            keys = [k for k in got_attr.keys() if k is not None]
            if keys:
                d[attr] = keys
    return d


@unittest.skipUnless(_HAS_CELLXGENE_CENSUS, "cellxgene-census is not installed")
class TestCellxgene(unittest.TestCase):
    def test_cellxgene_adata(self):
        test = "test_cellxgene_adata"
        expected_result = cellxgene_dict[test]["expected_result"]
        result_to_test = cellxgene(**cellxgene_dict[test]["args"])

        # Convert resulting AnnData object to dictionary
        result_to_test = repr_dict(result_to_test)

        self.assertEqual(result_to_test, expected_result)

    def test_cellxgene_metadata(self):
        test = "test_cellxgene_metadata"
        expected_result = cellxgene_dict[test]["expected_result"]
        result_to_test = cellxgene(**cellxgene_dict[test]["args"])

        # Convert dataframe to list (and only keep first 25 results)
        result_to_test = result_to_test.values.tolist()[:25]

        self.assertListEqual(result_to_test, expected_result)

    def test_cellxgene_metadata_macaca_mulatta(self):
        # Integration test for non-human primate support (Census LTS 2025-11-08+)
        test = "test_cellxgene_metadata_macaca_mulatta"
        expected_result = cellxgene_dict[test]["expected_result"]
        result_to_test = cellxgene(**cellxgene_dict[test]["args"])

        # Convert dataframe to list (and only keep first 25 results)
        result_to_test = result_to_test.values.tolist()[:25]

        self.assertListEqual(result_to_test, expected_result)


class TestCellxgeneValidation(unittest.TestCase):
    """Fast, network-free tests for the species allowlist validation."""

    def test_supported_species_includes_new_primates(self):
        for sp in [
            "homo_sapiens",
            "mus_musculus",
            "macaca_mulatta",
            "callithrix_jacchus",
            "pan_troglodytes",
        ]:
            self.assertIn(sp, SUPPORTED_SPECIES)

    def test_invalid_species_raises_valueerror(self):
        # Validation runs before any network access / optional dependency import,
        # so this must raise without contacting the Census API.
        with self.assertRaises(ValueError):
            cellxgene(species="not_a_species", tissue="lung")

    def test_typo_species_raises_valueerror(self):
        with self.assertRaises(ValueError):
            cellxgene(species="macaca_mulata", tissue="blood")


class TestReprDict(unittest.TestCase):
    """Network-free tests for the repr_dict helper (issue #265).

    These do not need cellxgene-census, so they run on every Python version
    (including ones where the live Census tests are skipped), guarding the
    None-key handling that keeps test_cellxgene_adata robust to upstream drift.
    """

    class _FakeAnnData:
        n_obs = 3
        n_vars = 2
        obs = {"cell_type": None, "tissue": None}
        var = {"feature_id": None}
        uns: dict = {}
        obsm: dict = {}
        varm: dict = {}
        layers = {None: "spurious"}  # cellxgene-census can expose a None-keyed layer
        obsp: dict = {}
        varp: dict = {}

    def test_repr_dict_ignores_none_layer_key(self):
        d = repr_dict(self._FakeAnnData())
        # A layer whose only key is None must not surface as structure.
        self.assertNotIn("layers", d)
        # Meaningful (named) elements are still reported.
        self.assertEqual(d["n_obs"], 3)
        self.assertEqual(d["obs"], ["cell_type", "tissue"])
        self.assertEqual(d["var"], ["feature_id"])
