import json
import unittest

import pytest
from gget.gget_blast import blast

from .from_json import from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_blast.json") as json_file:
    blast_dict = json.load(json_file)

# test_blast_nt submits a live search to NCBI's web BLAST queue, and gget.blast polls every
# 61 s until the job finishes. When the queue is backed up this has taken over 2.5 h,
# pushing the CI job toward GitHub's 6 h limit. Fail after 20 min instead (pytest-timeout).
pytestmark = pytest.mark.timeout(20 * 60)


class TestBlast(unittest.TestCase, metaclass=from_json(blast_dict, blast)):
    pass  # all tests are loaded from json
