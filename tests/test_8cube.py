import json
import os
import unittest

from gget.gget_8cube import gene_expression, psi_block, specificity

from .from_json import from_json

# Load JSON fixture
fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "test_8cube.json")

with open(fixture_path) as f:
    fixture = json.load(f)

# Split test cases by which function they belong to
specificity_tests = {k: v for k, v in fixture.items() if "specificity" in k}

psi_block_tests = {k: v for k, v in fixture.items() if "psi_block" in k}

gene_expression_tests = {k: v for k, v in fixture.items() if "gene_expression" in k}


class TestSpecificity(unittest.TestCase, metaclass=from_json(specificity_tests, specificity)):
    """Tests for specificity()"""

    pass


class TestPsiBlock(unittest.TestCase, metaclass=from_json(psi_block_tests, psi_block)):
    """Tests for psi_block()"""

    pass


class TestGeneExpression(unittest.TestCase, metaclass=from_json(gene_expression_tests, gene_expression)):
    """Tests for gene_expression()"""

    pass
