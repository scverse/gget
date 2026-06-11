import os
import logging
import shutil
import sys
import subprocess
import platform
import uuid
import tempfile
import pathlib
import importlib

from .utils import set_up_logger, check_file_for_error_message

logger = set_up_logger()

from .compile import PACKAGE_PATH
from .constants import (
    ELM_INSTANCES_FASTA_DOWNLOAD,
    ELM_CLASSES_TSV_DOWNLOAD,
    ELM_INSTANCES_TSV_DOWNLOAD,
    ELM_INTDOMAINS_TSV_DOWNLOAD,
)

## Variables for elm module
ELM_FILES = os.path.join(PACKAGE_PATH, "elm_files")
ELM_INSTANCES_FASTA = os.path.join(ELM_FILES, "elm_instances.fasta")
ELM_CLASSES_TSV = os.path.join(ELM_FILES, "elms_classes.tsv")
ELM_INSTANCES_TSV = os.path.join(ELM_FILES, "elm_instances.tsv")
ELM_INTDOMAINS_TSV = os.path.join(ELM_FILES, "elm_interaction_domains.tsv")

## Variables for alphafold module
ALPHAFOLD_GIT_REPO = "https://github.com/deepmind/alphafold"
ALPHAFOLD_GIT_REPO_VERSION = "main"  # Get version currently hosted on main branch
PDBFIXER_GIT_REPO = "https://github.com/openmm/pdbfixer.git"
# Unique ID to name temporary jackhmmer folder
UUID = "fcb45c67-8b27-4156-bbd8-9d11512babf2"
# # Path to temporary mounted disk (global)
# TMP_DISK = ""
# Model parameters
PARAMS_URL = (
    "https://storage.googleapis.com/alphafold/alphafold_params_colab_2022-12-06.tar"
)
PARAMS_DIR = os.path.join(PACKAGE_PATH, "bins/alphafold/")
PARAMS_PATH = os.path.join(PARAMS_DIR, "params_temp.tar")


def _install(package: str, import_name: str, verbose: bool = True):
    # Build list of installer commands to try (uv first if available, then pip)
    pip_cmds = []
    if shutil.which("uv"):
        pip_cmds.append(["uv", "pip", "install", "-U", package])
    pip_cmds.append([sys.executable, "-m", "pip", "install", "-q", "-U", package])

    for cmd in pip_cmds:
        cmd_str = " ".join(cmd)
        if verbose:
            logger.info(f"Attempting to install {package} using: {cmd_str}")
        with subprocess.Popen(cmd, stderr=subprocess.PIPE) as process:
            stderr = process.stderr.read().decode("utf-8")
        if process.wait() != 0:
            if stderr:
                sys.stderr.write(stderr)
            logger.error(
                f"{package} installation with '{cmd_str}' (https://pypi.org/project/{package}) failed."
            )
            if cmd == pip_cmds[-1]:
                logger.error(f"All installation attempts for {package} have failed. Note: Some dependencies (e.g., cellxgene-census) may not support the latest Python versions. If you encounter installation errors, try using an earlier Python version.")
                return
            else:
                if verbose:
                    logger.info(f"Retrying installation of {package} with next available installer.")
                continue
        # Test installation
        try:
            importlib.import_module(import_name)
            if verbose:
                logger.info(f"{import_name} installed successfully using {cmd_str}.")
            return
        except ImportError as e:
            logger.error(
                f"{package} installation with '{cmd_str}' (https://pypi.org/project/{package}) failed. Import error:\n{e}"
            )
            # Retry with pip if import after uv installation failed
            if cmd == pip_cmds[-1]:
                logger.error(f"All installation attempts for {package} have failed. Note: Some dependencies (e.g., cellxgene-census) may not support the latest Python versions. If you encounter installation errors, try using an earlier Python version.")
                return
            else:
                if verbose:
                    logger.info(f"Retrying installation of {package} with next available installer.")
                continue


