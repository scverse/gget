import unittest
from unittest.mock import patch

import pandas as pd
from gget.gget_search import search


class TestSearchParameters(unittest.TestCase):
    def test_search_binds_searchword_for_genes_and_transcripts(self):
        searchword = "O'Neil"
        results = pd.DataFrame(
            {
                "ensembl_id": ["ENSG00000000001"],
                "gene_name": ["example"],
                "ensembl_description": ["example description"],
                "ext_ref_description": [None],
                "biotype": ["protein_coding"],
                "synonym": [None],
            }
        )

        for id_type in ("gene", "transcript"):
            with (
                self.subTest(id_type=id_type),
                patch("gget.gget_search.sql.connect"),
                patch("gget.gget_search.pd.read_sql", return_value=results) as read_sql,
                patch("gget.gget_search.find_latest_ens_rel", return_value=110),
                patch("gget.gget_search.find_nv_kingdom", return_value=None),
            ):
                search(searchword, "drosophila_melanogaster_core_110_10", id_type=id_type, verbose=False)

                query = read_sql.call_args.args[0]
                self.assertEqual(read_sql.call_args.kwargs["params"], [f"%{searchword}%"] * 5)
                self.assertEqual(query.count("LIKE %s"), 5)
                self.assertNotIn(searchword, query)


if __name__ == "__main__":
    unittest.main()
