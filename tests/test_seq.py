import json
import time
import unittest
from unittest.mock import patch

import pandas as pd
from gget.gget_seq import seq

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_seq.json") as json_file:
    seq_dict = json.load(json_file)

# Sleep time in seconds (wait [sleep_time] seconds between server requests to avoid 502 errors for WB and FB IDs)
sleep_time = 10


# todo convert to json loading once wormbase & flybase IDs are fixed. At that point, the json test framework will need a way to handle the ANY values
class TestSeq(unittest.TestCase):
    def test_seq_gene(self):
        test = "test1"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_transcript_gene_WB(self):
        test = "test2"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])
        time.sleep(sleep_time)

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_transcript_transcript_WB(self):
        test = "test3"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])
        time.sleep(sleep_time)

        self.assertListEqual(result_to_test, expected_result)

    # def test_seq_transcript_gene_WB_iso(self):
    #     test = "test4"
    #     expected_result = seq_dict[test]["expected_result"]
    #     result_to_test = seq(**seq_dict[test]["args"])
    #     time.sleep(sleep_time)

    #     self.assertListEqual(result_to_test, expected_result)

    def test_seq_transcript_gene(self):
        test = "test5"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_transcript(self):
        test = "test6"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_gene_iso(self):
        test = "test7"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_gene_transcript_iso(self):
        test = "test8"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_transcript_gene_iso(self):
        test = "test9"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_transcript_transcript_iso(self):
        test = "test10"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)

    def test_seq_missing_uniprot_gene_name(self):
        test = "test11"
        expected_result = seq_dict[test]["expected_result"]
        result_to_test = seq(**seq_dict[test]["args"])

        self.assertListEqual(result_to_test, expected_result)


def _seq_entry(query, sequence, desc="chromosome:GRCh38:17:1:100:1", extra=None):
    """Build a fake Ensembl sequence/id POST entry (as returned before key cleanup)."""
    entry = {
        "query": query,
        "id": query,
        "version": 1,
        "molecule": "dna",
        "seq": sequence,
        "desc": desc,
    }
    if extra is not None:
        entry.update(extra)
    return entry


def _info_df(ensembl_id, object_type, all_transcripts=None, canonical_transcript=None):
    """Build a minimal gget.info-style DataFrame indexed by the queried Ensembl ID."""
    row = {"object_type": [object_type]}
    if all_transcripts is not None:
        row["all_transcripts"] = [all_transcripts]
    if canonical_transcript is not None:
        row["canonical_transcript"] = [canonical_transcript]
    return pd.DataFrame(row, index=[ensembl_id])


