import contextlib
import os
import unittest

# Used here to mock different operating systems
from unittest.mock import MagicMock, patch

from gget.compile import compile_muscle

# Get absolute package path
PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))


class TestCompilerWindows(unittest.TestCase):
    def test_compiler_windows(self):
        with self.assertRaises(OSError):
            # Using magic mock to mimick OS
            with patch("platform.system", MagicMock(return_value="Windows")):
                # Using contextlib to silence stdout
                with contextlib.redirect_stdout(open(os.devnull, "w")):
                    compile_muscle()


## The make command requires different programs for each OS, so these tests do not work universally
# class TestCompilerLinux(unittest.TestCase):
#     def test_compiler_linux(self):
#         with patch("platform.system", MagicMock(return_value="Linux")):
#             with contextlib.redirect_stdout(open(os.devnull, "w")):
#                 compile_muscle()
#         # Assert that muscle binary was created
#         PATH = os.path.join(PACKAGE_PATH, "bins/compiled/muscle/src/Linux/muscle")

#         # Assert that muscle binary was created and is readable
#         self.assertTrue(os.path.isfile(PATH) and os.access(PATH, os.R_OK))

#     def tearDown(self):
#         super(TestCompilerLinux, self).tearDown()
#         # Delete created compiled folder
#         shutil.rmtree(os.path.join(PACKAGE_PATH, "bins/compiled"))


# class TestCompilerDarwin(unittest.TestCase):
#     def test_compiler_linux(self):
#         with patch("platform.system", MagicMock(return_value="Darwin")):
#             with contextlib.redirect_stdout(open(os.devnull, "w")):
#                 compile_muscle()
#         # Assert that muscle binary was created
#         PATH = os.path.join(PACKAGE_PATH, "bins/compiled/muscle/src/Darwin/muscle")

#         # Assert that muscle binary was created and is readable
#         self.assertTrue(os.path.isfile(PATH) and os.access(PATH, os.R_OK))

#     def tearDown(self):
#         super(TestCompilerDarwin, self).tearDown()
#         # Delete created compiled folder
#         shutil.rmtree(os.path.join(PACKAGE_PATH, "bins/compiled"))
