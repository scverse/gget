import json
import unittest
from unittest import mock

from gget.gget_blast import blast

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_blast.json") as json_file:
    blast_dict = json.load(json_file)


class TestBlast(unittest.TestCase, metaclass=from_json(blast_dict, blast)):
    def test_blast_core_nt_accepted(self):
        # 'core_nt' must pass argument validation (i.e. must not raise the
        # "invalid database" ValueError) and be submitted to NCBI as a
        # nucleotide database, equivalently to 'nt'. The network call is
        # mocked so no live BLAST job is submitted (those take minutes).
        # NOTE: This does not exercise an end-to-end BLAST against core_nt;
        # that should be verified manually.
        sequence = "ATGCGTACGTAGCTAGCTAGCTAGCATCGATCGATCGTAGCTAGCTAGC"

        with mock.patch("gget.gget_blast.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = RuntimeError("network call reached")
            # Validation passes -> we reach the (mocked) network call, which
            # raises our sentinel. If validation rejected 'core_nt', a
            # ValueError would be raised before urlopen is ever called.
            with self.assertRaises(RuntimeError) as cm:
                blast(sequence, database="core_nt", verbose=False)

        self.assertEqual(str(cm.exception), "network call reached")
        self.assertTrue(mock_urlopen.called)
