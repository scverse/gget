import json
import os
import unittest

from gget.gget_cbio import cbio_search, download_cbioportal_data

from .from_json import do_call, from_json

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_cbio_search.json") as json_file:
    cb_search_dict = json.load(json_file)

with open("./tests/fixtures/test_cbio.json") as json_file:
    cb_dict = json.load(json_file)


class TestCbioSearch(unittest.TestCase, metaclass=from_json(cb_search_dict, cbio_search)):
    pass  # all tests are loaded from json


def _cbio_download(name: str, td, func):
    def cbio_download(self: unittest.TestCase):
        test = name
        expected_result = td[test]["expected_result"]

        if not isinstance(expected_result, dict) and not isinstance(expected_result, bool):
            raise ValueError("Expected result must be a dictionary or a boolean")

        result = do_call(func, td[test]["args"])

        if isinstance(expected_result, dict):
            # # check that all files downloaded
            # self.assertTrue(result)

            for file_name, _expected_hash in expected_result.items():
                if os.path.exists(file_name):
                    # # check non-empty
                    if os.path.getsize(file_name) == 0:
                        self.fail(f"File {file_name} is empty")
                    # # check md5 hash
                    # with open(file_name, "rb") as f:
                    #     file_content = f.read()
                    #     file_hash = hashlib.md5(file_content).hexdigest()
                    #     self.assertEqual(
                    #         file_hash,
                    #         expected_hash,
                    #         f"File {file_name} does not match expected hash",
                    #     )
        else:
            self.assertFalse(result)

    return cbio_download


class TestCbio(
    unittest.TestCase,
    metaclass=from_json(cb_dict, download_cbioportal_data, {"cbio_download": _cbio_download}),
):
    pass  # all tests are loaded from json
