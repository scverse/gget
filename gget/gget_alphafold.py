# Code adapted and heavily modified from the AlphaFold Colab notebook
# https://colab.research.google.com/github/deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb
# Copyright 2021 DeepMind; SPDX-License-Identifier: Apache-2.0

# Any publication that discloses findings arising from using this source code or the model parameters
# should cite the AlphaFold paper (https://www.nature.com/articles/s41586-021-03819-2) and, if applicable,
# the AlphaFold-Multimer paper (https://www.biorxiv.org/content/10.1101/2021.10.04.463034v1).

from datetime import datetime

# Get current date and time for default foldername
dt_string = datetime.now().strftime("%Y_%m_%d-%H%M")

import collections  # noqa: E402
import copy  # noqa: E402
import enum  # noqa: E402
import glob  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import random  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from concurrent import futures  # noqa: E402
from urllib import request  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from IPython import display  # noqa: E402
from ipywidgets import GridspecLayout, Output  # noqa: E402
from tqdm import tqdm  # noqa: E402

from .utils import set_up_logger  # noqa: E402

logger = set_up_logger()

TQDM_BAR_FORMAT = "{l_bar}{bar}| {n_fmt}/{total_fmt} [elapsed: {elapsed} remaining: {remaining}]"

from .compile import PACKAGE_PATH  # noqa: E402

# from .gget_setup import TMP_DISK
from .gget_setup import PARAMS_DIR, UUID  # noqa: E402

STEREO_CHEM_DIR = os.path.join(PARAMS_DIR, "stereo_chemical_props.txt")
# Path to jackhmmer binary
JACKHMMER_BINARY_PATH = os.path.join(PACKAGE_PATH, f"bins/{platform.system()}/jackhmmer")

# Test pattern to find closest source
test_url_pattern = "https://storage.googleapis.com/alphafold-colab{:s}/latest/uniref90_2022_01.fasta.1"

# Sequence validation parameters
MIN_PER_SEQUENCE_LENGTH = 16
MAX_PER_SEQUENCE_LENGTH = 3400
MAX_MONOMER_MODEL_LENGTH = 2500
MAX_LENGTH = 3400
MAX_VALIDATED_LENGTH = 3000

# Maximum hits per database
MAX_HITS = {
    "uniref90": 10_000,
    "smallbfd": 5_000,
    "mgnify": 501,
    "uniprot": 50_000,
}

# Color bands for visualizing plddt
PLDDT_BANDS = [
    (0, 50, "#FF7D45"),
    (50, 70, "#FFDB13"),
    (70, 90, "#65CBF3"),
    (90, 100, "#0053D6"),
]


def plot_plddt_legend():
    """Function to plot the legend for pLDDT."""
    thresh = [
        "Very low (pLDDT < 50)",
        "Low (70 > pLDDT > 50)",
        "Confident (90 > pLDDT > 70)",
        "Very high (pLDDT > 90)",
    ]

    colors = [x[2] for x in PLDDT_BANDS]

    plt.figure(figsize=(2, 2))
    for c in colors:
        plt.bar(0, 0, color=c)
    plt.legend(thresh, frameon=False, loc="center", fontsize=20)
    plt.xticks([])
    plt.yticks([])
    ax = plt.gca()
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    plt.title("Model Confidence", fontsize=20, pad=20)

    return plt


def fetch(source):
    """Support function for finding closest source."""
    request.urlretrieve(test_url_pattern.format(source))
    return source


def get_msa(fasta_path, msa_databases, total_jackhmmer_chunks):
    """Function to search for MSA for the given sequence using chunked Jackhmmer search."""
    from alphafold.data.tools import jackhmmer

    ## Run the search against chunks of genetic databases to save disk space
    raw_msa_results = collections.defaultdict(list)

    with tqdm(total=total_jackhmmer_chunks, bar_format=TQDM_BAR_FORMAT) as pbar:
        # Set progress bar description
        pbar.set_description("Jackhmmer search")

        def jackhmmer_chunk_callback(i):
            pbar.update(n=1)

        for db_config in msa_databases:
            db_name = db_config["db_name"]

            jackhmmer_runner = jackhmmer.Jackhmmer(
                binary_path=JACKHMMER_BINARY_PATH,
                database_path=db_config["db_path"],
                get_tblout=True,
                num_streamed_chunks=db_config["num_streamed_chunks"],
                streaming_callback=jackhmmer_chunk_callback,
                z_value=db_config["z_value"],
            )
            # Group the results by database name.
            raw_msa_results[db_name].extend(jackhmmer_runner.query(fasta_path))

    return raw_msa_results


