# Testing structure

Functions for each test type are defined in [from_json.py](https://github.com/scverse/gget/blob/main/tests/from_json.py), which are called in the individual \<module>.py files.

Arguments, expected results, and test type are defined for each module in the \<module>.json dictionaries in [/fixtures](https://github.com/scverse/gget/tree/main/tests/fixtures).

Run tests locally using `coverage run -m pytest -ra -v tests && coverage report --omit=main.py,tests*`
