import itertools
import os
import platform
import subprocess
import sys
import time
import uuid

# Custom functions
from .compile import MUSCLE_PATH, PACKAGE_PATH, compile_muscle
from .utils import aa_colors, create_tmp_fasta, n_colors, set_up_logger

logger = set_up_logger()

# Path to precompiled muscle binary
if platform.system() == "Windows":
    PRECOMPILED_MUSCLE_PATH = os.path.join(PACKAGE_PATH, f"bins/{platform.system()}/muscle.win64.exe")
else:
    PRECOMPILED_MUSCLE_PATH = os.path.join(PACKAGE_PATH, f"bins/{platform.system()}/muscle")


def muscle(fasta, super5=False, out=None, verbose=True):
    """Align multiple nucleotide or amino acid sequences against each other (using the Muscle v5 algorithm).

    Args:
    - fasta     List of sequences or path to fasta file containing the sequences to be aligned.
    - super5    True/False (default: False).
                If True, align input using Super5 algorithm instead of PPP algorithm to decrease time and memory.
                Use for large inputs (a few hundred sequences).
    - out       Path to save an 'aligned FASTA' (.afa) file with the results, e.g. 'path/to/directory/results.afa'.
                Default: 'None' -> Results will be printed in Clustal format.
    - verbose   True/False whether to print progress information. Default True.

    Returns alignment results in an "aligned FASTA" (.afa) file.
    """
    # Muscle v5 documentation: https://drive5.com/muscle5

    # Handle command line passing path to FASTA as a list
    if isinstance(fasta, list) and len(fasta) == 1:
        fasta = fasta[0]

    if "." in fasta:
        abs_fasta_path = os.path.abspath(fasta)
        fasta_provided = True
    else:
        fasta_path = create_tmp_fasta(fasta)
        abs_fasta_path = os.path.abspath(fasta_path)
        fasta_provided = False

    # Get absolute path to output .afa file
    if out is None:
        # Create temporary .afa file
        abs_out_path = os.path.join(os.getcwd(), f"tmp_{str(uuid.uuid4())}.afa")
    else:
        directory = "/".join(out.split("/")[:-1])
        if directory != "":
            os.makedirs(directory, exist_ok=True)
        abs_out_path = os.path.abspath(out)

    # Compile muscle if it is not already compiled
    if not os.path.isfile(PRECOMPILED_MUSCLE_PATH):
        # Compile muscle
        compile_muscle()
        muscle_path = MUSCLE_PATH

    else:
        if verbose:
            logger.info("MUSCLE compiled. ")
        muscle_path = PRECOMPILED_MUSCLE_PATH

    # Replace slashes in path for Windows compatibility
    if platform.system() == "Windows":
        muscle_path = muscle_path.replace("/", "\\")
        abs_fasta_path = abs_fasta_path.replace("/", "\\")
        abs_out_path = abs_out_path.replace("/", "\\")

    if platform.system() != "Windows":
        # Assign read, write, and execute permission to muscle binary
        with subprocess.Popen(
            ["chmod", "755", muscle_path],
            stderr=subprocess.PIPE,
        ) as process_1:
            stderr_1 = process_1.stderr.read().decode("utf-8")
            # Log the standard error if it is not empty
            if stderr_1:
                sys.stderr.write(stderr_1)
        # Exit system if the subprocess returned with an error
        if process_1.wait() != 0:
            return

    # Define muscle command as list (handles paths with spaces safely)
    if super5:
        command = [muscle_path, "-super5", abs_fasta_path, "-output", abs_out_path]
    else:
        command = [muscle_path, "-align", abs_fasta_path, "-output", abs_out_path]

    # Record MUSCLE align start
    start_time = time.time()
    if verbose:
        logger.info("MUSCLE aligning... ")

    # Run muscle command and write command output
    with subprocess.Popen(command, stderr=subprocess.PIPE) as process_2:
        stderr_2 = process_2.stderr.read().decode("utf-8")
        # Log the standard error if it is not empty
        if stderr_2:
            sys.stderr.write(stderr_2)
    # Exit system if the subprocess returned with an error
    if process_2.wait() != 0:
        return
    else:
        if verbose:
            logger.info(f"MUSCLE alignment complete. Alignment time: {round(time.time() - start_time, 2)} seconds")

    if out is None:
        ## Print cleaned up muscle output
        # Get the titles and sequences from the generated .afa file
        titles = []
        seqs_master = []
        seqs = []
        with open(abs_out_path) as aln_file:
            for i, line in enumerate(aln_file):
                # Recognize title lines by the '>' character
                if line[0] == ">":
                    # Record first listed identifier as title and remove the '>'
                    titles.append(line.split(" ")[0].split(">")[1])

                    # Append list containing seqs for the previous title to master list
                    if i != 0:
                        seqs_master.append(seqs)
                    # Empty the seqs list to append the sequences for this new title
                    seqs = []
                else:
                    seqs.append(line.strip())
        # Append seqs of last title to master seq list
        seqs_master.append(seqs)

        # Set of all possible nucleotides
        nucleotides = set("ATGCN-")

        # zip_longest pads to the longest length
        for seq_pair in list(itertools.zip_longest(*seqs_master)):
            # Add some space between lines
            print("\n")
            for idx, seq in enumerate(seq_pair):
                final_seq = []
                # If sequence is a nucleotide sequence,
                # assign nulceotide colors using the custom function n_colors
                if set(seq) <= nucleotides:
                    for letter in seq:
                        final_seq.append(n_colors(letter))

                # If sequence is not a nucleotide sequence, I assume it is an amino acid sequence
                # and assign amino acid colors using the custom function aa_colors
                else:
                    for letter in seq:
                        final_seq.append(aa_colors(letter))

                print(titles[idx], "\t", "".join(final_seq))

        # Remove temporary .afa file
        os.remove(abs_out_path)

    #  Remove temp .fa file if not provided by user
    if not fasta_provided:
        os.remove(abs_fasta_path)
