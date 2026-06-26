import os
import tempfile
import unittest

from gget.gget_g2p import _resolve_gene_from_uniprot, g2p


class TestG2P(unittest.TestCase):
    """Integration tests against the live Genomics 2 Proteins (G2P) portal.

    The G2P feature table is very wide (140+ columns) and its numeric values can
    change as the portal is updated, so these tests assert on stable structural
    properties (column names, stable identifiers) rather than hard-coding the
    full result.
    """

    def test_g2p_map(self):
        df = g2p("BRCA1", uniprot_id="P38398", resource="map", verbose=False)
        self.assertListEqual(
            list(df.columns),
            [
                "UniProtKB",
                "UniProt Isoform",
                "Ensembl Gene Id",
                "Ensembl Protein Id",
                "Ensembl Transcript Id",
                "RefSeq mRNA Id",
                "PDB Ids",
            ],
        )
        self.assertGreater(len(df), 0)
        # BRCA1's stable Ensembl gene ID should be present
        self.assertTrue((df["Ensembl Gene Id"] == "ENSG00000012048").any())

    def test_g2p_features(self):
        df = g2p("BRCA1", uniprot_id="P38398", resource="features", verbose=False)
        self.assertGreater(len(df), 100)
        for col in ["residueId", "AA", "AlphaFold confidence (pLDDT)"]:
            self.assertIn(col, df.columns)

    def test_g2p_alignment(self):
        df = g2p(
            "LDLR",
            uniprot_id="P01130-1",
            resource="alignment",
            isoform="P01130-2",
            verbose=False,
        )
        self.assertGreater(len(df), 0)
        self.assertIn("residueId", df.columns)
        self.assertIn("AA", df.columns)

    def test_g2p_gene_auto_resolved(self):
        """When `gene` is omitted, it must be resolved from `uniprot_id` via UniProt."""
        _resolve_gene_from_uniprot.cache_clear()
        df = g2p(uniprot_id="P38398", resource="map", verbose=False)
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
        self.assertTrue((df["Ensembl Gene Id"] == "ENSG00000012048").any())

    def test_g2p_invalid_pair_returns_none(self):
        """Regression: the G2P portal returns HTTP 200 with a JSON failure body when the
        gene/UniProt pair is unknown. Previously this leaked through as a 0-row DataFrame
        whose only column name was the JSON error string; now it must return None.
        """
        df = g2p("BRCA1", uniprot_id="P01130", resource="features", verbose=False)
        self.assertIsNone(df)

    def test_g2p_out_writes_to_explicit_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "g2p_map.csv")
            df = g2p(
                "BRCA1",
                uniprot_id="P38398",
                resource="map",
                out=out_path,
                verbose=False,
            )
            self.assertIsNotNone(df)
            self.assertTrue(os.path.exists(out_path))
            self.assertGreater(os.path.getsize(out_path), 0)


class TestG2PValidation(unittest.TestCase):
    """Fast, network-free tests for argument validation."""

    def test_invalid_resource_raises(self):
        with self.assertRaises(ValueError):
            g2p("BRCA1", uniprot_id="P38398", resource="not_a_resource")

    def test_missing_uniprot_raises(self):
        with self.assertRaises(ValueError):
            g2p("BRCA1", uniprot_id=None)

    def test_alignment_requires_isoform(self):
        with self.assertRaises(ValueError):
            g2p("LDLR", uniprot_id="P01130-1", resource="alignment")