def setup(module, verbose=True, out=None):
    """
    Function to install third-party dependencies for a specified gget module.
    Some modules require pip to be installed (https://pip.pypa.io/en/stable/installation).
    Some modules require curl to be installed (https://everything.curl.dev/get).

    Args:
    - module    (str) gget module for which dependencies should be installed, e.g. "alphafold", "cellxgene", "elm", "gpt", or "cbio".
    - verbose   True/False whether to print progress information. Default True.
    - out       (str) Path to directory to save downloaded files in (currently only applies when module='elm').
                NOTE: Do not use this argument when downloading the files for use with 'gget.elm'.
                Default None (files are saved in the gget installation directory).
    """
    supported_modules = ["alphafold", "cellxgene", "elm", "gpt", "cbio"]
    if module not in supported_modules:
        raise ValueError(
            f"'module' argument specified as {module}. Expected one of: {', '.join(supported_modules)}"
        )

    if module == "gpt":
        _install("openai<=0.28.1", "openai", verbose=verbose)

    elif module == "cellxgene":
        _install("cellxgene-census", "cellxgene_census", verbose=verbose)

    elif module == "elm":
        if verbose:
            logger.info(
                "ELM data can be downloaded & distributed for non-commercial use according to the following license: http://elm.eu.org/media/Elm_academic_license.pdf"
            )
            logger.info(
                "Downloading ELM database files (requires curl to be installed)..."
            )

        if out is not None:
            elm_files_out = os.path.abspath(out)
            elm_instances_fasta = os.path.join(elm_files_out, "elm_instances.fasta")
            elm_classes_tsv = os.path.join(elm_files_out, "elms_classes.tsv")
            elm_instances_tsv = os.path.join(elm_files_out, "elm_instances.tsv")
            elm_intdomains_tsv = os.path.join(
                elm_files_out, "elm_interaction_domains.tsv"
            )

            # Create folder for ELM files (if it does not exist)
            if not os.path.exists(elm_files_out):
                os.makedirs(elm_files_out)

        else:
            elm_instances_fasta = ELM_INSTANCES_FASTA
            elm_classes_tsv = ELM_CLASSES_TSV
            elm_instances_tsv = ELM_INSTANCES_TSV
            elm_intdomains_tsv = ELM_INTDOMAINS_TSV

            # Create folder for ELM files (if it does not exist)
            if not os.path.exists(ELM_FILES):
                os.makedirs(ELM_FILES)

        # --fail: non-zero exit on HTTP 4xx/5xx (so the && chain breaks instead of writing an error page).
        # --retry 3 / --retry-delay 5: re-try transient failures; elm.eu.org can be slow on cold cache.
        # --max-time 180: cap each download at 3 min so a hung server fails loudly instead of stalling forever.
        curl_opts = "--fail --retry 3 --retry-delay 5 --max-time 180"

        if platform.system() == "Windows":
            # The double-quotation marks allow white spaces in the path, but this does not work for Windows
            command = f"""
                curl {curl_opts} -o {elm_instances_fasta} \"{ELM_INSTANCES_FASTA_DOWNLOAD}\" \\
                &&  curl {curl_opts} -o {elm_classes_tsv} \"{ELM_CLASSES_TSV_DOWNLOAD}\" \\
                &&  curl {curl_opts} -o {elm_instances_tsv} \"{ELM_INSTANCES_TSV_DOWNLOAD}\" \\
                &&  curl {curl_opts} -o {elm_intdomains_tsv} \"{ELM_INTDOMAINS_TSV_DOWNLOAD}\"
                """

        else:
            command = f"""
                curl {curl_opts} -o '{elm_instances_fasta}' {ELM_INSTANCES_FASTA_DOWNLOAD} \\
                &&  curl {curl_opts} -o '{elm_classes_tsv}' {ELM_CLASSES_TSV_DOWNLOAD} \\
                &&  curl {curl_opts} -o '{elm_instances_tsv}' {ELM_INSTANCES_TSV_DOWNLOAD} \\
                &&  curl {curl_opts} -o '{elm_intdomains_tsv}' '{ELM_INTDOMAINS_TSV_DOWNLOAD}'
                """

        with subprocess.Popen(command, shell=True, stderr=subprocess.PIPE) as process:
            stderr = process.stderr.read().decode("utf-8")
            # Log the standard error if it is not empty
            if stderr:
                sys.stderr.write(stderr)

        # Exit system if the subprocess returned with an error
        if process.wait() != 0:
            raise RuntimeError(
                "ELM database files download failed (curl returned a non-zero exit code). "
                "Check the stderr above for details."
            )

        # Check if files are present; raise if any are missing so the failure surfaces
        # at setup time rather than later during gget.elm().
        missing = []
        for path, label, url in [
            (elm_instances_fasta, "ELM instances fasta file", ELM_INSTANCES_FASTA_DOWNLOAD),
            (elm_classes_tsv, "ELM classes tsv file", ELM_CLASSES_TSV_DOWNLOAD),
            (elm_instances_tsv, "ELM instances tsv file", ELM_INSTANCES_TSV_DOWNLOAD),
            (elm_intdomains_tsv, "ELM interaction domains tsv file", ELM_INTDOMAINS_TSV_DOWNLOAD),
        ]:
            if os.path.exists(path):
                check_file_for_error_message(path, label, url)
                if verbose:
                    logger.info(f"{label} present.")
            else:
                missing.append(label)

        if missing:
            raise RuntimeError(
                "ELM database files download failed; missing files: "
                + ", ".join(missing)
            )

    elif module == "alphafold":
        if platform.system() == "Windows":
            logger.error(
                "gget setup alphafold and gget alphafold are not supported on Windows OS."
            )
            return

        ## Ask user to install openmm if not already installed
        try:
            import simtk.openmm as openmm

            # Silence openmm logger
            logging.getLogger("openmm").setLevel(logging.WARNING)

            # Commenting the following out because openmm v7.7.0 does not support __version__
            # # Check if correct version was installed
            # if openmm.__version__ != "7.5.1":
            #     raise ImportError()

            # if verbose:
            #   logger.info(f"openmm v{openmm.__version__} already installed.")

        except ImportError as e:
            raise ImportError(
                f"""
                Trying to import openmm resulted in the following error: 
                {e}

                Please install AlphaFold third-party dependency openmm by running the following command from the command line: 
                For Python version < 3.10: 
                'conda install -qy conda==4.13.0 && conda install -qy -c conda-forge openmm=7.5.1' 
                For Python version 3.10: 
                'conda install -qy conda==24.1.2 && conda install -qy -c conda-forge openmm=7.7.0' 
                For Python version 3.11: 
                'conda install -qy conda==24.11.1 && conda install -qy -c conda-forge openmm=8.0.0' 
                (Recommendation: Follow with 'conda update -qy conda' to update conda to the latest version afterwards.)
                """
            )

        ## Install py3Dmol
        _install("py3Dmol", "py3Dmol", verbose=verbose)

        ## Install Alphafold if not already installed
        if verbose:
            logger.info("Installing AlphaFold from source (requires pip and git).")

        # Prefer uv when present for network robustness; use pip for flags uv lacks
        have_uv = shutil.which("uv") is not None
        pip_upgrade = "uv pip install --upgrade" if have_uv else "pip install -q --upgrade"
        pip_nodeps = "pip install -q --no-deps"  # uv lacks --no-deps
        os.environ.setdefault("UV_HTTP_TIMEOUT", "300")

        # Define AlphaFold folder name and location
        alphafold_folder = os.path.join(
            tempfile.gettempdir(), f"tmp_alphafold_{uuid.uuid4()}"
        )
        pathlib.Path(alphafold_folder).mkdir(parents=True, exist_ok=True)

        # Clean (unescaped) jackhmmer cache dir; we’ll patch file contents via Python
        jack_dir = os.path.expanduser(f"~/tmp/jackhmmer/{UUID}")

        # Core AlphaFold dependencies (Colab/CPU friendly set)
        alphafold_deps = [
            "absl-py>=2.1,<3",
            "dm-haiku<=0.0.12",          # dont upgrade to avoid clash with jax
            "dm-tree>=0.1.8",
            "filelock>=3.12",
            "jax==0.4.26",
            "jaxlib==0.4.26",
            # "jax-triton>=0.2,<0.3",    # jax-triton & triton aren’t needed on CPU-only use
            "jaxtyping>=0.2.30",
            "jmp>=0.0.4",
            "ml-collections>=0.1,<1",
            "ml-dtypes>=0.3.1,<0.6",
            "numpy>=1.26,<2",            # keeps TF 2.17 CPU happy
            "opt-einsum>=3.4,<4",
            "pillow>=10,<12",
            "protobuf<4",
            # "rdkit-pypi",              # rdkit pulls heavy wheels and may force newer numpy; skip unless needed
            "scipy>=1.10,<2",
            "tabulate>=0.9",
            "tqdm>=4.65",
            # "triton>=3,<4",            # only if you enable jax-triton above
            "typeguard>=2.13,<3",
            "zstandard>=0.21,<0.24",
        ]

        try:
            # Clone AlphaFold github repo
            subprocess.run(
                ["git", "clone", "-q", "--branch", ALPHAFOLD_GIT_REPO_VERSION, ALPHAFOLD_GIT_REPO, alphafold_folder],
                check=True,
            )

            # Patch jackhmmer.py
            jack_py = os.path.join(alphafold_folder, "alphafold", "data", "tools", "jackhmmer.py")
            with open(jack_py, "r", encoding="utf-8") as f:
                txt = f.read()

            txt = txt.replace("/tmp/ramdisk", jack_dir)
            if "logging.set_verbosity(logging.WARNING)" not in txt:
                txt = txt.replace(
                    "from absl import logging",
                    "from absl import logging\nlogging.set_verbosity(logging.WARNING)",
                    1,
                )

            with open(jack_py, "w", encoding="utf-8") as f:
                f.write(txt)

            # Base deps first (NumPy/TF/JAX in a known good combo)
            subprocess.run(
                [*pip_upgrade.split(), "numpy>=1.26,<2", "tensorflow-cpu>=2.17,<2.18"],
                check=True
            )

            # The rest of the deps
            subprocess.run(
                [*pip_upgrade.split(), *alphafold_deps],
                check=True
            )

            # Install AF itself without bringing in its pinned requirements
            subprocess.run(f'{pip_nodeps} "{alphafold_folder}"', check=True, shell=True)

        except subprocess.CalledProcessError as e:
            logger.error("AlphaFold installation failed.")
            # Show any captured stderr from our last step, if available
            try:
                sys.stderr.write(str(e) + "\n")
            except Exception:
                pass
            shutil.rmtree(alphafold_folder, ignore_errors=True)
            return

        # Clean up checkout
        shutil.rmtree(alphafold_folder, ignore_errors=True)

        try:
            import alphafold as AlphaFold
            if verbose:
                logger.info("AlphaFold installed succesfully.")
        except ImportError as e:
            logger.error(f"AlphaFold installation failed. Import error:\n{e}")
            return

        ## Append AlphaFold to path
        alphafold_path = os.path.abspath(os.path.dirname(AlphaFold.__file__))
        if alphafold_path not in sys.path:
            sys.path.append(alphafold_path)

        ## Install pdbfixer
        if verbose:
            logger.info("Installing pdbfixer from source (requires pip and git).")

        pdbfixer_folder = os.path.join(
            tempfile.gettempdir(), f"tmp_pdbfixer_{uuid.uuid4()}"
        )

        try:
            if openmm.__version__ == "7.5.1":
                # Install pdbfixer version compatible with openmm v7.5.1
                PDBFIXER_VERSION = "v1.7"
            else:
                PDBFIXER_VERSION = "v1.8.1"
        except:
            PDBFIXER_VERSION = "v1.8.1"

        pip_cmd = "uv pip install" if shutil.which("uv") else "pip install -q"

        command = f"""
            git clone -q --branch {PDBFIXER_VERSION} {PDBFIXER_GIT_REPO} {pdbfixer_folder} \\
            && {pip_cmd} {pdbfixer_folder}
            """

        with subprocess.Popen(command, shell=True, stderr=subprocess.PIPE) as process:
            stderr = process.stderr.read().decode("utf-8")
        # Exit system if the subprocess returned with an error
        if process.wait() != 0:
            if stderr:
                # Log the standard error if it is not empty
                sys.stderr.write(stderr)
            logger.error("pdbfixer installation failed.")
            return

        # Remove cloned directory
        shutil.rmtree(pdbfixer_folder)

        # Check if pdbfixer was installed successfully
        command = f"{sys.executable} -m pip list | grep pdbfixer"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        pdb_out, err = process.communicate()

        if pdb_out.decode() != "":
            logger.info(f"pdbfixer installed succesfully.")
        else:
            logger.error("pdbfixer installation failed.")
            return

        ## Download model parameters
        # Download parameters if the params directory is empty
        if not os.path.exists(os.path.join(PARAMS_DIR, "params/")):
            # Create folder to save parameter files
            os.makedirs(os.path.join(PARAMS_DIR, "params/"), exist_ok=True)

        if len(os.listdir(os.path.join(PARAMS_DIR, "params/"))) < 12:
            if verbose:
                logger.info(
                    "Downloading AlphaFold model parameters (requires 4.1 GB of storage). This might take a few minutes."
                )
            if platform.system() == "Windows":
                # The double-quotation marks allow white spaces in the path, but this does not work for Windows
                command = f"""
                    curl -# -o {PARAMS_PATH} {PARAMS_URL} \\
                    && tar --extract --file={PARAMS_PATH} --directory={PARAMS_DIR+'params/'} --preserve-permissions \\
                    && rm {PARAMS_PATH}
                    """
            else:
                command = f"""
                    curl -# -o '{PARAMS_PATH}' '{PARAMS_URL}' \\
                    && tar --extract --file='{PARAMS_PATH}' --directory='{PARAMS_DIR+'params/'}' --preserve-permissions \\
                    && rm '{PARAMS_PATH}'
                    """

            with subprocess.Popen(
                command, shell=True, stderr=subprocess.PIPE
            ) as process:
                stderr = process.stderr.read().decode("utf-8")
                # Log the standard error if it is not empty
                if stderr:
                    sys.stderr.write(stderr)
            # Exit system if the subprocess returned with an error
            if process.wait() != 0:
                logger.error("Model parameter download failed.")
                return
            else:
                if verbose:
                    logger.info("Model parameter download complete.")
        else:
            if verbose:
                logger.info("AlphaFold model parameters already downloaded.")

    elif module == "cbio":
        _install("bravado", "bravado", verbose=verbose)
