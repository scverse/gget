import pytest

from gget.utils import read_fasta


@pytest.mark.parametrize("prefix", ["", ">first\nACGT\n"])
@pytest.mark.parametrize("ending", ["", "\n", "\n\n", "\n \t\n"])
def test_read_fasta_missing_final_sequence(tmp_path, prefix, ending):
    fasta = tmp_path / "incomplete.fa"
    fasta.write_text(f"{prefix}>missing{ending}")

    with pytest.raises(ValueError, match="missing sequence"):
        read_fasta(str(fasta))


@pytest.mark.parametrize("ending", ["", "\n"])
@pytest.mark.parametrize("separator", ["\n", "\n\n", "\n \t\n"])
def test_read_fasta_complete_records(tmp_path, ending, separator):
    fasta = tmp_path / "complete.fa"
    fasta.write_text(f">first{separator}AC\nGT\n>second\nTGCA{ending}")

    assert read_fasta(str(fasta)) == (["first", "second"], ["ACGT", "TGCA"])


@pytest.mark.parametrize("separator", ["\n", "\n\n"])
def test_read_fasta_consecutive_headers(tmp_path, separator):
    fasta = tmp_path / "incomplete.fa"
    fasta.write_text(f">first{separator}>second\nACGT\n")

    with pytest.raises(ValueError, match="missing sequence"):
        read_fasta(str(fasta))
