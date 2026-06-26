import os
import tempfile
import unittest

from gget.gget_g2p import _resolve_gene_from_uniprot, _resolve_uniprot_from_gene, g2p


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
                "gene_name",
                "uniprot_id",
                "UniProtKB",
                "UniProt Isoform",
                "Ensembl Gene Id",
                "Ensembl Protein Id",
                "Ensembl Transcript Id",
                "RefSeq mRNA Id",
                "PDB Ids",
                "PDB Ids List",
            ],
        )
        self.assertGreater(len(df), 0)
        # Identifier columns are populated with the query pair on every row.
        self.assertTrue((df["gene_name"] == "BRCA1").all())
        self.assertTrue((df["uniprot_id"] == "P38398").all())
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

    def test_g2p_uniprot_auto_resolved(self):
        """When only `gene` is supplied, UniProt accession must be resolved via UniProt."""
        _resolve_uniprot_from_gene.cache_clear()
        df = g2p("BRCA1", resource="map", verbose=False)
        self.assertIsNotNone(df)
        # The canonical pair travels with the data both as leading columns and df.attrs
        self.assertIn("gene_name", df.columns)
        self.assertIn("uniprot_id", df.columns)
        self.assertTrue((df["gene_name"] == "BRCA1").all())
        self.assertTrue((df["uniprot_id"] == "P38398").all())
        self.assertEqual(df.attrs.get("gene_name"), "BRCA1")
        self.assertEqual(df.attrs.get("uniprot_id"), "P38398")

    def test_g2p_schema_invariant_across_input_modes(self):
        """Output schema must be identical whether the user passes gene-only,
        uniprot-only, or both — including the leading gene_name / uniprot_id columns."""
        df_both = g2p("BRCA1", uniprot_id="P38398", resource="map", verbose=False)
        df_gene_only = g2p("BRCA1", resource="map", verbose=False)
        df_uniprot_only = g2p(uniprot_id="P38398", resource="map", verbose=False)
        self.assertEqual(list(df_both.columns), list(df_gene_only.columns))
        self.assertEqual(list(df_both.columns), list(df_uniprot_only.columns))
        self.assertEqual(list(df_both.columns[:2]), ["gene_name", "uniprot_id"])

    def test_g2p_residues_filter(self):
        """`residues=` restricts the features table to the requested positions."""
        df = g2p(
            "BRCA1",
            uniprot_id="P38398",
            resource="features",
            residues=[1, 100, 1000],
            verbose=False,
        )
        self.assertIsNotNone(df)
        self.assertEqual(sorted(df["residueId"].tolist()), [1, 100, 1000])

    def test_g2p_residues_single_int(self):
        df = g2p(
            "BRCA1",
            uniprot_id="P38398",
            resource="features",
            residues=42,
            verbose=False,
        )
        self.assertIsNotNone(df)
        self.assertEqual(df["residueId"].tolist(), [42])

    def test_g2p_map_has_pdb_list_column(self):
        """The `map` resource gets a parsed `PDB Ids List` column for direct consumption."""
        df = g2p("BRCA1", uniprot_id="P38398", resource="map", verbose=False)
        self.assertIn("PDB Ids List", df.columns)
        # Each non-null entry should be a list of strings
        for entry in df["PDB Ids List"].head(3):
            self.assertIsInstance(entry, list)
            for item in entry:
                self.assertIsInstance(item, str)


class TestG2PValidation(unittest.TestCase):
    """Fast, network-free tests for argument validation."""

    def test_invalid_resource_raises(self):
        with self.assertRaises(ValueError):
            g2p("BRCA1", uniprot_id="P38398", resource="not_a_resource")

    def test_missing_both_raises(self):
        with self.assertRaises(ValueError):
            g2p()

    def test_alignment_requires_isoform(self):
        with self.assertRaises(ValueError):
            g2p("LDLR", uniprot_id="P01130-1", resource="alignment")

    def test_alignment_requires_explicit_uniprot(self):
        """Alignment cannot rely on gene→UniProt resolution (returns base accession, no isoform)."""
        with self.assertRaises(ValueError):
            g2p("LDLR", resource="alignment", isoform="P01130-2")

    def test_residues_on_map_raises(self):
        with self.assertRaises(ValueError):
            g2p("BRCA1", uniprot_id="P38398", resource="map", residues=[1, 2, 3])

    def test_residues_wrong_type_raises(self):
        with self.assertRaises(ValueError):
            g2p("BRCA1", uniprot_id="P38398", residues="not-ints")  # type: ignore[arg-type]
