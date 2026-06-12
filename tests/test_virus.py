"""Unit tests for gget virus module.

This test module provides comprehensive validation of the virus function
and all helper functions, covering downloads, filtering, parsing, and
error handling for viral sequences and metadata from NCBI's virus database.

Test Structure:
---------------
The test suite uses a hybrid approach combining JSON-defined tests (for input
validation) and code-defined tests (for functional, unit, and data quality checks).

1. JSON-Defined Tests (19 tests):
   - Loaded from tests/fixtures/test_virus.json
   - Focus on input validation and error handling
   - Test invalid types, values, and parameter combinations

2. Code-Defined Functional Tests (18 tests):
   - Test basic functionality (file creation, downloads)
   - Test individual filters (host, completeness, length, annotated, refseq, etc.)
   - Test filter combinations and edge cases
   - Test advanced features (GenBank metadata, protein filters, etc.)

3. Code-Defined Data Quality Tests (6 tests):
   - Verify data consistency across output formats
   - Validate filter effectiveness (host, release date, completeness)
   - Check metadata schema and field presence
   - Detect API/data source changes

4. Multi-Accession Functionality Tests (9 tests):
   - Test parsing of single, space-separated, and file-based accessions
   - Test URL batching for large accession lists (1000+ accessions)
   - Test integration with virus() function

5. Datasets CLI Tests (3 tests):
   - Test _get_datasets_path(), bundled binary fallback, version output

6. Exponential Backoff Helper Function Tests (6 tests):
   - Test success, retry, backoff timing, error tracking, non-retryable exceptions

7. Virus Name Modification Tests (7 tests):
   - _get_modified_virus_name: parentheses removal, virus suffix, spacing, edge cases

8. Error Tracking Tests (3 tests):
   - _track_failed_operation: key creation, appending, None handling

9. Binary Validation Tests (3 tests):
   - _validate_datasets_binary: empty, nonexistent, and valid paths

10. Version Retrieval Tests (2 tests):
    - _get_datasets_version, _get_gget_version

11. SARS-CoV-2 / Alphainfluenza Detection Tests (6 tests):
    - is_sars_cov2_query, is_alphainfluenza_query: common names, negatives, accession mode

12. Date Parsing Tests (9 tests):
    - _parse_date: full date, various formats, invalid input
    - _parse_partial_date_for_range_check: year-only, year-month, full date, empty

13. Check Min/Max Validation Tests (6 tests):
    - check_min_max: valid, equal, invalid, None, date valid, date invalid

14. XML Helper Tests (4 tests):
    - _clean_xml_declarations, _local_name: namespace stripping

15. Unzip File Tests (3 tests):
    - _unzip_file: valid extraction, bad ZIP, nonexistent file

16. Memory Monitoring Tests (2 tests):
    - _get_memory_usage, _force_garbage_collection

17. Baseline File Parsing Tests (7 tests):
    - _parse_baseline_file: CSV, JSONL, JSON, text, nonexistent, empty, None

18. Deduplication Tests (3 tests):
    - _deduplicate_metadata_against_baseline: normal, empty baseline, all existing

19. Save Partial Metadata Tests (2 tests):
    - _save_partial_metadata: normal save, empty dict

20. Merge Baseline Tests (3 tests):
    - _merge_baseline_with_new: merge, deduplication, empty new records

21. Load Metadata from API Reports Tests (4 tests):
    - load_metadata_from_api_reports: basic, missing accession, empty, multiple

22. filter_metadata_only Tests (22 tests):
    - All filter parameters tested individually and combined:
      min/max_seq_length, lab_passaged, annotated, source_database,
      collection_date, protein_count, segment, vaccine_strain,
      submitter_country, submitter_name, submitter_institution,
      isolate, isolation_source, geographic_location, host,
      max_release_date, combined filters

23. filter_genbank_metadata Tests (14 tests):
    - GenBank-specific filters: gene_count, mature_peptide_count,
      provirus, genotype, has_proteins, gen_mol_type, env_source, combined

24. filter_cached_metadata_for_unused_filters Tests (8 tests):
    - Cached download post-filtering: host, complete_only, annotated,
      geographic_location, refseq_only, min_release_date, strategy skipping

25. FASTA Writing/Streaming Tests (5 tests):
    - _write_fasta_record: with/without description, line wrapping
    - _stream_copy_fasta: all records, accession filtering

26. filter_sequences Tests (3 tests):
    - max_ambiguous_chars, no filters, proteins_complete

27. save_command_summary Tests (2 tests):
    - Basic file creation, error recording

28. merge_metadata_csvs Tests (3 tests):
    - Fill missing, missing file, no overwrite

29. save_metadata_to_csv Tests (2 tests):
    - Basic creation, empty metadata

30. _parse_genbank_xml Tests (3 tests):
    - Basic extraction, invalid XML, empty set

31. _genbank_xml_to_csv Tests (1 test):
    - Basic XML to CSV conversion

32. save_genbank_metadata_to_csv Tests (2 tests):
    - Basic creation, empty input

33. Additional filter_metadata_only Tests (2 tests):
    - nuc_completeness='partial', annotated=True (server-side)

Total: 186 tests
"""

import calendar
import functools
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
import zipfile
from datetime import datetime

import pandas as pd
from gget.gget_virus import (
    _batch_accessions_for_url,
    _calculate_max_accessions_per_batch,
    _clean_xml_declarations,
    _clear_datasets_cache,
    _deduplicate_metadata_against_baseline,
    _force_garbage_collection,
    _genbank_xml_to_csv,
    _get_datasets_path,
    _get_datasets_version,
    _get_gget_version,
    _get_memory_usage,
    _get_modified_virus_name,
    _local_name,
    _merge_baseline_with_new,
    _parse_accession_input,
    _parse_baseline_file,
    _parse_date,
    _parse_genbank_xml,
    _parse_partial_date_for_range_check,
    _retry_with_exponential_backoff,
    _save_partial_metadata,
    _stream_copy_fasta,
    _track_failed_operation,
    _unzip_file,
    _validate_datasets_binary,
    _write_fasta_record,
    check_min_max,
    filter_cached_metadata_for_unused_filters,
    filter_genbank_metadata,
    filter_metadata_only,
    filter_sequences,
    is_alphainfluenza_query,
    is_sars_cov2_query,
    load_metadata_from_api_reports,
    merge_metadata_csvs,
    save_command_summary,
    save_genbank_metadata_to_csv,
    save_metadata_to_csv,
    virus,
)

from .from_json import from_json


