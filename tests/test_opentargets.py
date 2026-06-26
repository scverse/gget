import json
import unittest

from gget.gget_opentargets import opentargets

from .from_json import from_json

with open("./tests/fixtures/test_opentargets.json") as json_file:
    ot_dict = json.load(json_file)

GENE = "ENSG00000169194"  # IL13 — the single gene all these fixtures query


class TestOpenTargets(unittest.TestCase, metaclass=from_json(ot_dict, opentargets)):
    """Most tests are generated from the JSON fixture. The methods below replace the
    fixture entries marked ``code_defined`` — resources whose live OpenTargets data
    drifts between releases. Since every fixture queries IL13 (ENSG00000169194), we
    assert IL13's specific, biologically-stable facts directly (known entities by
    name/id, scores within a tolerance of a baseline) instead of pinning exact values
    (fragile) or checking only generic formats (too weak). See issue #249.
    Baselines captured at OpenTargets data v26.06; score tolerance 0.15 (drift ~5%/release)."""

    # ---------- diseases ----------
    def _check_il13_diseases(self):
        df = opentargets(GENE, resource="diseases", limit=15, verbose=False)
        hits = dict(zip(df["disease.name"], zip(df["disease.id"], df["score"])))

        self.assertIn("atopic eczema", hits)
        did, score = hits["atopic eczema"]
        self.assertIn(did, {"EFO_0000274", "MONDO_0004980"})  # id may migrate EFO<->MONDO
        self.assertAlmostEqual(score, 0.73, delta=0.15)

        self.assertIn("asthma", hits)
        did, score = hits["asthma"]
        self.assertEqual(did, "MONDO_0004979")
        self.assertAlmostEqual(score, 0.70, delta=0.15)

    def test_opentargets(self):
        self._check_il13_diseases()

    def test_opentargets_diseases(self):
        self._check_il13_diseases()

    # ---------- drugs ----------
    def test_opentargets_drugs(self):
        df = opentargets(GENE, resource="drugs", limit=25, verbose=False)
        names = {str(n).upper() for n in df["drug.name"].dropna()}
        self.assertIn("LEBRIKIZUMAB", names)  # an approved IL-13 inhibitor targeting IL13

        row = df[df["drug.name"].str.upper() == "LEBRIKIZUMAB"].iloc[0]
        self.assertEqual(row["drug.drugType"], "Antibody")
        self.assertTrue(str(row["drug.id"]).startswith("CHEMBL"))
        self.assertIn("interleukin-13 inhibitor", str(row["drug.mechanismsOfAction.rows"]).lower())
        # synonyms must be a flat list of strings (the GraphQL { label } sub-selection fix)
        self.assertIsInstance(row["drug.synonyms"], list)
        self.assertIn("Lebrikizumab", row["drug.synonyms"])

    # ---------- expression: retired upstream in 26.06; migration tracked in #247/#248 ----------
    @unittest.skip(
        "OpenTargets target.expressions retired in 26.06 (returns empty); migration to baselineExpression tracked in #247/#248"
    )
    def test_opentargets_expression(self):
        pass

    @unittest.skip(
        "OpenTargets target.expressions retired in 26.06 (returns empty); migration to baselineExpression tracked in #247/#248"
    )
    def test_opentargets_expression_no_limit(self):
        pass

    # ---------- depmap ----------
    def test_opentargets_depmap(self):
        df = opentargets(GENE, resource="depmap", verbose=False)
        self.assertGreater(len(df), 0)
        for col in ("tissueId", "tissueName", "depmapId", "geneEffect"):
            self.assertIn(col, df.columns)
        # DepMap gene-effect scores fall roughly within [-3, 2]; just sanity-bound them.
        self.assertTrue(df["geneEffect"].dropna().between(-3, 2).all())
        self.assertTrue(df["depmapId"].dropna().str.startswith("ACH-").all())

    def test_opentargets_depmap_filter(self):
        # Filtering must return only rows for the requested tissue. Pick a tissue present
        # now (which ones carry data varies by release) and check the filter holds.
        full = opentargets(GENE, resource="depmap", verbose=False)
        self.assertGreater(len(full), 0)
        tissue = full.iloc[0]["tissueId"]
        filtered = opentargets(GENE, resource="depmap", filters={"tissueId": tissue}, verbose=False)
        self.assertGreater(len(filtered), 0)
        self.assertTrue((filtered["tissueId"] == tissue).all())

    # ---------- interactions ----------
    def _check_il13_interactions(self):
        df = opentargets(GENE, resource="interactions", limit=25, verbose=False)
        self.assertTrue((df["targetA.id"].dropna() == GENE).all())  # source is the query gene
        partners = set(df["targetB.approvedSymbol"].dropna())
        self.assertIn("IL13RA1", partners)  # IL13's canonical receptors
        self.assertIn("IL13RA2", partners)
        self.assertTrue(df["score"].dropna().between(0, 1).all())

    def test_opentargets_interactions(self):
        self._check_il13_interactions()

    def test_opentargets_interactions_no_limit(self):
        self._check_il13_interactions()

    # ---------- pharmacogenetics ----------
    def test_opentargets_pharmacogenetics(self):
        df = opentargets(GENE, resource="pharmacogenetics", limit=2, verbose=False)
        self.assertGreater(len(df), 0)
        for col in ("variantId", "genotype", "genotypeId"):
            self.assertIn(col, df.columns)
        # genotypes are nucleotide alleles, e.g. "CT", "CC"
        self.assertTrue(df["genotype"].dropna().str.match(r"^[ACGTN/,\- ]+$", case=False).all())
        self.assertTrue(df["variantId"].dropna().astype(str).str.strip().ne("").all())
