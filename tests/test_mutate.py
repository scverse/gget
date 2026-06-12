import json
import os
import tempfile
import unittest

import gget
import pandas as pd
import pytest

from .from_json import do_call, from_json

LONG_SEQUENCE = "CCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCG"
EXTRA_LONG_SEQUENCE = "CCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCG"
LONG_SEQUENCE_WITH_N = "CCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCNCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCGCCCCTCCCCGCCCCACCCCG"


@pytest.fixture
def create_temp_files():
    # Create a temporary CSV file
    temp_csv_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")

    # Data to write to CSV
    mutation_list = ["c.35G>A", "c.65G>A", "c.35del", "c.4_5insT"]
    protein_mutation_list = ["A12T", "A22T", "A12del", "A4_5insT"]
    mut_ID_list = [
        "GENE1_MUT1A_MUT1B",
        "GENE1_MUT2A_MUT2B",
        "GENE2_MUT1A_MUT1B",
        "GENE3_MUT1A_MUT1B",
    ]
    seq_ID_list = ["ENST1", "ENST2", "ENST3", "ENST4"]

    data = {
        "mutation": mutation_list,
        "mutation_aa": protein_mutation_list,
        "mut_ID": mut_ID_list,
        "seq_ID": seq_ID_list,
    }

    df = pd.DataFrame(data)
    df.to_csv(temp_csv_file.name, index=False)

    # Create a temporary FASTA file
    sequence_list = [LONG_SEQUENCE for _ in range(len(mutation_list))]
    temp_fasta_file = tempfile.NamedTemporaryFile(delete=False, suffix=".fasta")

    with open(temp_fasta_file.name, "w") as fasta_file:
        for seq_id, sequence in zip(seq_ID_list, sequence_list, strict=False):
            fasta_file.write(f">{seq_id}\n")
            fasta_file.write(f"{sequence}\n")

    yield temp_csv_file.name, temp_fasta_file.name

    # Cleanup
    os.remove(temp_csv_file.name)
    os.remove(temp_fasta_file.name)


def assert_global_variables_zero(
    number_intronic_position_mutations=0,
    number_posttranslational_region_mutations=0,
    number_uncertain_mutations=0,
    number_ambiguous_position_mutations=0,
    number_index_errors=0,
):
    assert gget.gget_mutate.intronic_mutations == number_intronic_position_mutations
    assert gget.gget_mutate.posttranslational_region_mutations == number_posttranslational_region_mutations
    assert gget.gget_mutate.uncertain_mutations == number_uncertain_mutations
    assert gget.gget_mutate.ambiguous_position_mutations == number_ambiguous_position_mutations
    assert gget.gget_mutate.mut_idx_outside_seq == number_index_errors


def _recursive_replace(v, old: str, new: str, exact=False):
    if isinstance(v, str):
        if exact:
            if v == old:
                return new
            else:
                return v
        else:
            return v.replace(old, new)
    elif isinstance(v, dict):
        return {
            _recursive_replace(k, old, new, exact=exact): _recursive_replace(v, old, new, exact=exact)
            for k, v in v.items()
        }
    elif isinstance(v, list):
        return [_recursive_replace(v, old, new, exact=exact) for v in v]
    else:
        return v


def _assert_mutate(name: str, td, func):
    ls = LONG_SEQUENCE

    def assert_mutate(self: unittest.TestCase):
        # reset global variables
        gget.gget_mutate.intronic_mutations = 0
        gget.gget_mutate.posttranslational_region_mutations = 0
        gget.gget_mutate.uncertain_mutations = 0
        gget.gget_mutate.ambiguous_position_mutations = 0
        gget.gget_mutate.mut_idx_outside_seq = 0

        test = name
        expected_result = td[test].get("expected_result", None)
        global_variables = td[test].get("global_variables", {})

        args = td[test]["args"]

        args = _recursive_replace(args, "<long_sequence>", ls, exact=True)
        # args = _recursive_replace(args, "<extra_long_sequence>", els, exact=True)
        # args = _recursive_replace(args, "<long_sequence_with_n>", ls_with_n, exact=True)

        result = do_call(func, args)

        if expected_result:
            self.assertEqual(result[0], expected_result)

        assert_global_variables_zero(**global_variables)

    return assert_mutate


def _assert_mutate_N(name: str, td, func):
    ls_with_n = LONG_SEQUENCE_WITH_N

    def assert_mutate_N(self: unittest.TestCase):
        # reset global variables
        gget.gget_mutate.intronic_mutations = 0
        gget.gget_mutate.posttranslational_region_mutations = 0
        gget.gget_mutate.uncertain_mutations = 0
        gget.gget_mutate.ambiguous_position_mutations = 0
        gget.gget_mutate.mut_idx_outside_seq = 0

        test = name
        expected_result = td[test].get("expected_result", None)
        global_variables = td[test].get("global_variables", {})

        args = td[test]["args"]

        args = _recursive_replace(args, "<long_sequence_with_N>", ls_with_n, exact=True)

        result = do_call(func, args)

        if expected_result:
            self.assertEqual(result[0], expected_result)

        assert_global_variables_zero(**global_variables)

    return assert_mutate_N


def _assert_mutate_long(name: str, td, func):
    els = EXTRA_LONG_SEQUENCE

    def assert_mutate_long(self: unittest.TestCase):
        # reset global variables
        gget.gget_mutate.intronic_mutations = 0
        gget.gget_mutate.posttranslational_region_mutations = 0
        gget.gget_mutate.uncertain_mutations = 0
        gget.gget_mutate.ambiguous_position_mutations = 0
        gget.gget_mutate.mut_idx_outside_seq = 0

        test = name
        expected_result = td[test].get("expected_result", None)
        global_variables = td[test].get("global_variables", {})

        args = td[test]["args"]

        args = _recursive_replace(args, "<extra_long_sequence>", els, exact=True)
        # args = _recursive_replace(args, "<long_sequence_with_n>", ls_with_n, exact=True)

        result = do_call(func, args)

        if expected_result:
            self.assertEqual(result[0], expected_result)

        assert_global_variables_zero(**global_variables)

    return assert_mutate_long


with open("./tests/fixtures/test_mutate.json") as json_file:
    mutate_dict = json.load(json_file)


class TestMutate(
    unittest.TestCase,
    metaclass=from_json(
        mutate_dict,
        gget.mutate,
        {
            "assert_mutate": _assert_mutate,
            "assert_mutate_N": _assert_mutate_N,
            "assert_mutate_long": _assert_mutate_long,
        },
    ),
):
    pass  # all tests are loaded from json


# special tests that don't fit the json format
def test_csv_of_mutations(create_temp_files):
    mutation_temp_csv_file, sequence_temp_fasta_path = create_temp_files

    result = gget.mutate(sequences=sequence_temp_fasta_path, mutations=mutation_temp_csv_file)

    assert result == [
        "GCCCCACCCCGCCCCTCCCCGCCCCACCCCACCCCTCCCCGCCCCACCCCGCCCCTCCCCG",
        "GCCCCTCCCCGCCCCACCCCGCCCCTCCCCACCCCACCCCG",
        "GCCCCACCCCGCCCCTCCCCGCCCCACCCCCCCCTCCCCGCCCCACCCCGCCCCTCCCCG",
        "CCCCTGCCCCACCCCGCCCCTCCCCGCCCCACCCC",
    ]

    assert_global_variables_zero()


def test_mismatch_error():
    gget.gget_mutate.mutate(sequences=LONG_SEQUENCE, mutations="c.2G>A")

    assert gget.gget_mutate.cosmic_incorrect_wt_base == 1

    assert_global_variables_zero()
