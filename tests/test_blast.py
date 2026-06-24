import json
import unittest

from gget.gget_blast import _build_algorithm_params, blast

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_blast.json") as json_file:
    blast_dict = json.load(json_file)


class TestBlast(unittest.TestCase, metaclass=from_json(blast_dict, blast)):
    pass  # all tests are loaded from json


class TestBuildAlgorithmParams(unittest.TestCase):
    """Network-free tests for the web-BLAST algorithm parameters (issue #58)."""

    def test_empty(self):
        self.assertEqual(_build_algorithm_params(), [])

    def test_all_params(self):
        params = _build_algorithm_params(
            word_size=11,
            gapcosts="11 1",
            matrix="blosum62",
            nucl_reward=1,
            nucl_penalty=-2,
            perc_identity=90.0,
        )
        self.assertEqual(
            params,
            [
                ("WORD_SIZE", 11),
                ("GAPCOSTS", "11 1"),
                ("MATRIX", "BLOSUM62"),
                ("NUCL_REWARD", 1),
                ("NUCL_PENALTY", -2),
                ("PERC_IDENT", 90.0),
            ],
        )

    def test_matrix_uppercased(self):
        self.assertEqual(_build_algorithm_params(matrix="pam30"), [("MATRIX", "PAM30")])

    def test_invalid_word_size(self):
        with self.assertRaises(ValueError):
            _build_algorithm_params(word_size=1)
        with self.assertRaises(ValueError):
            _build_algorithm_params(word_size="big")

    def test_invalid_gapcosts(self):
        with self.assertRaises(ValueError):
            _build_algorithm_params(gapcosts="11")
        with self.assertRaises(ValueError):
            _build_algorithm_params(gapcosts="a b")

    def test_invalid_matrix(self):
        with self.assertRaises(ValueError):
            _build_algorithm_params(matrix="banana")

    def test_invalid_perc_identity(self):
        with self.assertRaises(ValueError):
            _build_algorithm_params(perc_identity=150)
