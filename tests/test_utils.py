import unittest
import numpy as np
from gget.utils import (
    n_colors,
    aa_colors,
    get_uniprot_seqs,
    get_uniprot_info,
    rest_query,
    find_latest_ens_rel,
    search_species_options,
    ref_species_options,
    read_fasta,
)

from gget.constants import UNIPROT_REST_API, ENSEMBL_REST_API, ENSEMBL_FTP_URL_NV

from .fixtures import (
    LATEST_ENS_RELEASE,
    SPECIES_OPTIONS,
    IV_SPECIES_OPTIONS,
    REF_SPECIES_OPTIONS,
    REF_IV_SPECIES_OPTIONS,
)


class TestUtils(unittest.TestCase):
    def test_read_fasta(self):
        result_to_test1, result_to_test2 = read_fasta(
            "tests/fixtures/muscle_nt_test.fa"
        )
        result_to_test = result_to_test1 + result_to_test2

        expected_result1 = [
            "ENSTGUT00000006367 primary_assembly:bTaeGut1_v1.p:1:107513786:107528106:-1",
            "ENSTGUT00000027003 primary_assembly:bTaeGut1_v1.p:1:107513786:107526965:-1",
        ]
        expected_result2 = [
            "TAGTTGTGATACTGGTCAGTGTCACTGGGGCTGTTTCACCCTGTCATTTGAAGACTTCCATTT",
            "CTTTGTTGGAGGCTTTTTGCTGGGGCTGGCGTCGTAAGGACCCGAACATCTCTTCCAGATGGGAT",
        ]
        expected_result = expected_result1 + expected_result2

        self.assertEqual(result_to_test, expected_result)

    def test_n_colors(self):
        result_to_test = n_colors("A")
        expected_result = "\x1b[38;5;15m\x1b[48;5;9mA\x1b[0;0m"

        self.assertEqual(result_to_test, expected_result)

    def test_aa_colors(self):
        result_to_test = aa_colors("L")
        expected_result = "\x1b[38;5;15m\x1b[48;5;12mL\x1b[0;0m"

        self.assertEqual(result_to_test, expected_result)

    def test_get_uniprot_seqs(self):
        df = get_uniprot_seqs(
            UNIPROT_REST_API, ["ENST00000392653.3", "ENST00000392657.7"]
        )
        result_to_test = df.values.tolist()
        expected_result = [
            [
                "P35326",
                "Homo sapiens",
                "MSYQQQQCKQPCQPPPVCPTPKCPEPCPPPKCPEPCPPPKCPQPCPPQQCQQKYPPVTPSPPCQSKYPPKSK",
                72,
                "SPRR2A",
                "ENST00000392653.3",
            ],
            [
                "A7KAX9",
                "Homo sapiens",
                "METESESSTLGDDSVFWLESEVIIQVTDCEEEEREEKFRKMKSSVHSEEDDFVPELHRNVHPRERPDWEETLSAMARGADVPEIPGDLTLKTCGSTASMKVKHVKKLPFTKGHFPKMAECAHFHYENVEFGSIQLSLSEEQNEVMKNGCESKELVYLVQIACQGKSWIVKRSYEDFRVLDKHLHLCIYDRRFSQLSELPRSDTLKDSPESVTQMLMAYLSRLSAIAGNKINCGPALTWMEIDNKGNHLLVHEESSINTPAVGAAHVIKRYTARAPDELTLEVGDIVSVIDMPPKVLSTWWRGKHGFQVGLFPGHCVELINQKVPQSVTNSVPKPVSKKHGKLITFLRTFMKSRPTKQKLKQRGILKERVFGCDLGEHLLNSGFEVPQVLQSCTAFIERYGIVDGIYRLSGVASNIQRLRHEFDSEHVPDLTKEPYVQDIHSVGSLCKLYFRELPNPLLTYQLYEKFSDAVSAATDEERLIKIHDVIQQLPPPHYRTLEFLMRHLSLLADYCSITNMHAKNLAIVWAPNLLRSKQIESACFSGTAAFMEVRIQSVVVEFILNHVDVLFSGRISMAMQEGAASLSRPKSLLVSSPSTKLLTLEEAQARTQAQVNSPIVTENKYIEVGEGPAALQGKFHTIIEFPLERKRPQNKMKKSPVGSWRSFFNLGKSSSVSKRKLQRNESEPSEMKAMALKGGRAEGTLRSAKSEESLTSLHAVDGDSKLFRPRRPRSSSDALSASFNGEMLGNRCNSYDNLPHDNESEEEGGLLHIPALMSPHSAEDVDLSPPDIGVASLDFDPMSFQCSPPKAESECLESGASFLDSPGYSKDKPSANKKDAETGSSQCQTPGSTASSEPVSPLQEKLSPFFTLDLSPTEDKSSKPSSFTEKVVYAFSPKIGRKLSKSPSMSISEPISVTLPPRVSEVIGTVSNTTAQNASSSTWDKCVEERDATNRSPTQIVKMKTNETVAQEAYESEVQPLDQVAAEEVELPGKEDQSVSSSQSKAVASGQTQTGAVTHDPPQDSVPVSSVSLIPPPPPPKNVARMLALALAESAQQASTQSLKRPGTSQAGYTNYGDIAVATTEDNLSSSYSAVALDKAYFQTDRPAEQFHLQNNAPGNCDHPLPETTATGDPTHSNTTESGEQHHQVDLTGNQPHQAYLSGDPEKARITSVPLDSEKSDDHVSFPEDQSGKNSMPTVSFLDQDQSPPRFYSGDQPPSYLGASVDKLHHPLEFADKSPTPPNLPSDKIYPPSGSPEENTSTATMTYMTTTPATAQMSTKEASWDVAEQPTTADFAAATLQRTHRTNRPLPPPPSQRSAEQPPVVGQVQAATNIGLNNSHKVQGVVPVPERPPEPRAMDDPASAFISDSGAAAAQCPMATAVQPGLPEKVRDGARVPLLHLRAESVPAHPCGFPAPLPPTRMMESKMIAAIHSSSADATSSSNYHSFVTASSTSVDDALPLPLPVPQPKHASQKTVYSSFARPDVTTEPFGPDNCLHFNMTPNCQYRPQSVPPHHNKLEQHQVYGARSEPPASMGLRYNTYVAPGRNASGHHSKPCSRVEYVSSLSSSVRNTCYPEDIPPYPTIRRVQSLHAPPSSMIRSVPISRTEVPPDDEPAYCPRPLYQYKPYQSSQARSDYHVTQLQPYFENGRVHYRYSPYSSSSSSYYSPDGALCDVDAYGTVQLRPLHRLPNRDFAFYNPRLQGKSLYSYAGLAPRPRANVTGYFSPNDHNVVSMPPAADVKHTYTSWDLEDMEKYRMQSIRRESRARQKVKGPVMSQYDNMTPAVQDDLGGIYVIHLRSKSDPGKTGLLSVAEGKESRHAAKAISPEGEDRFYRRHPEAEMDRAHHHGGHGSTQPEKPSLPQKQSSLRSRKLPDMGCSLPEHRAHQEASHRQFCESKNGPPYPQGAGQLDYGSKGIPDTSEPVSYHNSGVKYAASGQESLRLNHKEVRLSKEMERPWVRQPSAPEKHSRDCYKEEEHLTQSIVPPPKPERSHSLKLHHTQNVERDPSVLYQYQPHGKRQSSVTVVSQYDNLEDYHSLPQHQRGVFGGGGMGTYVPPGFPHPQSRTYATALGQGAFLPAELSLQHPETQIHAE",
                2087,
                "ARHGAP32",
                "ENST00000392657.7",
            ],
        ]

        self.assertListEqual(result_to_test, expected_result)

    def test_get_uniprot_info_gene(self):
        df = get_uniprot_info(UNIPROT_REST_API, "ENSG00000187140")
        result_to_test = df.values.tolist()
        expected_result = [
            [
                "Q9UJU5",
                "FOXD3",
                ["HFH2"],
                "Forkhead box protein D3",
                "Binds to the consensus sequence 5'-A[AT]T[AG]TTTGTTT-3' and acts as a transcriptional repressor (PubMed:11891324). Also acts as a transcriptional activator (PubMed:11891324). Negatively regulates transcription of transcriptional repressor RHIT/ZNF205 (PubMed:22306510). Promotes development of neural crest cells from neural tube progenitors (PubMed:11891324). Restricts neural progenitor cells to the neural crest lineage while suppressing interneuron differentiation (PubMed:11891324). Required for maintenance of pluripotent cells in the pre-implantation and peri-implantation stages of embryogenesis (PubMed:11891324)",
                ["Nucleus"],
                "ENSG00000187140",
            ],
        ]

        self.assertListEqual(result_to_test, expected_result)

    def test_get_uniprot_info_transcript(self):
        df = get_uniprot_info(
            UNIPROT_REST_API,
            "ENST00000325404.3",
        )
        result_to_test = df.values.tolist()
        expected_result = [
            [
                "P48431",
                "SOX2",
                [unittest.mock.ANY],
                "Transcription factor SOX-2",
                "Transcription factor that forms a trimeric complex with OCT4 on DNA and controls the expression of a number of genes involved in embryonic development such as YES1, FGF4, UTF1 and ZFP206 (By similarity). Binds to the proximal enhancer region of NANOG (By similarity). Critical for early embryogenesis and for embryonic stem cell pluripotency (PubMed:18035408). Downstream SRRT target that mediates the promotion of neural stem cell self-renewal (By similarity). Keeps neural cells undifferentiated by counteracting the activity of proneural proteins and suppresses neuronal differentiation (By similarity). May function as a switch in neuronal development (By similarity)",
                ["Nucleus speckle", "Cytoplasm", "Nucleus"],
                "ENST00000325404.3",
            ]
        ]

        self.assertListEqual(result_to_test, expected_result)

    def test_rest_query(self):
        server = ENSEMBL_REST_API
        content_type = "application/json"
        ensembl_ID = "ENSPFOG00000009362"
        query = "lookup/id/" + ensembl_ID + "?"
        result_to_test = rest_query(server, query, content_type)
        expected_result = {
            "source": "ensembl",
            "id": "ENSPFOG00000009362",
            "db_type": "core",
            "species": "poecilia_formosa",
            "canonical_transcript": "ENSPFOT00000009352.1",
            "end": 504269,
            "logic_name": "ensembl",
            "version": 1,
            "strand": 1,
            "biotype": "protein_coding",
            "assembly_name": "PoeFor_5.1.2",
            "object_type": "Gene",
            "start": 502511,
            "seq_region_name": "KI519928.1",
        }

        self.assertEqual(result_to_test, expected_result)

    def test_rest_query_bad_type(self):
        server = ENSEMBL_REST_API
        content_type = "application/json"
        ensembl_ID = "banana"
        query = "lookup/id/" + ensembl_ID + "?"
        with self.assertRaises(RuntimeError):
            rest_query(server, query, content_type)

    def test_find_latest_ens_rel(self):
        result_to_test = find_latest_ens_rel()
        expected_result = LATEST_ENS_RELEASE

        self.assertEqual(result_to_test, expected_result)

    def test_search_species_options(self):
        result_to_test = search_species_options(release=106)
        expected_result = SPECIES_OPTIONS

        self.assertEqual(result_to_test, expected_result)

    def test_search_iv_species_options(self):
        result_to_test = search_species_options(database=ENSEMBL_FTP_URL_NV, release=57)
        expected_result = IV_SPECIES_OPTIONS

        self.assertEqual(result_to_test, expected_result)

    def test_search_species_options_bad_type(self):
        with self.assertRaises(RuntimeError):
            search_species_options(release=2000)

    def test_ref_species_options(self):
        result_to_test = ref_species_options("gtf", release=105)
        expected_result = REF_SPECIES_OPTIONS

        self.assertEqual(result_to_test, expected_result)

    def test_ref_iv_species_options(self):
        result_to_test = ref_species_options(
            database=ENSEMBL_FTP_URL_NV, which="dna", release=55
        )
        expected_result = REF_IV_SPECIES_OPTIONS

        self.assertEqual(result_to_test, expected_result)

    def test_ref_species_options_bad_type(self):
        with self.assertRaises(RuntimeError):
            ref_species_options("gtf", release=2000)