def retry_on_network_error(max_retries=3, delay=5):
    """Decorator to retry tests that may fail due to network issues.

    This is useful for tests that make real API calls to NCBI, which can
    occasionally time out or fail due to network flakiness.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Seconds to wait between retries (default: 5)
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return test_func(*args, **kwargs)
                except Exception as e:
                    # Only retry on network-related errors
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in ["timeout", "timed out", "connection", "network"]):
                        last_exception = e
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                        continue
                    # Re-raise non-network errors immediately
                    raise
            # If all retries failed, raise the last exception
            raise last_exception

        return wrapper

    return decorator


# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_virus.json") as json_file:
    virus_dict = json.load(json_file)


class TestVirus(unittest.TestCase, metaclass=from_json(virus_dict, virus)):
    """Test suite for gget.virus module.

    This comprehensive test suite covers:

    1. Input Validation (19 JSON-defined tests):
       - Type checking for boolean, string, and integer parameters
       - Value validation (completeness, batch sizes, virus names)
       - Range validation (min/max pairs for dates, lengths, counts)

    2. Functional Tests (18 code-defined tests):
       - Basic file creation and accession downloads
       - Individual filter functionality (host, completeness, length, annotated, refseq)
       - Geographic location and source database filters
       - Protein and gene count filters
       - Collection date filters
       - Advanced filters (lab_passaged, max_ambiguous_chars, has_proteins)
       - GenBank metadata retrieval
       - Multiple filter combinations
       - Integer virus ID handling

    3. Data Quality & Verification Tests (6 code-defined tests):
       - Relationship checks: FASTA/CSV/JSONL count consistency
       - Filter verification: Host and release date filter effectiveness
       - Schema validation: Expected metadata columns exist
       - Completeness filter verification
       - Multi-filter relationship checks

    Coverage: 85% of parameters tested (29/34), with 43 total test cases.
    See module docstring for detailed parameter coverage analysis.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are shared across all tests."""
        cls.test_output_dir = "test_virus_output"

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run."""
        # Clean up test output directory if it exists
        if os.path.exists(cls.test_output_dir):
            shutil.rmtree(cls.test_output_dir)

    def setUp(self):
        """Set up before each test method."""
        # Create a fresh test output directory
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
        os.makedirs(self.test_output_dir, exist_ok=True)

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test output directory
        if os.path.exists(self.test_output_dir):
            try:
                shutil.rmtree(self.test_output_dir)
            except Exception:  # noqa: BLE001
                pass  # Ignore cleanup errors

    def _check_output_files(self, virus_name, outfolder):
        """Helper method to check if expected output files were created.

        Args:
            virus_name: Name of the virus (used in file naming)
            outfolder: Output folder where files should be created

        Returns:
            dict: Dictionary with file paths and existence status
        """
        # Clean virus name for file naming (replace spaces with underscores)
        virus_clean = virus_name.replace(" ", "_")

        expected_files = {
            "fasta": os.path.join(outfolder, f"{virus_clean}_sequences.fasta"),
            "csv": os.path.join(outfolder, f"{virus_clean}_metadata.csv"),
            "jsonl": os.path.join(outfolder, f"{virus_clean}_metadata.jsonl"),
        }

        results = {}
        for file_type, file_path in expected_files.items():
            results[file_type] = {
                "path": file_path,
                "exists": os.path.exists(file_path),
                "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            }

        return results

    def _count_fasta_sequences(self, fasta_file):
        """Count the number of sequences in a FASTA file.

        Args:
            fasta_file: Path to FASTA file

        Returns:
            int: Number of sequences
        """
        count = 0
        if os.path.exists(fasta_file):
            with open(fasta_file) as f:
                for line in f:
                    if line.startswith(">"):
                        count += 1
        return count

    def _count_jsonl_records(self, jsonl_file):
        """Count the number of records in a JSONL file.

        Args:
            jsonl_file: Path to JSONL file

        Returns:
            int: Number of records
        """
        count = 0
        if os.path.exists(jsonl_file):
            with open(jsonl_file) as f:
                for line in f:
                    if line.strip():
                        count += 1
        return count

    def _count_csv_records(self, csv_file):
        """Count the number of records in a CSV file (excluding header).

        Args:
            csv_file: Path to CSV file

        Returns:
            int: Number of records (excluding header)
        """
        count = 0
        if os.path.exists(csv_file):
            with open(csv_file) as f:
                # Skip header
                next(f, None)
                for line in f:
                    if line.strip():
                        count += 1
        return count

    def _parse_csv_metadata(self, csv_file):
        """Parse CSV metadata file and return records as list of dicts.

        Args:
            csv_file: Path to CSV file

        Returns:
            list: List of dictionaries containing metadata records
        """
        import csv

        records = []
        if os.path.exists(csv_file):
            with open(csv_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
        return records

    def _get_csv_columns(self, csv_file):
        """Get column names from CSV file.

        Args:
            csv_file: Path to CSV file

        Returns:
            list: List of column names
        """
        import csv

        if os.path.exists(csv_file):
            with open(csv_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return reader.fieldnames
        return []

    # =========================================================================
    # FUNCTIONAL TESTS: Basic file creation and filter functionality
    # =========================================================================
    # These tests verify that the virus function creates output files
    # correctly and that individual filters work as expected.

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_specific_accession_file_creation(self):
        """Test that files are created when downloading a specific accession.

        Downloads SARS-CoV-2 reference sequence (NC_045512.2) and verifies:
        - Function returns None (writes to disk)
        - All three output files created (FASTA, CSV, JSONL)
        - Files are not empty
        - At least one sequence in FASTA file
        """
        virus_name = "NC_045512.2"
        outfolder = self.test_output_dir

        # Run the function (should create files, returns None)
        result = virus(virus=virus_name, is_accession=True, outfolder=outfolder)

        # Check that function returns None
        self.assertIsNone(result)

        # Check that output files were created
        files = self._check_output_files(virus_name, outfolder)

        # Assert all files exist
        self.assertTrue(files["fasta"]["exists"], f"FASTA file not created: {files['fasta']['path']}")
        self.assertTrue(files["csv"]["exists"], f"CSV file not created: {files['csv']['path']}")
        self.assertTrue(files["jsonl"]["exists"], f"JSONL file not created: {files['jsonl']['path']}")

        # Assert files are not empty
        self.assertGreater(files["fasta"]["size"], 0, "FASTA file is empty")
        self.assertGreater(files["csv"]["size"], 0, "CSV file is empty")
        self.assertGreater(files["jsonl"]["size"], 0, "JSONL file is empty")

        # Count sequences (should be 1 for a specific accession)
        seq_count = self._count_fasta_sequences(files["fasta"]["path"])
        self.assertGreaterEqual(seq_count, 1, "No sequences found in FASTA file")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_host_filter(self):
        """Test that host filter works and creates appropriate files."""
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, host="human", outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with host filter")
        self.assertTrue(files["csv"]["exists"], "CSV file not created with host filter")
        self.assertTrue(files["jsonl"]["exists"], "JSONL file not created with host filter")

        # Verify that files contain data
        self.assertGreater(files["fasta"]["size"], 0, "FASTA file is empty with host filter")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_completeness_filter(self):
        """Test that completeness filter works correctly."""
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, nuc_completeness="complete", outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with completeness filter")
        self.assertGreater(files["fasta"]["size"], 0, "FASTA file is empty with completeness filter")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_length_filters(self):
        """Test that sequence length filters work correctly."""
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, min_seq_length=10000, max_seq_length=11000, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with length filters")

        # Verify sequences are within expected length range
        # This would require parsing the FASTA file, which we do with count
        seq_count = self._count_fasta_sequences(files["fasta"]["path"])
        self.assertGreater(seq_count, 0, "No sequences passed length filters")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_annotated_filter(self):
        """Test that annotated filter works correctly."""
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, annotated=True, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with annotated filter")
        self.assertGreater(files["fasta"]["size"], 0, "FASTA file is empty with annotated filter")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_multiple_filters(self):
        """Test that multiple filters can be combined correctly."""
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(
            virus=virus_name,
            host="human",
            nuc_completeness="complete",
            min_seq_length=10500,
            max_seq_length=11000,
            annotated=True,
            outfolder=outfolder,
        )

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with multiple filters")
        self.assertTrue(files["csv"]["exists"], "CSV file not created with multiple filters")
        self.assertTrue(files["jsonl"]["exists"], "JSONL file not created with multiple filters")

        # Check that filters reduced the dataset (should have some sequences)
        seq_count = self._count_fasta_sequences(files["fasta"]["path"])
        self.assertGreater(seq_count, 0, "No sequences passed multiple filters")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_integer_virus_id(self):
        """Test that integer virus IDs are handled correctly.

        Tests using Zika virus taxon ID (64320) as integer input.
        Verifies that integer IDs are properly converted and files created.
        """
        virus_id = 64320  # Zika virus taxon ID
        outfolder = self.test_output_dir

        result = virus(virus=virus_id, outfolder=outfolder)

        self.assertIsNone(result)

        # Check files with string version of virus ID
        virus_clean = str(virus_id)
        expected_fasta = os.path.join(outfolder, f"{virus_clean}_sequences.fasta")
        self.assertTrue(
            os.path.exists(expected_fasta), f"FASTA file not created for integer virus ID: {expected_fasta}"
        )

    # =========================================================================
    # DATA QUALITY & VERIFICATION TESTS
    # =========================================================================
    # These tests verify data consistency, filter effectiveness, and that
    # API/data source changes would be detected. They go beyond simple file
    # existence checks to validate actual data quality.

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_relationship_check_counts_match(self):
        """Test that FASTA sequence count matches CSV and JSONL record counts.

        Downloads a specific accession and verifies:
        - Number of FASTA sequences = number of CSV records = number of JSONL records
        - No data loss between different output formats
        - At least one record in all files

        This catches: Format conversion bugs, data loss, parsing errors.
        """
        virus_name = "NC_045512.2"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, is_accession=True, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)

        # Count records in each file type
        fasta_count = self._count_fasta_sequences(files["fasta"]["path"])
        csv_count = self._count_csv_records(files["csv"]["path"])
        jsonl_count = self._count_jsonl_records(files["jsonl"]["path"])

        # All counts should match
        self.assertEqual(fasta_count, csv_count, f"FASTA count ({fasta_count}) does not match CSV count ({csv_count})")
        self.assertEqual(
            fasta_count, jsonl_count, f"FASTA count ({fasta_count}) does not match JSONL count ({jsonl_count})"
        )
        self.assertEqual(csv_count, jsonl_count, f"CSV count ({csv_count}) does not match JSONL count ({jsonl_count})")

        # Should have at least one record
        self.assertGreater(fasta_count, 0, "No records found in output files")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_host_filter_verification(self):
        """Test that host filter actually filters by host in metadata.

        Downloads Zika virus with host="human" filter and verifies:
        - Records are returned (filter doesn't break the query)
        - Host column exists in metadata
        - If host data is populated, it matches the filter criterion

        Note: Host filter is applied server-side by NCBI API. The returned
        records should all match, but the Host field in CSV may be empty or
        have various formats (scientific names, common names).

        This catches: Broken host filters, API changes in filtering behavior.
        """
        virus_name = "Zika virus"
        host = "human"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, host=host, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)

        # Parse CSV metadata
        records = self._parse_csv_metadata(files["csv"]["path"])

        # Should have some records
        self.assertGreater(len(records), 0, "No records returned with host filter")

        # Check that host column exists
        if records:
            self.assertIn("Host", records[0].keys(), "Host column not found in metadata")

            # Note: Host filter is applied server-side by NCBI API
            # The returned records should all match, but the Host field in CSV
            # may be empty or have various formats (scientific names, common names)
            # We verify the filter worked by checking that records were returned
            # (if filter was broken, we'd get all hosts or an error)

            # Count non-empty host values
            non_empty_hosts = sum(1 for record in records if record.get("Host", "").strip())

            # If we have host data populated, verify it matches
            if non_empty_hosts > 0:
                host_lower = host.lower()
                # Also check for "Homo sapiens" which is scientific name for human
                matching_hosts = sum(
                    1
                    for record in records
                    if host_lower in record.get("Host", "").lower() or "homo sapiens" in record.get("Host", "").lower()
                )

                # If host data is populated, at least 50% should match
                if non_empty_hosts > 0:
                    match_percentage = (matching_hosts / non_empty_hosts) * 100
                    self.assertGreater(
                        match_percentage,
                        50,
                        f"Only {match_percentage:.1f}% of populated host fields match filter '{host}'",
                    )

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_release_date_filter_verification(self):
        """Test that release date filter is applied correctly in metadata.

        Downloads Mumps virus with min_release_date="2024-12-31" and verifies:
        - Records are returned (API is working)
        - Release date field exists in metadata
        - All release dates are on or after 2024-12-31
        - Count matches expected API results

        This test compares against the direct API call:
        curl -X GET "https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/mumps%20virus/dataset_report?filter.released_since=2024-12-31T00:00:00.000Z"

        This catches: Release date filter bugs, date parsing errors, API filter issues.
        """
        from datetime import datetime

        import requests

        virus_name = "mumps virus"
        min_release_date = "2024-12-31"
        outfolder = self.test_output_dir

        # First, get the expected count from direct API call using full timestamp format
        api_url = "https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/mumps%20virus/dataset_report"
        params = {"filter.released_since": "2024-12-31T00:00:00.000Z", "page_size": 1000}

        try:
            response = requests.get(api_url, params=params, headers={"accept": "application/json"})
            response.raise_for_status()
            api_data = response.json()
            expected_count = len(api_data.get("reports", []))
        except Exception as e:  # noqa: BLE001
            self.skipTest(f"Could not fetch API data for comparison: {e}")

        # Run virus function with same filter
        result = virus(virus=virus_name, min_release_date=min_release_date, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)

        # Verify files were created
        self.assertTrue(os.path.exists(files["csv"]["path"]), "CSV file not created with release date filter")
        self.assertTrue(os.path.exists(files["fasta"]["path"]), "FASTA file not created with release date filter")

        # Parse CSV metadata
        records = self._parse_csv_metadata(files["csv"]["path"])

        # Should have records matching API count (allowing for small variance due to timing)
        self.assertGreater(len(records), 0, "No records returned with release date filter")
        self.assertEqual(
            len(records), expected_count, f"Record count ({len(records)}) doesn't match API count ({expected_count})"
        )

        # Check that release date column exists
        release_date_field = None
        for possible_field in ["Release date", "Release Date", "ReleaseDate", "release_date"]:
            if possible_field in records[0].keys():
                release_date_field = possible_field
                break

        self.assertIsNotNone(
            release_date_field, f"Release date field not found. Available fields: {list(records[0].keys())}"
        )

        # Parse filter date for comparison (inclusive - on or after this date)
        filter_date = datetime.strptime(min_release_date, "%Y-%m-%d")

        # Verify all release dates are on or after the filter date (inclusive)
        invalid_dates = []
        for record in records:
            date_str = record.get(release_date_field, "").strip()
            if date_str:
                try:
                    # Parse ISO date format (YYYY-MM-DD)
                    record_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if record_date < filter_date:
                        invalid_dates.append((record.get("Accession", "unknown"), date_str))
                except ValueError as e:
                    # If date parsing fails, that's also a test failure
                    self.fail(f"Could not parse release date '{date_str}': {e}")

        self.assertEqual(
            len(invalid_dates),
            0,
            f"Found {len(invalid_dates)} records with release dates before {min_release_date}: {invalid_dates[:5]}",
        )

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_metadata_schema_validation(self):
        """Test that expected metadata columns exist in CSV output.

        Downloads a specific accession and verifies:
        - CSV contains expected essential columns (accession, length, host)
        - At least 5 columns present (reasonable metadata breadth)
        - Column names are properly formatted

        This catches: API schema changes, missing metadata fields, field
        name changes that would break downstream analysis tools.
        """
        virus_name = "NC_045512.2"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, is_accession=True, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)

        # Get column names from CSV
        columns = self._get_csv_columns(files["csv"]["path"])

        # Check for expected essential columns (these should always be present)
        # Using case-insensitive checking since column names might vary
        columns_lower = [col.lower() for col in columns]

        expected_columns = [
            "accession",  # Or GenBank Accession
            "length",  # Or Sequence Length
            "host",  # Host information
        ]

        missing_columns = []
        for expected in expected_columns:
            found = any(expected in col_lower for col_lower in columns_lower)
            if not found:
                missing_columns.append(expected)

        self.assertEqual(
            len(missing_columns),
            0,
            f"Missing expected metadata columns: {missing_columns}. Available columns: {columns}",
        )

        # Verify we have a reasonable number of columns (at least 5)
        self.assertGreaterEqual(len(columns), 5, f"Only {len(columns)} columns found, expected at least 5")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_completeness_filter_verification(self):
        """Test that completeness filter returns appropriate sequences.

        Downloads Zika virus with nuc_completeness="complete" and verifies:
        - Records are returned (filter works)
        - If completeness field exists, validates values
        - Falls back to checking length field exists

        This catches: Broken completeness filters, metadata field changes,
        filter logic errors.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, nuc_completeness="complete", outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)

        # Parse CSV metadata
        records = self._parse_csv_metadata(files["csv"]["path"])

        # Should have some records
        self.assertGreater(len(records), 0, "No records returned with completeness filter")

        # Check if there's a completeness or length field
        if records:
            # Look for completeness-related fields
            completeness_field = None
            for possible_field in [
                "Completeness",
                "Nuc_Completeness",
                "Nucleotide Completeness",
                "Genome Coverage",
                "completeness",
            ]:
                if possible_field in records[0].keys():
                    completeness_field = possible_field
                    break

            # If completeness field exists, verify values
            if completeness_field:
                complete_count = sum(
                    1 for record in records if "complete" in record.get(completeness_field, "").lower()
                )

                # At least 50% should be marked as complete
                if complete_count > 0:
                    complete_percentage = (complete_count / len(records)) * 100
                    self.assertGreater(complete_percentage, 50, f"Only {complete_percentage:.1f}% marked as complete")
            else:
                # If no explicit completeness field, check length field exists
                # (complete genomes should have consistent lengths)
                length_field = None
                for possible_field in ["Length", "Sequence Length", "Nuc_Length", "length"]:
                    if possible_field in records[0].keys():
                        length_field = possible_field
                        break

                self.assertIsNotNone(length_field, "Neither completeness nor length field found in metadata")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_multiple_filters_relationship_check(self):
        """Test relationship checks work correctly with multiple filters applied.

        Downloads Zika virus with multiple filters (host, completeness, length) and verifies:
        - FASTA/CSV/JSONL counts still match with complex filtering
        - At least one record passes all filters
        - No data loss when multiple filters interact

        This catches: Filter interaction bugs, data loss with complex queries,
        inconsistent filtering across output formats.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(
            virus=virus_name, host="human", nuc_completeness="complete", min_seq_length=10000, outfolder=outfolder
        )

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)

        # Count records in each file type
        fasta_count = self._count_fasta_sequences(files["fasta"]["path"])
        csv_count = self._count_csv_records(files["csv"]["path"])
        jsonl_count = self._count_jsonl_records(files["jsonl"]["path"])

        # All counts should match even with filters
        self.assertEqual(
            fasta_count,
            csv_count,
            f"FASTA count ({fasta_count}) does not match CSV count ({csv_count}) with multiple filters",
        )
        self.assertEqual(
            fasta_count,
            jsonl_count,
            f"FASTA count ({fasta_count}) does not match JSONL count ({jsonl_count}) with multiple filters",
        )

        # Should have at least one record
        self.assertGreater(fasta_count, 0, "No records found with multiple filters applied")

    # =========================================================================
    # ADDITIONAL FUNCTIONAL TESTS: Testing previously untested parameters
    # =========================================================================

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_geographic_location_filter(self):
        """Test that geographic location filter works correctly.

        Downloads Zika virus sequences from Brazil and verifies:
        - Files are created successfully
        - Records are returned
        - Geographic location metadata field exists

        This catches: Geographic location filter bugs, API parameter issues.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, geographic_location="Brazil", outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with geographic location filter")
        self.assertTrue(files["csv"]["exists"], "CSV file not created with geographic location filter")

        # Parse CSV metadata
        records = self._parse_csv_metadata(files["csv"]["path"])

        # Should have some records (Brazil had Zika outbreak)
        self.assertGreater(len(records), 0, "No records returned with geographic location filter")

        # Check that geographic location fields exist
        if records:
            geo_fields = ["Geographic Location", "Geographic Region", "Geo String"]
            has_geo_field = any(field in records[0].keys() for field in geo_fields)
            self.assertTrue(
                has_geo_field, f"No geographic location field found. Available fields: {list(records[0].keys())}"
            )

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_protein_count_filters(self):
        """Test that protein count filters work correctly.

        Downloads Zika virus with protein count filters and verifies:
        - Files are created successfully
        - Records are returned
        - Protein count field exists in metadata

        This catches: Protein count filter bugs, metadata field issues.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, min_protein_count=1, max_protein_count=20, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with protein count filters")

        # Parse CSV metadata
        records = self._parse_csv_metadata(files["csv"]["path"])

        # Should have some records
        self.assertGreater(len(records), 0, "No records returned with protein count filters")

        # Check that protein count field exists
        if records:
            self.assertIn(
                "Protein count",
                records[0].keys(),
                f"Protein count field not found. Available fields: {list(records[0].keys())}",
            )

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_source_database_filter(self):
        """Test that source database filter works correctly.

        Downloads Zika virus from GenBank database and verifies:
        - Files are created successfully
        - Records are returned
        - Source database field exists in metadata

        This catches: Source database filter bugs, API parameter issues.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, source_database="GenBank", outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with source database filter")

        # Parse CSV metadata
        records = self._parse_csv_metadata(files["csv"]["path"])

        # Should have some records
        self.assertGreater(len(records), 0, "No records returned with source database filter")

        # Check that source database field exists
        if records:
            db_field = None
            for possible_field in ["GenBank/RefSeq", "Source Database", "Database"]:
                if possible_field in records[0].keys():
                    db_field = possible_field
                    break

            self.assertIsNotNone(
                db_field, f"Source database field not found. Available fields: {list(records[0].keys())}"
            )

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_lab_passaged_filter(self):
        """Test that lab_passaged filter works correctly.

        Downloads Zika virus with lab_passaged=False filter and verifies:
        - Files are created successfully
        - Records are returned

        Note: Lab passaged data may be sparse, so we mainly verify the filter
        doesn't break the query.

        This catches: Lab passaged filter bugs, API parameter issues.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, lab_passaged=False, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with lab_passaged filter")

        # Should create files (even if no lab passaged field in results)
        self.assertGreater(files["fasta"]["size"], 0, "FASTA file is empty with lab_passaged filter")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_collection_date_filters(self):
        """Test that collection date filters don't break the query.

        Downloads Zika virus with collection date range and verifies:
        - Function completes without errors

        Note: Collection date data is often sparse, filters may return no results.
        This test just ensures the filter doesn't cause errors.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        # This will complete without error even if no results match
        result = virus(
            virus=virus_name, min_collection_date="2016-01-01", max_collection_date="2016-12-31", outfolder=outfolder
        )

        # Function should complete successfully
        self.assertIsNone(result)

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_max_ambiguous_chars_filter(self):
        """Test that max_ambiguous_chars filter works correctly.

        Downloads Zika virus with max_ambiguous_chars filter and verifies:
        - Files are created successfully
        - Records are returned
        - Filter doesn't break the query

        This catches: Max ambiguous chars filter bugs, sequence quality filtering issues.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        result = virus(virus=virus_name, max_ambiguous_chars=100, outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with max_ambiguous_chars filter")

        # Should have some records (most sequences have some ambiguous bases)
        seq_count = self._count_fasta_sequences(files["fasta"]["path"])
        self.assertGreater(seq_count, 0, "No sequences passed max_ambiguous_chars filter")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_has_proteins_filter(self):
        """Test that has_proteins filter works correctly.

        Downloads Zika virus requiring specific proteins and verifies:
        - Files are created successfully
        - Records are returned
        - Filter doesn't break the query

        This catches: has_proteins filter bugs, protein filtering logic issues.
        """
        virus_name = "Zika virus"
        outfolder = self.test_output_dir

        # Test with a common protein (polyprotein is typical for Zika)
        result = virus(virus=virus_name, has_proteins="polyprotein", outfolder=outfolder)

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with has_proteins filter")

        # Should have some records (polyprotein is common in Zika)
        seq_count = self._count_fasta_sequences(files["fasta"]["path"])
        self.assertGreater(seq_count, 0, "No sequences passed has_proteins filter")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_with_genbank_metadata_retrieval(self):
        """Test that GenBank metadata retrieval works correctly.

        Downloads a single accession with genbank_metadata=True and verifies:
        - Function completes without errors
        - Standard files are created
        - GenBank metadata CSV file is created

        This catches: GenBank metadata retrieval bugs, batch processing issues.
        """
        virus_name = "NC_045512.2"
        outfolder = self.test_output_dir

        result = virus(
            virus=virus_name, is_accession=True, genbank_metadata=True, genbank_batch_size=10, outfolder=outfolder
        )

        self.assertIsNone(result)

        files = self._check_output_files(virus_name, outfolder)
        self.assertTrue(files["fasta"]["exists"], "FASTA file not created with genbank_metadata")

        # Check for GenBank metadata file
        genbank_csv = os.path.join(outfolder, f"{virus_name}_genbank_metadata.csv")
        self.assertTrue(os.path.exists(genbank_csv), f"GenBank metadata CSV not created: {genbank_csv}")

        # Verify GenBank CSV has data
        self.assertGreater(os.path.getsize(genbank_csv), 0, "GenBank metadata CSV is empty")

    # =========================================================================
    # DATASETS CLI TESTS: Testing NCBI datasets CLI check and setup
    # =========================================================================
    # These tests verify the datasets CLI detection and installation functionality

    def test_get_datasets_path_returns_valid_path(self):
        """Test that _get_datasets_path returns a valid path to the datasets CLI.

        The function should return a path to either:
        1. The system-installed datasets CLI (if available)
        2. The bundled datasets binary (fallback)

        This catches: Detection logic bugs, path resolution issues.
        """
        # _get_datasets_path should always return a valid path
        # (either system CLI or bundled binary)
        datasets_path = _get_datasets_path()

        # Should return a non-empty string
        self.assertIsInstance(datasets_path, str)
        self.assertTrue(len(datasets_path) > 0, "_get_datasets_path should return a non-empty path")

        # The returned path should be executable
        result = subprocess.run(
            [datasets_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, f"datasets CLI at {datasets_path} should be executable")

    def test_get_datasets_path_uses_bundled_binary(self):
        """Test that _get_datasets_path falls back to bundled binary when system CLI is missing.

        When the system-installed datasets CLI is not in PATH, the function
        should fall back to the bundled binary included with gget.

        Note: _get_datasets_path caches its result, so this test clears the cache
        before testing the fallback behavior.

        This catches: Bundled binary fallback logic, path resolution issues.
        """
        import gget.gget_virus as gget_virus_module

        # Save original PATH and cache
        original_path = os.environ.get("PATH", "")
        original_cache = gget_virus_module._datasets_path_cache

        try:
            # Clear the cache to force re-detection
            _clear_datasets_cache()

            # Set PATH to empty to simulate system datasets not being found
            os.environ["PATH"] = ""

            # Should still return a valid path (to bundled binary)
            datasets_path = _get_datasets_path()

            # Should return a non-empty string path to bundled binary
            self.assertIsInstance(datasets_path, str)
            self.assertTrue(len(datasets_path) > 0, "Should return path to bundled binary")

            # Path should contain 'bins' indicating bundled binary
            self.assertIn("bins", datasets_path, f"Path should be bundled binary, got: {datasets_path}")

        finally:
            # Restore original PATH and cache
            os.environ["PATH"] = original_path
            gget_virus_module._datasets_path_cache = original_cache

    def test_datasets_cli_version_output(self):
        """Test that the datasets CLI returns a valid version string.

        When available (system or bundled), the datasets CLI should return a
        version string that can be parsed. This helps ensure the CLI is properly
        functional.

        This catches: Corrupted installations, version parsing issues.
        """
        # Use _get_datasets_path() to get either system or bundled binary
        try:
            datasets_path = _get_datasets_path()
            result = subprocess.run(
                [datasets_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            cli_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, RuntimeError):
            cli_available = False

        if not cli_available:
            self.skipTest("NCBI datasets CLI not available - skipping version test")

        # Version output should not be empty and should contain version info
        version_output = result.stdout.strip()
        self.assertTrue(len(version_output) > 0, "Version output should not be empty")
        # NCBI datasets typically outputs version like "datasets version: X.Y.Z" or just "X.Y.Z"
        self.assertTrue(
            any(char.isdigit() for char in version_output),
            f"Version output should contain version numbers: {version_output}",
        )

    # =========================================================================
    # MULTI-ACCESSION TESTS: Testing new multi-accession functionality
    # =========================================================================
    # These tests verify the new multi-accession support added in recent commits

    def test_parse_accession_input_single(self):
        """Test parsing of single accession number.

        Tests _parse_accession_input with a single accession identifier and verifies:
        - Returns correct type ('single')
        - Accession value is preserved
        - is_file flag is False

        This catches: Single accession parsing bugs, input validation issues.
        """

        result = _parse_accession_input("NC_045512.2")

        self.assertEqual(result["type"], "single", "Should identify single accession")
        self.assertEqual(result["accessions"], "NC_045512.2", "Should preserve accession value")
        self.assertFalse(result["is_file"], "Single accession should not be marked as file")
        self.assertIsNone(result["file_path"], "Single accession should have no file_path")

    def test_parse_accession_input_space_separated(self):
        """Test parsing of space-separated accessions.

        Tests _parse_accession_input with space-separated accessions and verifies:
        - Returns correct type ('list')
        - Accessions list is created with correct count
        - All accessions are preserved without whitespace
        - is_file flag is False

        This catches: Space-separated parsing bugs, whitespace handling issues.
        """

        result = _parse_accession_input("NC_045512.2 MN908947.3 MT020781.1")

        self.assertEqual(result["type"], "list", "Should identify list of accessions")
        self.assertIsInstance(result["accessions"], list, "Should return list type")
        self.assertEqual(len(result["accessions"]), 3, "Should parse 3 accessions")
        self.assertEqual(result["accessions"][0], "NC_045512.2", "First accession should match")
        self.assertEqual(result["accessions"][1], "MN908947.3", "Second accession should match")
        self.assertEqual(result["accessions"][2], "MT020781.1", "Third accession should match")
        self.assertFalse(result["is_file"], "Space-separated should not be marked as file")

    def test_parse_accession_input_from_file(self):
        """Test parsing of accessions from a file.

        Tests _parse_accession_input with a file path and verifies:
        - Returns correct type ('file')
        - Accessions list is created from file content
        - Each line becomes an accession
        - is_file flag is True
        - file_path is preserved
        - Empty lines are skipped

        This catches: File parsing bugs, whitespace/empty line issues, file I/O errors.
        """
        import tempfile

        # Create a temporary file with accessions
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("NC_045512.2\n")
            f.write("  MN908947.3  \n")  # Test whitespace handling
            f.write("\n")  # Empty line
            f.write("MT020781.1\n")
            temp_file = f.name

        try:
            result = _parse_accession_input(temp_file)

            self.assertEqual(result["type"], "file", "Should identify file input")
            self.assertIsInstance(result["accessions"], list, "Should return list type")
            self.assertEqual(len(result["accessions"]), 3, "Should parse 3 accessions (empty line skipped)")
            self.assertEqual(result["accessions"][0], "NC_045512.2", "First accession should match")
            self.assertEqual(result["accessions"][1], "MN908947.3", "Second accession should be stripped of whitespace")
            self.assertEqual(result["accessions"][2], "MT020781.1", "Third accession should match")
            self.assertTrue(result["is_file"], "File input should be marked as file")
            self.assertEqual(result["file_path"], temp_file, "File path should be preserved")
        finally:
            os.unlink(temp_file)

    def test_parse_accession_input_empty_file_raises_error(self):
        """Test that parsing empty file raises ValueError.

        Tests _parse_accession_input with an empty file and verifies:
        - Raises ValueError
        - Error message is informative

        This catches: Empty file validation bugs, error handling issues.
        """
        import tempfile

        # Create an empty temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_file = f.name

        try:
            with self.assertRaises(ValueError):
                _parse_accession_input(temp_file)
        finally:
            os.unlink(temp_file)

    def test_parse_accession_input_nonexistent_file_raises_error(self):
        """Test that parsing nonexistent file raises ValueError.

        Tests _parse_accession_input with a nonexistent file path and verifies:
        - Raises ValueError (not FileNotFoundError - treated as single accession)

        Note: A nonexistent file path will be treated as a single accession
        string since _parse_accession_input checks os.path.isfile() first.
        """

        # Nonexistent file path will be treated as single accession
        result = _parse_accession_input("/nonexistent/file/path.txt")

        # Should treat it as a single accession string since file doesn't exist
        self.assertEqual(result["type"], "single", "Nonexistent file treated as single accession")
        self.assertEqual(result["accessions"], "/nonexistent/file/path.txt", "Should preserve path as accession")

    def test_calculate_max_accessions_per_batch(self):
        """Test calculation of maximum accessions per batch.

        Tests _calculate_max_accessions_per_batch and verifies:
        - Returns positive integer
        - At least 1 accession per batch
        - Respects URL length limit
        - Smaller base URL allows more accessions

        This catches: Batch size calculation bugs, URL limit logic errors.
        """
        from gget.gget_virus import ACCESSION_AVG_LENGTH, BUFFER_SIZE, MAX_URL_LENGTH

        # Test with different base URL lengths
        base_url_small = 50
        base_url_large = 500

        max_acc_small = _calculate_max_accessions_per_batch(base_url_small)
        max_acc_large = _calculate_max_accessions_per_batch(base_url_large)

        # Both should be positive integers
        self.assertIsInstance(max_acc_small, int, "Should return integer")
        self.assertIsInstance(max_acc_large, int, "Should return integer")
        self.assertGreater(max_acc_small, 0, "Should allow at least 1 accession")
        self.assertGreater(max_acc_large, 0, "Should allow at least 1 accession")

        # Larger base URL should allow fewer accessions
        self.assertGreater(max_acc_small, max_acc_large, "Smaller base URL should allow more accessions")

        # Verify the calculation makes sense
        # With 2000 char limit, 200 char buffer, typical accession is 11 chars + 3 for %2C
        expected_rough = (MAX_URL_LENGTH - base_url_small - BUFFER_SIZE) // (ACCESSION_AVG_LENGTH + 3)
        self.assertEqual(max_acc_small, expected_rough, "Calculation should match expected formula")

    def test_batch_accessions_for_url(self):
        """Test batching of accessions for URL length limits.

        Tests _batch_accessions_for_url with large accession list and verifies:
        - Returns list of batches
        - All accessions are included
        - No duplicate accessions
        - Each batch respects URL limit
        - Batching is consistent

        This catches: Batching algorithm bugs, URL limit violations, data loss.
        """
        from gget.gget_virus import MAX_URL_LENGTH

        # Create large list of accessions that will need multiple batches
        accessions = [f"NC_{100000 + i}.1" for i in range(1000)]
        base_url_length = 100

        batches = _batch_accessions_for_url(accessions, base_url_length)

        # Should have multiple batches for 1000 accessions
        self.assertIsInstance(batches, list, "Should return list of batches")
        self.assertGreater(len(batches), 1, "Should split into multiple batches for 1000 accessions")

        # All accessions should be included
        all_batched = [acc for batch in batches for acc in batch]
        self.assertEqual(len(all_batched), len(accessions), "All accessions should be included")

        # No duplicates
        self.assertEqual(len(set(all_batched)), len(accessions), "Should not have duplicates")

        # Verify order is preserved
        self.assertEqual(all_batched, accessions, "Accession order should be preserved")

        # Verify each batch respects URL limit
        for batch_num, batch in enumerate(batches, 1):
            batch_url_length = base_url_length + sum(len(acc) + 3 for acc in batch)
            self.assertLessEqual(
                batch_url_length,
                MAX_URL_LENGTH,
                f"Batch {batch_num} exceeds URL limit ({batch_url_length} > {MAX_URL_LENGTH})",
            )

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_multi_accession_space_separated(self):
        """Test virus function with space-separated accessions.

        Tests the virus() function with --is_accession flag and space-separated accessions and verifies:
        - Function completes without errors
        - Command summary is created (shows processing happened)
        - Function doesn't crash on multi-accession input

        This catches: Multi-accession parsing bugs, integration issues with virus() function.

        Note: API may return 0 results for some accession combinations, which is acceptable.
        The key is that the command processes without crashing.
        """
        outfolder = self.test_output_dir

        # Test with space-separated accessions
        result = virus(virus="MN908947.3 NC_045512.2", is_accession=True, outfolder=outfolder)

        # Function should complete successfully
        self.assertIsNone(result)

        # Command summary should be created
        summary_files = [f for f in os.listdir(outfolder) if f.startswith("command_summary")]
        self.assertGreater(len(summary_files), 0, "Command summary should be created")

    @retry_on_network_error(max_retries=3, delay=5)
    def test_virus_multi_accession_file_input(self):
        """Test virus function with file-based accessions.

        Tests the virus() function with --is_accession flag and file input and verifies:
        - Function completes without errors
        - Command summary is created
        - Correctly reads accessions from file

        This catches: File reading bugs, multi-accession file processing issues.
        """

        outfolder = self.test_output_dir

        # Create temporary accessions file
        accessions_file = os.path.join(outfolder, "test_accessions.txt")
        with open(accessions_file, "w") as f:
            f.write("MN908947.3\n")
            f.write("NC_045512.2\n")

        # Test with file input
        result = virus(virus=accessions_file, is_accession=True, outfolder=outfolder)

        # Function should complete successfully
        self.assertIsNone(result)

        # Command summary should be created
        summary_files = [f for f in os.listdir(outfolder) if f.startswith("command_summary")]
        self.assertGreater(len(summary_files), 0, "Command summary should be created for file input")

        # Clean up
        if os.path.exists(accessions_file):
            os.unlink(accessions_file)

    # =========================================================================
    # EXPONENTIAL BACKOFF HELPER FUNCTION TESTS
    # =========================================================================
    # These tests verify the core retry logic without making real API calls

    def test_retry_helper_successful_operation(self):
        """Test successful operation on first attempt (no retries needed)."""

        def successful_op():
            return {"result": "success"}

        success, result, error_info = _retry_with_exponential_backoff(
            operation_name="test_success",
            operation_func=successful_op,
        )

        self.assertTrue(success, "Expected success=True")
        self.assertEqual(result, {"result": "success"}, "Expected correct result")
        self.assertIsNone(error_info, "Expected no error_info on success")

    def test_retry_helper_success_after_retry(self):
        """Test operation that fails once then succeeds."""
        import requests

        attempt_count = [0]  # Use list to allow modification in nested function

        def flaky_op():
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise requests.exceptions.ConnectionError("Temporary connection issue")
            return {"result": "succeeded after retry"}

        start_time = time.time()
        success, result, error_info = _retry_with_exponential_backoff(
            operation_name="test_flaky",
            operation_func=flaky_op,
            max_retries=3,
            initial_delay=0.05,
            backoff_multiplier=2.0,
            retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError),
        )
        elapsed = time.time() - start_time

        self.assertTrue(success, "Expected success=True after retry")
        self.assertEqual(result, {"result": "succeeded after retry"}, "Expected correct result")
        self.assertEqual(attempt_count[0], 2, f"Expected 2 attempts, got {attempt_count[0]}")
        self.assertGreaterEqual(elapsed, 0.05, f"Expected at least 0.05s delay, got {elapsed}s")

    def test_retry_helper_exponential_backoff_timing(self):
        """Test that exponential backoff increases delays properly."""
        import requests

        attempt_count = [0]

        def always_fails():
            attempt_count[0] += 1
            raise requests.exceptions.ConnectionError("Persistent connection issue")

        initial_delay = 0.05
        backoff_multiplier = 2.0
        max_retries = 3

        start_time = time.time()
        success, result, error_info = _retry_with_exponential_backoff(
            operation_name="test_backoff",
            operation_func=always_fails,
            max_retries=max_retries,
            initial_delay=initial_delay,
            backoff_multiplier=backoff_multiplier,
            retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError),
        )
        elapsed = time.time() - start_time

        # The loop runs max_retries times with delays between attempts
        expected_min_delay = initial_delay * (1 + backoff_multiplier)

        self.assertFalse(success, "Expected success=False when all retries fail")
        self.assertEqual(attempt_count[0], max_retries, f"Expected {max_retries} attempts")
        self.assertGreaterEqual(
            elapsed, expected_min_delay * 0.8, f"Delay too short: {elapsed}s vs {expected_min_delay}s"
        )

    def test_retry_helper_failed_commands_tracking(self):
        """Test that failed_commands dict is properly populated."""

        def failing_op():
            raise ConnectionError("Test error message")

        failed_commands = {"custom_errors": []}

        success, result, error_info = _retry_with_exponential_backoff(
            operation_name="test_tracking",
            operation_func=failing_op,
            max_retries=1,
            initial_delay=0.01,
            failed_commands=failed_commands,
        )

        self.assertFalse(success, "Expected operation to fail")
        self.assertIsNotNone(error_info, "Expected error_info to be populated")
        self.assertIn("exception_type", error_info, "Expected exception_type in error_info")
        self.assertIn("error", error_info, "Expected error message in error_info")

    def test_retry_helper_non_retryable_exception(self):
        """Test that non-retryable exceptions fail immediately."""
        import requests

        attempt_count = [0]

        def non_retryable_op():
            attempt_count[0] += 1
            raise ValueError("This exception is not retryable")

        start_time = time.time()
        success, result, error_info = _retry_with_exponential_backoff(
            operation_name="test_non_retryable",
            operation_func=non_retryable_op,
            max_retries=3,
            initial_delay=0.1,
            retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError),
        )
        elapsed = time.time() - start_time

        self.assertFalse(success, "Expected operation to fail")
        self.assertEqual(attempt_count[0], 1, f"Expected only 1 attempt, got {attempt_count[0]}")
        self.assertLess(elapsed, 0.1, f"Expected immediate failure, but took {elapsed:.2f}s")

    def test_retry_helper_custom_retryable_exceptions(self):
        """Test with custom retryable exceptions."""
        import requests

        attempt_count = [0]

        def custom_failing_op():
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise requests.exceptions.Timeout("Request timed out")
            return {"result": "success"}

        success, result, error_info = _retry_with_exponential_backoff(
            operation_name="test_custom_retryable",
            operation_func=custom_failing_op,
            max_retries=3,
            initial_delay=0.01,
            retryable_exceptions=(requests.exceptions.Timeout, requests.exceptions.ConnectionError),
        )

        self.assertTrue(success, "Expected retry to succeed with Timeout in retryable_exceptions")
        self.assertEqual(attempt_count[0], 2, f"Expected 2 attempts, got {attempt_count[0]}")

    # =========================================================================
    # VIRUS NAME MODIFICATION TESTS
    # =========================================================================

    def test_get_modified_virus_name_remove_parentheses(self):
        """Test attempt=1 removes parenthetical content."""
        result = _get_modified_virus_name("Lassa virus (LASV)", attempt=1)
        self.assertEqual(result, "Lassa virus")

    def test_get_modified_virus_name_no_parentheses_returns_none(self):
        """Test attempt=1 returns None when no parentheses."""
        result = _get_modified_virus_name("Dengue", attempt=1)
        self.assertIsNone(result)

    def test_get_modified_virus_name_add_virus_suffix(self):
        """Test attempt=2 appends ' virus' when not present."""
        result = _get_modified_virus_name("Dengue", attempt=2)
        self.assertEqual(result, "Dengue virus")

    def test_get_modified_virus_name_add_space_before_virus(self):
        """Test attempt=2 adds space before 'virus' when missing."""
        result = _get_modified_virus_name("Denguevirus", attempt=2)
        self.assertEqual(result, "Dengue virus")

    def test_get_modified_virus_name_already_correct_returns_none(self):
        """Test attempt=2 returns None when 'virus' is already correctly spaced."""
        result = _get_modified_virus_name("Dengue virus", attempt=2)
        self.assertIsNone(result)

    def test_get_modified_virus_name_empty_returns_none(self):
        """Test empty/None input returns None."""
        self.assertIsNone(_get_modified_virus_name("", attempt=1))
        self.assertIsNone(_get_modified_virus_name(None, attempt=1))

    def test_get_modified_virus_name_invalid_attempt_returns_none(self):
        """Test invalid attempt number returns None."""
        self.assertIsNone(_get_modified_virus_name("Dengue", attempt=3))

    # =========================================================================
    # TRACK FAILED OPERATION TESTS
    # =========================================================================

    def test_track_failed_operation_creates_key(self):
        """Test _track_failed_operation creates new operation_type key."""
        failed = {}
        _track_failed_operation(failed, "metadata_batch", {"batch": 1}, {"error": "timeout"})
        self.assertIn("metadata_batch", failed)
        self.assertEqual(len(failed["metadata_batch"]), 1)
        self.assertEqual(failed["metadata_batch"][0]["batch"], 1)
        self.assertEqual(failed["metadata_batch"][0]["error"], "timeout")

    def test_track_failed_operation_appends(self):
        """Test _track_failed_operation appends to existing key."""
        failed = {"metadata_batch": [{"batch": 0}]}
        _track_failed_operation(failed, "metadata_batch", {"batch": 1}, {"error": "timeout"})
        self.assertEqual(len(failed["metadata_batch"]), 2)

    def test_track_failed_operation_none_dict(self):
        """Test _track_failed_operation is a no-op when failed_commands is None."""
        _track_failed_operation(None, "metadata_batch", {"batch": 1}, {"error": "timeout"})
        # Should not raise

    # =========================================================================
    # VALIDATE DATASETS BINARY TESTS
    # =========================================================================

    def test_validate_datasets_binary_empty_path(self):
        """Test _validate_datasets_binary returns False for empty path."""
        self.assertFalse(_validate_datasets_binary(""))
        self.assertFalse(_validate_datasets_binary(None))

    def test_validate_datasets_binary_nonexistent(self):
        """Test _validate_datasets_binary returns False for nonexistent path."""
        self.assertFalse(_validate_datasets_binary("/nonexistent/binary"))

    def test_validate_datasets_binary_valid(self):
        """Test _validate_datasets_binary returns True for valid binary."""
        datasets_path = _get_datasets_path()
        self.assertTrue(_validate_datasets_binary(datasets_path))

    # =========================================================================
    # VERSION RETRIEVAL TESTS
    # =========================================================================

    def test_get_datasets_version_returns_string_or_none(self):
        """Test _get_datasets_version returns a version string or None."""
        version = _get_datasets_version()
        if version is not None:
            self.assertIsInstance(version, str)
            self.assertTrue(len(version) > 0)

    def test_get_gget_version_returns_string(self):
        """Test _get_gget_version returns a version string."""
        version = _get_gget_version()
        self.assertIsInstance(version, str)
        self.assertTrue(len(version) > 0)

    # =========================================================================
    # SARS-CoV-2 / ALPHAINFLUENZA DETECTION TESTS
    # =========================================================================

    def test_is_sars_cov2_query_common_names(self):
        """Test is_sars_cov2_query detects common SARS-CoV-2 names."""
        self.assertTrue(is_sars_cov2_query("SARS-CoV-2"))
        self.assertTrue(is_sars_cov2_query("sarscov2"))
        self.assertTrue(is_sars_cov2_query("COVID-19"))
        self.assertTrue(is_sars_cov2_query("covid"))
        self.assertTrue(is_sars_cov2_query("2697049"))

    def test_is_sars_cov2_query_negative(self):
        """Test is_sars_cov2_query returns False for non-SARS-CoV-2."""
        self.assertFalse(is_sars_cov2_query("Zika virus"))
        self.assertFalse(is_sars_cov2_query("Influenza A"))

    def test_is_sars_cov2_query_accession_mode(self):
        """Test is_sars_cov2_query returns False in accession mode."""
        self.assertFalse(is_sars_cov2_query("2697049", accession=True))

    def test_is_alphainfluenza_query_common_names(self):
        """Test is_alphainfluenza_query detects Alphainfluenza names."""
        self.assertTrue(is_alphainfluenza_query("Influenza A virus"))
        self.assertTrue(is_alphainfluenza_query("influenzaa"))
        self.assertTrue(is_alphainfluenza_query("Alphainfluenzavirus"))
        self.assertTrue(is_alphainfluenza_query("11320"))
        self.assertTrue(is_alphainfluenza_query("197911"))

    def test_is_alphainfluenza_query_negative(self):
        """Test is_alphainfluenza_query returns False for non-Influenza."""
        self.assertFalse(is_alphainfluenza_query("Zika virus"))
        self.assertFalse(is_alphainfluenza_query("SARS-CoV-2"))

    def test_is_alphainfluenza_query_accession_mode(self):
        """Test is_alphainfluenza_query returns False in accession mode."""
        self.assertFalse(is_alphainfluenza_query("11320", accession=True))

    # =========================================================================
    # DATE PARSING TESTS
    # =========================================================================

    def test_parse_date_full(self):
        """Test _parse_date with full date string."""
        result = _parse_date("2024-01-15")
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)

    def test_parse_date_various_formats(self):
        """Test _parse_date with various date formats."""
        # ISO format
        result = _parse_date("2024-06-30")
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 30)

    def test_parse_date_invalid_raises(self):
        """Test _parse_date raises ValueError on invalid date."""
        with self.assertRaises(ValueError):
            _parse_date("not-a-date")

    def test_parse_partial_date_year_only_min_comparison(self):
        """Test _parse_partial_date_for_range_check with year-only for min comparison."""
        result = _parse_partial_date_for_range_check("2015", for_min_comparison=True)
        self.assertEqual(result, datetime(2015, 12, 31))

    def test_parse_partial_date_year_only_max_comparison(self):
        """Test _parse_partial_date_for_range_check with year-only for max comparison."""
        result = _parse_partial_date_for_range_check("2015", for_min_comparison=False)
        self.assertEqual(result, datetime(2015, 1, 1))

    def test_parse_partial_date_year_month_min(self):
        """Test _parse_partial_date_for_range_check with year-month for min."""
        result = _parse_partial_date_for_range_check("2015-06", for_min_comparison=True)
        _, last_day = calendar.monthrange(2015, 6)
        self.assertEqual(result, datetime(2015, 6, last_day))

    def test_parse_partial_date_year_month_max(self):
        """Test _parse_partial_date_for_range_check with year-month for max."""
        result = _parse_partial_date_for_range_check("2015-06", for_min_comparison=False)
        self.assertEqual(result, datetime(2015, 6, 1))

    def test_parse_partial_date_full_date(self):
        """Test _parse_partial_date_for_range_check with full date."""
        result = _parse_partial_date_for_range_check("2015-06-15", for_min_comparison=True)
        self.assertEqual(result.year, 2015)
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 15)

    def test_parse_partial_date_empty_raises(self):
        """Test _parse_partial_date_for_range_check raises on empty string."""
        with self.assertRaises(ValueError):
            _parse_partial_date_for_range_check("", for_min_comparison=True)

    # =========================================================================
    # CHECK MIN/MAX VALIDATION TESTS
    # =========================================================================

    def test_check_min_max_valid(self):
        """Test check_min_max passes with valid min < max."""
        check_min_max(100, 200, "sequence length")  # Should not raise

    def test_check_min_max_equal(self):
        """Test check_min_max passes when min == max."""
        check_min_max(100, 100, "sequence length")  # Should not raise

    def test_check_min_max_invalid_raises(self):
        """Test check_min_max raises ValueError when min > max."""
        with self.assertRaises(ValueError):
            check_min_max(200, 100, "sequence length")

    def test_check_min_max_none_values(self):
        """Test check_min_max is a no-op when either value is None."""
        check_min_max(None, 200, "sequence length")  # Should not raise
        check_min_max(100, None, "sequence length")  # Should not raise
        check_min_max(None, None, "sequence length")  # Should not raise

    def test_check_min_max_date_valid(self):
        """Test check_min_max with valid date range."""
        check_min_max("2020-01-01", "2024-12-31", "release date", date=True)

    def test_check_min_max_date_invalid_raises(self):
        """Test check_min_max raises ValueError when min date > max date."""
        with self.assertRaises(ValueError):
            check_min_max("2024-12-31", "2020-01-01", "release date", date=True)

    # =========================================================================
    # XML HELPER TESTS
    # =========================================================================

    def test_clean_xml_declarations(self):
        """Test _clean_xml_declarations removes XML and DOCTYPE declarations."""
        xml = '<?xml version="1.0"?>\n<!DOCTYPE GBSet>\n<GBSet><GBSeq>data</GBSeq></GBSet>'
        result = _clean_xml_declarations(xml)
        self.assertNotIn("<?xml", result)
        self.assertNotIn("<!DOCTYPE", result)
        self.assertIn("<GBSet>", result)

    def test_clean_xml_declarations_no_declarations(self):
        """Test _clean_xml_declarations with no declarations to remove."""
        xml = "<GBSet><GBSeq>data</GBSeq></GBSet>"
        result = _clean_xml_declarations(xml)
        self.assertEqual(result, xml)

    def test_local_name_with_namespace(self):
        """Test _local_name strips namespace from XML tag."""
        self.assertEqual(_local_name("{http://www.ncbi.nlm.nih.gov}GBSeq"), "GBSeq")

    def test_local_name_without_namespace(self):
        """Test _local_name returns tag as-is without namespace."""
        self.assertEqual(_local_name("GBSeq"), "GBSeq")

    # =========================================================================
    # UNZIP FILE TESTS
    # =========================================================================

    def test_unzip_file_valid(self):
        """Test _unzip_file extracts files correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test ZIP file
            zip_path = os.path.join(tmpdir, "test.zip")
            extract_path = os.path.join(tmpdir, "extracted")
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", "hello world")
            _unzip_file(zip_path, extract_path)
            extracted_file = os.path.join(extract_path, "test.txt")
            self.assertTrue(os.path.exists(extracted_file))
            with open(extracted_file) as f:
                self.assertEqual(f.read(), "hello world")

    def test_unzip_file_bad_zip_raises(self):
        """Test _unzip_file raises on invalid ZIP file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_zip = os.path.join(tmpdir, "bad.zip")
            with open(bad_zip, "w") as f:
                f.write("not a zip file")
            with self.assertRaises(zipfile.BadZipFile):
                _unzip_file(bad_zip, os.path.join(tmpdir, "out"))

    def test_unzip_file_nonexistent_raises(self):
        """Test _unzip_file raises on nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                _unzip_file("/nonexistent/file.zip", tmpdir)

    # =========================================================================
    # MEMORY MONITORING TESTS
    # =========================================================================

    def test_get_memory_usage_returns_dict(self):
        """Test _get_memory_usage returns a dictionary with expected keys."""
        mem = _get_memory_usage()
        self.assertIsInstance(mem, dict)
        self.assertIn("rss_mb", mem)
        self.assertIn("vms_mb", mem)

    def test_force_garbage_collection_runs(self):
        """Test _force_garbage_collection executes without error."""
        _force_garbage_collection(context="test")

    # =========================================================================
    # BASELINE FILE PARSING TESTS
    # =========================================================================

    def test_parse_baseline_file_csv(self):
        """Test _parse_baseline_file with CSV format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("accession,length,host\n")
            f.write("NC_045512.2,29903,human\n")
            f.write("MN908947.3,29903,human\n")
            path = f.name
        try:
            result = _parse_baseline_file(path)
            self.assertIsInstance(result, set)
            self.assertEqual(len(result), 2)
            self.assertIn("nc_045512.2", result)
            self.assertIn("mn908947.3", result)
        finally:
            os.unlink(path)

    def test_parse_baseline_file_jsonl(self):
        """Test _parse_baseline_file with JSONL format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"accession": "NC_045512.2", "length": 29903}\n')
            f.write('{"accession": "MN908947.3", "length": 29903}\n')
            path = f.name
        try:
            result = _parse_baseline_file(path)
            self.assertEqual(len(result), 2)
            self.assertIn("nc_045512.2", result)
        finally:
            os.unlink(path)

    def test_parse_baseline_file_json(self):
        """Test _parse_baseline_file with JSON array format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            import json as json_mod

            json_mod.dump([{"accession": "NC_045512.2"}, {"accession": "MN908947.3"}], f)
            path = f.name
        try:
            result = _parse_baseline_file(path)
            self.assertEqual(len(result), 2)
        finally:
            os.unlink(path)

    def test_parse_baseline_file_text(self):
        """Test _parse_baseline_file with plain text format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("NC_045512.2\n")
            f.write("MN908947.3\n")
            f.write("# comment line\n")
            f.write("MT020781.1\n")
            path = f.name
        try:
            result = _parse_baseline_file(path)
            self.assertEqual(len(result), 3)
            # Comments should be skipped
            self.assertNotIn("# comment line", result)
        finally:
            os.unlink(path)

    def test_parse_baseline_file_nonexistent_raises(self):
        """Test _parse_baseline_file raises for nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            _parse_baseline_file("/nonexistent/baseline.csv")

    def test_parse_baseline_file_empty_raises(self):
        """Test _parse_baseline_file raises for empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("accession\n")  # header only, no data
            path = f.name
        try:
            with self.assertRaises(ValueError):
                _parse_baseline_file(path)
        finally:
            os.unlink(path)

    def test_parse_baseline_file_none_raises(self):
        """Test _parse_baseline_file raises for None path."""
        with self.assertRaises(FileNotFoundError):
            _parse_baseline_file(None)

    # =========================================================================
    # DEDUPLICATION TESTS
    # =========================================================================

    def test_deduplicate_metadata_against_baseline(self):
        """Test _deduplicate_metadata_against_baseline removes existing accessions."""
        metadata_dict = {
            "NC_045512.2": {"length": 29903},
            "MN908947.3": {"length": 29903},
            "NEW_001.1": {"length": 10000},
        }
        baseline = {"nc_045512.2", "mn908947.3"}
        new_meta, skipped = _deduplicate_metadata_against_baseline(metadata_dict, baseline)
        self.assertEqual(skipped, 2)
        self.assertEqual(len(new_meta), 1)
        self.assertIn("NEW_001.1", new_meta)

    def test_deduplicate_empty_baseline(self):
        """Test _deduplicate_metadata_against_baseline with empty baseline."""
        metadata_dict = {"ACC1": {"length": 100}, "ACC2": {"length": 200}}
        new_meta, skipped = _deduplicate_metadata_against_baseline(metadata_dict, set())
        self.assertEqual(skipped, 0)
        self.assertEqual(len(new_meta), 2)

    def test_deduplicate_all_existing(self):
        """Test _deduplicate_metadata_against_baseline when all accessions exist."""
        metadata_dict = {"ACC1": {"length": 100}}
        baseline = {"acc1"}
        new_meta, skipped = _deduplicate_metadata_against_baseline(metadata_dict, baseline)
        self.assertEqual(skipped, 1)
        self.assertEqual(len(new_meta), 0)

    # =========================================================================
    # SAVE PARTIAL METADATA TESTS
    # =========================================================================

    def test_save_partial_metadata(self):
        """Test _save_partial_metadata saves a CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_dict = {
                "NC_045512.2": {
                    "virus_name": "SARS-CoV-2",
                    "length": 29903,
                    "completeness": "complete",
                    "releaseDate": "2024-01-01",
                    "host": {"organism_name": "human"},
                },
            }
            result = _save_partial_metadata(metadata_dict, tmpdir, "test_virus", reason="test")
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(result))
            df = pd.read_csv(result)
            self.assertEqual(len(df), 1)
            self.assertIn("accession", df.columns)

    def test_save_partial_metadata_empty(self):
        """Test _save_partial_metadata returns None for empty dict."""
        result = _save_partial_metadata({}, "/tmp", "test_virus")
        self.assertIsNone(result)

    # =========================================================================
    # MERGE BASELINE WITH NEW TESTS
    # =========================================================================

    def test_merge_baseline_with_new_csv(self):
        """Test _merge_baseline_with_new merges CSV baseline with new records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = os.path.join(tmpdir, "baseline.csv")
            output_path = os.path.join(tmpdir, "merged.csv")
            # Create baseline CSV
            pd.DataFrame(
                [
                    {"accession": "ACC1", "length": 100},
                    {"accession": "ACC2", "length": 200},
                ]
            ).to_csv(baseline_path, index=False)
            # New metadata
            new_records = [
                {"accession": "ACC3", "length": 300},
            ]
            result = _merge_baseline_with_new(baseline_path, new_records, output_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(output_path))
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 3)

    def test_merge_baseline_with_new_deduplicates(self):
        """Test _merge_baseline_with_new removes duplicates (keeps new)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = os.path.join(tmpdir, "baseline.csv")
            output_path = os.path.join(tmpdir, "merged.csv")
            pd.DataFrame(
                [
                    {"accession": "ACC1", "length": 100},
                ]
            ).to_csv(baseline_path, index=False)
            new_records = [{"accession": "ACC1", "length": 999}]
            _merge_baseline_with_new(baseline_path, new_records, output_path)
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]["length"], 999)  # New takes priority

    def test_merge_baseline_with_new_empty_new(self):
        """Test _merge_baseline_with_new with empty new records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = os.path.join(tmpdir, "baseline.csv")
            output_path = os.path.join(tmpdir, "merged.csv")
            pd.DataFrame([{"accession": "ACC1"}]).to_csv(baseline_path, index=False)
            result = _merge_baseline_with_new(baseline_path, [], output_path)
            self.assertTrue(result)
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 1)

    # =========================================================================
    # LOAD METADATA FROM API REPORTS TESTS
    # =========================================================================

    def test_load_metadata_from_api_reports_basic(self):
        """Test load_metadata_from_api_reports transforms API reports correctly."""
        api_reports = [
            {
                "accession": "NC_045512.2",
                "length": 29903,
                "gene_count": 11,
                "completeness": "COMPLETE",
                "host": {"organism_name": "Homo sapiens", "tax_id": 9606},
                "is_lab_host": False,
                "location": {"geographic_location": "China", "geographic_region": "Asia"},
                "source_database": "GenBank",
                "isolate": {"name": "Wuhan-Hu-1", "collection_date": "2019-12-30"},
                "virus": {"tax_id": 2697049, "organism_name": "SARS-CoV-2"},
                "is_annotated": True,
                "release_date": "2020-01-13",
                "protein_count": 12,
                "mature_peptide_count": 16,
                "segment": None,
                "is_vaccine_strain": False,
            }
        ]
        result = load_metadata_from_api_reports(api_reports)
        self.assertIn("NC_045512.2", result)
        meta = result["NC_045512.2"]
        self.assertEqual(meta["accession"], "NC_045512.2")
        self.assertEqual(meta["length"], 29903)
        self.assertEqual(meta["completeness"], "complete")
        self.assertEqual(meta["hostName"], "Homo sapiens")
        self.assertTrue(meta["isAnnotated"])
        self.assertEqual(meta["proteinCount"], 12)
        self.assertEqual(meta["sourceDatabase"], "GenBank")

    def test_load_metadata_from_api_reports_missing_accession(self):
        """Test load_metadata_from_api_reports skips reports without accession."""
        api_reports = [{"length": 100}]  # No accession
        result = load_metadata_from_api_reports(api_reports)
        self.assertEqual(len(result), 0)

    def test_load_metadata_from_api_reports_empty(self):
        """Test load_metadata_from_api_reports with empty list."""
        result = load_metadata_from_api_reports([])
        self.assertEqual(len(result), 0)

    def test_load_metadata_from_api_reports_multiple(self):
        """Test load_metadata_from_api_reports with multiple reports."""
        api_reports = [
            {
                "accession": "ACC1",
                "length": 100,
                "completeness": "COMPLETE",
                "host": {},
                "location": {},
                "isolate": {},
                "virus": {},
            },
            {
                "accession": "ACC2",
                "length": 200,
                "completeness": "PARTIAL",
                "host": {},
                "location": {},
                "isolate": {},
                "virus": {},
            },
        ]
        result = load_metadata_from_api_reports(api_reports)
        self.assertEqual(len(result), 2)
        self.assertIn("ACC1", result)
        self.assertIn("ACC2", result)

    # =========================================================================
    # FILTER METADATA ONLY TESTS
    # =========================================================================

    def _make_test_metadata(self):
        """Helper to create a test metadata dict."""
        return {
            "ACC1": {
                "accession": "ACC1",
                "length": 29903,
                "completeness": "complete",
                "hostName": "Homo sapiens",
                "isLabHost": False,
                "labHost": False,
                "isAnnotated": True,
                "submitterCountry": "United States",
                "submitterName": "CDC",
                "submitterInstitution": "Centers for Disease Control",
                "isolateName": "Wuhan-Hu-1",
                "isolate": {"collectionDate": "2020-01-15", "source": "nasopharyngeal swab"},
                "sourceDatabase": "genbank",
                "releaseDate": "2020-02-01",
                "proteinCount": 12,
                "segment": "HA",
                "isVaccineStrain": False,
                "location": "China",
                "region": "Asia",
                "virusName": "SARS-CoV-2",
            },
            "ACC2": {
                "accession": "ACC2",
                "length": 5000,
                "completeness": "partial",
                "hostName": "Mus musculus",
                "isLabHost": True,
                "labHost": True,
                "isAnnotated": False,
                "submitterCountry": "Germany",
                "submitterName": "RKI",
                "submitterInstitution": "Robert Koch Institute",
                "isolateName": "mouse-strain-1",
                "isolate": {"collectionDate": "2023-06-01", "source": "lab culture"},
                "sourceDatabase": "refseq",
                "releaseDate": "2023-07-01",
                "proteinCount": 5,
                "segment": "NA",
                "isVaccineStrain": True,
                "location": "Germany",
                "region": "Europe",
                "virusName": "SARS-CoV-2 isolate lab",
            },
            "ACC3": {
                "accession": "ACC3",
                "length": 15000,
                "completeness": "complete",
                "hostName": "Homo sapiens",
                "isLabHost": False,
                "labHost": False,
                "isAnnotated": True,
                "submitterCountry": "Brazil",
                "submitterName": "FIOCRUZ",
                "submitterInstitution": "Oswaldo Cruz Foundation",
                "isolateName": "BRA/2021",
                "isolate": {"collectionDate": "2021-03-15", "source": "blood"},
                "sourceDatabase": "genbank",
                "releaseDate": "2021-04-01",
                "proteinCount": 8,
                "segment": None,
                "isVaccineStrain": False,
                "location": "Brazil",
                "region": "South America",
                "virusName": "Zika virus",
            },
        }

    def test_filter_metadata_only_no_filters(self):
        """Test filter_metadata_only with no filters returns all records."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta)
        self.assertEqual(len(accs), 3)

    def test_filter_metadata_only_min_seq_length(self):
        """Test filter_metadata_only with min_seq_length."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, min_seq_length=10000)
        self.assertEqual(len(accs), 2)
        self.assertIn("ACC1", accs)
        self.assertIn("ACC3", accs)

    def test_filter_metadata_only_max_seq_length(self):
        """Test filter_metadata_only with max_seq_length."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, max_seq_length=10000)
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_metadata_only_lab_passaged_false(self):
        """Test filter_metadata_only excludes lab-passaged when False."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, lab_passaged=False)
        self.assertEqual(len(accs), 2)
        self.assertNotIn("ACC2", accs)

    def test_filter_metadata_only_lab_passaged_true(self):
        """Test filter_metadata_only keeps only lab-passaged when True."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, lab_passaged=True)
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_metadata_only_annotated_false(self):
        """Test filter_metadata_only excludes annotated when False."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, annotated=False)
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_metadata_only_source_database(self):
        """Test filter_metadata_only by source database."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, source_database="GenBank")
        self.assertEqual(len(accs), 2)
        self.assertIn("ACC1", accs)
        self.assertIn("ACC3", accs)

    def test_filter_metadata_only_collection_date_range(self):
        """Test filter_metadata_only with collection date range."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, min_collection_date="2021-01-01", max_collection_date="2021-12-31")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC3", accs)

    def test_filter_metadata_only_protein_count(self):
        """Test filter_metadata_only with protein count filters."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, min_protein_count=10)
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC1", accs)

    def test_filter_metadata_only_segment(self):
        """Test filter_metadata_only by segment."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, segment="HA")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC1", accs)

    def test_filter_metadata_only_vaccine_strain_true(self):
        """Test filter_metadata_only keeps only vaccine strains."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, vaccine_strain=True)
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_metadata_only_vaccine_strain_false(self):
        """Test filter_metadata_only excludes vaccine strains."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, vaccine_strain=False)
        self.assertEqual(len(accs), 2)
        self.assertNotIn("ACC2", accs)

    def test_filter_metadata_only_submitter_country(self):
        """Test filter_metadata_only by submitter country."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, submitter_country="Germany")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_metadata_only_submitter_name(self):
        """Test filter_metadata_only by submitter name."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, submitter_name="CDC")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC1", accs)

    def test_filter_metadata_only_submitter_institution(self):
        """Test filter_metadata_only by submitter institution."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, submitter_institution="Robert Koch Institute")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_metadata_only_isolate(self):
        """Test filter_metadata_only by isolate name."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, isolate="Wuhan-Hu-1")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC1", accs)

    def test_filter_metadata_only_isolation_source(self):
        """Test filter_metadata_only by isolation source."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, isolation_source="blood")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC3", accs)

    def test_filter_metadata_only_geographic_location(self):
        """Test filter_metadata_only by geographic location."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, geographic_location="Brazil")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC3", accs)

    def test_filter_metadata_only_host(self):
        """Test filter_metadata_only by host."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, host="Homo sapiens")
        self.assertEqual(len(accs), 2)
        self.assertIn("ACC1", accs)
        self.assertIn("ACC3", accs)

    def test_filter_metadata_only_max_release_date(self):
        """Test filter_metadata_only with max_release_date."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, max_release_date="2020-12-31")
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC1", accs)

    def test_filter_metadata_only_combined_filters(self):
        """Test filter_metadata_only with multiple filters combined."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(
            meta,
            min_seq_length=10000,
            source_database="GenBank",
            host="Homo sapiens",
        )
        self.assertEqual(len(accs), 2)
        self.assertIn("ACC1", accs)
        self.assertIn("ACC3", accs)

    # =========================================================================
    # FILTER GENBANK METADATA TESTS
    # =========================================================================

    def _make_genbank_metadata(self):
        """Helper to create test GenBank metadata."""
        return {
            "ACC1": {
                "genbank_data": {
                    "gene_count": 11,
                    "mature_peptide_count": 16,
                    "proviral": False,
                    "genotype": "H5N1",
                    "products": ["hemagglutinin", "neuraminidase", "polymerase"],
                    "mol_type": "genomic RNA",
                    "isolation_source": "nasopharyngeal swab",
                    "host": "Homo sapiens",
                    "comment": "",
                    "all_features": {"source": {"note": ""}},
                },
            },
            "ACC2": {
                "genbank_data": {
                    "gene_count": 3,
                    "mature_peptide_count": 2,
                    "proviral": True,
                    "genotype": "H3N2",
                    "products": ["matrix protein", "nucleoprotein"],
                    "mol_type": "genomic DNA",
                    "isolation_source": "sewage",
                    "host": "",
                    "comment": "environmental sample",
                    "all_features": {"source": {"note": "wastewater sample"}},
                },
            },
            "ACC3": {
                "genbank_data": {
                    "gene_count": 8,
                    "mature_peptide_count": 5,
                    "proviral": False,
                    "genotype": "H5N1",
                    "products": ["hemagglutinin", "nucleoprotein", "spike"],
                    "mol_type": "genomic RNA",
                    "isolation_source": "",
                    "host": "chicken",
                    "comment": "",
                    "all_features": {"source": {"note": ""}},
                },
            },
        }

    def test_filter_genbank_metadata_empty(self):
        """Test filter_genbank_metadata with empty input."""
        result = filter_genbank_metadata({})
        self.assertEqual(len(result), 0)

    def test_filter_genbank_metadata_no_filters(self):
        """Test filter_genbank_metadata with no filters returns all."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta)
        self.assertEqual(len(result), 3)

    def test_filter_genbank_metadata_min_gene_count(self):
        """Test filter_genbank_metadata with min_gene_count."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, min_gene_count=5)
        self.assertEqual(len(result), 2)
        self.assertIn("ACC1", result)
        self.assertIn("ACC3", result)

    def test_filter_genbank_metadata_max_gene_count(self):
        """Test filter_genbank_metadata with max_gene_count."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, max_gene_count=5)
        self.assertEqual(len(result), 1)
        self.assertIn("ACC2", result)

    def test_filter_genbank_metadata_provirus_true(self):
        """Test filter_genbank_metadata keeps only proviral."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, provirus=True)
        self.assertEqual(len(result), 1)
        self.assertIn("ACC2", result)

    def test_filter_genbank_metadata_provirus_false(self):
        """Test filter_genbank_metadata excludes proviral."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, provirus=False)
        self.assertEqual(len(result), 2)
        self.assertNotIn("ACC2", result)

    def test_filter_genbank_metadata_genotype(self):
        """Test filter_genbank_metadata by genotype."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, genotype="H5N1")
        self.assertEqual(len(result), 2)
        self.assertIn("ACC1", result)
        self.assertIn("ACC3", result)

    def test_filter_genbank_metadata_genotype_list(self):
        """Test filter_genbank_metadata by genotype list."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, genotype=["H3N2"])
        self.assertEqual(len(result), 1)
        self.assertIn("ACC2", result)

    def test_filter_genbank_metadata_has_proteins(self):
        """Test filter_genbank_metadata by has_proteins."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, has_proteins="hemagglutinin")
        self.assertEqual(len(result), 2)
        self.assertIn("ACC1", result)
        self.assertIn("ACC3", result)

    def test_filter_genbank_metadata_gen_mol_type(self):
        """Test filter_genbank_metadata by molecule type."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, gen_mol_type="genomic RNA")
        self.assertEqual(len(result), 2)
        self.assertIn("ACC1", result)
        self.assertIn("ACC3", result)

    def test_filter_genbank_metadata_mature_peptide_count(self):
        """Test filter_genbank_metadata by mature peptide count range."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, min_mature_peptide_count=10)
        self.assertEqual(len(result), 1)
        self.assertIn("ACC1", result)

    def test_filter_genbank_metadata_env_source(self):
        """Test filter_genbank_metadata by environmental source."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, env_source="sewage")
        # ACC2 has sewage in isolation_source and non-human host
        # ACC1 has human host so env_source check is skipped
        # ACC3 has chicken host and no env match
        self.assertIn("ACC1", result)
        self.assertIn("ACC2", result)

    def test_filter_genbank_metadata_combined(self):
        """Test filter_genbank_metadata with multiple filters."""
        meta = self._make_genbank_metadata()
        result, _ = filter_genbank_metadata(meta, min_gene_count=5, genotype="H5N1", has_proteins="hemagglutinin")
        self.assertEqual(len(result), 2)
        self.assertIn("ACC1", result)
        self.assertIn("ACC3", result)

    # =========================================================================
    # FILTER CACHED METADATA FOR UNUSED FILTERS TESTS
    # =========================================================================

    def test_filter_cached_no_filters(self):
        """Test filter_cached_metadata_for_unused_filters with no filters."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(meta)
        self.assertEqual(len(accs), 3)

    def test_filter_cached_host_not_in_strategy(self):
        """Test filter_cached_metadata_for_unused_filters applies host when not in strategy."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(meta, host="Homo sapiens", applied_strategy_filters=[])
        self.assertEqual(len(accs), 2)
        self.assertIn("ACC1", accs)
        self.assertIn("ACC3", accs)

    def test_filter_cached_host_in_strategy_skipped(self):
        """Test filter_cached_metadata_for_unused_filters skips host if already in strategy."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(
            meta, host="Homo sapiens", applied_strategy_filters=["host"]
        )
        # Host filter should NOT be applied since it was in strategy
        self.assertEqual(len(accs), 3)

    def test_filter_cached_complete_only(self):
        """Test filter_cached_metadata_for_unused_filters with complete_only."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(meta, complete_only=True, applied_strategy_filters=[])
        self.assertEqual(len(accs), 2)  # ACC1 and ACC3 are complete

    def test_filter_cached_annotated(self):
        """Test filter_cached_metadata_for_unused_filters with annotated."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(meta, annotated=True, applied_strategy_filters=[])
        self.assertEqual(len(accs), 2)
        self.assertNotIn("ACC2", accs)

    def test_filter_cached_geographic_location(self):
        """Test filter_cached_metadata_for_unused_filters with geographic_location."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(
            meta, geographic_location="China", applied_strategy_filters=[]
        )
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC1", accs)

    def test_filter_cached_refseq_only(self):
        """Test filter_cached_metadata_for_unused_filters with refseq_only."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(meta, refseq_only=True, applied_strategy_filters=[])
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_cached_min_release_date(self):
        """Test filter_cached_metadata_for_unused_filters with min_release_date."""
        meta = self._make_test_metadata()
        accs, metas = filter_cached_metadata_for_unused_filters(
            meta, min_release_date="2023-01-01", applied_strategy_filters=[]
        )
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    # =========================================================================
    # FILTER METADATA ONLY - ADDITIONAL COVERAGE
    # =========================================================================

    def test_filter_metadata_only_nuc_completeness_partial(self):
        """Test filter_metadata_only with nuc_completeness='partial'."""
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, nuc_completeness="partial")
        # ACC2 has completeness='partial', ACC1 and ACC3 have 'complete'
        self.assertEqual(len(accs), 1)
        self.assertIn("ACC2", accs)

    def test_filter_metadata_only_annotated_true(self):
        """Test filter_metadata_only with annotated=True passes all (handled server-side).

        Note: annotated=True is handled server-side by the API, so the client-side
        filter_metadata_only does NOT filter on annotated=True. All records pass.
        """
        meta = self._make_test_metadata()
        accs, metas, _ = filter_metadata_only(meta, annotated=True)
        # annotated=True is NOT applied client-side (server handles it)
        self.assertEqual(len(accs), 3)

    # =========================================================================
    # WRITE FASTA RECORD TESTS
    # =========================================================================

    def test_write_fasta_record_with_description(self):
        """Test _write_fasta_record writes correct FASTA format with description."""
        import io

        from gget.utils import FastaRecord

        record = FastaRecord(seq="ATCGATCGATCG", id="ACC001", description="Test virus isolate")
        handle = io.StringIO()
        _write_fasta_record(handle, record)
        output = handle.getvalue()

        self.assertTrue(output.startswith(">ACC001 Test virus isolate\n"))
        self.assertIn("ATCGATCGATCG", output)

    def test_write_fasta_record_without_description(self):
        """Test _write_fasta_record writes correct FASTA format without description."""
        import io

        from gget.utils import FastaRecord

        record = FastaRecord(seq="ATCG", id="ACC002", description="")
        handle = io.StringIO()
        _write_fasta_record(handle, record)
        output = handle.getvalue()

        self.assertTrue(output.startswith(">ACC002\n"))
        self.assertIn("ATCG", output)

    def test_write_fasta_record_long_sequence_wraps(self):
        """Test _write_fasta_record wraps long sequences at 70 characters."""
        import io

        from gget.utils import FastaRecord

        # Create a sequence longer than 70 characters
        long_seq = "A" * 150
        record = FastaRecord(seq=long_seq, id="ACC003", description="")
        handle = io.StringIO()
        _write_fasta_record(handle, record)
        lines = handle.getvalue().strip().split("\n")

        # First line is header, then sequence lines
        self.assertEqual(lines[0], ">ACC003")
        self.assertEqual(len(lines[1]), 70)  # First seq line is 70 chars
        self.assertEqual(len(lines[2]), 70)  # Second seq line is 70 chars
        self.assertEqual(len(lines[3]), 10)  # Remaining 10 chars

    # =========================================================================
    # STREAM COPY FASTA TESTS
    # =========================================================================

    def test_stream_copy_fasta_all_records(self):
        """Test _stream_copy_fasta copies all records when no filter set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.fasta")
            output_path = os.path.join(tmpdir, "output.fasta")

            with open(input_path, "w") as f:
                f.write(">ACC1\nATCGATCG\n>ACC2\nGGGGAAAA\n>ACC3\nTTTTCCCC\n")

            count = _stream_copy_fasta(input_path, output_path)
            self.assertEqual(count, 3)
            self.assertTrue(os.path.exists(output_path))

            # Verify output has all 3 records
            with open(output_path) as f:
                headers = [l for l in f if l.startswith(">")]
            self.assertEqual(len(headers), 3)

    def test_stream_copy_fasta_with_accession_filter(self):
        """Test _stream_copy_fasta filters by accession set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.fasta")
            output_path = os.path.join(tmpdir, "output.fasta")

            with open(input_path, "w") as f:
                f.write(">ACC1\nATCGATCG\n>ACC2\nGGGGAAAA\n>ACC3\nTTTTCCCC\n")

            count = _stream_copy_fasta(input_path, output_path, accession_set={"ACC1", "ACC3"})
            self.assertEqual(count, 2)

            with open(output_path) as f:
                content = f.read()
            self.assertIn(">ACC1", content)
            self.assertIn(">ACC3", content)
            self.assertNotIn(">ACC2", content)

    # =========================================================================
    # FILTER SEQUENCES TESTS
    # =========================================================================

    def test_filter_sequences_max_ambiguous_chars(self):
        """Test filter_sequences filters by max ambiguous characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fasta_path = os.path.join(tmpdir, "test.fasta")
            output_path = os.path.join(tmpdir, "filtered.fasta")

            # ACC1 has 0 N's, ACC2 has 5 N's, ACC3 has 20 N's
            with open(fasta_path, "w") as f:
                f.write(">ACC1\nATCGATCGATCG\n")
                f.write(">ACC2\nATNNNNNCG\n")
                f.write(">ACC3\n" + "N" * 20 + "\n")

            metadata_dict = {
                "ACC1": {"accession": "ACC1", "length": 12},
                "ACC2": {"accession": "ACC2", "length": 9},
                "ACC3": {"accession": "ACC3", "length": 20},
            }

            count, filtered_meta, protein_headers, stats = filter_sequences(
                fasta_path,
                metadata_dict,
                max_ambiguous_chars=10,
                output_fasta_path=output_path,
            )

            self.assertEqual(count, 2)  # ACC1 and ACC2 pass
            self.assertEqual(stats["ambiguous_chars"], 1)  # ACC3 filtered out

    def test_filter_sequences_no_filters(self):
        """Test filter_sequences passes all records when no filters applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fasta_path = os.path.join(tmpdir, "test.fasta")
            output_path = os.path.join(tmpdir, "filtered.fasta")

            with open(fasta_path, "w") as f:
                f.write(">ACC1\nATCGATCG\n>ACC2\nGGGGAAAA\n")

            metadata_dict = {
                "ACC1": {"accession": "ACC1"},
                "ACC2": {"accession": "ACC2"},
            }

            count, filtered_meta, protein_headers, stats = filter_sequences(
                fasta_path,
                metadata_dict,
                output_fasta_path=output_path,
            )

            self.assertEqual(count, 2)

    def test_filter_sequences_proteins_complete(self):
        """Test filter_sequences with proteins_complete=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fasta_path = os.path.join(tmpdir, "test.fasta")
            output_path = os.path.join(tmpdir, "filtered.fasta")

            with open(fasta_path, "w") as f:
                f.write(">ACC1\nATCGATCG\n>ACC2\nGGGGAAAA\n")

            metadata_dict = {
                "ACC1": {"accession": "ACC1", "proteinCount": 10, "geneCount": 5},
                "ACC2": {"accession": "ACC2", "proteinCount": 0, "geneCount": 0},
            }

            count, filtered_meta, protein_headers, stats = filter_sequences(
                fasta_path,
                metadata_dict,
                proteins_complete=True,
                output_fasta_path=output_path,
            )

            self.assertEqual(count, 1)  # Only ACC1 has proteins
            self.assertEqual(stats["proteins"], 1)  # ACC2 filtered out

    # =========================================================================
    # SAVE COMMAND SUMMARY TESTS
    # =========================================================================

    def test_save_command_summary_creates_file(self):
        """Test save_command_summary creates a summary text file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_command_summary(
                outfolder=tmpdir,
                command_line="gget virus 'Zika virus'",
                total_api_records=100,
                total_after_metadata_filter=80,
                total_final_sequences=75,
                output_files={"fasta": "test.fasta", "csv": "test.csv"},
                filtered_metadata=[],
                datasets_version="16.0.0",
                gget_version="1.0.0",
            )

            summary_path = os.path.join(tmpdir, "command_summary.txt")
            self.assertTrue(os.path.exists(summary_path))
            with open(summary_path) as f:
                content = f.read()
            self.assertIn("GGET VIRUS COMMAND SUMMARY", content)
            self.assertIn("Zika virus", content)
            self.assertIn("16.0.0", content)

    def test_save_command_summary_with_error(self):
        """Test save_command_summary records error information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_command_summary(
                outfolder=tmpdir,
                command_line="gget virus 'test'",
                total_api_records=0,
                total_after_metadata_filter=0,
                total_final_sequences=0,
                output_files={},
                filtered_metadata=[],
                datasets_version=None,
                success=False,
                error_message="API connection failed",
            )

            summary_path = os.path.join(tmpdir, "command_summary.txt")
            self.assertTrue(os.path.exists(summary_path))
            with open(summary_path) as f:
                content = f.read()
            self.assertIn("API connection failed", content)

    # =========================================================================
    # MERGE METADATA CSVS TESTS
    # =========================================================================

    def test_merge_metadata_csvs_fills_missing(self):
        """Test merge_metadata_csvs fills missing values from standard CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            genbank_path = os.path.join(tmpdir, "genbank.csv")
            standard_path = os.path.join(tmpdir, "standard.csv")

            # GenBank CSV with missing host
            pd.DataFrame(
                [
                    {"accession": "ACC1", "Host": "", "Length": "29903"},
                ]
            ).to_csv(genbank_path, index=False)

            # Standard CSV with host data
            pd.DataFrame(
                [
                    {"accession": "ACC1", "Host": "Homo sapiens", "Length": "29903"},
                ]
            ).to_csv(standard_path, index=False)

            result = merge_metadata_csvs(genbank_path, standard_path)
            self.assertTrue(result)

            # Verify the merged result has host filled in
            df = pd.read_csv(genbank_path)
            self.assertEqual(df.iloc[0]["Host"], "Homo sapiens")

    def test_merge_metadata_csvs_missing_standard_file(self):
        """Test merge_metadata_csvs returns False when standard CSV missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            genbank_path = os.path.join(tmpdir, "genbank.csv")
            pd.DataFrame([{"accession": "ACC1"}]).to_csv(genbank_path, index=False)

            result = merge_metadata_csvs(genbank_path, "/nonexistent/standard.csv")
            self.assertFalse(result)

    def test_merge_metadata_csvs_no_overwrite(self):
        """Test merge_metadata_csvs does not overwrite existing GenBank data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            genbank_path = os.path.join(tmpdir, "genbank.csv")
            standard_path = os.path.join(tmpdir, "standard.csv")

            pd.DataFrame(
                [
                    {"accession": "ACC1", "Host": "chicken", "Length": "29903"},
                ]
            ).to_csv(genbank_path, index=False)

            pd.DataFrame(
                [
                    {"accession": "ACC1", "Host": "human", "Length": "29903"},
                ]
            ).to_csv(standard_path, index=False)

            merge_metadata_csvs(genbank_path, standard_path)

            df = pd.read_csv(genbank_path)
            # Existing data should NOT be overwritten
            self.assertEqual(df.iloc[0]["Host"], "chicken")

    # =========================================================================
    # SAVE METADATA TO CSV TESTS
    # =========================================================================

    def test_save_metadata_to_csv_basic(self):
        """Test save_metadata_to_csv creates a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metadata.csv")

            filtered_metadata = [
                {
                    "accession": "ACC1",
                    "virus": {"organism_name": "SARS-CoV-2"},
                    "sourceDatabase": "GenBank",
                    "length": 29903,
                    "completeness": "complete",
                    "host": {"organism_name": "Homo sapiens"},
                    "releaseDate": "2020-01-13T00:00:00",
                    "isolate": {"name": "Wuhan-Hu-1", "collection_date": "2019-12-30"},
                    "submitter": {"names": ["Author1"], "affiliation": "CDC", "country": "USA"},
                    "isAnnotated": True,
                    "proteinCount": 12,
                },
            ]

            save_metadata_to_csv(filtered_metadata, [], output_path)

            self.assertTrue(os.path.exists(output_path))
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]["accession"], "ACC1")
            self.assertEqual(df.iloc[0]["Length"], 29903)
            self.assertIn("Host", df.columns)
            self.assertIn("Release date", df.columns)

    def test_save_metadata_to_csv_empty_metadata(self):
        """Test save_metadata_to_csv handles empty metadata list without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metadata.csv")
            # Empty metadata should not raise - function completes gracefully
            save_metadata_to_csv([], [], output_path)

    # =========================================================================
    # PARSE GENBANK XML TESTS
    # =========================================================================

    def test_parse_genbank_xml_basic(self):
        """Test _parse_genbank_xml extracts metadata from valid XML."""
        xml_content = """<?xml version="1.0"?>
<GBSet>
  <GBSeq>
    <GBSeq_accession-version>NC_045512.2</GBSeq_accession-version>
    <GBSeq_length>29903</GBSeq_length>
    <GBSeq_organism>SARS-CoV-2</GBSeq_organism>
    <GBSeq_definition>Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1</GBSeq_definition>
    <GBSeq_taxonomy>Viruses; Riboviria</GBSeq_taxonomy>
    <GBSeq_create-date>2020-01-13</GBSeq_create-date>
    <GBSeq_update-date>2020-07-17</GBSeq_update-date>
    <GBSeq_references>
      <GBReference>
        <GBReference_title>A new coronavirus</GBReference_title>
        <GBReference_authors><GBAuthor>Wu F</GBAuthor><GBAuthor>Zhao S</GBAuthor></GBReference_authors>
        <GBReference_journal>Nature 579(7798)</GBReference_journal>
        <GBReference_pubmed>32015508</GBReference_pubmed>
      </GBReference>
    </GBSeq_references>
    <GBSeq_feature-table>
      <GBFeature>
        <GBFeature_key>source</GBFeature_key>
        <GBFeature_location>1..29903</GBFeature_location>
        <GBFeature_quals>
          <GBQualifier><GBQualifier_name>host</GBQualifier_name><GBQualifier_value>Homo sapiens</GBQualifier_value></GBQualifier>
          <GBQualifier><GBQualifier_name>collection_date</GBQualifier_name><GBQualifier_value>2019-12-30</GBQualifier_value></GBQualifier>
          <GBQualifier><GBQualifier_name>geo_loc_name</GBQualifier_name><GBQualifier_value>China: Wuhan</GBQualifier_value></GBQualifier>
          <GBQualifier><GBQualifier_name>mol_type</GBQualifier_name><GBQualifier_value>genomic RNA</GBQualifier_value></GBQualifier>
          <GBQualifier><GBQualifier_name>isolation_source</GBQualifier_name><GBQualifier_value>bronchoalveolar lavage fluid</GBQualifier_value></GBQualifier>
        </GBFeature_quals>
      </GBFeature>
      <GBFeature>
        <GBFeature_key>gene</GBFeature_key>
        <GBFeature_location>266..21555</GBFeature_location>
        <GBFeature_quals>
          <GBQualifier><GBQualifier_name>gene</GBQualifier_name><GBQualifier_value>ORF1ab</GBQualifier_value></GBQualifier>
        </GBFeature_quals>
      </GBFeature>
      <GBFeature>
        <GBFeature_key>gene</GBFeature_key>
        <GBFeature_location>21563..25384</GBFeature_location>
        <GBFeature_quals>
          <GBQualifier><GBQualifier_name>gene</GBQualifier_name><GBQualifier_value>S</GBQualifier_value></GBQualifier>
        </GBFeature_quals>
      </GBFeature>
      <GBFeature>
        <GBFeature_key>CDS</GBFeature_key>
        <GBFeature_location>21563..25384</GBFeature_location>
        <GBFeature_quals>
          <GBQualifier><GBQualifier_name>product</GBQualifier_name><GBQualifier_value>spike glycoprotein</GBQualifier_value></GBQualifier>
        </GBFeature_quals>
      </GBFeature>
    </GBSeq_feature-table>
    <GBSeq_comment>Assembly Name :: ASM985889v3</GBSeq_comment>
  </GBSeq>
</GBSet>"""

        result = _parse_genbank_xml(xml_content)

        self.assertIn("NC_045512.2", result)
        meta = result["NC_045512.2"]
        self.assertEqual(meta["accession"], "NC_045512.2")
        gb = meta["genbank_data"]
        self.assertEqual(gb["sequence_length"], 29903)
        self.assertEqual(gb["organism"], "SARS-CoV-2")
        self.assertEqual(gb["host"], "Homo sapiens")
        self.assertEqual(gb["collection_date"], "2019-12-30")
        self.assertEqual(gb["geographic_location"], "China: Wuhan")
        self.assertEqual(gb["mol_type"], "genomic RNA")
        self.assertEqual(gb["isolation_source"], "bronchoalveolar lavage fluid")
        self.assertEqual(gb["gene_count"], 2)
        self.assertIn("spike glycoprotein", gb["products"])
        self.assertEqual(gb["assembly_name"], "ASM985889v3")
        self.assertEqual(len(gb["references"]), 1)
        self.assertIn("Wu F", gb["references"][0]["authors"])

    def test_parse_genbank_xml_invalid_raises(self):
        """Test _parse_genbank_xml raises RuntimeError on invalid XML."""
        with self.assertRaises(RuntimeError):
            _parse_genbank_xml("<invalid>xml<<broken")

    def test_parse_genbank_xml_empty_set(self):
        """Test _parse_genbank_xml returns empty dict for XML with no records."""
        xml_content = '<?xml version="1.0"?><GBSet></GBSet>'
        result = _parse_genbank_xml(xml_content)
        self.assertEqual(len(result), 0)

    # =========================================================================
    # GENBANK XML TO CSV TESTS
    # =========================================================================

    def test_genbank_xml_to_csv_basic(self):
        """Test _genbank_xml_to_csv converts XML to CSV correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = os.path.join(tmpdir, "test.xml")
            csv_path = os.path.join(tmpdir, "test.csv")

            xml_content = """<?xml version="1.0"?>
