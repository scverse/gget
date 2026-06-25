import json
import re
import unittest

import pandas as pd
from gget.gget_opentargets import opentargets

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_opentargets.json") as json_file:
    ot_dict = json.load(json_file)

# Invariant value-format patterns: loose enough to survive routine OpenTargets data
# drift across releases, strict enough to catch genuine shape/format regressions.
_CURIE = re.compile(r"^[A-Za-z][A-Za-z0-9]*[_:][A-Za-z0-9]+$")  # e.g. MONDO_0004980, EFO_0000274, UBERON_0000977
_ENSG = re.compile(r"^ENSG\d+$")
_ACH = re.compile(r"^ACH-\d+$")  # DepMap cell-line id, e.g. ACH-000092
_GENOTYPE = re.compile(r"^[ACGTN/,\- ]+$", re.IGNORECASE)  # nucleotide-allele genotypes, e.g. CT, CC, TT


class TestOpenTargets(unittest.TestCase, metaclass=from_json(ot_dict, opentargets)):
    """Most tests are generated from the JSON fixture. The methods below override the
    fixture entries marked ``code_defined`` for resources whose live data legitimately
    drifts between OpenTargets releases (disease ids/scores, DepMap rows, interaction
    partners, pharmacogenetics genotypes).

    They assert structure and value *format* / invariants rather than pinning exact
    values, so they keep catching real regressions (wrong columns, malformed ids,
    empty-where-guaranteed, broken filtering) without breaking on routine upstream
    data updates. See issue #249."""

    def _run(self, name, **overrides):
        """Call opentargets with the fixture args for ``name`` (quietly)."""
        args = {**ot_dict[name]["args"], "verbose": False, **overrides}
        return opentargets(**args)

    # ----- diseases: top disease id + score drift each release -----
    def _assert_diseases(self, df):
        self.assertGreater(len(df), 0, "diseases query returned no rows")
        for col in ("score", "disease.id", "disease.name"):
            self.assertIn(col, df.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(df["score"]))
        for s in df["score"].dropna().head(50):
            self.assertGreaterEqual(float(s), 0.0)
            self.assertLessEqual(float(s), 1.0)
        for disease_id in df["disease.id"].dropna().head(50):
            self.assertRegex(str(disease_id), _CURIE)
        for disease_name in df["disease.name"].dropna().head(50):
            self.assertTrue(str(disease_name).strip(), "empty disease name")

    def test_opentargets(self):
        self._assert_diseases(self._run("test_opentargets"))

    def test_opentargets_diseases(self):
        self._assert_diseases(self._run("test_opentargets_diseases"))

    # ----- depmap: gene-effect rows change between releases -----
    def test_opentargets_depmap(self):
        df = self._run("test_opentargets_depmap")
        self.assertGreater(len(df), 0, "depmap query returned no rows")
        for col in ("tissueId", "tissueName", "depmapId", "geneEffect"):
            self.assertIn(col, df.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(df["geneEffect"]))
        for tissue_id in df["tissueId"].dropna().head(50):
            self.assertRegex(str(tissue_id), _CURIE)
        for depmap_id in df["depmapId"].dropna().head(50):
            self.assertRegex(str(depmap_id), _ACH)

    def test_opentargets_depmap_filter(self):
        # The filter invariant must hold regardless of which tissues currently carry
        # data: pick a tissue that is present now, then assert filtering returns only
        # rows for that tissue. (Pinning a specific tissue id is fragile — a given
        # tissue's screens can be empty in some releases.)
        eid = ot_dict["test_opentargets_depmap_filter"]["args"]["ensembl_id"]
        full = opentargets(ensembl_id=eid, resource="depmap", verbose=False)
        self.assertIn("tissueId", full.columns)
        self.assertGreater(len(full), 0, "depmap query returned no rows to filter")
        tissue = full.iloc[0]["tissueId"]
        filtered = opentargets(ensembl_id=eid, resource="depmap", filters={"tissueId": tissue}, verbose=False)
        self.assertGreater(len(filtered), 0)
        self.assertTrue((filtered["tissueId"] == tissue).all(), "filter returned rows for other tissues")

    # ----- interactions: partner ids change between releases -----
    def _assert_interactions(self, df):
        self.assertGreater(len(df), 0, "interactions query returned no rows")
        for col in ("score", "targetA.id", "targetB.id"):
            self.assertIn(col, df.columns)
        self.assertTrue(pd.api.types.is_numeric_dtype(df["score"]))
        for s in df["score"].dropna().head(50):
            self.assertGreaterEqual(float(s), 0.0)
            self.assertLessEqual(float(s), 1.0)
        for gene_id in df["targetA.id"].dropna().head(50):
            self.assertRegex(str(gene_id), _ENSG)
        for gene_id in df["targetB.id"].dropna().head(50):
            self.assertRegex(str(gene_id), _ENSG)

    def test_opentargets_interactions(self):
        self._assert_interactions(self._run("test_opentargets_interactions"))

    def test_opentargets_interactions_no_limit(self):
        self._assert_interactions(self._run("test_opentargets_interactions_no_limit"))

    # ----- pharmacogenetics: surfaced genotype / row order drift -----
    def test_opentargets_pharmacogenetics(self):
        df = self._run("test_opentargets_pharmacogenetics")
        self.assertGreater(len(df), 0, "pharmacogenetics query returned no rows")
        for col in ("variantId", "genotype", "genotypeId"):
            self.assertIn(col, df.columns)
        for genotype in df["genotype"].dropna().head(50):
            self.assertRegex(str(genotype), _GENOTYPE)
        for variant_id in df["variantId"].dropna().head(50):
            self.assertTrue(str(variant_id).strip(), "empty variantId")