def clean_up():
    """Function to clean up temporary files after running gget alphafold."""
    # # Remove fasta files with input sequences
    # files = glob.glob("target_*.fasta")
    # for f in files:
    #     try:
    #         os.remove(f)
    #     except:
    #         None

    # # Unmount temporary TMPFS
    # if platform.system() == "Linux":
    #   command = f"unmount /tmp/ramdisk"
    # elif platform.system() == "Darwin":
    #   # Detach last added disk
    #   command = f"hdiutil detach {TMP_DISK}"

    # if command:
    #   with subprocess.Popen(command, shell=True, stderr=subprocess.PIPE) as process:
    #     stderr = process.stderr.read().decode("utf-8")
    #     # Exit system if the subprocess returned with an error
    #     if process.wait() != 0:
    #         if stderr:
    #           # Log the standard error if it is not empty
    #           sys.stderr.write(stderr)

    # Delete any fasta files left in temporary jackhmmer folder
    for file in glob.glob(os.path.expanduser(f"~/tmp/jackhmmer/{UUID}/*.fasta")):
        if os.path.exists(file):
            os.remove(file)

    # Delete empty parent folders
    os.removedirs(os.path.expanduser(f"~/tmp/jackhmmer/{UUID}"))


def alphafold(
    sequence,
    out=f"{dt_string}_gget_alphafold_prediction",
    multimer_for_monomer=False,
    relax=False,
    multimer_recycles=3,
    plot=True,
    show_sidechains=True,
    verbose=True,
):
    """Predicts the structure of a protein using a slightly simplified version of AlphaFold v2.3.0 (https://doi.org/10.1038/s41586-021-03819-2).

    published in the AlphaFold Colab notebook (https://colab.research.google.com/github/deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb).

    Args:
      - sequence                Amino acid sequence (str), a list of sequences, or path to a FASTA file.
      - out                     Path to folder to save prediction results in (str).
                                Default: "./[date_time]_gget_alphafold_prediction"
      - multimer_for_monomer    Use multimer model for a monomer (default: False).
      - multimer_recycles       The multimer model will continue recycling until the predictions stop changing, up to the limit set here (default: 3).
                                For higher accuracy, at the potential cost of longer inference times, set this to 20.
      - relax                   True/False whether to AMBER relax the best model (default: False).
      - plot                    True/False whether to provide a graphical overview of the prediction (default: True).
      - show_sidechains         True/False whether to show side chains in the plot (default: True).
      - verbose                 True/False whether to print progress information. Default True.

    Saves the predicted aligned error (json) and the prediction (PDB) in the defined 'out' folder.

    From the AlphaFold Colab notebook (https://colab.research.google.com/github/deepmind/alphafold/blob/main/notebooks/AlphaFold.ipynb):
    "In comparison to AlphaFold v2.3.0, this [algorithm] uses no templates (homologous structures)
    and only a selected portion of the BFD database (https://bfd.mmseqs.com/). We have validated these
    changes on several thousand recent PDB structures. While accuracy will be near-identical to the full
    AlphaFold system on many targets, a small fraction have a large drop in accuracy due to the smaller MSA
    and lack of templates. For best reliability, we recommend instead using the full open source AlphaFold (https://github.com/deepmind/alphafold/),
    or the AlphaFold Protein Structure Database (https://alphafold.ebi.ac.uk/).
    This [algorithm] has a small drop in average accuracy for multimers compared to local AlphaFold installation,
    for full multimer accuracy it is highly recommended to run AlphaFold locally (https://github.com/deepmind/alphafold#running-alphafold).
    Moreover, the AlphaFold-Multimer requires searching for MSA for every unique sequence in the complex, hence it is substantially slower.[...]
    Please note that this [algorithm] is provided for theoretical modelling only and caution should be exercised in its use."

    If you use this function, please cite the gget (https://doi.org/10.1101/2022.05.17.492392) and AphaFold (https://doi.org/10.1038/s41586-021-03819-2) papers
    and, if applicable, the AlphaFold-Multimer paper (https://www.biorxiv.org/content/10.1101/2021.10.04.463034v1).
    """
    if platform.system() == "Windows":
        logger.warning("gget setup alphafold and gget alphafold are not supported on Windows OS.")

    ## Check if third-party dependencies are installed
    # Check if openmm is installed
    try:
        import simtk.openmm as openmm  # noqa: F401
    except ImportError as e:
        raise ImportError(
            f"""
            Importing openmm resulted in the following error:
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
        ) from e

    # Check if AlphaFold is installed
    try:
        import alphafold as AlphaFold
    except ImportError:
        logger.error(
            """
            Some third-party dependencies are missing. Please run the following command:
            >>> gget.setup('alphafold') or $ gget setup alphafold
            """
        )
        return

    # Check if pdbfixer is installed
    command = "pip list | grep pdbfixer"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    pdb_out, err = process.communicate()

    if pdb_out.decode() == "":
        logger.error(
            """
            Some third-party dependencies are missing. Please run the following command:
            >>> gget.setup('alphafold') or $ gget setup alphafold
            """
        )
        return

    ## Check if model parameters were downloaded
    if not os.path.exists(os.path.join(PARAMS_DIR, "params/")):
        logger.error(
            """
            The AlphaFold model parameters are missing. Please run the following command:
            >>> gget.setup('alphafold') or $ gget setup alphafold
            """
        )
        return

    if len(os.listdir(os.path.join(PARAMS_DIR, "params/"))) < 12:
        logger.error(
            """
            The AlphaFold model parameters are missing. Please run the following command:
            >>> gget.setup('alphafold') or $ gget setup alphafold
            """
        )
        return

    ## Import AlphaFold functions
    from alphafold.common import protein
    from alphafold.data import feature_processing, msa_pairing, pipeline, pipeline_multimer
    from alphafold.model import config, data, model
    from alphafold.notebooks import notebook_utils

    try:
        from alphafold.relax import utils
    except ModuleNotFoundError as e:
        if "openmm" in str(e):
            raise ImportError(
                f"""
                Importing openmm resulted in the following error:
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
            ) from e

    if relax:
        # Import AlphaFold relax package
        try:
            from alphafold.relax import relax as run_relax
        except ModuleNotFoundError as e:
            if "openmm" in str(e):
                raise ImportError(
                    f"""
                    Importing openmm resulted in the following error:
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
                ) from e

    ## Move stereo_chemical_props.txt from gget bins to Alphafold package so it can be found
    # logger.info("Locate files containing stereochemical properties.")
    ALPHAFOLD_PATH = os.path.abspath(os.path.dirname(AlphaFold.__file__))
    os.makedirs(os.path.join(ALPHAFOLD_PATH, "common/"), exist_ok=True)
    shutil.copyfile(
        STEREO_CHEM_DIR,
        os.path.join(ALPHAFOLD_PATH, "common/stereo_chemical_props.txt"),
    )

    ## Validate input sequence(s)
    if verbose:
        logger.info("Validating input sequence(s).")

    # Handle command line passing path to FASTA as a list
    if isinstance(sequence, list) and len(sequence) == 1:
        sequence = sequence[0]

    # If the path to a fasta file was provided instead of a nucleotide sequence,
    # read the file and extract the first sequence
    if "." in sequence:
        if ".txt" in sequence:
            # Read the text file
            titles = []
            seqs = []
            with open(sequence) as text_file:
                for i, line in enumerate(text_file):  # noqa: B007
                    # Recognize a title line by the '>' character
                    if line[0] == ">":
                        # Append title line to titles list
                        titles.append(line.strip())
                    else:
                        seqs.append(line.strip())

        elif ".fa" in sequence:
            # Read the FASTA
            titles = []
            seqs = []
            with open(sequence) as fasta_file:
                for i, line in enumerate(fasta_file):
                    # Each second line will be a title line
                    if i % 2 == 0:
                        if line[0] != ">":
                            raise ValueError("Expected FASTA to start with a '>' character. ")
                        else:
                            # Append title line to titles list
                            titles.append(line.strip())
                    else:
                        if line[0] == ">":
                            raise ValueError(
                                "FASTA contains two lines starting with '>' in a row -> missing sequence line. "
                            )
                        # Append sequences line to seqs list
                        else:
                            seqs.append(line.strip())
        else:
            raise ValueError("File format not recognized. gget alphafold only supports '.txt' or '.fa' files. ")
    elif isinstance(sequence, str) and "." not in sequence:
        # Convert string to list
        seqs = [sequence]
    else:
        seqs = sequence

    # Use AlphaFold function to validate input sequence(s)
    class ModelType(enum.Enum):
        MONOMER = 0
        MULTIMER = 1

    sequences = notebook_utils.clean_and_validate_input_sequences(
        input_sequences=seqs,
        min_sequence_length=MIN_PER_SEQUENCE_LENGTH,
        max_sequence_length=MAX_PER_SEQUENCE_LENGTH,
    )
    if len(seqs) == 1:
        if multimer_for_monomer:
            if verbose:
                logger.info("Using the multimer model for a single chain, as requested.")
            model_type_to_use = ModelType.MULTIMER
        else:
            if verbose:
                logger.info("Using the single-chain (monomer) model.")
            model_type_to_use = ModelType.MONOMER
    else:
        if verbose:
            logger.info(f"Using the multimer model with {len(seqs)} sequences.")
        model_type_to_use = ModelType.MULTIMER

    # Check whether total length exceeds limit
    total_sequence_length = sum([len(seq) for seq in seqs])
    if total_sequence_length > MAX_LENGTH:
        raise ValueError(
            f"The total sequence length is too long: {total_sequence_length}, while the maximum is {MAX_LENGTH}."
        )

    # Check whether seq exceeds the monomer limit
    if model_type_to_use == ModelType.MONOMER:
        if len(seqs[0]) > MAX_MONOMER_MODEL_LENGTH:
            raise ValueError(
                f"""
                Input sequence is too long: {len(sequences[0])} amino acids, while the maximum for the monomer model is {MAX_MONOMER_MODEL_LENGTH}.
                You can try to run this sequence with the multimer model by using the flag [-mfm] ('multimer_for_monomer=True').
                """
            )

    if total_sequence_length > MAX_VALIDATED_LENGTH:
        logger.warning(
            f"The accuracy of this algorithm has not been fully validated above 3000 residues, and you may experience long running times or run out of memory. Total sequence length is {total_sequence_length} residues."
        )

    ## Find the closest source
    if verbose:
        logger.info("Finding closest source for reference database.")

    ex = futures.ThreadPoolExecutor(3)
    fs = [ex.submit(fetch, source) for source in ["", "-europe", "-asia"]]
    source = None
    for f in futures.as_completed(fs):
        source = f.result()
        ex.shutdown()
        break

    DB_ROOT_PATH = f"https://storage.googleapis.com/alphafold-colab{source}/latest/"
    MSA_DATABASES = [
        {
            "db_name": "uniref90",
            "db_path": f"{DB_ROOT_PATH}uniref90_2022_01.fasta",
            "num_streamed_chunks": 62,
            "z_value": 144_113_457,
        },
        {
            "db_name": "smallbfd",
            "db_path": f"{DB_ROOT_PATH}bfd-first_non_consensus_sequences.fasta",
            "num_streamed_chunks": 17,
            "z_value": 65_984_053,
        },
        {
            "db_name": "mgnify",
            "db_path": f"{DB_ROOT_PATH}mgy_clusters_2022_05.fasta",
            "num_streamed_chunks": 120,
            "z_value": 623_796_864,
        },
    ]

    # Search UniProt and construct the all_seq features (only for heteromers, not homomers).
    if model_type_to_use == ModelType.MULTIMER and len(set(sequences)) > 1:
        MSA_DATABASES.extend(
            [
                # Swiss-Prot and TrEMBL are concatenated together as UniProt
                {
                    "db_name": "uniprot",
                    "db_path": f"{DB_ROOT_PATH}uniprot_2021_04.fasta",
                    "num_streamed_chunks": 101,
                    "z_value": 225_013_025 + 565_928,
                },
            ]
        )

    TOTAL_JACKHMMER_CHUNKS = sum([cfg["num_streamed_chunks"] for cfg in MSA_DATABASES])

    ### Search against existing databases
    # Get absolute path to output file and create output directory
    if out is not None:
        os.makedirs(out, exist_ok=True)
        abs_out_path = os.path.abspath(out)
    else:
        # Use temporary jackhmmer folder which will later be deleted
        abs_out_path = os.path.expanduser(f"~/tmp/jackhmmer/{UUID}")

    # Create folder to save temporary jackhmmer database chunks in
    os.makedirs(os.path.expanduser(f"~/tmp/jackhmmer/{UUID}"), exist_ok=True)

    features_for_chain = {}
    raw_msa_results_for_sequence = {}
    for sequence_index, sequence in enumerate(sequences, start=1):
        # logger.info(f"Getting MSA for sequence {sequence_index}.")

        ## Manage permissions to jackhmmer binary
        command = f"chmod 755 {JACKHMMER_BINARY_PATH}"
        with subprocess.Popen(command, shell=True, stderr=subprocess.PIPE) as process:
            stderr = process.stderr.read().decode("utf-8")
        # Exit system if the subprocess returned with an error
        if process.wait() != 0:
            if stderr:
                # Log the standard error if it is not empty
                sys.stderr.write(stderr)
            logger.error("Giving chmod 755 permissions to jackhmmer binary failed.")
            return

        # Save the target sequence in a fasta file
        fasta_path = os.path.join(abs_out_path, f"target_{sequence_index}.fasta")
        with open(fasta_path, "w") as f:
            f.write(f">query\n{sequence}")

        # Don't do redundant work for multiple copies of the same chain in the multimer
        if sequence not in raw_msa_results_for_sequence:
            raw_msa_results = get_msa(
                fasta_path=fasta_path,
                msa_databases=MSA_DATABASES,
                total_jackhmmer_chunks=TOTAL_JACKHMMER_CHUNKS,
            )
            raw_msa_results_for_sequence[sequence] = raw_msa_results
        else:
            raw_msa_results = copy.deepcopy(raw_msa_results_for_sequence[sequence])

        ## Extract the MSAs from the Stockholm files.
        # NB: deduplication happens later in pipeline.make_msa_features.
        single_chain_msas = []
        uniprot_msa = None
        for db_name, db_results in raw_msa_results.items():
            merged_msa = notebook_utils.merge_chunked_msa(results=db_results, max_hits=MAX_HITS.get(db_name))
            if merged_msa.sequences and db_name != "uniprot":
                single_chain_msas.append(merged_msa)
                msa_size = len(set(merged_msa.sequences))
                if verbose:
                    logger.info(f"{msa_size} unique sequences found in {db_name} for sequence {sequence_index}.")
            elif merged_msa.sequences and db_name == "uniprot":
                uniprot_msa = merged_msa

        notebook_utils.show_msa_info(single_chain_msas=single_chain_msas, sequence_index=sequence_index)

        # Turn the raw data into model features.
        feature_dict = {}
        feature_dict.update(
            pipeline.make_sequence_features(sequence=sequence, description="query", num_res=len(sequence))
        )
        feature_dict.update(pipeline.make_msa_features(msas=single_chain_msas))
        # Add empty placeholder features
        feature_dict.update(notebook_utils.empty_placeholder_template_features(num_templates=0, num_res=len(sequence)))

        # Construct the all_seq features only for heteromers, not homomers
        if model_type_to_use == ModelType.MULTIMER and len(set(sequences)) > 1:
            valid_feats = msa_pairing.MSA_FEATURES + ("msa_species_identifiers",)
            all_seq_features = {
                f"{k}_all_seq": v for k, v in pipeline.make_msa_features([uniprot_msa]).items() if k in valid_feats
            }
            feature_dict.update(all_seq_features)

        features_for_chain[protein.PDB_CHAIN_IDS[sequence_index - 1]] = feature_dict

    # Further feature post-processing depending on the model type
    if model_type_to_use == ModelType.MONOMER:
        np_example = features_for_chain[protein.PDB_CHAIN_IDS[0]]

    elif model_type_to_use == ModelType.MULTIMER:
        all_chain_features = {}
        for chain_id, chain_features in features_for_chain.items():
            all_chain_features[chain_id] = pipeline_multimer.convert_monomer_features(chain_features, chain_id)

        all_chain_features = pipeline_multimer.add_assembly_features(all_chain_features)

        np_example = feature_processing.pair_and_merge(all_chain_features=all_chain_features)

        # Pad MSA to avoid zero-sized extra_msa
        np_example = pipeline_multimer.pad_msa(np_example, min_num_seq=512)

    ## Run AlphaFold
    # Run model
    if model_type_to_use == ModelType.MONOMER:
        model_names = config.MODEL_PRESETS["monomer"] + ("model_2_ptm",)
    elif model_type_to_use == ModelType.MULTIMER:
        model_names = config.MODEL_PRESETS["multimer"]

    plddts = {}
    ranking_confidences = {}
    pae_outputs = {}
    unrelaxed_proteins = {}

    with tqdm(total=len(model_names) + 1, bar_format=TQDM_BAR_FORMAT) as pbar:
        for model_name in model_names:
            # Set progress bar description
            pbar.set_description(f"Running {model_name}")

            cfg = config.model_config(model_name)
            if model_type_to_use == ModelType.MONOMER:
                cfg.data.eval.num_ensemble = 1
            elif model_type_to_use == ModelType.MULTIMER:
                cfg.model.num_ensemble_eval = 1

            if model_type_to_use == ModelType.MULTIMER:
                cfg.model.num_recycle = multimer_recycles
                cfg.model.recycle_early_stop_tolerance = 0.5

            params = data.get_model_haiku_params(model_name, PARAMS_DIR)
            model_runner = model.RunModel(cfg, params)
            processed_feature_dict = model_runner.process_features(np_example, random_seed=0)
            prediction = model_runner.predict(processed_feature_dict, random_seed=random.randrange(sys.maxsize))

            if model_type_to_use == ModelType.MONOMER:
                if "predicted_aligned_error" in prediction:
                    pae_outputs[model_name] = (
                        prediction["predicted_aligned_error"],
                        prediction["max_predicted_aligned_error"],
                    )
                else:
                    # Monomer models are sorted by mean pLDDT. Do not put monomer pTM models here as they
                    # should never get selected.
                    ranking_confidences[model_name] = prediction["ranking_confidence"]
                    plddts[model_name] = prediction["plddt"]
            elif model_type_to_use == ModelType.MULTIMER:
                # Multimer models are sorted by pTM+ipTM.
                ranking_confidences[model_name] = prediction["ranking_confidence"]
                plddts[model_name] = prediction["plddt"]
                pae_outputs[model_name] = (
                    prediction["predicted_aligned_error"],
                    prediction["max_predicted_aligned_error"],
                )

            # Set the b-factors to the per-residue plddt.
            final_atom_mask = prediction["structure_module"]["final_atom_mask"]
            b_factors = prediction["plddt"][:, None] * final_atom_mask
            unrelaxed_protein = protein.from_prediction(
                processed_feature_dict,
                prediction,
                b_factors=b_factors,
                remove_leading_feature_dimension=(model_type_to_use == ModelType.MONOMER),
            )
            unrelaxed_proteins[model_name] = unrelaxed_protein

            # Delete unused outputs to save memory
            del model_runner
            del params
            del prediction
            pbar.update(n=1)

        ## AMBER relax the best model
        # Find the best model according to the mean pLDDT.
        best_model_name = max(ranking_confidences.keys(), key=lambda x: ranking_confidences[x])

        if relax:
            pbar.set_description("AMBER relaxation")

            amber_relaxer = run_relax.AmberRelaxation(
                max_iterations=0,
                tolerance=2.39,
                stiffness=10.0,
                exclude_residues=[],
                max_outer_iterations=3,
                use_gpu=False,
            )
            relaxed_pdb, _, _ = amber_relaxer.process(prot=unrelaxed_proteins[best_model_name])
        else:
            logger.warning(
                "\nRunning model without relaxation stage. Use flag [--relax] ('relax=True') to include AMBER relaxation."
            )
            relaxed_pdb = protein.to_pdb(unrelaxed_proteins[best_model_name])

        pbar.update(n=1)

    pae, max_pae = list(pae_outputs.values())[0]

    if out is not None:
        ## Save the prediction
        pred_output_path = os.path.join(abs_out_path, "selected_prediction.pdb")
        with open(pred_output_path, "w") as f:
            f.write(relaxed_pdb)

        ## Save the predicted aligned error
        pae_output_path = os.path.join(abs_out_path, "predicted_aligned_error.json")
        if pae_outputs:
            # Check the PAE array is the correct shape
            if pae.ndim != 2 or pae.shape[0] != pae.shape[1]:
                raise ValueError(f"PAE must be a square matrix, got {pae.shape}")

            # Round the predicted aligned errors to 1 decimal place
            rounded_errors = np.round(pae.astype(np.float64), decimals=1)

            # Create dictionary with PAE and pLDDT
            formatted_output = {
                "predicted_aligned_error": rounded_errors.tolist(),
                "max_predicted_aligned_error": max_pae.item(),
                "plddt": plddts[best_model_name].tolist(),
                "final_atom_mask": final_atom_mask.tolist(),
            }

            with open(pae_output_path, "w", encoding="utf-8") as f:
                json.dump(formatted_output, f, ensure_ascii=False, indent=4)

    ## Plotting
    if plot:
        if verbose:
            logger.info("Plotting prediction results.")
        import py3Dmol

        # Construct multiclass b-factors to indicate confidence bands
        # 0=very low, 1=low, 2=confident, 3=very high
        banded_b_factors = []
        for plddt in plddts[best_model_name]:
            for idx, (min_val, max_val, _) in enumerate(PLDDT_BANDS):
                if plddt >= min_val and plddt <= max_val:
                    banded_b_factors.append(idx)
                    break

        banded_b_factors = np.array(banded_b_factors)[:, None] * final_atom_mask
        to_visualize_pdb = utils.overwrite_b_factors(relaxed_pdb, banded_b_factors)

        # Show the structure coloured by chain if the multimer model has been used.
        if model_type_to_use == ModelType.MULTIMER:
            multichain_view = py3Dmol.view(width=800, height=600)
            multichain_view.addModelsAsFrames(to_visualize_pdb)
            multichain_style = {"cartoon": {"colorscheme": "chain"}}
            multichain_view.setStyle({"model": -1}, multichain_style)
            multichain_view.zoomTo()
            multichain_view.show()

        # Color the structure by per-residue pLDDT
        color_map = {i: bands[2] for i, bands in enumerate(PLDDT_BANDS)}
        view = py3Dmol.view(width=800, height=600)
        view.addModelsAsFrames(to_visualize_pdb)
        style = {"cartoon": {"colorscheme": {"prop": "b", "map": color_map}}}
        if show_sidechains:
            style["stick"] = {}
        view.setStyle({"model": -1}, style)
        view.zoomTo()

        grid = GridspecLayout(1, 2)
        output_plt = Output()
        with output_plt:
            view.show()
        grid[0, 0] = output_plt

        output_plt = Output()
        with output_plt:
            plot_plddt_legend().show()
        grid[0, 1] = output_plt

        display.display(grid)

        # Display pLDDT and predicted aligned error (if output by the model).
        if pae_outputs:
            num_plots = 2
        else:
            num_plots = 1

        plt.figure(figsize=[8 * num_plots, 6])
        plt.subplot(1, num_plots, 1)
        plt.plot(plddts[best_model_name])
        plt.title("Predicted LDDT")
        plt.xlabel("Residue")
        plt.ylabel("pLDDT")

        if num_plots == 2:
            plt.subplot(1, 2, 2)
            plt.imshow(pae, vmin=0.0, vmax=max_pae, cmap="Greens_r")
            plt.colorbar(fraction=0.046, pad=0.04)

            # Display lines at chain boundaries.
            best_unrelaxed_prot = unrelaxed_proteins[best_model_name]
            total_num_res = best_unrelaxed_prot.residue_index.shape[-1]
            chain_ids = best_unrelaxed_prot.chain_index
            for chain_boundary in np.nonzero(chain_ids[:-1] - chain_ids[1:]):
                if chain_boundary.size:
                    plt.plot(
                        [0, total_num_res],
                        [chain_boundary, chain_boundary],
                        color="red",
                    )
                    plt.plot(
                        [chain_boundary, chain_boundary],
                        [0, total_num_res],
                        color="red",
                    )

            plt.title("Predicted Aligned Error")
            plt.xlabel("Scored residue")
            plt.ylabel("Aligned residue")

            if out is not None:
                plt.savefig(
                    os.path.join(abs_out_path, "gget_alphafold_results.png"),
                    dpi=300,
                    bbox_inches="tight",
                    transparent=True,
                )

    ## Run clean_up function
    clean_up()