class TestSeqTranscriptMocked(unittest.TestCase):
    """Network-free tests for the #187 fix: gget seq must request the spliced cDNA
    (type=cdna) for transcript/ENST IDs instead of the default genomic span.

    All Ensembl/UniProt calls are mocked so these tests are deterministic and offline.
    """

    # ----- non-isoform bulk path (lookup/id -> split cDNA vs genomic) -----

    def test_versioned_transcript_requests_cdna(self):
        """A versioned ENST id (.N) is version-stripped and fetched as cDNA, not genomic."""

        def fake_post_query(server, endpoint, data):
            if endpoint == "lookup/id":
                # The version must already be stripped before lookup
                self.assertEqual(data["ids"], ["ENST00000361390"])
                return {"ENST00000361390": {"object_type": "Transcript"}}
            if endpoint == "sequence/id?type=cdna":
                return [_seq_entry(i, "ATGCDNASPLICED", desc=None) for i in data["ids"]]
            raise AssertionError(f"Unexpected genomic request for a transcript: {endpoint}")

        with patch("gget.gget_seq.post_query", side_effect=fake_post_query) as mock_pq:
            result = seq("ENST00000361390.2", verbose=False)

        endpoints = [call.args[1] for call in mock_pq.call_args_list]
        self.assertIn("sequence/id?type=cdna", endpoints)
        self.assertNotIn("sequence/id", endpoints)  # no genomic request for a transcript
        # desc is None for cDNA responses -> header has no trailing description
        self.assertEqual(result, [">ENST00000361390", "ATGCDNASPLICED"])

    def test_noncoding_transcript_requests_cdna(self):
        """A non-coding (e.g. lincRNA) transcript is handled by the same cDNA path."""

        def fake_post_query(server, endpoint, data):
            if endpoint == "lookup/id":
                return {"ENST00000456328": {"object_type": "Transcript", "biotype": "lncRNA"}}
            if endpoint == "sequence/id?type=cdna":
                return [_seq_entry(i, "NCRNASEQ", desc=None) for i in data["ids"]]
            raise AssertionError(f"Unexpected genomic request for ncRNA transcript: {endpoint}")

        with patch("gget.gget_seq.post_query", side_effect=fake_post_query) as mock_pq:
            result = seq("ENST00000456328", verbose=False)

        endpoints = [call.args[1] for call in mock_pq.call_args_list]
        self.assertIn("sequence/id?type=cdna", endpoints)
        self.assertNotIn("sequence/id", endpoints)
        self.assertEqual(result, [">ENST00000456328", "NCRNASEQ"])

    def test_mixed_gene_and_transcript_batch_splits_requests(self):
        """A single call with a gene + a transcript splits into a genomic and a cDNA request."""
        gene_id = "ENSG00000012048"
        transcript_id = "ENST00000357654"

        cdna_ids = []
        genomic_ids = []

        def fake_post_query(server, endpoint, data):
            if endpoint == "lookup/id":
                return {
                    gene_id: {"object_type": "Gene"},
                    transcript_id: {"object_type": "Transcript"},
                }
            if endpoint == "sequence/id?type=cdna":
                cdna_ids.extend(data["ids"])
                return [_seq_entry(i, "CDNASEQ", desc=None) for i in data["ids"]]
            if endpoint == "sequence/id":
                genomic_ids.extend(data["ids"])
                return [_seq_entry(i, "GENOMICSEQ", desc="chromosome:GRCh38:17") for i in data["ids"]]
            raise AssertionError(endpoint)

        with patch("gget.gget_seq.post_query", side_effect=fake_post_query):
            result = seq([gene_id, transcript_id], verbose=False)

        # The transcript went to the cDNA batch, the gene to the genomic batch
        self.assertEqual(cdna_ids, [transcript_id])
        self.assertEqual(genomic_ids, [gene_id])
        # Both sequences are present, each under its own header
        self.assertIn(">" + transcript_id, result)
        self.assertIn("CDNASEQ", result)
        self.assertIn(">" + gene_id + " chromosome:GRCh38:17", result)
        self.assertIn("GENOMICSEQ", result)

    def test_entry_with_no_desc_builds_header_gracefully(self):
        """An Ensembl cDNA entry lacking a 'desc' field must not break FASTA header building."""

        def fake_post_query(server, endpoint, data):
            if endpoint == "lookup/id":
                return {"ENST00000361390": {"object_type": "Transcript"}}
            if endpoint == "sequence/id?type=cdna":
                # Note: no "desc" key at all (and no version/molecule)
                return [{"query": "ENST00000361390", "id": "ENST00000361390", "seq": "ATGC"}]
            raise AssertionError(endpoint)

        with patch("gget.gget_seq.post_query", side_effect=fake_post_query):
            result = seq("ENST00000361390", verbose=False)

        self.assertEqual(result, [">ENST00000361390", "ATGC"])

    def test_id_absent_from_response_is_skipped_gracefully(self):
        """If Ensembl returns no entry for an ID, it is logged and skipped (no crash, empty FASTA)."""

        def fake_post_query(server, endpoint, data):
            if endpoint == "lookup/id":
                return {"ENST00000361390": {"object_type": "Transcript"}}
            if endpoint == "sequence/id?type=cdna":
                return []  # nothing returned for the requested transcript
            raise AssertionError(endpoint)

        with patch("gget.gget_seq.post_query", side_effect=fake_post_query):
            with self.assertLogs(level="ERROR") as captured:
                result = seq("ENST00000361390", verbose=False)

        self.assertEqual(result, [])
        self.assertTrue(any("ENST00000361390" in line for line in captured.output))

    # ----- isoforms=True path (per-transcript rest_query) -----

    def test_isoforms_gene_requests_cdna_for_each_transcript(self):
        """isoforms=True on a gene fetches each transcript as cDNA via rest_query."""
        gene_id = "ENSG00000012048"
        queries = []

        def fake_rest_query(server, query, content_type):
            queries.append(query)
            tid = query.split("/")[-1].split("?")[0]
            return {"id": tid, "seq": "CDNA_" + tid, "desc": None}

        with (
            patch(
                "gget.gget_seq.info",
                return_value=_info_df(gene_id, "Gene", all_transcripts=["ENST00000357654", "ENST00000352993"]),
            ),
            patch("gget.gget_seq.rest_query", side_effect=fake_rest_query),
        ):
            result = seq(gene_id, isoforms=True, verbose=False)

        # Every transcript was requested as cDNA
        self.assertTrue(queries)
        for q in queries:
            self.assertTrue(q.endswith("?type=cdna"), q)
        self.assertIn(">ENST00000357654", result)
        self.assertIn("CDNA_ENST00000357654", result)
        self.assertIn(">ENST00000352993", result)

    def test_isoforms_transcript_requests_cdna_and_warns(self):
        """isoforms=True on a transcript fetches cDNA and warns that isoforms only apply to genes."""
        transcript_id = "ENST00000357654"
        queries = []

        def fake_rest_query(server, query, content_type):
            queries.append(query)
            return {"id": transcript_id, "seq": "CDNAISO", "desc": None}

        with (
            patch("gget.gget_seq.info", return_value=_info_df(transcript_id, "Transcript")),
            patch("gget.gget_seq.rest_query", side_effect=fake_rest_query),
            self.assertLogs(level="WARNING") as captured,
        ):
            result = seq(transcript_id, isoforms=True, verbose=False)

        self.assertEqual(queries, ["sequence/id/" + transcript_id + "?type=cdna"])
        self.assertEqual(result, [">" + transcript_id, "CDNAISO"])
        self.assertTrue(any("isoform" in line.lower() for line in captured.output))

    # ----- translate=True path (UniProt) -----

    def test_translate_transcript_queries_uniprot(self):
        """translate=True on a transcript queries UniProt with the transcript ID."""
        transcript_id = "ENST00000357654"
        uniprot_df = pd.DataFrame(
            {
                "uniprot_id": ["P38398"],
                "query": [transcript_id],
                "gene_name": ["BRCA1"],
                "organism": ["Homo sapiens"],
                "sequence_length": [3],
                "sequence": ["MEN"],
            }
        )

        with (
            patch("gget.gget_seq.info", return_value=_info_df(transcript_id, "Transcript")),
            patch("gget.gget_seq.get_uniprot_seqs", return_value=uniprot_df) as mock_uniprot,
        ):
            result = seq(transcript_id, translate=True, verbose=False)

        # UniProt queried with the transcript ID
        self.assertEqual(list(mock_uniprot.call_args.args[1]), [transcript_id])
        self.assertEqual(len(result), 2)
        self.assertIn("uniprot_id: P38398", result[0])
        self.assertIn(transcript_id, result[0])
        self.assertEqual(result[1], "MEN")
