import os
import platform
import subprocess
import sys

from .constants import MUSCLE_GITHUB_LINK
from .utils import set_up_logger

logger = set_up_logger()

# Get absolute package path
PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))
# Path to muscle binary (only exists after 'compile_muscle' was executed)
MUSCLE_PATH = os.path.join(PACKAGE_PATH, f"bins/compiled/muscle/src/{platform.system()}/muscle")


def compile_muscle():
    """Compiles MUSCLE from source.

    Currently only supports Linux and Darwin.
    """
    if platform.system() != "Linux" and platform.system() != "Darwin":
        raise OSError(f"Muscle compiler currently only supports Linux and Darwin, not {platform.system()}.\n")

    logger.info("Compiling MUSCLE binary from source... ")

    # Record current working directory
    cwd = os.getcwd()

    # Change path to package path
    os.chdir(PACKAGE_PATH)
    # Create folders 'bins/compiled/' inside gget package
    os.makedirs("bins/compiled/", exist_ok=True)
    # Change path to PACKAGE_PATH/bins/compiled/
    os.chdir("bins/compiled/")

    # Clone MUSCLE repo into PACKAGE_PATH/bins/compiled/
    command1 = "git clone " + MUSCLE_GITHUB_LINK + " -q"

    with subprocess.Popen(command1, shell=True, stderr=subprocess.PIPE) as process_1:
        stderr_1 = process_1.stderr.read().decode("utf-8")
        # Log the standard error if it is not empty
        if stderr_1:
            sys.stderr.write(stderr_1)
    # Exit system if the subprocess returned with an error
    if process_1.wait() != 0:
        sys.exit(f"'{command1}' command returned with error {process_1.wait()}.")

    # Change path to PACKAGE_PATH/bins/compiled/muscle/src/
    os.chdir("muscle/src/")

    # Run make command
    if platform.system() == "Linux":
        logger.warning("Compiling MUSCLE requires that g++, make, sed and git are installed.")
    if platform.system() == "Darwin":
        logger.warning("Compiling MUSCLE requires that gcc v11, make, sed and git are installed.")
        logger.warning("Please run 'brew install gcc' to install gcc v11 if the compile fails.")

    command2 = "make -s"

    with subprocess.Popen(command2, shell=True, stderr=subprocess.PIPE) as process_2:
        stderr_2 = process_2.stderr.read().decode("utf-8")
        # Log the standard error if it is not empty
        if stderr_2:
            sys.stderr.write(stderr_2)
    # Exit system if the subprocess returned with an error
    if process_2.wait() != 0:
        sys.exit(f"'{command2}' command returned with error {process_2.wait()}.")

    logger.info("MUSCLE compiled.")

    # Change path back to cwd
    os.chdir(cwd)
