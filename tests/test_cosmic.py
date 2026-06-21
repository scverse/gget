import json
import os
import pathlib as pl
import time
import unittest

from gget.gget_cosmic import cosmic

# from gget.utils import get_latest_cosmic
from .from_json import from_json

# COSMIC release
cosmic_version = 104

# Only this combo is used for example testing (no login required)
arg_combinations = [
    ("cancer_example", 37, "CancerMutationCensus_AllData", cosmic_version),
]

# Load dictionary containing arguments and expected results
with open("./tests/fixtures/test_cosmic.json") as json_file:
    cosmic_dict = json.load(json_file)

# Sleep time in seconds (wait between server requests to avoid 429 errors)
sleep_time = 10


class TestCaseBase(unittest.TestCase):
    def assertIsFile(self, path):
        if not pl.Path(path).resolve().is_file():
            raise AssertionError(f"File does not exist: {path}")


class TestCosmicWorkflow(
    TestCaseBase, metaclass=from_json(cosmic_dict, cosmic, pre_test=lambda: time.sleep(sleep_time))
):
    """
    Combined test class to:
    1. Download COSMIC cancer_example data
    2. Run all test cases using from_json
    3. Clean up afterward
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        time.sleep(sleep_time)

        # Download data if it doesn't already exist
        mut_class, grch_version, file_name, version = arg_combinations[0]

        if mut_class == "cancer_example":
            cls.tarred_folder = f"example_GRCh{grch_version}"
        else:
            cls.tarred_folder = f"{file_name}_Tsv_v{version}_GRCh{grch_version}"

        cls.file_name = file_name
        cls.grch_version = grch_version
        cls.cosmic_version = version

        expected_file = os.path.join(cls.tarred_folder, f"{file_name}_v{version}_GRCh{grch_version}.tsv")

        if not os.path.exists(expected_file):
            cosmic(
                searchterm=None,
                download_cosmic=True,
                cosmic_project=mut_class,
                cosmic_version=version,
                grch_version=grch_version,
                gget_mutate=True,
            )

        # Check that files were downloaded correctly
        contained_file = f"{file_name}_v{version}_GRCh{grch_version}.tsv"
        gm_file = f"{file_name}_v{version}_GRCh{grch_version}_mutation_workflow.csv"

        path1 = pl.Path(os.path.abspath(os.path.join(cls.tarred_folder, contained_file)))
        path2 = pl.Path(os.path.abspath(os.path.join(cls.tarred_folder, gm_file)))

        if not path1.is_file() or not path2.is_file():
            raise FileNotFoundError("Expected COSMIC files were not found after download.")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up COSMIC files after all tests have run.
        """
        try:
            os.remove(cls.tarred_folder + ".tar")
        except FileNotFoundError:
            pass

        if os.path.exists(cls.tarred_folder):
            for root, dirs, files in os.walk(cls.tarred_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(cls.tarred_folder)

        super().tearDownClass()
