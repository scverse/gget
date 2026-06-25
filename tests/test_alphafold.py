import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import gget.gget_alphafold as gget_alphafold
from gget.gget_alphafold import clean_up, get_jackhmmer_dir
from gget.gget_setup import UUID

# AlphaFold requires heavy third-party dependencies (alphafold, openmm, jackhmmer, model
# parameters) that are not available in the CI/test environment, so a full prediction run
# cannot be exercised here. These tests validate the user-facing jackhmmer save-directory
# option (https://github.com/scverse/gget/issues/49) at the argument/path-handling level.


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


if __name__ == "__main__":
    unittest.main()
