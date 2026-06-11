from __future__ import annotations

import unittest

unittest.TestCase.maxDiff = 10_000

# from typing import Callable, Any, Optional, Union
import hashlib  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import sys  # noqa: E402

import pandas as pd  # noqa: E402

# Here's a question: how many errors does Copilot know? Answer: see below.
_KNOWN_ERRORS = {
    "ValueError": ValueError,
    "RuntimeError": RuntimeError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "AssertionError": AssertionError,
    "AttributeError": AttributeError,
    "NotImplementedError": NotImplementedError,
    "FileNotFoundError": FileNotFoundError,
    "IndexError": IndexError,
    "OSError": OSError,
    "PermissionError": PermissionError,
    "ConnectionError": ConnectionError,
    "TimeoutError": TimeoutError,
    "RecursionError": RecursionError,
    "OverflowError": OverflowError,
    "ZeroDivisionError": ZeroDivisionError,
    "ArithmeticError": ArithmeticError,
    "ImportError": ImportError,
    "ModuleNotFoundError": ModuleNotFoundError,
    "NameError": NameError,
    "SyntaxError": SyntaxError,
    "IndentationError": IndentationError,
    "TabError": TabError,
    "SystemError": SystemError,
    "SystemExit": SystemExit,
    "KeyboardInterrupt": KeyboardInterrupt,
    "GeneratorExit": GeneratorExit,
    "StopIteration": StopIteration,
    "MemoryError": MemoryError,
    "BufferError": BufferError,
    "LookupError": LookupError,
    "EnvironmentError": EnvironmentError,
    "IOError": IOError,
    "BlockingIOError": BlockingIOError,
    "ChildProcessError": ChildProcessError,
    "BrokenPipeError": BrokenPipeError,
    "ConnectionAbortedError": ConnectionAbortedError,
    "ConnectionRefusedError": ConnectionRefusedError,
}


def do_call(func, args):
    if isinstance(args, dict):
        return func(**args)
    return func(*args)


def _assert_equal(name, td, func):
    def assert_equal(self: unittest.TestCase):
        test = name
        expected_result = td[test]["expected_result"]
        result_to_test = do_call(func, td[test]["args"])
        if test == "test_cosmic_defaults":  # special case for cosmic
            import numpy as np

            expected_result = pd.DataFrame(expected_result[0])
            expected_result = expected_result.replace({None: np.nan})
            # result_to_test.equals(expected_result)
            pd.testing.assert_frame_equal(result_to_test, expected_result, check_dtype=False)
            return

        # If result is a DataFrame, convert to list
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = result_to_test.dropna(axis=1).values.tolist()

        self.assertEqual(result_to_test, expected_result)

    return assert_equal


def _assert_equal_na(name, td, func):
    def assert_equal_na(self: unittest.TestCase):
        test = name
        expected_result = td[test]["expected_result"]
        result_to_test = do_call(func, td[test]["args"])
        # If result is a DataFrame, convert to list
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = result_to_test.values.tolist()

        self.assertEqual(result_to_test, expected_result)

    return assert_equal_na


def _assert_none(name, td, func):
    def assert_none(self: unittest.TestCase):
        test = name
        expected_result = td[test].get("expected_result", None)
        msg = td[test].get("msg", None)
        expected_log = td[test].get("expected_log", None)

        self.assertIsNone(
            expected_result,
            "assert_none test must not have a non-null expected_result key.",
        )

        if expected_log is not None:
            # Captures logs across all loggers, so the function under test
            # cannot silently return None for the wrong reason (e.g. a
            # rate-limited HTML response from an upstream API).
            with self.assertLogs(level=logging.DEBUG) as captured:
                result_to_test = do_call(func, td[test]["args"])
            joined = "\n".join(captured.output)
            self.assertIn(
                expected_log,
                joined,
                msg=(f"Expected log substring {expected_log!r} not found. Captured: {joined}"),
            )
        else:
            result_to_test = do_call(func, td[test]["args"])

        self.assertIsNone(result_to_test, msg=msg)

    return assert_none


def _assert_equal_json_hash(name, td, func):
    def assert_equal_json_hash(self: unittest.TestCase):
        test = name
        expected_result = td[test]["expected_result"]
        result_to_test = do_call(func, td[test]["args"])
        # If result is a DataFrame, convert to list
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = result_to_test.dropna(axis=1).values.tolist()

        result_to_test = json.dumps(result_to_test)
        result_to_test = hashlib.md5(result_to_test.encode()).hexdigest()

        self.assertEqual(result_to_test, expected_result)

    return assert_equal_json_hash


def _assert_equal_nested(name, td, func):
    def assert_equal_nested(self: unittest.TestCase):
        test = name
        expected_result = td[test]["expected_result"]
        result_to_test = do_call(func, td[test]["args"])
        # If result is a DataFrame, convert to json (nested dataframes prevent easy listification)
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = json.loads(result_to_test.to_json(orient="records", force_ascii=False))

        self.assertEqual(result_to_test, expected_result)

    return assert_equal_nested


def _assert_equal_json_hash_nested(name, td, func):
    def assert_equal_json_hash_nested(self: unittest.TestCase):
        test = name
        expected_result = td[test]["expected_result"]
        result_to_test = do_call(func, td[test]["args"])
        # If result is a DataFrame, convert to json (nested dataframes prevent easy listification)
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = json.loads(result_to_test.to_json(orient="records", force_ascii=False))

        result_to_test = json.dumps(result_to_test)
        result_to_test = hashlib.md5(result_to_test.encode()).hexdigest()

        self.assertEqual(result_to_test, expected_result)

    return assert_equal_json_hash_nested


