import contextlib
import filecmp
import os
import unittest

# Library to test functions that have calls to print()
from unittest import mock

from gget.gget_muscle import muscle


class TestMuscle(unittest.TestCase):
    def test_muscle_nt(self):
        # File with sequences to align
        fasta = "tests/fixtures/muscle_nt_test.fa"
        # File the results will be saved in
        out = "tests/fixtures/tmp.afa"

        # Run muscle (trying to use contextlib here to silence muscle return (unsuccesfully))
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            muscle(fasta, out=out)

        # Expected result
        ref_path = "tests/fixtures/muscle_nt_test.afa"
        self.assertTrue(
            filecmp.cmp(out, ref_path, shallow=False),
            "The reference and muscle nucleotide alignment are not the same.",
        )

    def tearDown(self):
        super().tearDown()
        # Delete temporary result file
        os.remove("tests/fixtures/tmp.afa")

    def test_muscle_nt_txt(self):
        # File with sequences to align
        fasta = "tests/fixtures/muscle_nt_test.txt"
        # File the results will be saved in
        out = "tests/fixtures/tmp.afa"

        # Run muscle
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            muscle(fasta, out=out)

        # Expected result
        ref_path = "tests/fixtures/muscle_nt_test.afa"
        self.assertTrue(
            filecmp.cmp(out, ref_path, shallow=False),
            "The reference and muscle nucleotide alignment are not the same.",
        )


class TestMuscleSuper(unittest.TestCase):
    def test_muscle_nt_super5(self):
        # File with sequences to align
        fasta = "tests/fixtures/muscle_nt_test.fa"
        # File the results will be saved in
        out = "tests/fixtures/tmp.afa"

        # Run muscle
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            muscle(fasta, out=out, super5=True)

        # Expected result
        ref_path = "tests/fixtures/muscle_super5_nt_test.afa"
        self.assertTrue(
            filecmp.cmp(out, ref_path, shallow=False),
            "The reference and muscle super5 nucleotide alignment are not the same.",
        )

    def tearDown(self):
        super().tearDown()
        # Delete temporary result file
        os.remove("tests/fixtures/tmp.afa")


class TestMuscleAA(unittest.TestCase):
    def test_muscle_aa(self):
        # File with sequences to align
        fasta = "tests/fixtures/muscle_aa_test.fa"
        # File the results will be saved in
        out = "tests/fixtures/tmp.afa"

        # Run muscle
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            muscle(fasta, out=out)

        # Expected result
        ref_path = "tests/fixtures/muscle_aa_test.afa"
        self.assertTrue(
            filecmp.cmp(out, ref_path, shallow=False),
            "The reference and muscle amino acid alignment are not the same.",
        )

    def tearDown(self):
        super().tearDown()
        # Delete temporary result file
        os.remove("tests/fixtures/tmp.afa")


class TestMuscleSeqsInput(unittest.TestCase):
    def test_muscle_seqs_as_input(self):
        # File the results will be saved in
        out = "tests/fixtures/tmp.afa"

        # Run muscle
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            muscle(
                [
                    "MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS",
                    "MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS",
                    "MSAASWLLAAQSTIEQQAKTFLDKFHEAEDLFYQSS",
                ],
                out=out,
            )

        # Expected result
        ref_path = "tests/fixtures/muscle_SeqsAsInput_test.afa"
        self.assertTrue(
            filecmp.cmp(out, ref_path, shallow=False),
            "The reference and muscle amino acid alignment are not the same.",
        )

    def tearDown(self):
        super().tearDown()
        # Delete temporary result file
        os.remove("tests/fixtures/tmp.afa")


class TestMuscleAASuper(unittest.TestCase):
    def test_muscle_aa_super5(self):
        # File with sequences to align
        fasta = "tests/fixtures/muscle_aa_test.fa"
        # File the results will be saved in
        out = "tests/fixtures/tmp.afa"

        # Run muscle
        with contextlib.redirect_stdout(open(os.devnull, "w")):
            muscle(fasta, out=out, super5=True)

        # Expected result
        ref_path = "tests/fixtures/muscle_super5_aa_test.afa"
        self.assertTrue(
            filecmp.cmp(out, ref_path, shallow=False),
            "The reference and muscle super5 amino acid alignment are not the same.",
        )

    def tearDown(self):
        super().tearDown()
        # Delete temporary result file
        os.remove("tests/fixtures/tmp.afa")


class TestMusclePrints(unittest.TestCase):
    def test_muscle_print_nt(self):
        # File with sequences to align
        fasta = "tests/fixtures/muscle_nt_print_test.fa"

        # Capture muscle print output (for some reason, this only captures the last print output)
        with mock.patch("builtins.print") as print_mock:
            # Run muscle
            muscle(fasta)
            # print_mock.assert_called_with("\n")
            # print_mock.assert_called_with("test1\n", "\x1b[38;5;15m\x1b[48;5;9mA\x1b[0;0m")
            print_mock.assert_called_with("test2\n", "\t", "\x1b[38;5;15m\x1b[48;5;9mA\x1b[0;0m")
