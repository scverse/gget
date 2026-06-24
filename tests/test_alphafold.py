import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import gget.gget_alphafold as gget_alphafold
from gget.gget_alphafold import (
    clean_up,
    detect_msa_format,
    get_jackhmmer_dir,
    parse_custom_msa,
)
from gget.gget_setup import UUID

# AlphaFold requires heavy third-party dependencies (alphafold, openmm, jackhmmer, model
# parameters) that are not available in the CI/test environment, so a full prediction run
# cannot be exercised here. These tests validate the user-facing jackhmmer save-directory
# option (https://github.com/scverse/gget/issues/49) at the argument/path-handling level and
# the user-provided custom MSA input feature (https://github.com/scverse/gget/issues/52) at
# the parsing/validation level (the logic that turns a custom a3m/FASTA file into AlphaFold
# MSA features).

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
A3M_FIXTURE = os.path.join(FIXTURE_DIR, "test_alphafold_msa.a3m")
FASTA_FIXTURE = os.path.join(FIXTURE_DIR, "test_alphafold_msa.fasta")

QUERY = "MKVLAAGSTKDEFGHIKLMN"


class TestAlphafoldJackhmmerSavedir(unittest.TestCase):
    def test_default_dir(self):
        """Without a custom save directory, the default ~/tmp/jackhmmer/<UUID> is used."""
        expected = os.path.expanduser(os.path.join("~", "tmp", "jackhmmer", UUID))
        self.assertEqual(get_jackhmmer_dir(), expected)
        self.assertEqual(get_jackhmmer_dir(None), expected)

    def test_custom_dir(self):
        """A custom save directory is honored and returned as an absolute path."""
        custom = os.path.join("some", "custom", "place")
        result = get_jackhmmer_dir(custom)
        expected = os.path.abspath(os.path.join(custom, "jackhmmer", UUID))
        self.assertEqual(result, expected)
        self.assertTrue(os.path.isabs(result))

    def test_clean_up_removes_custom_dir(self):
        """clean_up() deletes leftover FASTA files and the temporary folder it is given."""
        import tempfile

        with tempfile.TemporaryDirectory() as parent:
            jackhmmer_dir = get_jackhmmer_dir(parent)
            os.makedirs(jackhmmer_dir, exist_ok=True)
            fasta_path = os.path.join(jackhmmer_dir, "target_1.fasta")
            with open(fasta_path, "w") as f:
                f.write(">query\nMKV")

            clean_up(jackhmmer_dir)

            self.assertFalse(os.path.exists(fasta_path))
            self.assertFalse(os.path.isdir(jackhmmer_dir))

    def test_clean_up_missing_dir_is_safe(self):
        """clean_up() does not raise if the target directory does not exist."""
        missing = get_jackhmmer_dir(os.path.join("definitely", "not", "there"))
        # Should be a no-op rather than raising.
        clean_up(missing)

    def test_clean_up_default_dir_when_none(self):
        """clean_up(None) resolves the default directory via get_jackhmmer_dir()."""
        import tempfile

        with tempfile.TemporaryDirectory() as parent:
            default_dir = os.path.join(parent, "jackhmmer", "default")
            os.makedirs(default_dir, exist_ok=True)
            # Patch get_jackhmmer_dir so the None default resolves to a temp folder
            # (never the real ~/tmp) for the duration of the call.
            with patch.object(gget_alphafold, "get_jackhmmer_dir", return_value=default_dir) as mock_dir:
                clean_up()
                mock_dir.assert_called_once()
            self.assertFalse(os.path.isdir(default_dir))

    def test_cli_exposes_jackhmmer_savedir_flag(self):
        """The command-line interface exposes the --jackhmmer_savedir option."""
        result = subprocess.run(
            [sys.executable, "-m", "gget", "alphafold", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertIn("--jackhmmer_savedir", result.stdout)


class TestAlphafoldCustomMSA(unittest.TestCase):
    def test_detect_msa_format(self):
        self.assertEqual(detect_msa_format("alignment.a3m"), "a3m")
        self.assertEqual(detect_msa_format("/path/to/ALIGNMENT.A3M"), "a3m")
        self.assertEqual(detect_msa_format("alignment.fasta"), "fasta")
        self.assertEqual(detect_msa_format("alignment.fa"), "fasta")
        self.assertEqual(detect_msa_format("alignment.afa"), "fasta")

    def test_detect_msa_format_unsupported(self):
        with self.assertRaises(ValueError):
            detect_msa_format("alignment.txt")
        with self.assertRaises(ValueError):
            detect_msa_format("alignment.sto")

    def test_parse_a3m_fixture(self):
        with open(A3M_FIXTURE) as f:
            aligned_sequences, deletion_matrix, descriptions = parse_custom_msa(f.read())

        # Four sequences, the first of which is the query.
        self.assertEqual(len(aligned_sequences), 4)
        self.assertEqual(len(descriptions), 4)
        self.assertEqual(aligned_sequences[0], QUERY)

        # After removing a3m insertions, every aligned row has the query's length.
        for seq in aligned_sequences:
            self.assertEqual(len(seq), len(QUERY))

        # Deletion matrix rows align 1:1 with the aligned columns.
        for seq, deletions in zip(aligned_sequences, deletion_matrix, strict=True):
            self.assertEqual(len(deletions), len(seq))

        # The query and the gapped homolog carry no insertions.
        self.assertEqual(sum(deletion_matrix[0]), 0)
        self.assertEqual(sum(deletion_matrix[2]), 0)

        # homolog3 has two lowercase insertion characters ("ef") after the third residue.
        self.assertEqual(sum(deletion_matrix[3]), 2)
        self.assertEqual(deletion_matrix[3][3], 2)

    def test_parse_fasta_fixture_has_no_insertions(self):
        with open(FASTA_FIXTURE) as f:
            aligned_sequences, deletion_matrix, _ = parse_custom_msa(f.read())

        self.assertEqual(aligned_sequences[0], QUERY)
        # Aligned FASTA contains no lowercase insertions -> deletion matrix is all zeros.
        for deletions in deletion_matrix:
            self.assertEqual(sum(deletions), 0)

    def test_query_matches_first_msa_sequence(self):
        # Mirrors the validation gget performs: first MSA sequence (gaps removed) == query.
        with open(A3M_FIXTURE) as f:
            aligned_sequences, _, _ = parse_custom_msa(f.read())
        query_in_msa = aligned_sequences[0].replace("-", "").upper()
        self.assertEqual(query_in_msa, QUERY)

    def test_parse_empty_msa_raises(self):
        with self.assertRaises(ValueError):
            parse_custom_msa("")

    def test_parse_non_fasta_raises(self):
        with self.assertRaises(ValueError):
            parse_custom_msa("MKVLAAG\nNOHEADERLINE\n")

    def test_cli_exposes_msa_flag(self):
        """The command-line interface exposes the --msa option for gget alphafold."""
        result = subprocess.run(
            [sys.executable, "-m", "gget", "alphafold", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertIn("--msa", result.stdout)


if __name__ == "__main__":
    unittest.main()