def _assert_equal_json_with_keys(name, td, func):
    def assert_equal_json_with_keys(self: unittest.TestCase):
        def normalize(x):
            if isinstance(x, tuple):
                x = [normalize(v) for v in x]

            if isinstance(x, list):
                x = [normalize(v) for v in x]

                # Detect list-of-pairs -> dict recursively.
                if all(isinstance(i, list) and len(i) == 2 for i in x):
                    try:
                        x = {i[0]: i[1] for i in x}
                    except Exception:  # noqa: BLE001
                        try:
                            x = {i[1]: i[0] for i in x}
                        except Exception:  # noqa: BLE001
                            pass

                # Collapse singleton wrappers such as:
                # [{"drug": {...}}] -> {"drug": {...}}
                # ["26387812"] -> "26387812"
                if isinstance(x, list) and len(x) == 1:
                    return normalize(x[0])

            if isinstance(x, dict):
                x = {k: normalize(v) for k, v in x.items()}

                # Collapse single-key wrapper dicts such as:
                # {"drug": {...}} -> {...}
                # {"drug": None} -> None
                if len(x) == 1:
                    return normalize(next(iter(x.values())))

                return x

            return x

        test = name

        expected_result = td[test]["expected_result"]
        result_to_test = do_call(func, td[test]["args"])
        if isinstance(result_to_test, pd.DataFrame):
            result_to_test = json.loads(
                result_to_test.dropna(axis=1, how="all").to_json(orient="records", force_ascii=False)
            )

        result_to_test = normalize(result_to_test)
        expected_result = normalize(expected_result)

        # ✅ Infer keys from expected_result
        if not expected_result:
            raise ValueError(f"Test {test} has empty expected_result")

        keys = list(expected_result[0].keys())

        # Convert list-of-lists → list-of-dicts
        if isinstance(result_to_test, list) and len(result_to_test) > 0 and isinstance(result_to_test[0], list):
            result_to_test = [dict(zip(keys, row, strict=False)) for row in result_to_test]

        # Optional: float rounding
        def round_dict(d, ndigits=10):
            return {k: round(v, ndigits) if isinstance(v, float) else v for k, v in d.items()}

        result_to_test = [round_dict(r) for r in result_to_test]
        expected_result = [round_dict(r) for r in expected_result]

        self.assertEqual(result_to_test, expected_result)

    return assert_equal_json_with_keys


def _error(name, td, func):
    try:
        # noinspection PyPep8Naming
        Error = td[name]["expected_result"]
    except KeyError:
        raise ValueError("Error test must have an 'expected_result' key.") from None

    if Error not in _KNOWN_ERRORS:
        raise ValueError(f"Unknown error type: {Error}")

    # noinspection PyPep8Naming
    Error = _KNOWN_ERRORS[Error]

    if "expected_msg" not in td[name]:
        print(f"^ Warning: 'error' test should have an 'expected_msg' key, but test '{name}' lacks one.")

    def error(self: unittest.TestCase):
        test = name
        with self.assertRaises(Error) as cm:
            do_call(func, td[test]["args"])
        the_exception = cm.exception

        if "expected_msg" in td[test]:
            self.assertEqual(td[test]["expected_msg"], str(the_exception), "Error message mismatch")

    return error


# _test_constructor = Callable[[str, dict[str, dict[str, ...]], Callable], Callable]
_TYPES = {
    "assert_equal": _assert_equal,
    "assert_equal_na": _assert_equal_na,
    "assert_none": _assert_none,
    "assert_equal_json_hash": _assert_equal_json_hash,
    "assert_equal_nested": _assert_equal_nested,
    "assert_equal_json_hash_nested": _assert_equal_json_hash_nested,
    "assert_equal_json_with_keys": _assert_equal_json_with_keys,
    "error": _error,
}


def from_json(
    test_dict,
    func,
    custom_types=None,
    pre_test=None,
):
    """
    Create a metaclass that will generate test methods from a (json-loaded) dictionary.
    """

    local_types = _TYPES.copy()
    if custom_types:
        local_types.update(custom_types)

    class C(type):
        def __new__(cls, name, bases, dct):
            # assert (
            #     unittest.TestCase in bases
            # ), "from_json should only be applied to unittest.TestCase subclasses."
            for k, v in test_dict.items():
                type_ = v["type"]
                if type_ == "code_defined":
                    if k not in dct:
                        raise ValueError(f"Test {k} is not defined in code, despite being of type 'code_defined'.")
                    continue
                if type_ in local_types:
                    if not k.startswith("test_"):
                        print(f"Invalid test name: {k}", file=sys.stderr)
                        continue

                    if k in dct:
                        print(f"Duplicate test name: {k}", file=sys.stderr)
                        continue

                    # Create the test method for the given type and add it to the new class
                    test_func = local_types[type_](k, test_dict, func)
                    if pre_test:
                        # This has to be done with nested functions to actually close on `test_func`.
                        # Otherwise, it just becomes a recursive mess
                        def wrap(tf):
                            def inner(*args, **kwargs):
                                pre_test()
                                tf(*args, **kwargs)

                            return inner

                        test_func = wrap(test_func)

                    dct[k] = test_func
                    print(f"Loaded test {k} of type {type_} from json.")
                else:
                    if k not in dct:
                        raise ValueError(f"Unknown test type: {type_} and no test method defined.")
                    print(f"Unknown test type: {type_}", file=sys.stderr)

            return super().__new__(cls, name, bases, dct)

    return C