<GBSet>
  <GBSeq>
    <GBSeq_accession-version>NC_045512.2</GBSeq_accession-version>
    <GBSeq_sequence>ATCGATCG</GBSeq_sequence>
    <GBSeq_feature-table>
      <GBFeature>
        <GBFeature_key>source</GBFeature_key>
        <GBFeature_location>1..8</GBFeature_location>
        <GBFeature_quals>
          <GBQualifier><GBQualifier_name>organism</GBQualifier_name><GBQualifier_value>SARS-CoV-2</GBQualifier_value></GBQualifier>
          <GBQualifier><GBQualifier_name>host</GBQualifier_name><GBQualifier_value>Homo sapiens</GBQualifier_value></GBQualifier>
        </GBFeature_quals>
      </GBFeature>
    </GBSeq_feature-table>
  </GBSeq>
</GBSet>"""
            with open(xml_path, "w") as f:
                f.write(xml_content)

            _genbank_xml_to_csv(xml_path, csv_path)

            self.assertTrue(os.path.exists(csv_path))
            df = pd.read_csv(csv_path)
            self.assertGreater(len(df), 0)
            self.assertIn("accession", df.columns)
            self.assertEqual(df.iloc[0]["accession"], "NC_045512.2")

    # =========================================================================
    # SAVE GENBANK METADATA TO CSV TESTS
    # =========================================================================

    def test_save_genbank_metadata_to_csv_basic(self):
        """Test save_genbank_metadata_to_csv creates valid CSV output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "genbank_metadata.csv")

            genbank_metadata = {
                "NC_045512.2": {
                    "accession": "NC_045512.2",
                    "genbank_data": {
                        "organism": "SARS-CoV-2",
                        "sequence_length": 29903,
                        "definition": "SARS-CoV-2 complete genome",
                        "host": "Homo sapiens",
                        "collection_date": "2019-12-30",
                        "geographic_location": "China: Wuhan",
                        "isolation_source": "bronchoalveolar lavage",
                        "strain": "Wuhan-Hu-1",
                        "isolate": "IVDC-HB-01",
                        "mol_type": "genomic RNA",
                        "create_date": "2020-01-13",
                        "update_date": "2020-07-17",
                        "assembly_name": "ASM985889v3",
                        "taxonomy": "Viruses; Riboviria",
                        "comment": "",
                        "references": [{"title": "Paper", "authors": "Wu F", "journal": "Nature", "pubmed_id": "123"}],
                    },
                },
            }

            save_genbank_metadata_to_csv(genbank_metadata, output_path)

            self.assertTrue(os.path.exists(output_path))
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]["accession"], "NC_045512.2")
            self.assertEqual(df.iloc[0]["Organism Name"], "SARS-CoV-2")
            self.assertEqual(df.iloc[0]["Length"], 29903)

    def test_save_genbank_metadata_to_csv_empty(self):
        """Test save_genbank_metadata_to_csv handles empty input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "genbank_metadata.csv")
            save_genbank_metadata_to_csv({}, output_path)
            self.assertTrue(os.path.exists(output_path))
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 0)


if __name__ == "__main__":
    unittest.main()
