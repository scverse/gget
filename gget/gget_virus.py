import os
import re
import json
import sys           # For accessing command line arguments
import time          # For adding delays between requests
import logging       # For logging level checks
import shutil        # For directory operations  
import subprocess    # For executing external commands
import traceback     # For error traceback logging
import platform      # For OS detection
import stat          # For file permission constants
import gc            # For garbage collection to manage memory
import pandas as pd  # For data manipulation and CSV output
import requests      # For HTTP requests to NCBI API
import zipfile       # For extracting downloaded ZIP files
from tqdm import tqdm            # For progress bar display
from datetime import datetime  # For date handling
from dateutil import parser  # For flexible date parsing
import xml.etree.ElementTree as ET # For XML parsing
import http.client
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib.parse import quote
import calendar

# Internal imports for logging, unique ID generation, and FASTA parsing
from .utils import set_up_logger, FastaIO
from .constants import NCBI_API_BASE, NCBI_EUTILS_BASE_EFETCH, NCBI_EUTILS_BASE_ESEARCH
from .compile import PACKAGE_PATH

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# =============================================================================
# MODULE-LEVEL CONSTANTS
# =============================================================================

# API and Network Configuration
API_PAGE_SIZE = 1000  # Maximum records per API request (NCBI limit)
API_REQUEST_TIMEOUT = 120  # Timeout in seconds for API requests (increased for large pages)
API_MAX_RETRIES = 5  # Maximum retry attempts for failed API requests
API_INITIAL_RETRY_DELAY = 3.0  # Initial delay in seconds between retries
API_RETRY_BACKOFF_MULTIPLIER = 2.0  # Multiplier for exponential backoff
MAX_RETRY_DELAY = 30  # Maximum delay in seconds between retries (caps exponential growth)
MIN_PAGE_SIZE_FALLBACK = 20  # Minimum page size to try before giving up
PAGE_SIZE_FALLBACK_DECREMENT = 50  # Decrease page size by this amount on retry

# E-utilities Configuration
EUTILS_TIMEOUT = 300  # Timeout in seconds for E-utilities requests
EUTILS_DEFAULT_BATCH_SIZE = 200  # Default batch size for E-utilities requests
EUTILS_INTER_BATCH_DELAY = 0.5  # Delay in seconds between batch requests
EUTILS_INTER_BATCH_DELAY_WITH_KEY = 0.11  # Delay when using API key (10 req/sec allowed)
EUTILS_MIN_BATCH_SIZE_FOR_SPLIT = 50  # Minimum batch size before giving up on splitting

# EPost + EFetch History Server Configuration
EPOST_BATCH_SIZE = 500  # Max accessions per EPost call (NCBI recommended)
EFETCH_FASTA_RETMAX = 500  # Records per EFetch call when downloading FASTA via History Server

# GenBank Configuration
GENBANK_DEFAULT_BATCH_SIZE = 200  # Default batch size for GenBank requests
GENBANK_INTER_BATCH_DELAY = 0.35  # Delay in seconds between GenBank batch requests
GENBANK_MAX_BATCH_SIZE_WARNING = 500  # Warn user if batch size exceeds this
GENBANK_RETRY_ATTEMPTS = 5  # Number of retry attempts for GenBank requests
GENBANK_XML_CHUNK_SIZE = 10000  # Rows to process before writing to CSV
GENBANK_COMPLEXITY = 1 # Complexity level with only the accessions requested. All levels explained here: https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch

# Resolve API key from environment variable NCBI_API_KEY.
# Users can also pass an api_key argument directly to the virus() function / CLI --api_key.
# Without an API key, NCBI E-utilities rate limit is 3 requests/sec;
# with a key it increases to 10 requests/sec.
API_KEY = os.environ.get("NCBI_API_KEY")

# Subprocess and Download Configuration
SUBPROCESS_VERSION_TIMEOUT = 5  # Timeout for version check commands
DOWNLOAD_OVERALL_TIMEOUT = 1800  # Maximum total download time (30 minutes)
DOWNLOAD_PROGRESS_TIMEOUT = 300  # Maximum time without progress (5 minutes)
DOWNLOAD_PROGRESS_CHECK_INTERVAL = 0.1  # Interval for checking download progress

# Chunked Download Configuration (for large datasets)
CHUNKED_DOWNLOAD_START_YEAR = 1970  # Default start year for chunked downloads
CHUNKED_DOWNLOAD_INTER_CHUNK_DELAY = 0.5  # Delay between yearly chunks

# NCBI Taxonomy IDs
NCBI_ALL_VIRUSES_TAXID = "10239"  # Taxonomy ID for all viruses
NCBI_SARS_COV2_TAXID = "2697049"  # Taxonomy ID for SARS-CoV-2
NCBI_ALPHAINFLUENZA_GENUS_TAXID = "197911"  # Alphainfluenza genus
NCBI_ALPHAINFLUENZA_SPECIES_TAXID = "2955291"  # Alphainfluenzavirus influenzae species
NCBI_INFLUENZA_A_TAXID = "11320"  # Influenza A virus

# Virus Detection Identifiers
SARS_COV2_IDENTIFIERS = {
    'sarscov2', 'sars2', '2697049', 'sarscov', 
    'severeacuterespiratorysyndromecoronavirus2',
    'covid19', 'covid', 'coronavirusdisease', 'ncov', 'hcov19'
}

ALPHAINFLUENZA_IDENTIFIERS = {
    'alphainfluenza', 'alphainfluenzavirus', 'alphainfluenzavirusinfluenzae',
    'influenzaavirus', 'influenzaa', 'flua',
    '197911',  # Alphainfluenza genus
    '2955291',  # Alphainfluenzavirus influenzae species
    '11320'  # Influenza A virus
}

# Default taxon for Alphainfluenza downloads (most comprehensive cached data)
ALPHAINFLUENZA_DEFAULT_TAXON = "Alphainfluenzavirus influenzae"

# Progress Indicator Keywords (for subprocess monitoring)
PROGRESS_INDICATORS = ['%', '=', 'downloading', 'fetching', 'MB', 'GB', 'bytes']

# Protein/Gene Keywords for Header Parsing
PROTEIN_KEYWORDS = [
    'hemagglutinin', 'neuraminidase', 'polymerase', 'nucleoprotein',
    'matrix protein', 'nonstructural protein', 'ns1', 'ns2',
    'spike', 'envelope', 'membrane', 'nucleocapsid',
    'orf', 'nsp', 'pp1a', 'pp1ab',
    'segment 1', 'segment 2', 'segment 3', 'segment 4',
    'segment 5', 'segment 6', 'segment 7', 'segment 8',
]

# Date Parsing Configuration
DATE_PARSE_DEFAULT_YEAR = 1500  # Default year for incomplete date strings

# HTTP Retry Configuration
HTTP_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]  # Status codes to retry on
HTTP_MAX_LOCAL_RETRIES = 3  # Maximum local retry attempts
HTTP_INITIAL_BACKOFF = 1.0  # Initial backoff in seconds

# File Size Configuration
BYTES_PER_MB = 1024 * 1024  # Bytes in a megabyte for file size display diviser
MIN_VALID_ZIP_SIZE = 5 * 1024  # 100 KB in bytes (minimum size for a valid ZIP file from cached downloads)
MIN_VALID_FASTA_SIZE_MB = 0.1  # Minimum size in MB for a valid FASTA file (100 KB)

# URL Length Configuration
# Most browsers and servers support URLs up to ~2000-8000 chars, but NCBI recommends keeping under 2000
# We use a conservative limit to ensure compatibility
MAX_URL_LENGTH = 2000  # Maximum URL length for API requests
ACCESSION_URL_ENCODING = "%2C"  # URL-encoded comma for joining accessions
ACCESSION_AVG_LENGTH = 11  # Average length of an accession number (e.g., "NC_045512.2")
BUFFER_SIZE = 200  # Buffer for URL query parameters (filters) and safety margin

# Batched Processing Configuration
METADATA_CSV_CHUNK_SIZE = 50000  # Number of metadata records to process per chunk for CSV output
FASTA_STREAM_LOG_INTERVAL = 100000  # Log progress every N sequences during FASTA streaming

# =============================================================================
# End of Constants
# =============================================================================

# =============================================================================
# MEMORY MONITORING HELPERS
# =============================================================================

def _get_memory_usage():
    """
    Get current memory usage information for debugging.
    
    Returns:
        dict: Dictionary with memory stats including:
            - rss_mb: Resident Set Size in MB (actual RAM used)
            - vms_mb: Virtual Memory Size in MB
            - percent: Percent of total system memory used
            - available_mb: Available system memory in MB
            
    Note:
        Falls back to /proc/self/status on Linux if psutil is not available.
    """
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            sys_mem = psutil.virtual_memory()
            
            return {
                'rss_mb': mem_info.rss / (1024 * 1024),
                'vms_mb': mem_info.vms / (1024 * 1024),
                'percent': process.memory_percent(),
                'available_mb': sys_mem.available / (1024 * 1024),
                'total_mb': sys_mem.total / (1024 * 1024),
                'system_percent': sys_mem.percent,
                'psutil_available': True
            }
        except Exception as e:
            pass  # Fall through to /proc fallback
    
    # Fallback for Linux: read from /proc/self/status
    result = {
        'rss_mb': None,
        'vms_mb': None, 
        'percent': None,
        'available_mb': None,
        'psutil_available': False
    }
    
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS is in kB
                    rss_kb = int(line.split()[1])
                    result['rss_mb'] = rss_kb / 1024
                elif line.startswith('VmSize:'):
                    vms_kb = int(line.split()[1])
                    result['vms_mb'] = vms_kb / 1024
    except (FileNotFoundError, PermissionError, ValueError):
        pass  # Not on Linux or can't read /proc
    
    # Try to get system memory from /proc/meminfo
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    avail_kb = int(line.split()[1])
                    result['available_mb'] = avail_kb / 1024
                elif line.startswith('MemTotal:'):
                    total_kb = int(line.split()[1])
                    result['total_mb'] = total_kb / 1024
    except (FileNotFoundError, PermissionError, ValueError):
        pass
    
    # Calculate percent if we have both values
    if result.get('rss_mb') and result.get('total_mb'):
        result['percent'] = (result['rss_mb'] / result['total_mb']) * 100
    
    return result


def _log_memory_usage(context=""):
    """
    Log current memory usage with context information.
    
    Args:
        context (str): Description of where in the code this is being called.
    """
    mem = _get_memory_usage()
    
    if not mem.get('psutil_available'):
        logger.debug("Memory monitoring: psutil not available (install with 'pip install psutil' for memory debugging)")
        return
    
    if mem.get('rss_mb') is not None:
        logger.info("📊 MEMORY [%s]: Process RSS=%.1f MB (%.1f%%), System: %.1f%% used, %.1f MB available of %.1f MB total",
                   context,
                   mem['rss_mb'],
                   mem.get('percent', 0),
                   mem.get('system_percent', 0),
                   mem.get('available_mb', 0),
                   mem.get('total_mb', 0))
    else:
        logger.debug("Memory monitoring: Unable to get memory info - %s", mem.get('error', 'unknown error'))


def _force_garbage_collection(context=""):
    """
    Force garbage collection and log the results.
    
    Args:
        context (str): Description of where in the code this is being called.
    """
    before = _get_memory_usage()
    collected = gc.collect()
    after = _get_memory_usage()
    
    if before.get('rss_mb') is not None and after.get('rss_mb') is not None:
        freed = before['rss_mb'] - after['rss_mb']
        logger.info("🗑️ GC [%s]: Collected %d objects, freed %.1f MB (%.1f MB -> %.1f MB)",
                   context, collected, freed, before['rss_mb'], after['rss_mb'])
    else:
        logger.debug("GC [%s]: Collected %d objects", context, collected)


# =============================================================================
# END OF MEMORY MONITORING HELPERS
# =============================================================================

# Set up logger for this module
logger = set_up_logger()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
random_suffix = os.urandom(3).hex() # random suffix for naming uniqueness

# Path to precompiled datasets binary
if platform.system() == "Windows":
    PRECOMPILED_DATASETS_PATH = os.path.join(
        PACKAGE_PATH, "bins", "Windows", "datasets.exe"
    )
else:
    PRECOMPILED_DATASETS_PATH = os.path.join(
        PACKAGE_PATH, "bins", platform.system(), "datasets"
    )

# Cache for the datasets path to avoid repeated checks
_datasets_path_cache = None

# =============================================================================
# HELPER FUNCTIONS FOR RETRIES AND ERROR TRACKING
# =============================================================================

def _retry_with_exponential_backoff(
    operation_name,
    operation_func,
    max_retries=API_MAX_RETRIES,
    initial_delay=API_INITIAL_RETRY_DELAY,
    backoff_multiplier=API_RETRY_BACKOFF_MULTIPLIER,
    max_delay=MAX_RETRY_DELAY,
    retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError),
    failed_commands=None,
):
    """
    Execute an operation with exponential backoff retry logic.
    
    This is a reusable helper that consolidates the exponential backoff retry
    pattern used throughout the module. It handles retryable exceptions with
    configurable delays and logging.
    
    Args:
        operation_name (str): Name of the operation for logging (e.g., "batch_10").
        operation_func (callable): Function to execute, should raise an exception on failure.
        max_retries (int): Maximum number of retry attempts.
        initial_delay (float): Initial delay in seconds between retries.
        backoff_multiplier (float): Multiplier for exponential backoff.
        retryable_exceptions (tuple): Exception types to retry on.
        failed_commands (dict, optional): Dictionary to track failed operations.
        
    Returns:
        tuple: (success, result, error_info)
            - success (bool): True if operation succeeded.
            - result: Return value of operation_func (or None if failed).
            - error_info (dict): Details about the failure (if any).
    """
    retry_delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            result = operation_func()
            return True, result, None
            
        except retryable_exceptions as e:
            last_exception = e
            is_retryable = True
            
            # For HTTPError, check if it's a server error (5xx)
            if isinstance(e, requests.exceptions.HTTPError) and hasattr(e, 'response') and e.response:
                is_retryable = 500 <= e.response.status_code < 600
            
            if attempt < max_retries - 1 and is_retryable:
                capped_delay = min(retry_delay, max_delay)
                logger.warning(
                    "⚠️ %s failed (attempt %d/%d): %s. Retrying in %.1f seconds...",
                    operation_name, attempt + 1, max_retries, e, capped_delay
                )
                time.sleep(capped_delay)
                retry_delay *= backoff_multiplier
                continue
            else:
                # Out of retries or non-retryable error
                break
                
        except Exception as e:
            # Non-retryable exception types
            last_exception = e
            break
    
    # Operation failed after retries
    error_info = {
        'error': str(last_exception),
        'exception_type': type(last_exception).__name__,
    }
    
    return False, None, error_info


def _track_failed_operation(failed_commands, operation_type, batch_info, error_info):
    """
    Track a failed operation in the failed_commands dictionary.
    
    This ensures consistent error tracking across all operation types for
    later reporting in the command summary.
    
    Args:
        failed_commands (dict): Dictionary to track failures.
        operation_type (str): Type of operation ('metadata_batch', 'sequence_batch', 'pagination', etc.).
        batch_info (dict): Information about the failed batch/operation.
        error_info (dict): Error details from the operation.
    """
    if failed_commands is None:
        return
    
    if operation_type not in failed_commands:
        failed_commands[operation_type] = []
    
    failure_record = {**batch_info, **error_info}
    failed_commands[operation_type].append(failure_record)
    logger.debug("Tracked failed %s: %s", operation_type, failure_record)


def _validate_datasets_binary(path):
    """
    Validate that a datasets binary exists and is functional.
    
    Args:
        path (str): Path to the datasets binary to validate.
        
    Returns:
        bool: True if the binary exists and runs successfully, False otherwise.
    """
    if not path:
        return False
    
    # Check if the file exists (for bundled binary) or is in PATH (for system binary)
    if not os.path.isfile(path) and not shutil.which(path):
        return False
    
    # Verify the binary actually works
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_VERSION_TIMEOUT,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return False


def _clear_datasets_cache():
    """
    Clear the cached datasets path, forcing re-detection on next call.
    
    This is useful when the environment changes (e.g., user installs/uninstalls
    the datasets CLI) or when the cached binary becomes unavailable.
    """
    global _datasets_path_cache
    _datasets_path_cache = None
    logger.debug("Cleared datasets path cache")


def _get_datasets_path():
    """
    Get the path to the NCBI datasets CLI binary.

    This helper first checks if datasets is available in the system PATH.
    If found, it uses the system-installed version. Otherwise, it falls back
    to the precompiled binary bundled with gget.

    The result is cached after the first successful call. The cache is automatically
    invalidated if the cached binary becomes unavailable (e.g., deleted or environment
    changed), triggering re-detection.

    Returns:
        str: Path to the datasets binary ("datasets" for system PATH, or full path for bundled).

    Raises:
        RuntimeError: If no working datasets binary is available.
    """
    global _datasets_path_cache
    
    # If we have a cached path, validate it's still working
    if _datasets_path_cache is not None:
        if _validate_datasets_binary(_datasets_path_cache):
            return _datasets_path_cache
        else:
            # Cached binary is no longer valid, clear cache and re-detect
            logger.warning(
                "⚠️ Previously cached datasets binary at '%s' is no longer available. "
                "Re-detecting...", _datasets_path_cache
            )
            _clear_datasets_cache()
    
    # First, check if datasets is available in the system PATH
    datasets_path = shutil.which("datasets")
    if datasets_path:
        try:
            result = subprocess.run(
                [datasets_path, "--version"],
                capture_output=True,
                text=True,
                timeout=SUBPROCESS_VERSION_TIMEOUT,
            )
            if result.returncode == 0:
                logger.info(
                    "✅ Using system-installed NCBI datasets CLI: %s", result.stdout.strip()
                )
                _datasets_path_cache = datasets_path
                return datasets_path
        except (subprocess.TimeoutExpired, OSError):
            pass  # System binary didn't work, try bundled
    
    # Fall back to the bundled binary
    datasets_path = PRECOMPILED_DATASETS_PATH
    
    # Check if the precompiled binary exists
    if not os.path.isfile(datasets_path):
        raise RuntimeError(
            f"NCBI datasets binary not found at {datasets_path}. "
            "Please reinstall gget to restore the bundled datasets binary, "
            "or install the NCBI datasets CLI manually: "
            "https://www.ncbi.nlm.nih.gov/datasets/docs/v2/download-and-install/"
        )
    
    # On non-Windows systems, ensure the binary is executable
    if platform.system() != "Windows":
        try:
            os.chmod(datasets_path, os.stat(datasets_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError as e:
            raise RuntimeError(
                f"Failed to make NCBI datasets binary executable: {e}"
            )
    
    # Verify the bundled binary works
    try:
        result = subprocess.run(
            [datasets_path, "--version"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_VERSION_TIMEOUT,
        )
        if result.returncode == 0:
            logger.info(
                "✅ Using bundled NCBI datasets CLI: %s", result.stdout.strip()
            )
            _datasets_path_cache = datasets_path
            return datasets_path
    except (subprocess.TimeoutExpired, OSError) as e:
        raise RuntimeError(
            f"Failed to verify bundled NCBI datasets binary at {datasets_path}: {e}"
        )
    
    raise RuntimeError(
        f"NCBI datasets binary at {datasets_path} failed verification."
    )


def _get_datasets_version():
    """
    Get the version of the NCBI datasets CLI if available.
    
    Attempts to retrieve the version string from the datasets binary.
    Returns None if datasets is not available or version check fails.
    
    Returns:
        str or None: Version string from datasets (e.g., "16.11.0") or None if unavailable.
    """
    try:
        datasets_path = _get_datasets_path()
        result = subprocess.run(
            [datasets_path, "--version"],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_VERSION_TIMEOUT,
        )
        if result.returncode == 0:
            # Extract version from output (e.g., "datasets version 16.11.0")
            version_output = result.stdout.strip()
            logger.debug("Datasets version output: %s", version_output)
            return version_output
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as e:
        logger.debug("Could not retrieve datasets version: %s", e)
    
    return None


def _get_gget_version():
    """
    Get the version of gget.
    
    Returns:
        str: Version string (e.g., "1.2.0") or "unknown" if not available.
    """
    try:
        from . import __version__
        return __version__
    except (ImportError, AttributeError):
        return "unknown"


def _get_modified_virus_name(virus_name, attempt=1):
    """
    Modify the virus name for retry attempts when the NCBI server is unreachable.
    
    This function generates alternative virus names to try when the initial
    query fails due to server unreachability. The modification strategies are:
        1. (attempt=1) If the name contains parentheses, remove them and their contents.
           (e.g., "Lassa virus (LASV)" -> "Lassa virus")
        2. (attempt=2) If the name doesn't contain "virus" anywhere, append " virus" to it.
           (e.g., "Dengue" -> "Dengue virus")
        3. (attempt=2) If the name ends with "virus" without a space, add a space.
           (e.g., "Denguevirus" -> "Dengue virus")
    
    Args:
        virus_name (str): Original virus name that failed.
        attempt (int): Which modification attempt this is (1 or 2).
        
    Returns:
        str or None: Modified virus name to retry, or None if no modification is possible.
        
    Example:
        >>> _get_modified_virus_name("Lassa virus (LASV)", attempt=1)
        'Lassa virus'
        >>> _get_modified_virus_name("Dengue", attempt=1)
        None  # No parentheses to remove
        >>> _get_modified_virus_name("Dengue", attempt=2)
        'Dengue virus'
        >>> _get_modified_virus_name("Denguevirus", attempt=2)
        'Dengue virus'
        >>> _get_modified_virus_name("Dengue virus", attempt=2)
        None  # Already contains "virus" properly
    """
    if not virus_name:
        return None
    
    virus_lower = virus_name.lower().strip()
    
    # Attempt 1: Try removing parenthetical content
    if attempt == 1:
        # Check if there are parentheses to remove
        if '(' in virus_name and ')' in virus_name:
            # Remove parenthetical content (e.g., "(LASV)" or "(strain XYZ)")
            modified = re.sub(r'\s*\([^)]*\)\s*', ' ', virus_name).strip()
            # Clean up any double spaces
            modified = re.sub(r'\s+', ' ', modified)
            if modified and modified.lower() != virus_lower:
                logger.debug("Modified virus name by removing parentheses: '%s' -> '%s'", 
                            virus_name, modified)
                return modified
        return None
    
    # Attempt 2: Try adding "virus" suffix or spacing
    if attempt == 2:
        # Check if the name already contains "virus" anywhere (case-insensitive)
        if "virus" in virus_lower:
            # Add a space before "virus" only if there isn't one already
            idx = virus_name.lower().rfind("virus")
            if idx > 0 and virus_name[idx - 1] != ' ':
                modified = virus_name[:idx] + " " + virus_name[idx:]
                logger.debug("Modified virus name by adding space before 'virus': '%s' -> '%s'", 
                            virus_name, modified)
                return modified
            # Already has "virus" correctly spaced in the name, no modification needed
            return None
        
        # Name doesn't contain "virus" anywhere, so append " virus"
        modified = virus_name + " virus"
        logger.debug("Modified virus name by appending ' virus': '%s' -> '%s'", 
                    virus_name, modified)
        return modified
    
    return None


def _parse_accession_input(accession_input):
    """
    Parse accession input which can be:
    1. Single accession: 'NC_045512.2'
    2. Space-separated accessions: 'NC_045512.2 MN908947.3 MT020781.1'
    3. Path to text file: '/path/to/accessions.txt' (one accession per line)
    
    Args:
        accession_input (str): The accession input string.
        
    Returns:
        dict: A dictionary with keys:
            - 'type': 'single', 'list', or 'file'
            - 'accessions': list of accession strings (for 'list' type) or single accession (for 'single')
            - 'file_path': file path (for 'file' type only)
            - 'is_file': True if input is a file path
            
    Raises:
        ValueError: If file path doesn't exist or file is empty.
        
    Example:
        >>> _parse_accession_input('NC_045512.2')
        {'type': 'single', 'accessions': 'NC_045512.2', 'file_path': None, 'is_file': False}
        
        >>> _parse_accession_input('NC_045512.2 MN908947.3')
        {'type': 'list', 'accessions': ['NC_045512.2', 'MN908947.3'], 'file_path': None, 'is_file': False}
        
        >>> _parse_accession_input('/path/to/accessions.txt')
        {'type': 'file', 'accessions': ['NC_045512.2', 'MN908947.3', ...], 'file_path': '/path/to/accessions.txt', 'is_file': True}
    """
    accession_input = accession_input.strip()
    
    # Check if input is a file path
    if os.path.isfile(accession_input):
        logger.info("Parsing accession numbers from file: %s", accession_input)
        try:
            with open(accession_input, 'r') as f:
                accessions = [line.strip() for line in f if line.strip()]
            
            if not accessions:
                raise ValueError(f"Accession file {accession_input} is empty.")
            
            logger.info("Loaded %d accession(s) from file", len(accessions))
            return {
                'type': 'file',
                'accessions': accessions,
                'file_path': accession_input,
                'is_file': True
            }
        except IOError as e:
            raise ValueError(f"Error reading accession file {accession_input}: {e}")
    
    # Check if input is space-separated accessions
    if ' ' in accession_input:
        accessions = accession_input.split()
        logger.info("Parsed %d accession(s) from space-separated input", len(accessions))
        return {
            'type': 'list',
            'accessions': accessions,
            'file_path': None,
            'is_file': False
        }
    
    # Single accession
    logger.debug("Single accession input: %s", accession_input)
    return {
        'type': 'single',
        'accessions': accession_input,
        'file_path': None,
        'is_file': False
    }


def _parse_baseline_file(baseline_path):
    """
    Parse a baseline metadata file to extract accession numbers for deduplication.
    
    Supports multiple file formats:
    - CSV: Looks for 'accession' column (case-insensitive)
    - JSONL: Looks for 'accession' key in each JSON object
    - JSON: Looks for 'accession' key in a list of objects
    - Text: Treats each non-empty line as an accession number
    
    Accession numbers are normalized (stripped, lowercased) for consistent comparison.
    
    Args:
        baseline_path (str): Path to the baseline metadata file.
        
    Returns:
        set: Set of normalized accession numbers from the baseline file.
        
    Raises:
        FileNotFoundError: If the baseline file does not exist.
        ValueError: If no accessions could be extracted.
    """
    if not baseline_path or not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}")
    
    baseline_accessions = set()
    file_ext = os.path.splitext(baseline_path)[1].lower()

    logger.info("Parsing baseline file: %s (format: %s)", baseline_path, file_ext or "auto-detect")
    
    try:
        if file_ext == '.csv':
            # CSV format: look for 'accession' column
            df = pd.read_csv(baseline_path, low_memory=False)
            # Case-insensitive column name search
            acc_col = None
            for col in df.columns:
                if col.strip().lower() == 'accession':
                    acc_col = col
                    break
            if acc_col is None:
                raise ValueError(
                    f"Baseline CSV file '{baseline_path}' has no 'accession' column. "
                    f"Available columns: {list(df.columns)}"
                )
            baseline_accessions = set(
                str(acc).strip().lower() for acc in df[acc_col].dropna() if str(acc).strip()
            )
            
        elif file_ext == '.jsonl':
            # JSONL format: one JSON object per line
            with open(baseline_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        acc = record.get('accession', '')
                        if acc and str(acc).strip():
                            baseline_accessions.add(str(acc).strip().lower())
                    except json.JSONDecodeError:
                        logger.debug("Skipping invalid JSON on line %d of baseline file", line_num)
                        
        elif file_ext == '.json':
            # JSON format: list of objects
            with open(baseline_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                for record in data:
                    if isinstance(record, dict):
                        acc = record.get('accession', '')
                        if acc and str(acc).strip():
                            baseline_accessions.add(str(acc).strip().lower())
            elif isinstance(data, dict):
                # Single object or dict of accession -> metadata
                for key in data:
                    baseline_accessions.add(str(key).strip().lower())

        else:
            # Text format or unknown: try CSV first, then fall back to line-per-accession
            try:
                df = pd.read_csv(baseline_path, low_memory=False)
                acc_col = None
                for col in df.columns:
                    if col.strip().lower() == 'accession':
                        acc_col = col
                        break
                if acc_col is not None:
                    baseline_accessions = set(
                        str(acc).strip().lower() for acc in df[acc_col].dropna() if str(acc).strip()
                    )
                    logger.debug("Auto-detected CSV format with 'accession' column")
                else:
                    raise ValueError("No accession column found, trying text format")
            except (ValueError, pd.errors.ParserError):
                # Fall back to text format: one accession per line
                with open(baseline_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Take first whitespace-delimited token as accession
                            acc = line.split()[0]
                            baseline_accessions.add(acc.lower())
                logger.debug("Parsed as text format (one accession per line)")
    
    except (FileNotFoundError, ValueError):
        raise
    except Exception as e:
        raise ValueError(f"Failed to parse baseline file '{baseline_path}': {e}") from e
    
    if not baseline_accessions:
        raise ValueError(
            f"No accessions found in baseline file '{baseline_path}'. "
            f"Ensure the file contains accession numbers."
        )
    
    logger.info("✅ Loaded %d accessions from baseline file", len(baseline_accessions))
    return baseline_accessions


def _deduplicate_metadata_against_baseline(metadata_dict, baseline_accessions):
    """
    Remove metadata records whose accessions are already in the baseline set.
    
    Args:
        metadata_dict (dict): Dictionary mapping accession -> metadata.
        baseline_accessions (set): Set of normalized accession numbers from baseline.
        
    Returns:
        tuple: (new_metadata_dict, skipped_count)
    """
    new_metadata = {}
    skipped_count = 0

    for acc, meta in metadata_dict.items():
        if acc.strip().lower() in baseline_accessions:
            skipped_count += 1
        else:
            new_metadata[acc] = meta

    logger.info("Deduplication results: %d new, %d skipped (already in baseline)",
               len(new_metadata), skipped_count)
    return new_metadata, skipped_count


def _save_partial_metadata(metadata_dict, outfolder, virus_clean, reason="api_failure"):
    """
    Save partial metadata to CSV for recovery via --baseline.

    Args:
        metadata_dict (dict): Dictionary mapping accession -> metadata.
        outfolder (str): Output folder for the partial file.
        virus_clean (str): Sanitized virus name for the filename.
        reason (str): Reason for saving (for the filename).

    Returns:
        str or None: Path to the saved partial metadata file.
    """
    if not metadata_dict:
        return None

    os.makedirs(outfolder, exist_ok=True)
    partial_file = os.path.join(outfolder, f"{virus_clean}_partial_{timestamp}.csv")

    try:
        rows = []
        for acc, meta in metadata_dict.items():
            row = {'accession': acc}
            for key in ['virus_name', 'length', 'completeness', 'releaseDate',
                        'location', 'sourceDatabase', 'isolateName']:
                if key in meta:
                    row[key] = meta[key]
            host_info = meta.get('host', {})
            if isinstance(host_info, dict):
                row['host'] = host_info.get('organism_name', '')
            elif host_info:
                row['host'] = str(host_info)
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(partial_file, index=False)
        logger.info("Partial metadata saved: %s (%d records)", partial_file, len(df))
        return partial_file
    except Exception as e:
        logger.warning("Failed to save partial metadata: %s", e)
        return None


def _merge_baseline_with_new(baseline_path, new_metadata_list, output_path):
    """
    Merge baseline metadata with newly fetched metadata into a single CSV.

    Args:
        baseline_path (str): Path to the baseline metadata file.
        new_metadata_list (list): List of new metadata dictionaries.
        output_path (str): Path for the merged CSV output.

    Returns:
        bool: True if merge was successful, False otherwise.
    """
    try:
        # Load baseline data
        file_ext = os.path.splitext(baseline_path)[1].lower()
        
        if file_ext == '.csv':
            baseline_df = pd.read_csv(baseline_path, low_memory=False)
        elif file_ext == '.jsonl':
            records = []
            with open(baseline_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            baseline_df = pd.DataFrame(records)
        elif file_ext == '.json':
            with open(baseline_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                baseline_df = pd.DataFrame(data)
            elif isinstance(data, dict):
                baseline_df = pd.DataFrame(list(data.values()) if all(isinstance(v, dict) for v in data.values()) else [data])
            else:
                baseline_df = pd.DataFrame()
        else:
            accessions = []
            with open(baseline_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        accessions.append(line.split()[0])
            baseline_df = pd.DataFrame({'accession': accessions})
        
        # Create new DataFrame from new metadata
        if new_metadata_list:
            new_df = pd.DataFrame(new_metadata_list)
        else:
            new_df = pd.DataFrame()
        
        # Merge: concatenate baseline + new
        merged_df = pd.concat([baseline_df, new_df], ignore_index=True, sort=False)

        acc_col = None
        for col in merged_df.columns:
            if col.strip().lower() == 'accession':
                acc_col = col
                break
        if acc_col:
            merged_df = merged_df.drop_duplicates(subset=[acc_col], keep='last')
        
        merged_df.to_csv(output_path, index=False)
        logger.info("Merged output saved: %s (%d total records)", output_path, len(merged_df))
        return True
        
    except Exception as e:
        logger.error("❌ Failed to merge baseline with new metadata: %s", e)
        return False


def _calculate_max_accessions_per_batch(base_url_length):
    """
    Calculate the maximum number of accessions that can fit in a single API URL.
    
    The NCBI API URL format for multiple accessions is:
    https://api.ncbi.nlm.nih.gov/datasets/v2/virus/accession/ACC1%2CACC2%2CACC3/dataset_report
    
    Args:
        base_url_length (int): Length of the base URL without accessions.
        
    Returns:
        int: Maximum number of accessions per batch.
        
    Example:
        >>> _calculate_max_accessions_per_batch(80)
        100  # Approximate, depends on accession lengths
    """
    # Calculate available space for accessions
    available_length = MAX_URL_LENGTH - base_url_length - BUFFER_SIZE  
    
    # Each accession takes: average accession length + URL-encoded comma (%2C = 3 chars)
    chars_per_accession = ACCESSION_AVG_LENGTH + len(ACCESSION_URL_ENCODING)
    
    max_accessions = max(1, available_length // chars_per_accession)
    logger.debug("Calculated max accessions per batch: %d (URL limit: %d, base URL: %d)", 
                max_accessions, MAX_URL_LENGTH, base_url_length)
    
    return max_accessions


def _batch_accessions_for_url(accessions, base_url_length):
    """
    Split a list of accessions into batches that fit within URL length limits.
    
    Args:
        accessions (list): List of accession numbers.
        base_url_length (int): Length of the base URL without accessions.
        
    Returns:
        list: List of accession batches (each batch is a list of accessions).
        
    Example:
        >>> batches = _batch_accessions_for_url(['NC_045512.2', 'MN908947.3', ...], 80)
        >>> len(batches)  # Number of batches needed
        3
    """
    max_per_batch = _calculate_max_accessions_per_batch(base_url_length)
    
    batches = []
    for i in range(0, len(accessions), max_per_batch):
        batch = accessions[i:i + max_per_batch]
        batches.append(batch)
    
    logger.info("Split %d accessions into %d batches (max %d per batch)", 
               len(accessions), len(batches), max_per_batch)
    
    return batches


def _fetch_metadata_for_accession_list(
    accessions,
    host=None,
    geographic_location=None,
    annotated=None,
    complete_only=None,
    min_release_date=None,
    refseq_only=None,
    failed_commands=None,
    temp_output_dir=None,
):
    """
    Fetch metadata for a list of accessions, handling URL length limits with retries.
    
    This function fetches metadata for multiple accessions by:
    1. Splitting the accession list into batches that fit within URL limits
    2. Making separate API calls for each batch with exponential backoff retries
    3. Combining all results into a single list
    4. Continuing processing even if some batches fail (graceful degradation)
    
    The NCBI API URL format for multiple accessions is:
    https://api.ncbi.nlm.nih.gov/datasets/v2/virus/accession/ACC1%2CACC2%2CACC3/dataset_report
    
    Args:
        accessions (list): List of accession numbers to fetch.
        host (str, optional): Host organism filter.
        geographic_location (str, optional): Geographic location filter.
        annotated (bool, optional): Annotation status filter.
        complete_only (bool, optional): Complete genome filter.
        min_release_date (str, optional): Minimum release date filter.
        refseq_only (bool, optional): RefSeq only filter.
        failed_commands (dict, optional): Dictionary to track failed operations.
        temp_output_dir (str, optional): Directory for temporary files.
        
    Returns:
        list: Combined list of metadata records from all batches. 
              Returns partial results even if some batches fail.
        
    Raises:
        RuntimeError: If all batches fail to fetch.
    """
    if not accessions:
        logger.warning("No accessions provided to fetch metadata for")
        return []
    
    # Initialize failed_commands tracking if not already done
    if failed_commands is not None and 'api_batches' not in failed_commands:
        failed_commands['api_batches'] = []
    
    # Calculate base URL length for batch sizing
    # BUFFER_SIZE accounts for query parameters (filters) added by fetch_virus_metadata
    base_url_length = len(f"{NCBI_API_BASE}/virus/accession//dataset_report")
    
    # Split accessions into URL-safe batches
    batches = _batch_accessions_for_url(accessions, base_url_length)
    
    all_reports = []
    failed_batches = []
    aggregated_deferred_filters = None  # Track deferred filters from batches
    
    logger.info("Fetching metadata for %d accessions in %d batch(es) with exponential backoff retries", 
               len(accessions), len(batches))
    
    for batch_num, batch in tqdm(enumerate(batches, 1), total=len(batches), desc="Fetching accession batches", unit="batch", disable=len(batches)==1):
        logger.info("Processing accession batch %d/%d (%d accessions)", 
                   batch_num, len(batches), len(batch))
        
        # Join accessions with URL-encoded comma for the API URL
        accession_string = ACCESSION_URL_ENCODING.join(batch)
        
        # Define the fetch operation for retries
        def fetch_batch_metadata():
            """Callable for retry helper"""
            return fetch_virus_metadata(
                virus=accession_string,
                accession=True,  # This is an accession-based query
                host=host,
                geographic_location=geographic_location,
                annotated=annotated,
                complete_only=complete_only,
                min_release_date=min_release_date,
                refseq_only=refseq_only,
                failed_commands=failed_commands,
                temp_output_dir=temp_output_dir,
            )
        
        # Use exponential backoff helper for batch retries
        success, batch_result, error_info = _retry_with_exponential_backoff(
            operation_name=f"Accession batch {batch_num}/{len(batches)} ({len(batch)} accessions)",
            operation_func=fetch_batch_metadata,
            max_retries=API_MAX_RETRIES,
            initial_delay=API_INITIAL_RETRY_DELAY,
            backoff_multiplier=API_RETRY_BACKOFF_MULTIPLIER,
            retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout),
            failed_commands=failed_commands,
        )
        
        # Unpack the tuple result from fetch_virus_metadata
        batch_reports = None
        batch_deferred_filters = None
        if success and batch_result is not None:
            if isinstance(batch_result, tuple):
                batch_reports, batch_deferred_filters = batch_result
            else:
                # Backward compatibility if result is just a list
                batch_reports = batch_result
        
        # If batch_reports is a file path (string), read reports from it
        # This happens when fetch_virus_metadata streams to disk
        if isinstance(batch_reports, str) and os.path.isfile(batch_reports):
            file_reports = []
            try:
                with open(batch_reports, 'r', encoding='utf-8') as bf:
                    for line in bf:
                        line = line.strip()
                        if line:
                            try:
                                file_reports.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            except IOError:
                file_reports = []
            batch_reports = file_reports
        
        if success and batch_reports:
            all_reports.extend(batch_reports)
            # Track deferred filters (should be the same across all batches if any)
            if batch_deferred_filters and aggregated_deferred_filters is None:
                aggregated_deferred_filters = batch_deferred_filters
                logger.debug("Batch %d has deferred filters: %s", batch_num, batch_deferred_filters)
            tqdm.write(f"✅ Batch {batch_num}: Retrieved {len(batch_reports)} records")
        else:
            # Batch failed or returned empty
            error_msg = error_info['error'] if error_info else "No data returned"
            tqdm.write(f"❌ Batch {batch_num} failed after {API_MAX_RETRIES} retries: {error_msg}")
            
            # Build URL with applied filters for manual retry
            base_url = f"{NCBI_API_BASE}/virus/accession/{accession_string}/dataset_report"
            query_params = []
            if refseq_only:
                query_params.append("filter.refseq_only=true")
            if annotated is True:
                query_params.append("filter.annotated_only=true")
            if complete_only:
                query_params.append("filter.complete_only=true")
            if host:
                query_params.append(f"filter.host={host.replace('_', ' ')}")
            if geographic_location:
                query_params.append(f"filter.geo_location={geographic_location.replace('_', ' ')}")
            if min_release_date:
                query_params.append(f"filter.released_since={min_release_date}T00:00:00.000Z")
            
            api_url = base_url + ("?" + "&".join(query_params) if query_params else "")
            
            failed_batch_info = {
                'batch_num': batch_num,
                'accession_count': len(batch),
                'accessions': batch,
                'api_url': api_url,
            }
            failed_batches.append(failed_batch_info)
            
            # Track in failed_commands for later reporting
            _track_failed_operation(
                failed_commands,
                'api_batches',
                failed_batch_info,
                error_info if error_info else {'error': 'No data returned', 'exception_type': 'EmptyResponse'}
            )
        
        # Add a small delay between batches to respect rate limits
        if batch_num < len(batches):
            time.sleep(EUTILS_INTER_BATCH_DELAY)
    
    # Log summary
    if failed_batches:
        logger.warning("⚠️ %d out of %d accession batches failed to fetch metadata", 
                      len(failed_batches), len(batches))
        for fb in failed_batches:
            logger.debug("Failed batch %d (%d accessions): %s", 
                        fb['batch_num'], fb['accession_count'], fb['accessions'][:3])
    
    # Continue with partial results if at least some batches succeeded
    if all_reports:
        logger.info("Successfully retrieved %d total metadata records from %d batches", 
                   len(all_reports), len(batches) - len(failed_batches))
        if failed_batches:
            logger.warning("⚠️ Continuing pipeline with partial results (%d/%d batches succeeded)", 
                          len(batches) - len(failed_batches), len(batches))
        if aggregated_deferred_filters:
            logger.info("Deferred filters will be applied in metadata filtering stage: %s", aggregated_deferred_filters)
        return all_reports, aggregated_deferred_filters
    
    # Only raise if ALL batches failed
    if failed_batches:
        raise RuntimeError(
            f"All {len(batches)} accession batches failed to fetch metadata. "
            f"Last error: {failed_batches[-1]['accessions']}"
        )
    
    # Fallback (shouldn't reach here)
    logger.warning("No accession batches were processed")
    return [], None


def _try_modified_virus_names(
    virus,
    accession,
    host,
    geographic_location,
    annotated,
    complete_only,
    min_release_date,
    refseq_only,
    failed_commands,
    _retry_attempt,
    error_type="Error",
    temp_output_dir=None
):
    """
    Try fetching virus metadata with modified virus names.
    
    This helper function iterates through available retry strategies (modification
    of virus name) and attempts to fetch metadata with each modified name.
    
    Args:
        virus: Original virus name.
        accession: Accession filter.
        host: Host filter.
        geographic_location: Geographic location filter.
        annotated: Annotated filter.
        complete_only: Complete genome filter.
        min_release_date: Minimum release date filter.
        refseq_only: RefSeq only filter.
        failed_commands: List to track failed commands.
        _retry_attempt: Current retry attempt number.
        error_type: String describing the error type for logging.
        
    Returns:
        list or None: The fetched metadata if successful, None if all retries failed.
    """
    if _retry_attempt >= 2 or accession or virus.isdigit():
        return None
    
    # Try modification strategies in order
    for attempt_num in range(_retry_attempt + 1, 3):  # Try remaining attempts (1 and/or 2)
        modified_virus = _get_modified_virus_name(virus, attempt=attempt_num)
        if modified_virus:
            logger.warning("%s with virus name '%s'. "
                          "Retrying with modified name: '%s' (strategy %d)", 
                          error_type, virus, modified_virus, attempt_num)
            try:
                return fetch_virus_metadata(
                    virus=modified_virus,
                    accession=accession,
                    host=host,
                    geographic_location=geographic_location,
                    annotated=annotated,
                    complete_only=complete_only,
                    min_release_date=min_release_date,
                    refseq_only=refseq_only,
                    failed_commands=failed_commands,
                    _retry_attempt=attempt_num,
                    temp_output_dir=temp_output_dir,
                )
            except RuntimeError:
                logger.warning("Retry with modified virus name '%s' failed", modified_virus)
                # Continue to try next strategy
                continue
    
    # All retry strategies exhausted
    logger.warning("All retry strategies failed")
    return None


def fetch_virus_metadata(
    virus,
    accession=False,
    host=None,
    geographic_location=None,
    annotated=None,
    complete_only=None,
    min_release_date=None,
    refseq_only=None,
    failed_commands=None,
    _retry_attempt=0,
    temp_output_dir=None,
):
    """
    Fetch virus metadata using NCBI Datasets API.
    
    This function retrieves metadata for virus sequences from the NCBI Datasets API
    using either taxon-based or accession-based queries. It handles pagination
    automatically to retrieve all available results.
    
    When the server is unreachable, this function will automatically retry with
    modified virus names:
        1. First retry: Remove parenthetical content (e.g., "(LASV)")
        2. Second retry: Add " virus" suffix or fix spacing
    
    Args:
        virus (str): Virus taxon name/ID or accession number.
        accession (bool): Whether virus parameter is an accession number.
        host (str, optional): Host organism name filter.
        geographic_location (str, optional): Geographic location filter.
        annotated (bool, optional): Filter for annotated genomes only.
        complete_only (bool, optional): Filter for complete genomes only.
        min_release_date (str, optional): Minimum release date filter (YYYY-MM-DD format).
        refseq_only (bool, optional): Limit to RefSeq genomes only.
        failed_commands (dict, optional): Dictionary to track failed operations.
        _retry_attempt (int): Internal counter for retry attempts (0=original, 1=first retry, 2=second retry).
        
    Returns:
        list: List of virus metadata records from the API response.
        
    Raises:
        RuntimeError: If the API request fails.
    
    Note:
        Metadata is streamed to a temporary JSONL file during fetching to reduce RAM usage
        for large datasets. If temp_output_dir is provided, the file is saved there;
        otherwise it's saved in the system temp directory.
    """
    
    metadata_file = None
    temp_metadata_file = None
    
    # Save original filter values before URL encoding (for deferred local filtering)
    original_geographic_location = geographic_location
    original_host = host
    
    # Choose the appropriate API endpoint based on whether we're querying by accession or taxon
    if accession:
        # For accession numbers (e.g., NC_045512.2), use the accession-specific endpoint
        # For multiple accessions, virus will contain accessions joined with %2C (URL-encoded comma)
        # e.g., "NC_045512.2%2CMN908947.3%2CMT020781.1"
        url = f"{NCBI_API_BASE}/virus/accession/{virus}/dataset_report"
        logger.debug("Using accession endpoint for virus: %s", virus)
        params = {}
    else:
        # For taxon names/IDs (e.g., 'Zika Virus', 'influenza'), use the taxon endpoint  
        url = f"{NCBI_API_BASE}/virus/taxon/{virus}/dataset_report"
        logger.debug("Using taxon endpoint for virus: %s", virus)
        params = {}

    # Add API-level filters to reduce the amount of data we need to download
    # These filters are applied server-side before results are returned
    if refseq_only:
        # Limit results to RefSeq database entries only
        params['filter.refseq_only'] = 'true'
        logger.debug("Applied RefSeq-only filter")
    
    if annotated is True:
        # Only return sequences that have been annotated with gene/protein information
        params['filter.annotated_only'] = 'true'
        logger.debug("Applied annotated-only filter")
    
    if complete_only:
        # Only return complete genome sequences (not partial sequences)
        params['filter.complete_only'] = 'true'
        logger.debug("Applied complete-only filter")
        
    if host:
        # Filter by host organism name, replacing underscores with spaces for API compatibility
        host = host.strip('"\'-_<|>`\'')
        host = host.replace('-', '+').replace('_', '+').replace(' ', '+')
        params['filter.host'] = host
        logger.debug("Applied host filter: %s", host)
        
    if geographic_location:
        # Filter by geographic location, replacing underscores with spaces for API compatibility
        geographic_location = geographic_location.strip('"-_<|>`')
        geographic_location = geographic_location.replace("'", "%27").replace("`", "%27")
        geographic_location = geographic_location.replace('-', '+').replace('_', '+').replace(' ', '+')
        params['filter.geo_location'] = geographic_location
        logger.debug("Applied geographic location filter: %s", geographic_location)

    if min_release_date:
        # Convert date to ISO format expected by the API (YYYY-MM-DDTHH:MM:SS.sssZ)
        params['filter.released_since'] = f"{min_release_date}T00:00:00.000Z"
        logger.debug("Applied minimum release date filter: %s", min_release_date)

    # Set page size to maximum allowed to minimize the number of API calls needed
    # The NCBI API supports pagination for large result sets
    params['page_size'] = API_PAGE_SIZE
    logger.debug("Set page size to maximum: %d records per request", API_PAGE_SIZE)
    
    # Initialize variables for handling paginated results
    total_records_streamed = 0  # Counter for records written to temp file (NOT held in RAM)
    page_token = None     # Token for accessing subsequent pages
    page_count = 0        # Track number of pages processed for logging
    pages_pbar = None     # Progress bar for pagination (created when we know total pages)
    
    # Create a temporary file to stream metadata as it arrives from the API
    # This prevents large datasets from consuming all system RAM
    # Save in output temp directory
    os.makedirs(temp_output_dir, exist_ok=True)
    temp_metadata_file = os.path.join(temp_output_dir, f"gget_metadata_{timestamp}_{random_suffix}.jsonl")
    metadata_file = None
    try:
        metadata_file = open(temp_metadata_file, 'w', encoding='utf-8')
        logger.info("Streaming API metadata to temporary file: %s", temp_metadata_file)
    except IOError as e:
        logger.warning("Could not open temporary metadata file for streaming: %s. Metadata will be held in RAM.", e)
        temp_metadata_file = None
    
    # Main pagination loop - continue until all pages are retrieved
    loop = True
    while loop:
        page_count += 1
        
        # Add pagination token if we're not on the first page
        if page_token:
            params['page_token'] = page_token
        
        def fetch_single_page():
            """Callable that fetches a single page of results"""
            # Build the query string manually to preserve '+' characters in filter values
            # The requests library would URL-encode '+' to '%2B', but NCBI API expects literal '+'
            query_parts = []
            for key, value in params.items():
                # Only encode special characters, but preserve '+' which NCBI uses for spaces
                encoded_value = quote(str(value), safe="+:")
                query_parts.append(f"{key}={encoded_value}")
            full_url = url + ("?" + "&".join(query_parts) if query_parts else "")
            
            # Make the HTTP GET request to the NCBI API  
            logger.debug("Making API request to: %s", url)
            logger.debug("Request parameters: %s", params)
            response = requests.get(full_url, timeout=API_REQUEST_TIMEOUT)
            logger.debug("Explicit URL request sent: %s", response.url)
            
            # Raise an exception if the HTTP request failed (4xx or 5xx status codes)
            response.raise_for_status()

            # Parse the JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"NCBI API returned non-JSON response (HTTP {response.status_code}): {response.text[:200]}"
                ) from e
            logger.debug("Received response with %d bytes", len(response.content))
            
            return data
        
        # Use exponential backoff helper for single page fetch
        success, page_data, error_info = _retry_with_exponential_backoff(
            operation_name=f"API page {page_count}",
            operation_func=fetch_single_page,
            max_retries=API_MAX_RETRIES,
            initial_delay=API_INITIAL_RETRY_DELAY,
            backoff_multiplier=API_RETRY_BACKOFF_MULTIPLIER,
            retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout),
            failed_commands=failed_commands,
        )
        
        # If the initial page fetch failed, try filter removal strategies FIRST, then page size reduction
        if not success and _retry_attempt == 0:
            logger.debug("⚠️ Page fetch failed with page_size=%d. Trying filter removal strategies...", params['page_size'])
            
            # Helper to close temp files before retry
            def close_temp_files():
                nonlocal pages_pbar, metadata_file
                if pages_pbar:
                    pages_pbar.close()
                    pages_pbar = None
                if metadata_file:
                    try:
                        metadata_file.close()
                    except OSError as e:
                        logger.debug("Failed to clean up metadata_file: %s", e)
            
            # STRATEGY 1: If geo_location filter exists, try without it (keeping host)
            if not success and geographic_location:
                logger.warning("🔄 FETCH FAILED - ATTEMPTING WITHOUT GEOGRAPHIC FILTER")
                logger.warning("Retrying without the geographic_location filter '%s' (will be applied later)...", original_geographic_location)
                close_temp_files()
                
                try:
                    retry_result = fetch_virus_metadata(
                        virus=virus,
                        accession=accession,
                        host=original_host,  # Keep host filter (original value)
                        geographic_location=None,  # Remove geo filter
                        annotated=annotated,
                        complete_only=complete_only,
                        min_release_date=min_release_date,
                        refseq_only=refseq_only,
                        failed_commands=failed_commands,
                        _retry_attempt=1,  # Mark as retry to prevent infinite loops
                        temp_output_dir=temp_output_dir,
                    )
                    
                    # Handle None return (signals chunking needed) - propagate it
                    if retry_result is None:
                        logger.warning("Retry without geographic filter returned None (dataset too large for single request)")
                    else:
                        retry_reports = retry_result[0] if isinstance(retry_result, tuple) else retry_result
                        if retry_reports is not None:
                            logger.info("✅ Successfully retrieved records without geographic filter")
                            logger.info("Geographic location filter '%s' will be applied during metadata filtering", original_geographic_location)
                            return retry_reports, {'geographic_location': original_geographic_location}
                except Exception as retry_error:
                    logger.warning("Retry without geographic filter failed: %s", retry_error)
            
            # STRATEGY 2: If BOTH geo_location and host filters exist, try without both
            # Skip this strategy for "all viruses" (taxon 10239) since downloading ~15M unfiltered records is not viable as a retry strategy - chunked download handles it
            if not success and geographic_location and host and virus != NCBI_ALL_VIRUSES_TAXID:
                logger.warning("🔄 ATTEMPTING WITHOUT BOTH GEOGRAPHIC AND HOST FILTERS")
                logger.warning("Retrying without both filters (will be applied later)...")
                close_temp_files()
                
                try:
                    retry_result = fetch_virus_metadata(
                        virus=virus,
                        accession=accession,
                        host=None,  # Remove host filter
                        geographic_location=None,  # Remove geo filter
                        annotated=annotated,
                        complete_only=complete_only,
                        min_release_date=min_release_date,
                        refseq_only=refseq_only,
                        failed_commands=failed_commands,
                        _retry_attempt=1,  # Mark as retry to prevent infinite loops
                        temp_output_dir=temp_output_dir,
                    )
                    
                    # Handle None return (signals chunking needed) - propagate it
                    if retry_result is None:
                        logger.warning("Retry without both filters returned None (dataset too large for single request)")
                    else:
                        retry_reports = retry_result[0] if isinstance(retry_result, tuple) else retry_result
                        if retry_reports is not None:
                            logger.info("✅ Successfully retrieved records without geographic and host filters")
                            logger.info("Geographic location filter '%s' will be applied during metadata filtering", original_geographic_location)
                            logger.info("Host filter '%s' will be applied during metadata filtering", original_host)
                            return retry_reports, {'geographic_location': original_geographic_location, 'host': original_host}
                except Exception as retry_error:
                    logger.warning("Retry without both filters failed: %s", retry_error)
            elif not success and geographic_location and host and virus == NCBI_ALL_VIRUSES_TAXID:
                logger.info("Skipping unfiltered retry for 'all viruses' taxon (dataset too large) - will use chunked download")
            
            # STRATEGY 3: If host filter exists (whether or not geo_location was tried), try without host only
            # Skip for "all viruses" taxon - the API also fails with just geo filter for this taxon
            if not success and host and virus != NCBI_ALL_VIRUSES_TAXID:
                logger.warning("🔄 ATTEMPTING WITHOUT HOST FILTER ONLY")
                logger.warning("Retrying without the host filter '%s' (will be applied later)...", original_host)
                close_temp_files()
                
                try:
                    retry_result = fetch_virus_metadata(
                        virus=virus,
                        accession=accession,
                        host=None,  # Remove host filter
                        geographic_location=original_geographic_location,  # Keep geo filter if present (original value)
                        annotated=annotated,
                        complete_only=complete_only,
                        min_release_date=min_release_date,
                        refseq_only=refseq_only,
                        failed_commands=failed_commands,
                        _retry_attempt=1,  # Mark as retry to prevent infinite loops
                        temp_output_dir=temp_output_dir,
                    )
                    
                    # Handle None return (signals chunking needed) - propagate it
                    if retry_result is None:
                        logger.warning("Retry without host filter returned None (dataset too large for single request)")
                    else:
                        retry_reports = retry_result[0] if isinstance(retry_result, tuple) else retry_result
                        if retry_reports is not None:
                            logger.info("✅ Successfully retrieved records without host filter")
                            logger.info("Host filter '%s' will be applied during metadata filtering", original_host)
                            return retry_reports, {'host': original_host}
                except Exception as retry_error:
                    logger.warning("❌ Retry without host filter failed: %s", retry_error)
            
            # STRATEGY 4: If all filter removal strategies failed, try reducing page size
            # Skip for all-viruses taxon since the issue is query scope, not page size
        if not success and params['page_size'] > MIN_PAGE_SIZE_FALLBACK and virus != NCBI_ALL_VIRUSES_TAXID:
            logger.info("All filter removal strategies failed. Trying smaller page sizes...")
            
            # Re-open temp file for continued attempts
            try:
                metadata_file = open(temp_metadata_file, 'a', encoding='utf-8')
            except IOError:
                metadata_file = None
            
            current_page_size = params['page_size']
            page_size_retry_count = 0
            
            while not success and current_page_size > MIN_PAGE_SIZE_FALLBACK:
                # Decrease page size for next retry
                current_page_size = max(MIN_PAGE_SIZE_FALLBACK, current_page_size - PAGE_SIZE_FALLBACK_DECREMENT)
                page_size_retry_count += 1
                
                logger.debug("📉 Attempting retry #%d with page_size=%d (page %d)", 
                            page_size_retry_count, current_page_size, page_count)
                
                # Update params with new page size
                params['page_size'] = current_page_size
                
                # Retry the fetch with the smaller page size
                success, page_data, error_info = _retry_with_exponential_backoff(
                    operation_name=f"API page {page_count} (page_size={current_page_size})",
                    operation_func=fetch_single_page,
                    max_retries=API_MAX_RETRIES,
                    initial_delay=API_INITIAL_RETRY_DELAY,
                    backoff_multiplier=API_RETRY_BACKOFF_MULTIPLIER,
                    retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout),
                    failed_commands=failed_commands,
                )
                
                if success:
                    logger.debug("✅ Successfully fetched page with page_size=%d after %d retry attempt(s)", 
                                current_page_size, page_size_retry_count)
                    # Update the global page_size for remaining pages if successful
                    params['page_size'] = current_page_size
                    
                    # If progress bar exists, recalculate total pages based on new page size
                    if pages_pbar is not None and page_data:
                        total_count = page_data.get('total_count', 0)
                        if total_count > 0:
                            new_total_pages = (total_count + current_page_size - 1) // current_page_size
                            logger.debug("📊 Recalculating progress bar: page_size changed to %d, total pages now: %d", 
                                        current_page_size, new_total_pages)
                            pages_pbar.total = new_total_pages
                    break
            
            # If still failed after trying all page sizes down to minimum
            if not success:
                logger.warning("⚠️ All page size fallback attempts failed (page %d)", page_count)
        
        # Handle page fetch result
        if success and page_data:
            # Extract the virus reports from the response
            reports = page_data.get('reports', [])
            # Create progress bar on first page when we know total pages
            # Use current page_size (which may have been reduced) for accurate total page calculation
            if pages_pbar is None and page_count == 1:
                total_pages = page_data.get('total_count', 0)
                current_page_size = params['page_size']
                if total_pages > 0:
                    total_pages = (total_pages + current_page_size - 1) // current_page_size
                pages_pbar = tqdm(total=max(total_pages, 1), desc="Fetching pages", unit="page", leave=False)
            if pages_pbar:
                pages_pbar.update(1)
                pages_pbar.set_postfix({"records": total_records_streamed})
            
            # Stream reports to temporary file if available
            if metadata_file and reports:
                try:
                    for report in reports:
                        metadata_file.write(json.dumps(report) + '\n')
                    metadata_file.flush()  # Ensure data is written to disk
                    logger.debug("Streamed %d records to temporary metadata file", len(reports))
                except IOError as e:
                    logger.warning("Error writing to temporary metadata file: %s", e)
            
            # Track count only - records are on disk, NOT held in RAM
            total_records_streamed += len(reports)
            
            # Check if there are more pages to retrieve
            next_page_token = page_data.get('next_page_token')
            if not next_page_token:
                if pages_pbar:
                    pages_pbar.close()
                loop = False
                break
            
            # Set up for the next page
            page_token = next_page_token
            logger.debug("Next page token received, continuing pagination...")
            
        else:
            # Page fetch failed after retries or returned empty data
            # Handle case where success=True but page_data is empty (error_info will be None)
            if not error_info:
                # Success=True but no data returned - this shouldn't happen in normal operation
                # but we should handle it gracefully
                logger.warning("⚠️ API request succeeded but returned no data (page %d)", page_count)
                if total_records_streamed > 0:
                    logger.info("Continuing with %d records collected so far...", total_records_streamed)
                    loop = False
                    break
                else:
                    # First page returned empty - before failing, try fallback strategies
                    # (same logic as when success=False but for empty data case)
                    if _retry_attempt == 0:
                        # Helper to close temp files before retry
                        if pages_pbar:
                            pages_pbar.close()
                            pages_pbar = None
                        if metadata_file:
                            try:
                                metadata_file.close()
                            except OSError as e:
                                logger.debug("Failed to clean up metadata_file: %s", e)
                        
                        # FALLBACK 1: If geo_location filter exists, try without it
                        if geographic_location:
                            logger.warning("🔄 EMPTY RESPONSE - ATTEMPTING WITHOUT GEOGRAPHIC FILTER")
                            logger.warning("Retrying without the geographic_location filter '%s' (will be applied locally)...", original_geographic_location)
                            
                            try:
                                retry_result = fetch_virus_metadata(
                                    virus=virus,
                                    accession=accession,
                                    host=original_host,  # Keep host filter (original value)
                                    geographic_location=None,  # Remove geo filter
                                    annotated=annotated,
                                    complete_only=complete_only,
                                    min_release_date=min_release_date,
                                    refseq_only=refseq_only,
                                    failed_commands=failed_commands,
                                    _retry_attempt=1,  # Mark as retry to prevent infinite loops
                                    temp_output_dir=temp_output_dir,
                                )
                                
                                # Handle None return (signals chunking needed) - propagate it
                                if retry_result is None:
                                    logger.warning("Retry without geographic filter returned None (dataset too large for single request)")
                                else:
                                    retry_reports = retry_result[0] if isinstance(retry_result, tuple) else retry_result
                                    if retry_reports is not None:
                                        logger.info("✅ Successfully retrieved records without geographic filter")
                                        logger.info("Geographic location filter '%s' will be applied during metadata filtering", original_geographic_location)
                                        return retry_reports, {'geographic_location': original_geographic_location}
                            except Exception as retry_error:
                                logger.warning("Retry without geographic filter failed: %s", retry_error)
                        
                        # FALLBACK 2: If host filter exists and geo retry failed or wasn't tried
                        if host:
                            logger.warning("🔄 ATTEMPTING WITHOUT HOST FILTER")
                            logger.warning("Retrying without the host filter '%s' (will be applied locally)...", original_host)
                            
                            try:
                                retry_result = fetch_virus_metadata(
                                    virus=virus,
                                    accession=accession,
                                    host=None,  # Remove host filter
                                    geographic_location=None if geographic_location else None,  # Also remove geo if present
                                    annotated=annotated,
                                    complete_only=complete_only,
                                    min_release_date=min_release_date,
                                    refseq_only=refseq_only,
                                    failed_commands=failed_commands,
                                    _retry_attempt=1,
                                    temp_output_dir=temp_output_dir,
                                )
                                
                                # Handle None return (signals chunking needed) - propagate it
                                if retry_result is None:
                                    logger.warning("Retry without host filter returned None (dataset too large for single request)")
                                else:
                                    retry_reports = retry_result[0] if isinstance(retry_result, tuple) else retry_result
                                    if retry_reports is not None:
                                        deferred = {'host': original_host}
                                        if geographic_location:
                                            deferred['geographic_location'] = original_geographic_location
                                        logger.info("✅ Successfully retrieved records without filters")
                                        logger.info("Deferred filters will be applied during metadata filtering: %s", list(deferred.keys()))
                                        return retry_reports, deferred
                            except Exception as retry_error:
                                logger.warning("Retry without host filter failed: %s", retry_error)
                    
                    # All fallback strategies exhausted or we're already in retry mode
                    error_msg = f"API request returned no data for {virus}. The dataset may be empty or unavailable. Please verify the virus name and filters, or try again later."
                    if failed_commands is not None:
                        failed_commands['empty_response'] = {'error': error_msg}
                    logger.error(error_msg)
                    raise RuntimeError(error_msg) from None
            
            last_exception = error_info
            
            if isinstance(last_exception.get('exception_type'), str) and last_exception['exception_type'] == 'Timeout':
                # For pagination timeouts, we can continue with partial results
                if page_count > 1 and total_records_streamed > 0:
                    # We have collected some pages already
                    logger.warning("⚠️ Request timed out while fetching additional pages (page %d)", page_count)
                    logger.info("Continuing with %d records collected so far...", total_records_streamed)
                    
                    # Track timeout in failed_commands for user reference
                    if failed_commands is not None:
                        if 'pagination_timeouts' not in failed_commands:
                            failed_commands['pagination_timeouts'] = []
                        failed_commands['pagination_timeouts'].append({
                            'page': page_count,
                            'error': 'API request timeout',
                            'url': url,
                            'records_retrieved': total_records_streamed,
                        })
                    
                    # Break pagination loop and return partial results
                    loop = False
                    break
                else:
                    # Handle timeout error with specific guidance for known problematic filters
                    error_msg = f"Request timed out while fetching virus metadata: {last_exception.get('error', 'Unknown')}"
                    
                    # Track API timeout information for summary
                    if failed_commands is not None:
                        failed_commands['api_timeout'] = {
                            'error': 'API request timeout',
                            'url': url,
                            'alternative_command': None
                        }
                    
                    # Log the timeout error before raising
                    logger.error("=" * 80)
                    logger.error("REQUEST TIMEOUT")
                    logger.error("=" * 80)
                    logger.error(error_msg)
                    logger.error("=" * 80)
                    
                    # Close temporary file and progress bar before raising exception
                    if pages_pbar:
                        pages_pbar.close()
                    if metadata_file:
                        try:
                            metadata_file.close()
                        except OSError as e:
                            logger.debug("Failed to clean up metadata_file: %s", e)
                            
                    raise RuntimeError(error_msg) from None
                
            elif last_exception.get('exception_type') == 'ConnectionError':
                # For pagination connection errors, continue with partial results if available
                if page_count > 1 and total_records_streamed > 0:
                    logger.warning("⚠️ Connection error while fetching additional pages (page %d)", page_count)
                    logger.info("Continuing with %d records collected so far...", total_records_streamed)
                    
                    # Track error in failed_commands
                    if failed_commands is not None:
                        if 'pagination_errors' not in failed_commands:
                            failed_commands['pagination_errors'] = []
                        failed_commands['pagination_errors'].append({
                            'page': page_count,
                            'error_type': 'ConnectionError',
                            'error': last_exception.get('error', 'Unknown'),
                            'records_retrieved': total_records_streamed,
                        })
                    
                    loop = False
                    break
                else:
                    # Handle connection errors (network issues, DNS failures, etc.)
                    # Try retrying with modified virus names (up to 2 retry strategies)
                    retry_result = _try_modified_virus_names(
                        virus=virus,
                        accession=accession,
                        host=host,
                        geographic_location=geographic_location,
                        annotated=annotated,
                        complete_only=complete_only,
                        min_release_date=min_release_date,
                        refseq_only=refseq_only,
                        failed_commands=failed_commands,
                        _retry_attempt=_retry_attempt,
                        error_type="Connection error",
                        temp_output_dir=temp_output_dir
                    )
                    if retry_result is not None:
                        return retry_result
                    
                    # Log the connection error before raising
                    error_msg = f"Connection error while fetching virus metadata: {last_exception.get('error', 'Unknown')}"
                    logger.error("=" * 80)
                    logger.error("CONNECTION ERROR")
                    logger.error("=" * 80)
                    logger.error(error_msg)
                    logger.error("Please check your internet connection and try again.")
                    logger.error("=" * 80)
                    
                    # Close temporary file before raising exception
                    if metadata_file:
                        try:
                            metadata_file.close()
                        except OSError as e:
                            logger.debug("Failed to clean up metadata_file: %s", e)
                            
                    raise RuntimeError(error_msg) from None
                
            elif last_exception.get('exception_type') == 'HTTPError':
                # For pagination HTTP errors, continue with partial results if available
                if page_count > 1 and total_records_streamed > 0:
                    logger.warning("⚠️ HTTP error while fetching additional pages (page %d): %s", page_count, last_exception.get('error'))
                    logger.info("Continuing with %d records collected so far...", total_records_streamed)
                    
                    # Track error in failed_commands
                    if failed_commands is not None:
                        if 'pagination_errors' not in failed_commands:
                            failed_commands['pagination_errors'] = []
                        failed_commands['pagination_errors'].append({
                            'page': page_count,
                            'error_type': 'HTTPError',
                            'error': last_exception.get('error', 'Unknown'),
                            'records_retrieved': total_records_streamed,
                        })
                    
                    loop = False
                    break
                else:
                    # Handle HTTP errors with specific guidance for known issues
                    error_msg = f"HTTP error while fetching virus metadata: {last_exception.get('error', 'Unknown')}"
                    
                    # Check for specific server error patterns (5xx errors indicate server unreachability)
                    is_server_error = '500' in last_exception.get('error', '') or '502' in last_exception.get('error', '') or '503' in last_exception.get('error', '') or '504' in last_exception.get('error', '')
                    
                    if is_server_error:
                        # Special handling for "all viruses" query
                        # If this is the first page and we're querying all viruses without date filters,
                        # the dataset is too large for NCBI to handle - need to chunk by date
                        if virus == NCBI_ALL_VIRUSES_TAXID and not accession and page_count == 1 and not min_release_date:
                            logger.warning("⚠️ NCBI API cannot handle 'all viruses' query in a single request")
                            logger.info("🔄 Automatically switching to date-chunked download strategy...")
                            logger.info("This will split the download into yearly chunks to avoid server overload")
                            
                            # Close temporary file before returning None
                            if metadata_file:
                                try:
                                    metadata_file.close()
                                except OSError as e:
                                    logger.debug("Failed to clean up metadata_file: %s", e)
                            
                            # Return None to signal that chunking is needed
                            # The calling function will handle the chunking strategy
                            return None
                        
                        # Special handling for numeric taxon IDs that fail with 500 errors
                        # These are often transient issues with NCBI's server
                        if virus.isdigit():
                            logger.warning("⚠️ Server error for numeric taxon ID: %s", virus)
                            logger.info("Numeric taxon IDs sometimes encounter temporary server issues at NCBI.")
                            logger.info("This may be a transient problem. Recommendations:")
                            logger.info("  1. Wait a few minutes and try again")
                            logger.info("  2. Try using the virus name instead of the taxon ID")
                            logger.info("  3. Consider using more specific filters to reduce the dataset size")
                        
                        # Try retrying with modified virus names (skip for numeric IDs since they won't have modified versions)
                        if not virus.isdigit():
                            retry_result = _try_modified_virus_names(
                                virus=virus,
                                accession=accession,
                                host=host,
                                geographic_location=geographic_location,
                                annotated=annotated,
                                complete_only=complete_only,
                                min_release_date=min_release_date,
                                refseq_only=refseq_only,
                                failed_commands=failed_commands,
                                _retry_attempt=_retry_attempt,
                                error_type="Server error (5xx)",
                                temp_output_dir=temp_output_dir
                            )
                            if retry_result is not None:
                                return retry_result
                        
                        # Note: Retry without geographic_location is now handled in the page size
                        # reduction loop above, after the first smaller page size fails
                        
                        error_msg += (
                            f"\n\n🔧 SERVER ERROR DETECTED: "
                            f"NCBI's API is experiencing temporary server-side issues. "
                            f"This could be due to the specific virus/taxon ID or a genuine server problem. "
                            f"All page size and filter removal retries have been exhausted."
                        )
                    
                    # Log the error details before raising
                    logger.error("=" * 80)
                    logger.error("API REQUEST FAILED")
                    logger.error("=" * 80)
                    logger.error(error_msg)
                    logger.error("=" * 80)
                    
                    # Close temporary file before raising exception
                    if metadata_file:
                        try:
                            metadata_file.close()
                        except OSError as e:
                            logger.debug("Failed to clean up metadata_file: %s", e)
                    
                    raise RuntimeError(error_msg) from None
                
            else:
                # Handle any other request-related errors
                # For pagination errors with partial results, continue
                if page_count > 1 and total_records_streamed > 0:
                    logger.warning("⚠️ Error while fetching additional pages (page %d): %s", page_count, last_exception.get('error'))
                    logger.info("Continuing with %d records collected so far...", total_records_streamed)
                    
                    # Track error in failed_commands
                    if failed_commands is not None:
                        if 'pagination_errors' not in failed_commands:
                            failed_commands['pagination_errors'] = []
                        failed_commands['pagination_errors'].append({
                            'page': page_count,
                            'error_type': last_exception.get('exception_type', 'Unknown'),
                            'error': last_exception.get('error', 'Unknown'),
                            'records_retrieved': total_records_streamed,
                        })
                    
                    if pages_pbar:
                        pages_pbar.close()
                    loop = False
                    break
                else:
                    error_msg = f"Failed to fetch virus metadata: {last_exception.get('error', 'Unknown')}"
                    logger.error("=" * 80)
                    logger.error("REQUEST FAILED")
                    logger.error("=" * 80)
                    logger.error(error_msg)
                    logger.error("=" * 80)
                    
                    # Close temporary file before raising exception
                    if metadata_file:
                        try:
                            metadata_file.close()
                        except OSError as e:
                            logger.debug("Failed to clean up metadata_file: %s", e)
                    
                    raise RuntimeError(error_msg) from None
    
    # Close the temporary metadata file if it was created
    if metadata_file:
        try:
            metadata_file.close()
            logger.debug("✅ Closed temporary metadata file: %s", temp_metadata_file)
            logger.debug("   This file is being used to reduce RAM usage during API metadata fetching")
            logger.debug("   It will be kept in: %s", temp_output_dir)
        except IOError as e:
            logger.warning("Error closing temporary metadata file: %s", e)
    
    # Log the final results summary
    logger.info("Successfully retrieved %d virus records from NCBI API across %d pages", 
                total_records_streamed, page_count)
    
    if temp_metadata_file and os.path.exists(temp_metadata_file):
        file_size_mb = os.path.getsize(temp_metadata_file) / (1024 * 1024)
        logger.info("Temporary metadata file size: %.2f MB", file_size_mb)
    
    # Return the temp file path instead of holding all records in RAM. The caller will stream from this file to build metadata_dict.
    return temp_metadata_file, None  # (temp_file_path, deferred_filters) - None means no deferred filters


def fetch_virus_metadata_chunked(
    virus, 
    accession=False, 
    host=None, 
    geographic_location=None, 
    annotated=None,
    complete_only=False,
    min_release_date=None,
    max_release_date=None,
    refseq_only=False,
    failed_commands=None,
    temp_output_dir=None
):
    """
    Fetch virus metadata using a chunked date-range strategy for very large datasets.
    
    This function is used as a fallback when the standard fetch_virus_metadata fails due to dataset size limitations. It breaks down the request into yearly chunks starting from a reasonable start date or user's min_release_date to the present.
    
    Because the NCBI API currently cannot handle broad taxon queries (e.g., taxon 10239 for all viruses) with server-side filters like host or geographic_location, this function makes UNFILTERED requests and tracks those filters as deferred, to be applied later during metadata filtering.
    
    Args:
        Same as fetch_virus_metadata.
        
    Returns:
        tuple: (list of virus metadata records, dict of deferred_filters or None)
        
    Raises:
        RuntimeError: If any chunk fails to download.
    """
    
    logger.info("=" * 80)
    logger.info("📦 CHUNKED DOWNLOAD MODE ACTIVATED")
    logger.info("=" * 80)
    logger.info("The 'all viruses' dataset is too large for NCBI to handle in one request.")
    logger.info("Splitting download into yearly chunks to ensure successful completion.")
    logger.info("This may take a while, but ensures all data is retrieved.")
    logger.info("=" * 80)
    
    # Since the API cannot handle broad taxon queries with filters (returns 500), we make unfiltered requests and track filters as deferred for post-hoc application.
    deferred_filters = {}
    if host:
        deferred_filters['host'] = host
        logger.info("Host filter '%s' will be deferred and applied during metadata filtering", host)
    if geographic_location:
        deferred_filters['geographic_location'] = geographic_location
        logger.info("Geographic location filter '%s' will be deferred and applied during metadata filtering", geographic_location)
    
    if deferred_filters:
        logger.info("Filters deferred to post-download filtering: %s", list(deferred_filters.keys()))
    
    # Define date range for chunking
    # If user specified min_release_date, use it; otherwise start from default year
    if min_release_date:
        # Extract year from user's min_release_date
        start_year = int(min_release_date.split('-')[0])
        logger.info(f"Starting from user-specified year: {start_year}")
    else:
        # Start from default year as most valuable viral sequence data is from then onwards
        start_year = CHUNKED_DOWNLOAD_START_YEAR
        logger.info("Starting from year %d (default for 'all viruses' downloads)", CHUNKED_DOWNLOAD_START_YEAR)
    
    current_date = datetime.now()
    current_year = current_date.year
    
    # If max_release_date is specified, limit the end year to avoid downloading unnecessary data
    end_year = current_year
    if max_release_date:
        try:
            end_year = int(max_release_date.split('-')[0])
            logger.info("Limiting chunked download to year %d based on max_release_date '%s'", end_year, max_release_date)
            # max_release_date will be applied by the caller's metadata filtering step (already in the filters dict), so no need to add it to deferred_filters here
        except (ValueError, IndexError):
            logger.warning("Could not parse max_release_date '%s' for year limit, downloading to current year", max_release_date)
            end_year = current_year
    
    all_reports = []
    chunk_temp_files = []  # Track temp file paths from each chunk
    total_records_count = 0  # Track total records without holding in RAM
    total_chunks = end_year - start_year + 1
    
    logger.info(f"Will process {total_chunks} year(s) from {start_year} to {end_year}")
    logger.info("=" * 80)
    
    for year in tqdm(range(start_year, end_year + 1), total=total_chunks, desc="Fetching yearly chunks", unit="year"):
        chunk_start = f"{year}-01-01"
        chunk_end = f"{year}-12-31"
        
        # For the current year, use today's date as the end
        if year == current_year:
            chunk_end = current_date.strftime("%Y-%m-%d")
        
        chunk_num = year - start_year + 1
        tqdm.write(f"📥 Chunk {chunk_num}/{total_chunks}: Fetching data for year {year} ({chunk_start} to {chunk_end})")
        
        try:
            # Fetch metadata for this date chunk WITHOUT host/geo filters
            # (the API currently cannot handle them for broad taxon queries)
            chunk_result = fetch_virus_metadata(
                virus=virus,
                accession=accession,
                host=None,  # Deferred - will be applied post-download
                geographic_location=None,  # Deferred - will be applied post-download
                annotated=annotated,
                complete_only=complete_only,
                min_release_date=chunk_start,
                refseq_only=refseq_only,
                failed_commands=failed_commands,
                temp_output_dir=temp_output_dir
            )
            
            # Handle tuple return (reports, deferred_filters)
            chunk_reports = None
            chunk_deferred_filters = None
            if chunk_result is not None:
                if isinstance(chunk_result, tuple):
                    chunk_reports, chunk_deferred_filters = chunk_result
                else:
                    chunk_reports = chunk_result
            
            # If we got None, it means even this chunk is too large
            if chunk_reports is None:
                logger.error(f"❌ Chunk for year {year} returned None (dataset too large even for yearly chunk)")
                logger.error("This is unexpected and may indicate an API issue")
                raise RuntimeError(f"Year {year} chunk failed - dataset too large even when split by year")
            
            # Merge any deferred filters from the chunk itself (e.g., if annotated was deferred)
            if chunk_deferred_filters:
                for k, v in chunk_deferred_filters.items():
                    if k not in deferred_filters:
                        deferred_filters[k] = v
                        logger.debug("Chunk %d added deferred filter: %s=%s", chunk_num, k, v)
            
            # Handle chunk_reports which can be a file path (string) or a list
            if isinstance(chunk_reports, str) and os.path.isfile(chunk_reports):
                # Count records in the chunk file without loading into RAM
                chunk_count = 0
                try:
                    with open(chunk_reports, 'r', encoding='utf-8') as cf:
                        for line in cf:
                            if line.strip():
                                chunk_count += 1
                except IOError:
                    chunk_count = 0
                chunk_temp_files.append(chunk_reports)
                total_records_count += chunk_count
            else:
                # chunk_reports is a list (small dataset)
                chunk_count = len(chunk_reports)
                all_reports.extend(chunk_reports)
                total_records_count += chunk_count
            
            tqdm.write(f"✅ Chunk {chunk_num}/{total_chunks}: Retrieved {chunk_count:,} records (total: {total_records_count:,})")
            
            # Add a small delay between chunks to be respectful to NCBI servers
            if year < end_year:
                time.sleep(CHUNKED_DOWNLOAD_INTER_CHUNK_DELAY)
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch chunk for year {year}: {e}")
            raise RuntimeError(f"Chunked download failed at year {year}") from e
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ CHUNKED DOWNLOAD COMPLETE")
    logger.info(f"   Total records retrieved: {total_records_count:,}")
    logger.info(f"   Total chunks processed: {total_chunks}")
    if deferred_filters:
        logger.info("   Deferred filters to apply: %s", deferred_filters)
    logger.info("=" * 80)
    
    # If we have chunk temp files, merge them into a single JSONL and return the path
    if chunk_temp_files:
        # Create a merged temp file path
        merged_temp_file = os.path.join(temp_output_dir, f"gget_metadata_chunked_{timestamp}_{random_suffix}.jsonl")
        try:
            with open(merged_temp_file, 'w', encoding='utf-8') as outf:
                # First, write any in-memory reports (from small chunks)
                for report in all_reports:
                    outf.write(json.dumps(report) + '\n')
                # Then append contents of chunk temp files
                for chunk_file in chunk_temp_files:
                    with open(chunk_file, 'r', encoding='utf-8') as inf:
                        for line in inf:
                            if line.strip():
                                outf.write(line if line.endswith('\n') else line + '\n')
            logger.info("Merged %d chunk files into: %s", len(chunk_temp_files), merged_temp_file)
            return merged_temp_file, deferred_filters if deferred_filters else None
        except IOError as e:
            logger.warning("Failed to merge chunk files: %s. Falling back to in-memory.", e)
            # Fall through to return all_reports if merge fails
    
    return all_reports, deferred_filters if deferred_filters else None


def is_sars_cov2_query(virus, accession=False):
    """
    Check if the query is for SARS-CoV-2 to enable optimized cached downloads.
    
    Args:
        virus (str): Virus taxon name/ID or accession number.
        accession (bool): Whether virus parameter is an accession number.
        
    Returns:
        bool: True if this is a SARS-CoV-2 query.
    """
    if accession:
        # When in accession mode, let the user explicitly set is_sars_cov2=True
        # rather than trying to detect it
        return False
    
    # Check for common SARS-CoV-2 identifiers in taxon names
    virus_lower = virus.lower().replace('-', '').replace('_', '').replace(' ', '')
    
    # Check if the query matches any SARS-CoV-2 identifier
    for identifier in SARS_COV2_IDENTIFIERS:
        if identifier in virus_lower:
            logger.info("Detected SARS-CoV-2 query: %s matches %s", virus, identifier)
            return True
    
    # logger.info("=== Not a SARS-CoV-2 query: %s", virus)
    return False


def is_alphainfluenza_query(virus, accession=False):
    """
    Check if the query is for Alphainfluenza to enable optimized cached downloads.
    
    Cached packages are available for:
        - Alphainfluenza (genus, taxid: 197911)
        - Alphainfluenzavirus influenzae (species, taxid: 2955291)
        - Influenza A virus (no-rank, taxid: 11320)
    
    Args:
        virus (str): Virus taxon name/ID or accession number.
        accession (bool): Whether virus parameter is an accession number.
        
    Returns:
        bool: True if this is an Alphainfluenza query.
    """
    if accession:
        # When in accession mode, let the user explicitly set is_alphainfluenza=True
        # rather than trying to detect it
        return False
    
    # Check for common Alphainfluenza identifiers in taxon names
    virus_lower = virus.lower().replace('-', '').replace('_', '').replace(' ', '')
    
    # Check if the query matches any Alphainfluenza identifier
    for identifier in ALPHAINFLUENZA_IDENTIFIERS:
        if identifier in virus_lower:
            logger.info("Detected Alphainfluenza query: %s matches %s", virus, identifier)
            return True
    
    # logger.info("=== Not an Alphainfluenza query: %s", virus)
    return False


def process_cached_download(zip_file, virus_type="virus"):
    """
    Process a cached download ZIP file and extract sequences with metadata.
    
    This helper function extracts sequences from a cached ZIP download and loads the rich metadata from data_report.jsonl (if available). The metadata is essential for post-download filtering operations.
    
    NCBI cached downloads typically include:
        - genomic.fna: FASTA sequences
        - data_report.jsonl: Rich metadata with virus genome information
        - dataset_catalog.json: List of files in the package
    
    Args:
        zip_file (str): Path to the downloaded ZIP file.
        virus_type (str): Type of virus for logging messages.
        
    Returns:
        tuple: (sequences, metadata_dict, success)
            - sequences: List of all sequence records from the cached download.
            - metadata_dict: Dictionary mapping accessions to metadata (rich metadata
              from data_report.jsonl if available, or basic metadata from FASTA headers).
            - success: Boolean indicating if processing was successful.
            
    Raises:
        RuntimeError: If no valid sequences are found in the cached data.
    """
    if not zip_file or not os.path.exists(zip_file):
        return None, None, False
    
    # Extract directory path from zip file name
    extract_dir = os.path.splitext(zip_file)[0]
    _unzip_file(zip_file, extract_dir)
    
    if not os.path.exists(extract_dir):
        logger.warning("Extraction directory not found: %s", extract_dir)
        return None, None, False
    
    logger.info("🔬 PROCESSING CACHED DATA...")
    logger.info("Extracted cached data to: %s", extract_dir)
    
    # Find and load metadata from data_report.jsonl (rich metadata from NCBI)
    metadata_files = []
    fasta_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file == 'data_report.jsonl':
                metadata_files.append(os.path.join(root, file))
            elif file.endswith(('.fasta', '.fa', '.fna')):
                fasta_files.append(os.path.join(root, file))
    
    # Write rich metadata from data_report.jsonl to a temp JSONL file (memory-efficient)
    # Instead of building a dict of millions of records in RAM, we stream to disk and let the caller load/filter from the file with _load_metadata_dict_from_temp_jsonl
    cached_metadata_jsonl_path = None
    cached_metadata_record_count = 0
    if metadata_files:
        logger.info("Found %d metadata file(s) in cached download", len(metadata_files))
        # Create temp JSONL path next to the zip file
        cached_metadata_jsonl_path = os.path.join(extract_dir, "_cached_metadata_internal.jsonl")
        
        try:
            with open(cached_metadata_jsonl_path, 'w', encoding='utf-8') as out_jsonl:
                for metadata_file in metadata_files:
                    try:
                        # Get file size for progress bar estimation
                        file_size = os.path.getsize(metadata_file)
                        file_size_mb = file_size / BYTES_PER_MB
                        logger.debug("Streaming metadata file to temp JSONL: %s (%.1f MB)", metadata_file, file_size_mb)
                        
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            # Use tqdm to show progress while reading the file
                            pbar = tqdm(
                                total=file_size,
                                unit='B',
                                unit_scale=True,
                                unit_divisor=1024,
                                desc="Processing metadata",
                                ncols=80,
                                leave=True
                            )
                            
                            for line in f:
                                if line.strip():
                                    # Update progress based on bytes read
                                    pbar.update(len(line.encode('utf-8')))
                                    
                                    report = json.loads(line)
                                    # Extract accession from the report
                                    accession = report.get('accession', '')
                                    if not accession:
                                        continue
                                    
                                    cached_metadata_record_count += 1
                                    
                                    # Update progress bar description with record count
                                    if cached_metadata_record_count % 10000 == 0:
                                        pbar.set_description(f"Processing metadata ({cached_metadata_record_count:,} records)")
                                    
                                    # Transform the NCBI report format to our internal metadata format
                                    # This mirrors the logic in load_metadata_from_api_reports
                                    metadata = {
                                        'accession': accession,
                                        'length': report.get('length'),
                                        'geneCount': report.get('geneCount'),
                                        'completeness': report.get('completeness', '').lower(),
                                    }
                                    
                                    # Extract virus info
                                    virus_info = report.get('virus', {})
                                    metadata['virusName'] = virus_info.get('organismName')
                                    metadata['virusTaxId'] = virus_info.get('taxId')
                                    metadata['virusPangolinClassification'] = virus_info.get('pangolinClassification')
                                    
                                    # Extract host info
                                    host_info = report.get('host', {})
                                    metadata['hostName'] = host_info.get('organismName') 
                                    metadata['hostTaxId'] = host_info.get('taxId') 
                                    
                                    # Extract isolate info 
                                    isolate_info = report.get('isolate', {})
                                    metadata['isolateName'] = isolate_info.get('name')
                                    # Store isolate as nested dict to match filter_metadata_only expectations
                                    metadata['isolate'] = {
                                        'collectionDate': isolate_info.get('collectionDate'),  
                                        'source': isolate_info.get('source'),
                                    }
                                    
                                    # Extract location info
                                    location_info = report.get('location', {})
                                    metadata['location'] = location_info.get('geographicLocation')
                                    metadata['region'] = location_info.get('geographicRegion')
                                                                
                                    # Extract other fields
                                    metadata['releaseDate'] = report.get('releaseDate')
                                    metadata['isAnnotated'] = report.get('isAnnotated', False)
                                    metadata['sourceDatabase'] = report.get('sourceDatabase')
                                    metadata['isLabHost'] = report.get('isLabHost', False)
                                    
                                    # Gene and protein counts
                                    metadata['proteinCount'] = report.get('proteinCount')
                                    metadata['maturePeptideCount'] = report.get('maturePeptideCount')
                                    
                                    # Extract segment
                                    metadata['segment'] = report.get('segment')
                                    
                                    # Extract vaccine strain flag
                                    metadata['isVaccineStrain'] = report.get('isVaccineStrain', False)

                                    submitter_info = report.get('submitter', {})
                                    metadata['submitterName'] = submitter_info.get('names')
                                    metadata['submitterCountry'] = submitter_info.get('country')
                                    metadata['submitterInstitution'] = submitter_info.get('affiliation')
                                    
                                    # Write transformed record to temp JSONL (one line per record)
                                    out_jsonl.write(json.dumps(metadata) + "\\n")
                            
                            pbar.close()
                            
                        logger.info("✅ Streamed %d metadata records from %s to temp JSONL", 
                                   cached_metadata_record_count, metadata_file)
                    except Exception as e:
                        logger.warning("❌ Failed to process metadata file %s: %s", metadata_file, e)
                        continue
        except Exception as e:
            logger.warning("❌ Failed to create cached metadata JSONL: %s", e)
            cached_metadata_jsonl_path = None
    else:
        logger.warning("No data_report.jsonl found in cached download. Post-download filters may be limited.")
    
    if not fasta_files:
        logger.error("❌ No FASTA files found in cached data.")
        raise RuntimeError("No FASTA files found in cached data")
    
    for fasta_file in fasta_files:
        file_size = os.path.getsize(fasta_file)
        file_size_mb = file_size / BYTES_PER_MB
        if file_size_mb < MIN_VALID_FASTA_SIZE_MB:
            logger.warning("⚠️ FASTA file %s is smaller than expected (%.1f MB). It may not contain valid sequences.", fasta_file, file_size_mb)
        else:
            logger.info("✅ Cached FASTA file available for streaming: %s (%.1f MB)", fasta_file, file_size_mb)
    
    # If no rich metadata was loaded, create minimal metadata from FASTA headers
    if not cached_metadata_jsonl_path or cached_metadata_record_count == 0:
        logger.info("Creating basic metadata from FASTA headers (no data_report.jsonl available)")
        logger.info("Streaming FASTA files to extract minimal metadata...")
        
        cached_metadata_jsonl_path = os.path.join(extract_dir, "_cached_metadata_internal.jsonl")
        cached_metadata_record_count = 0
        seen_fasta_accessions = set()
        
        try:
            with open(cached_metadata_jsonl_path, 'w', encoding='utf-8') as out_jsonl:
                for fasta_file in fasta_files:
                    try:
                        file_size = os.path.getsize(fasta_file)
                        
                        with open(fasta_file, 'r', encoding='utf-8') as f:
                            pbar = tqdm(
                                total=file_size,
                                unit='B',
                                unit_scale=True,
                                unit_divisor=1024,
                                desc="Extracting FASTA metadata",
                                ncols=80,
                                leave=True
                            )
                            
                            current_accession = None
                            sequence_length = 0
                            description = ""
                            
                            for line in f:
                                pbar.update(len(line.encode('utf-8')))
                                
                                if line.startswith('>'):
                                    # Save previous sequence if exists
                                    if current_accession and current_accession not in seen_fasta_accessions:
                                        seen_fasta_accessions.add(current_accession)
                                        metadata = {
                                            'accession': current_accession,
                                            'description': description,
                                            'length': sequence_length,
                                            'source': 'cached_fasta_header'
                                        }
                                        out_jsonl.write(json.dumps(metadata) + "\\n")
                                        cached_metadata_record_count += 1
                                    
                                    # Parse new header
                                    header = line[1:].strip()
                                    current_accession = header.split()[0]
                                    description = header
                                    sequence_length = 0
                                    
                                else:
                                    # Count bases in sequence (not including whitespace)
                                    sequence_length += len(line.strip())
                            
                            # Save last sequence
                            if current_accession and current_accession not in seen_fasta_accessions:
                                seen_fasta_accessions.add(current_accession)
                                metadata = {
                                    'accession': current_accession,
                                    'description': description,
                                    'length': sequence_length,
                                    'source': 'cached_fasta_header'
                                }
                                out_jsonl.write(json.dumps(metadata) + "\\n")
                                cached_metadata_record_count += 1
                            
                            pbar.close()
                            
                        logger.info("✅ Extracted metadata for sequences from %s", fasta_file)
                        
                    except Exception as e:
                        logger.warning("❌ Failed to extract metadata from FASTA %s: %s", fasta_file, e)
                        continue
            
            logger.info("Created basic metadata for %d sequences", cached_metadata_record_count)
        except Exception as e:
            logger.warning("❌ Failed to create FASTA metadata JSONL: %s", e)
            cached_metadata_jsonl_path = None
    
    logger.info("🎉 CACHED DATA LOADING SUCCESSFUL!")
    logger.debug("Cached %s sequences will be streamed on-demand (not loaded to RAM)", virus_type)
    if metadata_files:
        logger.info("Rich metadata available from data_report.jsonl for post-download filtering")
    
    # Return the cached FASTA file path and the path to the metadata JSONL (not loaded to RAM)
    # Sequences and metadata will be streamed on-demand when needed
    cached_fasta_file = fasta_files[0] if fasta_files else None
    return cached_fasta_file, cached_metadata_jsonl_path, True


def _monitor_subprocess_with_progress(process, cmd, timeout=None, progress_timeout=None):
    """
    Monitor a subprocess with progress tracking and timeout handling.
    
    This helper function monitors a running subprocess. When stdout/stderr are piped, it checks for progress indicators. When they're not piped (output goes to console), it simply polls for completion.
    
    Args:
        process: subprocess.Popen instance to monitor.
        cmd (list): Command that was executed (for error reporting).
        timeout (int): Maximum total execution time in seconds. Defaults to DOWNLOAD_OVERALL_TIMEOUT.
        progress_timeout (int): Maximum time without progress in seconds. Defaults to DOWNLOAD_PROGRESS_TIMEOUT.
        
    Returns:
        subprocess.CompletedProcess: Result of the completed process.
        
    Raises:
        subprocess.TimeoutExpired: If timeout conditions are met.
    """
    # Apply default timeouts if not specified
    if timeout is None:
        timeout = DOWNLOAD_OVERALL_TIMEOUT
    if progress_timeout is None:
        progress_timeout = DOWNLOAD_PROGRESS_TIMEOUT
    
    start_time = time.time()
    last_progress = start_time
    
    while True:
        # Check if process has finished
        retcode = process.poll()
        if retcode is not None:
            break
            
        # Only check for progress if stderr was captured (is not None)
        if process.stderr is not None:
            # Read stderr without blocking
            stderr = process.stderr.readline()
            if stderr:
                # Log the stderr for debugging
                # logger.debug("Progress output: %s", stderr.strip())
                
                # If we see any progress indicator, update the last_progress time
                if any(indicator.lower() in stderr.lower() for indicator in PROGRESS_INDICATORS):
                    last_progress = time.time()
                    # logger.debug("Progress detected, updating last_progress time")
        
        # Check timeout conditions:
        # 1. Less than total timeout, continue
        # 2. If more than total timeout but progress in last progress_timeout, continue
        # 3. Otherwise, timeout
        current_time = time.time()
        total_time = current_time - start_time
        time_since_progress = current_time - last_progress
        
        if total_time > timeout and time_since_progress > progress_timeout:
            process.kill()
            raise subprocess.TimeoutExpired(cmd, timeout)
        
        time.sleep(DOWNLOAD_PROGRESS_CHECK_INTERVAL)  # Prevent CPU spin
    
    # Only call communicate if process was created with pipes, otherwise just wait
    if process.stdout is not None or process.stderr is not None:
        stdout, stderr = process.communicate()
    else:
        stdout = None
        stderr = None
        process.wait()
    
    return subprocess.CompletedProcess(
        args=cmd,
        returncode=retcode,
        stdout=stdout,
        stderr=stderr
    )


def _download_optimized_cached(
    virus_type,
    strategies,
    zip_path,
    outdir,
    use_accession=False,
    accession=None,
    requested_filters=None
):
    """
    Execute optimized cached download strategies with fallback.
    
    This is a generic implementation of the hierarchical fallback download pattern
    used for both SARS-CoV-2 and Alphainfluenza. It tries each strategy in order
    until one succeeds, with comprehensive error handling and logging.
    
    Args:
        virus_type (str): Type of virus for error messages ('SARS-CoV-2', 'Alphainfluenza', etc.).
        strategies (list): List of tuples (strategy_name, cmd, applied_filters).
        zip_path (str): Path where ZIP file should be saved.
        outdir (str): Output directory for download.
        use_accession (bool): Whether using accession-based download.
        accession (str, optional): Accession number if using accession-based download.
        requested_filters (dict, optional): Dictionary of originally requested filters.
        
    Returns:
        tuple: (zip_path, applied_filters, missing_filters)
            - zip_path (str): Path to the successfully downloaded ZIP file.
            - applied_filters (list): List of filter names applied in successful strategy.
            - missing_filters (list): List of filter names not applied (need post-processing).
        
    Raises:
        RuntimeError: If all strategies fail or datasets CLI is not available.
        
    Example:
        >>> strategies = [
        ...     ("Strategy 1 (specific)", ["datasets", "download", ...], ["complete-only"]),
        ...     ("Strategy 2 (general)", ["datasets", "download", ...], [])
        ... ]
        >>> zip_file, applied, missing = _download_optimized_cached(
        ...     "SARS-CoV-2", strategies, "/path/to/output.zip", "/output/dir"
        ... )
    """
    
    # Get the path to the datasets CLI binary (uses precompiled binary bundled with gget)
    datasets_path = _get_datasets_path()
    
    last_error = None
    
    for strategy_name, cmd, applied_filters in strategies:
        # Replace "datasets" with the actual path to the binary
        if cmd and cmd[0] == "datasets":
            cmd = [datasets_path] + cmd[1:]
        
        logger.info("🔄 Trying optimised strategy download with %s...", strategy_name)
        
        if applied_filters:
            logger.info("Applied filters: %s", ", ".join(applied_filters))
        else:
            logger.info("No specific filters applied")
        
        logger.debug("Command: %s", " ".join(cmd))
        
        try:
            # Log the exact command being executed
            cmd_str = " ".join(cmd)
            logger.debug("📋 Executing command: %s", cmd_str)

            # Start subprocess for progress monitoring
            # Note: We don't use cwd=outdir because the command already includes full paths
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=None,
                    stderr=None,
                    text=True
                )
            except FileNotFoundError as fnf_error:
                # Datasets binary not found - this shouldn't happen if bundled correctly
                error_msg = (
                    f"❌ datasets binary not found at expected path.\n\n"
                    f"Expected path: {datasets_path}\n\n"
                    "🔧 SOLUTION:\n"
                    "• Please reinstall gget to restore the bundled datasets binary.\n"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from fnf_error
            
            # Monitor progress with timeout handling using helper function
            result = _monitor_subprocess_with_progress(process, cmd)
            
            # Check if the command was successful
            if result.returncode == 0 and os.path.exists(zip_path):
                file_size = os.path.getsize(zip_path)
                
                # Check if file is too small (likely empty result) - if so, try next strategy. It's not zero since the folder always comes with a generic (readme) files.
                if file_size < MIN_VALID_ZIP_SIZE:
                    logger.warning("⚠️ %s resulted in file that's too small (%.2f MB, < 100 KB minimum). Trying next strategy...", 
                                 strategy_name, file_size / 1024 / 1024)
                    # Clean up invalid file
                    try:
                        os.remove(zip_path)
                    except OSError:
                        pass
                    continue
                
                logger.info("✅ %s successful: %s (%.2f MB)", 
                           strategy_name, os.path.basename(zip_path), file_size / 1024 / 1024)
                
                # Log any important output from the datasets CLI
                # if result.stdout:
                #     logger.debug("datasets CLI output: %s", result.stdout.strip())
                
                # Check which filters from the original request weren't applied in this strategy
                if requested_filters:
                    requested_filter_list = []
                    for key, value in requested_filters.items():
                        logger.debug("Requested filter: %s=%s", key, value)
                        if value is not None and value is not False:
                            logger.debug("Adding filter to requested list: %s=%s", key, value)
                            if isinstance(value, bool):
                                logger.debug("Boolean filter detected, adding key only: %s", key)
                                requested_filter_list.append(key)
                            else:
                                logger.debug("Non-boolean filter detected, adding key=value: %s=%s", key, value)
                                requested_filter_list.append(f"{key}={value}")
                    
                    missing_filters = [f for f in requested_filter_list if f not in applied_filters]
                    if missing_filters:
                        logger.warning("⚠️ Some requested filters were not applied in successful strategy:")
                        logger.warning("   Filters applied: %s", ", ".join(applied_filters) if applied_filters else "none")
                        logger.warning("   Filters missing: %s", ", ".join(missing_filters))
                        logger.warning("   These filters will need to be applied through post-processing")
                else:
                    missing_filters = []
                
                return zip_path, applied_filters, missing_filters
            else:
                # Strategy failed, prepare error message
                error_msg = f"{strategy_name} failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr.strip()}"
                logger.warning("%s", error_msg)
                last_error = error_msg
                
                # If this was an accession download that failed, provide specific guidance
                if use_accession:
                    error_msg = (
                        f"Failed to download {virus_type} sequence for accession '{accession}'. "
                        f"Please verify that this is a valid {virus_type} accession number. "
                        f"If you're not sure, try without the is_{virus_type.lower().replace('-', '_').replace(' ', '_')} flag."
                    )
                    raise RuntimeError(error_msg)
                
                # Clean up failed download file if it exists
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except OSError:
                        pass
                continue # Try next strategy
                
        except subprocess.TimeoutExpired:
            error_msg = f"{strategy_name} timed out after 30 minutes"
            logger.warning("%s", error_msg)
            last_error = error_msg
            continue
            
        except subprocess.CalledProcessError as e:
            error_msg = f"{strategy_name} execution failed: {e}"
            logger.warning("%s", error_msg)
            last_error = error_msg
            continue
            
        except Exception as e:
            error_msg = f"{strategy_name} unexpected error: {e}"
            logger.warning("%s", error_msg)
            last_error = error_msg
            continue
    
    # All strategies failed
    logger.warning("🚨 All cached download strategies failed. Last error: %s", last_error)
    
    # Provide helpful guidance based on virus type
    example_taxon = "SARS-CoV-2" if "sars" in virus_type.lower() else virus_type
    guidance_messages = [
        "🔧 TROUBLESHOOTING SUGGESTIONS:",
        "1. Check your internet connection",
        "2. Try running the command manually to see detailed error messages:",
        f"   {datasets_path} download virus genome taxon \"{example_taxon}\" --filename test.zip",
        "3. NCBI servers may be temporarily unavailable - try again later",
        f"4. Consider using the general API method by removing {virus_type} specific terms from your query"
    ]
    
    for msg in guidance_messages:
        logger.info(msg)
    
    # Raise error with the last failure details
    raise RuntimeError(
        f"All {virus_type} cached download strategies failed. "
        f"Last error: {last_error}. "
        f"Consider using the general API method instead."
    )


def download_sars_cov2_optimized(
    host=None,
    complete_only=None,
    annotated=None,
    outdir=None,
    lineage=None,
    accession=None,
    use_accession=False,
):
    """
    Download SARS-CoV-2 sequences using NCBI's optimized cached data packages.
    
    NCBI provides pre-computed, highly compressed cached packages for SARS-CoV-2
    that offer faster and more reliable downloads than the general API endpoints.
    This function uses the datasets CLI to download these optimized packages with
    hierarchical fallback from specific to general cached files.
    
    Download strategies (in order of precedence):
        1. If use_accession=True: Direct accession download using accession endpoint.
        2. If use_accession=False:
           a. Specific lineage + complete + host filters using taxon endpoint.
           b. Complete genomes only using taxon endpoint.
           c. All SARS-CoV-2 genomes using taxon endpoint (default fallback).
    
    Args:
        host (str, optional): Host organism filter (optimized for 'human').
        complete_only (bool, optional): Whether to download only complete genomes.
        annotated (bool, optional): Whether to download only annotated genomes.
        outdir (str, optional): Output directory for downloaded files.
        lineage (str, optional): SARS-CoV-2 lineage filter (e.g., 'B.1.1.7', 'P.1').
        accession (str, optional): Specific SARS-CoV-2 accession or taxon ID.
        use_accession (bool): Whether to use accession endpoint. Defaults to False.
        
    Returns:
        str: Path to the downloaded ZIP file containing sequences and metadata.
        
    Raises:
        RuntimeError: If the datasets CLI is not available or download fails.
    """
    
    # Determine filter specificity for logging
    filter_count = sum(1 for param in [host, complete_only, annotated, lineage] if param is not None)
    if filter_count > 0:
        logger.info("Attempting SARS-CoV-2 cached download with %d specific filters", filter_count)
    else:
        logger.info("Attempting general SARS-CoV-2 cached download (no specific filters)")
    
    # Determine output directory
    if not outdir:
        outdir = os.getcwd()
        logger.debug("No output directory specified, using current directory: %s", outdir)
    
    # Ensure output directory exists
    os.makedirs(outdir, exist_ok=True)
    logger.debug("Output directory ready: %s", outdir)
    
    # Create descriptive filename with timestamp and random suffix
    zip_filename = f"sars_cov_2_{timestamp}_{random_suffix}.zip"
    zip_path = os.path.join(outdir, zip_filename)
    
    # Define which filters are available for this download
    logger.debug("Available filters for SARS-CoV-2 download:")
    if complete_only:
        logger.debug("- complete-only filter")
    if lineage:
        logger.debug("- lineage filter: %s", lineage)
    if host:
        logger.debug("- host filter: %s", host)
    if annotated:
        logger.debug("- annotated filter")
    
    # Define fallback strategies in order of preference
    strategies = []
    
    if use_accession:
        # Parse the accession input to handle single, space-separated, or file-based accessions
        parsed = _parse_accession_input(accession)
        
        if parsed['is_file']:
            # File-based input: use --inputfile flag
            cmd1 = ["datasets", "download", "virus", "genome", "accession", 
                   "--inputfile", parsed['file_path']]
            cmd1.extend(["--filename", zip_path])
            strategies.append(("Strategy 1 (accessions from file)", cmd1, [f"inputfile={parsed['file_path']}"]))
            logger.debug("Using accession input file: %s", parsed['file_path'])
        elif parsed['type'] == 'list':
            # Space-separated accessions: pass as arguments
            cmd1 = ["datasets", "download", "virus", "genome", "accession"] + parsed['accessions']
            cmd1.extend(["--filename", zip_path])
            strategies.append(("Strategy 1 (multiple accessions)", cmd1, [f"accessions={', '.join(parsed['accessions'][:3])}..."]))
            logger.debug("Using multiple accessions: %s", ", ".join(parsed['accessions']))
        else:
            # Single accession
            cmd1 = ["datasets", "download", "virus", "genome", "accession", parsed['accessions']]
            cmd1.extend(["--filename", zip_path])
            strategies.append(("Strategy 1 (direct accession)", cmd1, [f"accession={parsed['accessions']}"]))
            logger.debug("Using single accession: %s", parsed['accessions'])
    elif lineage or complete_only or host or annotated:
        # Strategy 1: Try with specific filters using taxon endpoint
        cmd1 = ["datasets", "download", "virus", "genome", "taxon", "SARS-CoV-2"]
        filters1 = []
        
        if complete_only:
            cmd1.append("--complete-only")
            filters1.append("complete-only")
        
        if lineage:
            cmd1.extend(["--lineage", lineage])
            filters1.append(f"lineage={lineage}")

        if host:
            cmd1.extend(["--host", host])
            filters1.append(f"host={host}")
        
        if annotated:
            cmd1.append("--annotated")
            filters1.append("annotated")

        cmd1.extend(["--filename", zip_path])
        strategies.append(("Strategy 1 (specific filters)", cmd1, filters1))
    
    # Strategy 2: Try complete-only and host if it was requested (without lineage)
    if complete_only and host and lineage:  # Only add this if we had lineage in strategy 1
        cmd2 = ["datasets", "download", "virus", "genome", "taxon", "SARS-CoV-2", "--complete-only", "--host", host, "--filename", zip_path]
        strategies.append(("Strategy 2 (complete-only and host)", cmd2, ["complete-only", f"host={host}"]))

    # Strategy 3: Try complete-only if it was requested
    if complete_only and (host or lineage):  
        cmd3 = ["datasets", "download", "virus", "genome", "taxon", "SARS-CoV-2", "--complete-only", "--filename", zip_path]
        strategies.append(("Strategy 3 (complete-only)", cmd3, ["complete-only"]))

    # Strategy 4: Try host if it was requested 
    if host and (complete_only or lineage):  
        cmd4 = ["datasets", "download", "virus", "genome", "taxon", "SARS-CoV-2", "--host", host, "--filename", zip_path]
        strategies.append(("Strategy 4 (host)", cmd4, [f"host={host}"]))

    # Strategy 5: Try lineage if it was requested 
    if lineage and (complete_only or host):  
        cmd5 = ["datasets", "download", "virus", "genome", "taxon", "SARS-CoV-2", "--lineage", lineage, "--filename", zip_path]
        strategies.append(("Strategy 5 (lineage)", cmd5, [f"lineage={lineage}"]))

    # Strategy 6: General SARS-CoV-2 package (no filters)
    cmd6 = ["datasets", "download", "virus", "genome", "taxon", "SARS-CoV-2", "--filename", zip_path]
    strategies.append(("Strategy 6 (general package)", cmd6, []))

    # Use the common download function with all strategies
    requested_filters_dict = {
        'complete-only': complete_only,
        'lineage': lineage,
        'host': host,
        'annotated': annotated
    }
    
    return _download_optimized_cached(
        virus_type="SARS-CoV-2",
        strategies=strategies,
        zip_path=zip_path,
        outdir=outdir,
        use_accession=use_accession,
        accession=accession,
        requested_filters=requested_filters_dict
    )


def download_alphainfluenza_optimized(
    host=None,
    complete_only=None,
    annotated=None,
    outdir=None,
    accession=None,
    use_accession=False,
):
    """
    Download Alphainfluenza sequences using NCBI's optimized cached data packages.
    
    NCBI provides pre-computed, highly compressed cached packages for Alphainfluenza
    that offer faster and more reliable downloads than the general API endpoints.
    This function uses the datasets CLI to download these optimized packages with
    hierarchical fallback from specific to general cached files.
    
    Cached packages are available for the following Alphainfluenza taxonomic nodes:
        1. Alphainfluenza (genus, taxid: 197911)
        2. Alphainfluenzavirus influenzae (species, taxid: 2955291)
        3. Influenza A virus (no-rank, taxid: 11320)
    
    For each taxon, filtered sets are available:
        1. All genomes
        2. Human host only
        3. Human host only & complete
        4. Complete only
    
    Args:
        host (str, optional): Host organism filter (optimized for 'human').
        complete_only (bool, optional): Whether to download only complete genomes.
        annotated (bool, optional): Whether to download only annotated genomes.
        outdir (str, optional): Output directory for downloaded files.
        accession (str, optional): Specific Alphainfluenza accession or taxon ID.
        use_accession (bool): Whether to use accession endpoint. Defaults to False.
        
    Returns:
        str: Path to the downloaded ZIP file containing sequences and metadata.
        
    Raises:
        RuntimeError: If the datasets CLI is not available or download fails.
    """
    
    # Determine filter specificity for logging
    filter_count = sum(1 for param in [host, complete_only, annotated] if param is not None)
    if filter_count > 0:
        logger.info("Attempting Alphainfluenza cached download with %d specific filters", filter_count)
    else:
        logger.info("Attempting general Alphainfluenza cached download (no specific filters)")
    
    # Determine output directory
    if not outdir:
        outdir = os.getcwd()
        logger.debug("No output directory specified, using current directory: %s", outdir)
    
    # Ensure output directory exists before passing path to datasets CLI
    os.makedirs(outdir, exist_ok=True)
    logger.debug("Output directory ready: %s", outdir)
    
    # Create descriptive filename with timestamp and random suffix
    zip_filename = f"alphainfluenza_{timestamp}_{random_suffix}.zip"
    zip_path = os.path.join(outdir, zip_filename)
    
    # Ensure the parent directory exists (in case outdir has subdirectories)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    
    # Define which filters are available for this download
    logger.debug("Available filters for Alphainfluenza download:")
    if complete_only:
        logger.debug("- complete-only filter")
    if host:
        logger.debug("- host filter: %s", host)
    if annotated:
        logger.debug("- annotated filter")
    
    # Define fallback strategies in order of preference
    strategies = []
    
    # Default taxon to use (most specific: Alphainfluenzavirus influenzae species)
    # This taxon ID has the most comprehensive cached data
    default_taxon = ALPHAINFLUENZA_DEFAULT_TAXON
    
    if use_accession:
        # Parse the accession input to handle single, space-separated, or file-based accessions
        parsed = _parse_accession_input(accession)
        
        if parsed['is_file']:
            # File-based input: use --inputfile flag
            cmd1 = ["datasets", "download", "virus", "genome", "accession", 
                   "--inputfile", parsed['file_path']]
            cmd1.extend(["--filename", zip_path])
            strategies.append(("Strategy 1 (accessions from file)", cmd1, [f"inputfile={parsed['file_path']}"]))
            logger.debug("Using accession input file: %s", parsed['file_path'])
        elif parsed['type'] == 'list':
            # Space-separated accessions: pass as arguments
            cmd1 = ["datasets", "download", "virus", "genome", "accession"] + parsed['accessions']
            cmd1.extend(["--filename", zip_path])
            strategies.append(("Strategy 1 (multiple accessions)", cmd1, [f"accessions={', '.join(parsed['accessions'][:3])}..."]))
            logger.debug("Using multiple accessions: %s", ", ".join(parsed['accessions']))
        else:
            # Single accession
            cmd1 = ["datasets", "download", "virus", "genome", "accession", parsed['accessions']]
            cmd1.extend(["--filename", zip_path])
            strategies.append(("Strategy 1 (direct accession)", cmd1, [f"accession={parsed['accessions']}"]))
            logger.debug("Using single accession: %s", parsed['accessions'])
    elif complete_only or host or annotated:
        # Strategy 1: Try with specific filters using taxon endpoint
        cmd1 = ["datasets", "download", "virus", "genome", "taxon", default_taxon]
        filters1 = []
        
        if complete_only:
            cmd1.append("--complete-only")
            filters1.append("complete-only")

        if host:
            cmd1.extend(["--host", host])
            filters1.append(f"host={host}")
        
        if annotated:
            cmd1.append("--annotated")
            filters1.append("annotated")

        cmd1.extend(["--filename", zip_path])
        strategies.append(("Strategy 1 (specific filters)", cmd1, filters1))
    
    # Strategy 2: Try complete-only and host if both were requested
    if complete_only and host:
        cmd2 = ["datasets", "download", "virus", "genome", "taxon", default_taxon, "--complete-only", "--host", host, "--filename", zip_path]
        strategies.append(("Strategy 2 (complete-only and host)", cmd2, ["complete-only", f"host={host}"]))

    # Strategy 3: Try complete-only if it was requested
    if complete_only and (host or annotated):  
        cmd3 = ["datasets", "download", "virus", "genome", "taxon", default_taxon, "--complete-only", "--filename", zip_path]
        strategies.append(("Strategy 3 (complete-only)", cmd3, ["complete-only"]))

    # Strategy 4: Try host if it was requested 
    if host and (complete_only or annotated):  
        cmd4 = ["datasets", "download", "virus", "genome", "taxon", default_taxon, "--host", host, "--filename", zip_path]
        strategies.append(("Strategy 4 (host)", cmd4, [f"host={host}"]))

    # Strategy 5: General Alphainfluenza package (no filters)
    cmd5 = ["datasets", "download", "virus", "genome", "taxon", default_taxon, "--filename", zip_path]
    strategies.append(("Strategy 5 (general package)", cmd5, []))

    # Use the common download function with all strategies
    requested_filters_dict = {
        'complete-only': complete_only,
        'host': host,
        'annotated': annotated
    }
    
    return _download_optimized_cached(
        virus_type="Alphainfluenza",
        strategies=strategies,
        zip_path=zip_path,
        outdir=outdir,
        use_accession=use_accession,
        accession=accession,
        requested_filters=requested_filters_dict
    )


def download_sequences_by_accessions(accessions, outdir=None, batch_size=200, failed_commands=None, api_key=None):
    """
    Download virus genome sequences for a specific list of accession numbers.
    
    This function downloads sequences for a pre-filtered list of accessions,
    using NCBI E-utilities API with batching to avoid URL length limitations.
    Large requests are automatically split into smaller batches.
    
    Args:
        accessions (list): List of accession numbers to download.
        outdir (str, optional): Output directory for downloaded files.
        batch_size (int): Maximum number of accessions per batch. Defaults to 200.
        failed_commands (dict, optional): Dictionary to track failed operations.
        api_key (str, optional): NCBI API key for higher rate limits (10 req/sec vs 3).
        
    Returns:
        str: Path to the downloaded FASTA file containing sequences.
        
    Raises:
        RuntimeError: If the download request fails.
        ValueError: If no accessions are provided.
    """
    
    if not accessions:
        raise ValueError("No accessions provided for download")
    
    logger.info("Downloading sequences for %d accessions using E-utilities API", len(accessions))
    logger.debug("Accession list: %s", accessions[:5] + ['...'] if len(accessions) > 5 else accessions)
    
    # Determine output directory - use current working directory if not specified
    if not outdir:
        outdir = os.getcwd()
        logger.debug("No output directory specified, using current directory: %s", outdir)
    
    # Ensure output directory exists
    os.makedirs(outdir, exist_ok=True)
    logger.debug("Ensured output directory exists: %s", outdir)
    
    # Create output FASTA file path
    fasta_path = os.path.join(outdir, f"virus_sequences_{timestamp}_{random_suffix}.fasta")
    logger.debug("Saving sequences to: %s", fasta_path)
    
    # For large datasets, prefer the EPost + EFetch History Server pipeline
    # This is NCBI's recommended approach and is significantly faster
    if len(accessions) > batch_size:
        logger.info("Large request detected (%d accessions). Trying EPost+EFetch History Server pipeline...", 
                   len(accessions))
        try:
            _download_sequences_epost_efetch(accessions, fasta_path, failed_commands)
        except Exception as epost_error:
            logger.warning("EPost+EFetch pipeline failed: %s", epost_error)
            logger.info("Falling back to direct batched E-utilities requests...")
            # Reset the file in case partial data was written
            if os.path.exists(fasta_path):
                os.remove(fasta_path)
            return _download_sequences_batched(accessions, NCBI_EUTILS_BASE_EFETCH, fasta_path, batch_size, failed_commands, api_key=api_key)
        
        # Check for missing sequences and retry them via direct batched download
        downloaded_accs = set()
        try:
            with open(fasta_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('>'):
                        acc = line[1:].split()[0].strip()
                        downloaded_accs.add(acc)
        except IOError:
            pass
        
        requested_set = set(accessions)
        missing_accs = requested_set - downloaded_accs
        
        if missing_accs:
            logger.warning("⚠️ EPost+EFetch pipeline missed %d/%d sequences. "
                          "Retrying missing accessions via direct batched download...",
                          len(missing_accs), len(accessions))
            
            # Retry the missing accessions by appending to the existing FASTA file
            temp_retry_path = fasta_path + ".retry_tmp"
            try:
                _download_sequences_batched(
                    list(missing_accs), NCBI_EUTILS_BASE_EFETCH, 
                    temp_retry_path, batch_size, failed_commands, api_key=api_key
                )
                # Append recovered sequences to the main FASTA file
                if os.path.exists(temp_retry_path) and os.path.getsize(temp_retry_path) > 0:
                    with open(fasta_path, 'a', encoding='utf-8') as main_f:
                        with open(temp_retry_path, 'r', encoding='utf-8') as retry_f:
                            main_f.write(retry_f.read())
                    # Count recovered sequences
                    recovered = 0
                    with open(temp_retry_path, 'r', encoding='utf-8') as retry_f:
                        for line in retry_f:
                            if line.startswith('>'):
                                recovered += 1
                    logger.info("✅ Recovered %d/%d missing sequences via direct download",
                               recovered, len(missing_accs))
            except Exception as retry_error:
                logger.warning("⚠️ Retry of missing sequences failed: %s. "
                              "Proceeding with %d/%d sequences.",
                              retry_error, len(downloaded_accs), len(accessions))
            finally:
                if os.path.exists(temp_retry_path):
                    os.remove(temp_retry_path)
        
        return fasta_path
    
    # For smaller requests, use single request
    return _download_sequences_single_batch(accessions, NCBI_EUTILS_BASE_EFETCH, fasta_path, failed_commands, api_key=api_key)


def _download_sequences_epost_efetch(accessions, fasta_path, failed_commands=None, api_key=None):
    """
    Download FASTA sequences using NCBI EPost + EFetch History Server pipeline.
    
    This is NCBI's recommended approach for large datasets. It uploads accession
    IDs to the History Server via EPost, then retrieves FASTA sequences in batches
    using the WebEnv/query_key reference. This avoids URL length limitations and
    is significantly faster than individual batched requests.
    
    Args:
        accessions (list): List of accession numbers to download.
        fasta_path (str): Path where FASTA file should be saved.
        failed_commands (dict, optional): Dictionary to track failed operations.
        api_key (str, optional): NCBI API key for higher rate limits (10 req/sec vs 3).
        
    Returns:
        str: Path to the saved FASTA file.
        
    Raises:
        RuntimeError: If EPost fails or no sequences are retrieved.
    """
    # Resolve API key: argument > module-level env var
    if api_key is None:
        api_key = API_KEY

    logger.info("Starting EPost+EFetch pipeline for %d accessions", len(accessions))

    # Step 1: Upload accessions to NCBI History Server via EPost
    web_env, query_key = _epost_accessions(accessions, api_key=api_key)
    
    if not web_env or not query_key:
        raise RuntimeError(
            "EPost failed: could not upload accessions to NCBI History Server. "
            "The server may be temporarily unavailable."
        )
    
    # Step 2: Fetch FASTA sequences in batches using the History Server reference
    total = len(accessions)
    retmax = EFETCH_FASTA_RETMAX
    total_downloaded = 0
    batch_failures = 0
    
    # Determine inter-batch delay based on API key availability
    delay = EUTILS_INTER_BATCH_DELAY_WITH_KEY if api_key else EUTILS_INTER_BATCH_DELAY
    
    logger.info("Fetching FASTA sequences in batches of %d (total: %d)", retmax, total)
    
    try:
        with open(fasta_path, 'w', encoding='utf-8') as fasta_handle:
            for retstart in range(0, total, retmax):
                batch_num = (retstart // retmax) + 1
                total_batches = (total + retmax - 1) // retmax
                
                logger.debug("EFetch FASTA batch %d/%d (retstart=%d, retmax=%d)",
                            batch_num, total_batches, retstart, retmax)
                
                # Define the fetch operation for retry helper
                def _fetch_fasta_batch(rs=retstart):
                    params = {
                        'db': 'nucleotide',
                        'WebEnv': web_env,
                        'query_key': query_key,
                        'retstart': rs,
                        'retmax': retmax,
                        'rettype': 'fasta',
                        'retmode': 'text',
                    }
                    if api_key:
                        params['api_key'] = api_key
                    
                    response = requests.get(
                        NCBI_EUTILS_BASE_EFETCH,
                        params=params,
                        timeout=EUTILS_TIMEOUT,
                        headers={'User-Agent': 'gget/1.0'}
                    )
                    response.raise_for_status()
                    
                    # Validate FASTA content
                    text = response.text.strip()
                    if not text or not text.startswith('>'):
                        raise RuntimeError(
                            f"Invalid FASTA response for batch at retstart={rs}: "
                            f"response starts with '{text[:50]}'"
                        )
                    return text
                
                # Use exponential backoff retry
                success, fasta_text, error_info = _retry_with_exponential_backoff(
                    operation_name=f"EFetch FASTA batch {batch_num}/{total_batches}",
                    operation_func=_fetch_fasta_batch,
                    max_retries=API_MAX_RETRIES,
                    initial_delay=API_INITIAL_RETRY_DELAY,
                    backoff_multiplier=API_RETRY_BACKOFF_MULTIPLIER,
                    retryable_exceptions=(
                        requests.exceptions.ConnectionError,
                        requests.exceptions.HTTPError,
                        requests.exceptions.Timeout,
                        requests.exceptions.ChunkedEncodingError,
                    ),
                    failed_commands=failed_commands,
                )
                
                if success:
                    # Write FASTA data to file
                    fasta_handle.write(fasta_text)
                    if not fasta_text.endswith('\n'):
                        fasta_handle.write('\n')
                    
                    seq_count = fasta_text.count('>')
                    total_downloaded += seq_count
                    logger.debug("Batch %d/%d: wrote %d sequences (total: %d)",
                                batch_num, total_batches, seq_count, total_downloaded)
                else:
                    batch_failures += 1
                    logger.warning("❌ Batch %d/%d failed after retries: %s",
                                  batch_num, total_batches, 
                                  error_info.get('error', 'unknown'))
                    
                    # Track the failure
                    _track_failed_operation(
                        failed_commands,
                        'sequence_batches',
                        {'batch_num': batch_num, 'retstart': retstart, 'retmax': retmax},
                        error_info if error_info else {'error': 'unknown'}
                    )
                
                # Respect NCBI rate limits
                if retstart + retmax < total:
                    time.sleep(delay)
    
    except IOError as e:
        raise RuntimeError(f"Failed to write FASTA file {fasta_path}: {e}") from e
    
    # Validate results
    if total_downloaded == 0:
        # Clean up empty file
        if os.path.exists(fasta_path):
            os.remove(fasta_path)
        raise RuntimeError(
            f"EPost+EFetch pipeline downloaded 0 sequences out of {total} requested. "
            f"All {batch_failures} batches failed."
        )
    
    file_size_mb = os.path.getsize(fasta_path) / BYTES_PER_MB
    logger.info("✅ EPost+EFetch pipeline complete: %d sequences downloaded (%.2f MB)",
               total_downloaded, file_size_mb)
    
    if batch_failures > 0:
        logger.warning("⚠️ %d batch(es) failed during download. %d/%d sequences retrieved.",
                      batch_failures, total_downloaded, total)
    
    return fasta_path


def _download_sequences_single_batch(accessions, NCBI_EUTILS_BASE_EFETCH, fasta_path, failed_commands=None, api_key=None):
    """
    Download sequences in a single E-utilities request with exponential backoff retries.
    
    This function handles downloading virus sequences for a list of accessions
    using a single HTTP request to NCBI E-utilities. It's optimized for
    smaller batches (< 200 accessions) to avoid URL length limitations. Includes
    exponential backoff retries for transient failures.
    
    Args:
        accessions (list): List of accession numbers to download.
        NCBI_EUTILS_BASE_EFETCH (str): Base URL for NCBI E-utilities API.
        fasta_path (str): Path where FASTA file should be saved.
        failed_commands (dict, optional): Dictionary to track failed operations.
        
    Returns:
        str: Path to the saved FASTA file.
        
    Raises:
        RuntimeError: If the download fails after retries or response is invalid
        
    Note:
        - Validates FASTA format before saving
        - Includes extended timeout for large datasets
        - Implements exponential backoff retries for transient failures
        - Automatically falls back to batching if URL is too long
        
    Example:
        >>> accessions = ['NC_045512.2', 'MN908947.3']
        >>> path = _download_sequences_single_batch(accessions, BASE_URL, 'output.fasta')
    """
    
    # Build accession string (E-utils supports comma-separated IDs)
    accession_string = ",".join(accessions)
    
    def execute_request():
        params = {
            'db': 'nucleotide',
            'id': accession_string,
            'rettype': 'fasta',
            'retmode': 'text'
        }
        if api_key:
            params['api_key'] = api_key
        logger.debug("E-utilities URL: %s", NCBI_EUTILS_BASE_EFETCH)
        response = requests.get(NCBI_EUTILS_BASE_EFETCH, params=params, timeout=EUTILS_TIMEOUT)
        response.raise_for_status()
        
        # Verify we got FASTA data
        if not response.text.strip().startswith('>'):
            raise RuntimeError(f"Invalid FASTA response: {response.text[:100]}")
        
        return response.text
    
    logger.info("Initiating E-utilities request for %d accessions", len(accessions))
    
    # Use exponential backoff helper for retries
    success, response_text, error_info = _retry_with_exponential_backoff(
        operation_name=f"E-utilities request ({len(accessions)} accessions)",
        operation_func=execute_request,
        max_retries=API_MAX_RETRIES,
        initial_delay=API_INITIAL_RETRY_DELAY,
        backoff_multiplier=API_RETRY_BACKOFF_MULTIPLIER,
        retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout),
        failed_commands=failed_commands,
    )
    
    if not success:
        # Check for specific URL length error
        error_msg = error_info['error']
        if "414" in error_msg or "Request-URI Too Long" in error_msg:
            logger.info("URL too long error detected. Retrying with batch processing...")
            # Retry with smaller batches (half of default)
            return _download_sequences_batched(accessions, NCBI_EUTILS_BASE_EFETCH, fasta_path, batch_size=EUTILS_DEFAULT_BATCH_SIZE // 2, failed_commands=failed_commands, api_key=api_key)
        
        # Log and track the failure
        logger.error("❌ E-utilities request failed after %d retries: %s", API_MAX_RETRIES, error_msg)
        
        # Track failed operation for later reporting in command summary
        retry_url = f"{NCBI_EUTILS_BASE_EFETCH}?db=nucleotide&id={accession_string}&rettype=fasta&retmode=text"
        _track_failed_operation(
            failed_commands, 
            'sequence_fetch',
            {
                'operation': 'single_batch_download',
                'accession_count': len(accessions),
                'retry_url': retry_url,
            },
            error_info
        )
        
        raise RuntimeError(f"❌ Failed to download virus sequences via E-utilities after {API_MAX_RETRIES} retries: {error_msg}") from None
    
    # Save to file
    try:
        # Count sequences in response
        sequence_count = response_text.count('>')
        logger.info("Received %d sequences from E-utilities", sequence_count)
        
        # Write FASTA data to file
        with open(fasta_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
            
        logger.info("Successfully saved sequences to: %s (%.2f MB)", 
                   fasta_path, len(response_text.encode('utf-8')) / 1024 / 1024)
        return fasta_path
        
    except IOError as e:
        logger.error("❌ Failed to save FASTA file: %s", e)
        raise RuntimeError(f"❌ Failed to save downloaded sequences: {e}") from e


def _download_sequences_batched(accessions, NCBI_EUTILS_BASE_EFETCH, fasta_path, batch_size, failed_commands=None, api_key=None):
    """
    Download sequences using multiple batched E-utilities requests with incremental file writing.
    
    This function handles large sequence downloads by splitting them into smaller
    batches and writing results incrementally to avoid memory issues. It includes
    robust error handling with automatic exponential backoff retries for failed batches.
    
    Key features:
    - Batched requests to avoid URL length limits
    - Exponential backoff retries for each batch
    - Incremental file writing to manage memory
    - Automatic retry with smaller batch sizes for URL length failures
    - Progress tracking and detailed logging
    - Graceful handling of partial failures (continues after batch failures)
    
    Args:
        accessions (list): List of accession numbers to download.
        NCBI_EUTILS_BASE_EFETCH (str): Base URL for NCBI E-utilities API.
        fasta_path (str): Path where FASTA file should be saved.
        batch_size (int): Number of accessions per batch.
        failed_commands (dict, optional): Dictionary to track failed operations.
        api_key (str, optional): NCBI API key for higher rate limits (10 req/sec vs 3).
        
    Returns:
        str: Path to the saved FASTA file containing all downloaded sequences
        
    Raises:
        RuntimeError: If all batches fail or no sequences are downloaded
        
    Note:
        - Respects NCBI rate limits with 0.5s delays between batches
        - Implements exponential backoff for individual batch retries
        - Automatically reduces batch size for URL length errors
        - Continues processing even if some batches fail
        - Writes sequences immediately to reduce memory usage
        
    Example:
        >>> large_accession_list = ['NC_045512.2', 'MN908947.3', ...]  # 1000+ accessions
        >>> path = _download_sequences_batched(large_accession_list, BASE_URL, 'out.fasta', 200)
    """
    
    # Initialize failed_commands tracking if not already done
    if failed_commands is not None and 'sequence_batches' not in failed_commands:
        failed_commands['sequence_batches'] = []
    
    # Split accessions into batches
    batches = [accessions[i:i + batch_size] for i in range(0, len(accessions), batch_size)]
    logger.info("Downloading %d accessions in %d batches of size %d", 
               len(accessions), len(batches), batch_size)
    
    total_downloaded = 0
    batch_failed_count = 0
    
    # Open file once and write batches incrementally to avoid storing all data in memory
    try:
        with open(fasta_path, 'w', encoding='utf-8') as f:
            for batch_num, batch_accessions in tqdm(enumerate(batches, 1), total=len(batches), desc="Downloading batches", unit="batch"):
                
                # Build accession string for this batch
                accession_string = ",".join(batch_accessions)
                
                def download_batch():
                    """Callable for retry helper function"""
                    params = {
                        'db': 'nucleotide',
                        'id': accession_string,
                        'rettype': 'fasta',
                        'retmode': 'text'
                    }
                    if api_key:
                        params['api_key'] = api_key
                    response = requests.get(NCBI_EUTILS_BASE_EFETCH, params=params, timeout=EUTILS_TIMEOUT)
                    response.raise_for_status()
                    
                    # Verify we got FASTA data
                    if not response.text.strip().startswith('>'):
                        raise RuntimeError(f"Invalid FASTA response: {response.text[:100]}")
                    
                    return response.text
                
                # Use exponential backoff helper for batch retries
                success, batch_response_text, error_info = _retry_with_exponential_backoff(
                    operation_name=f"Batch {batch_num}/{len(batches)} ({len(batch_accessions)} accessions)",
                    operation_func=download_batch,
                    max_retries=API_MAX_RETRIES,
                    initial_delay=API_INITIAL_RETRY_DELAY,
                    backoff_multiplier=API_RETRY_BACKOFF_MULTIPLIER,
                    retryable_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.HTTPError, requests.exceptions.Timeout),
                    failed_commands=failed_commands,
                )
                
                if success:
                    # Count sequences in this batch
                    batch_sequence_count = batch_response_text.count('>')
                    total_downloaded += batch_sequence_count
                    
                    # Write sequences immediately to file (incremental write)
                    f.write(batch_response_text)
                    if not batch_response_text.endswith('\n'):
                        f.write('\n')  # Ensure proper line endings between batches
                    f.flush()  # Force write to disk immediately
                    
                    # Update progress bar description with current stats
                    batch_size_mb = len(batch_response_text.encode('utf-8')) / BYTES_PER_MB
                    logger.debug(f"✓ Batch {batch_num}: Downloaded {batch_sequence_count} sequences ({batch_size_mb:.2f} MB)")
                    
                else:
                    # Batch failed after retries
                    error_msg = error_info['error']
                    batch_failed_count += 1
                    
                    # Check for URL length error
                    if "414" in error_msg and batch_size > EUTILS_MIN_BATCH_SIZE_FOR_SPLIT:
                        tqdm.write(f"⚠️ WARNING: Batch {batch_num} URL too long (size={batch_size}). Retrying with smaller batch...")
                        # Recursively retry this batch with smaller size by splitting it further
                        temp_batch_path = f"temp_batch_{batch_num}.fasta"
                        try:
                            _download_sequences_batched(
                                batch_accessions, NCBI_EUTILS_BASE_EFETCH, temp_batch_path, batch_size // 2, failed_commands, api_key=api_key
                            )
                            # Read the temporary file and append to main file
                            with open(temp_batch_path, 'r', encoding='utf-8') as temp_f:
                                batch_content = temp_f.read()
                                f.write(batch_content)
                                if not batch_content.endswith('\n'):
                                    f.write('\n')
                                f.flush()
                                # Count sequences in this recovered batch
                                recovered_count = batch_content.count('>')
                                total_downloaded += recovered_count
                                batch_failed_count -= 1  # This batch succeeded after retry
                                tqdm.write(f"✓ Recovered batch {batch_num} with smaller size: {recovered_count} sequences")
                            os.remove(temp_batch_path)  # Clean up temp file
                        except Exception as file_error:
                            tqdm.write(f"❌ Failed to recover batch {batch_num}: {file_error}")
                            # Track the failed batch
                            _track_failed_operation(
                                failed_commands,
                                'sequence_batches',
                                {
                                    'batch_num': batch_num,
                                    'accession_count': len(batch_accessions),
                                    'accessions': batch_accessions,
                                    'retry_url': f"{NCBI_EUTILS_BASE_EFETCH}?db=nucleotide&id={accession_string}&rettype=fasta&retmode=text",
                                },
                                error_info
                            )
                            continue
                    else:
                        # Track the failed batch for later reporting
                        tqdm.write(f"❌ Batch {batch_num} failed after {API_MAX_RETRIES} retries: {error_msg}")
                        _track_failed_operation(
                            failed_commands,
                            'sequence_batches',
                            {
                                'batch_num': batch_num,
                                'accession_count': len(batch_accessions),
                                'accessions': batch_accessions,
                                'retry_url': f"{NCBI_EUTILS_BASE_EFETCH}?db=nucleotide&id={accession_string}&rettype=fasta&retmode=text",
                            },
                            error_info
                        )
                        continue
                
                # Add small delay between requests to be respectful to NCBI servers
                if batch_num < len(batches):  # Don't delay after the last batch
                    time.sleep(EUTILS_INTER_BATCH_DELAY)
        
        # Check if we downloaded anything
        if total_downloaded == 0:
            raise RuntimeError("❌ All batches failed. No sequences were downloaded.")
        
        if batch_failed_count > 0:
            logger.warning(f"⚠️ WARNING: {batch_failed_count} out of {len(batches)} batches failed. Successfully downloaded {total_downloaded} sequences.")
            tqdm.write(f"⚠️ WARNING: {batch_failed_count} out of {len(batches)} batches failed. Successfully downloaded {total_downloaded} sequences.")
        
        file_size = os.path.getsize(fasta_path)
        logger.info("Successfully saved %d sequences to: %s (%.2f MB)", 
                   total_downloaded, fasta_path, file_size / BYTES_PER_MB)
        return fasta_path
        
    except IOError as e:
        logger.error("❌ Failed to write FASTA file: %s", e)
        raise RuntimeError(f"❌ Failed to save downloaded sequences: {e}") from e


def _unzip_file(zip_file_path, extract_to_path):
    """
    Extract a ZIP file to a specified directory.
    
    Args:
        zip_file_path (str): Path to the ZIP file.
        extract_to_path (str): Target directory for extraction.
    """
    os.makedirs(extract_to_path, exist_ok=True)
    logger.debug("Created extraction directory: %s", extract_to_path)
    
    try:
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(extract_to_path)
            file_list = zip_ref.namelist()
            logger.info("Extracted %d files from %s", len(file_list), zip_file_path)
            
    except zipfile.BadZipFile as e:
        raise zipfile.BadZipFile(f"Invalid or corrupted ZIP file: {zip_file_path}") from e
    except PermissionError as e:
        raise PermissionError(f"Permission denied when extracting to: {extract_to_path}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(f"ZIP file not found: {zip_file_path}") from e


def _parse_date(date_str, filtername=""):
    """
    Parse various date formats into a datetime object.
    
    Args:
        date_str (str): Date string to parse (various formats accepted).
        filtername (str): Name of the filter/field for error reporting.
        
    Returns:
        datetime: Parsed datetime object, or None if parsing fails.
        
    Raises:
        ValueError: If date parsing fails
        
    Note:
        Uses a default date of year 1500 for incomplete date strings to ensure
        proper comparison behavior with minimum date filters.
    """
    try:
        # Use dateutil parser for flexible date parsing
        # Default to a very early year for partial dates to handle edge cases properly
        parsed_date = parser.parse(date_str, default=datetime(DATE_PARSE_DEFAULT_YEAR, 1, 1))
        logger.debug("Successfully parsed date '%s' as %s", date_str, parsed_date)
        return parsed_date
        
    except (ValueError, TypeError) as exc:
        error_msg = (
            f"Invalid date detected for argument {filtername}: '{date_str}'.\n"
            "Note: Please check for errors such as incorrect day values "
            "(e.g., June 31st does not exist) or typos in the date format "
            "(should be YYYY-MM-DD)."
        )
        logger.error("❌ Date parsing failed: %s", error_msg)
        raise ValueError(error_msg) from exc
        # if not verbose:
        #     if not date_str or not date_str.strip():
        #         logger.debug("Empty or missing date for filter '%s'", filtername)
        #     else:
        #         logger.warning("⚠️ Failed to parse date '%s' for filter '%s': %s", date_str, filtername, exc)
        #     return None


def _parse_partial_date_for_range_check(date_str, for_min_comparison=True, filtername=""):
    """
    Parse partial dates with range-aware handling for comparison.
    
    When comparing partial dates (year-only or year-month) against specific dates,
    we need to handle them based on the comparison direction:
    
    - For min_collection_date comparisons: use the END of the partial range
      (e.g., "2015" -> 2015-12-31, "2015-06" -> 2015-06-30, "2021/2022" -> 2022-12-31)
      This ensures records from that year/month are included if they COULD be >= min.
      
    - For max_collection_date comparisons: use the START of the partial range
      (e.g., "2015" -> 2015-01-01, "2015-06" -> 2015-06-01, "2021/2022" -> 2021-01-01)
      This ensures records from that year/month are included if they COULD be <= max.
    
    Args:
        date_str (str): Date string to parse (various formats).
        for_min_comparison (bool): True if comparing against min date, False for max date.
        filtername (str): Name of the filter for error messages.
        
    Returns:
        datetime: Parsed datetime object with partial dates adjusted appropriately.
        
    Raises:
        ValueError: If date parsing fails.
    """    
    if not date_str or not date_str.strip():
        raise ValueError(f"Empty date string for {filtername}")
    
    date_str = date_str.strip()
    
    # Detect date precision based on format
    # Year-only: "2015" (4 digits)
    # Year-range: "2021/2022" or "2021-2022" (two 4-digit years)
    # Year-month: "2015-06", "2015/06", "Jun 2015", etc.
    # Full date: "2015-06-15", "2015/06/15", "Jun 15, 2015", etc.
    
    year_only_pattern = r'^(\d{4})$'
    year_month_pattern = r'^(\d{4})[-/](\d{1,2})$'
    year_range_pattern = r'^(\d{4})[-/](\d{4})$'
    # NCBI API returns date ranges as "[2021 TO 2022]" or "[2021-06 TO 2022-03]"
    bracket_range_pattern = r'^\[(.+?)\s+TO\s+(.+?)\]$'
    
    year_match = re.match(year_only_pattern, date_str)
    year_month_match = re.match(year_month_pattern, date_str)
    year_range_match = re.match(year_range_pattern, date_str)
    bracket_range_match = re.match(bracket_range_pattern, date_str, re.IGNORECASE)
    
    try:
        if bracket_range_match:
            # Bracket range from NCBI API like "[2021 TO 2022]" or "[2021-06 TO 2022-03]"
            range_start_str = bracket_range_match.group(1).strip()
            range_end_str = bracket_range_match.group(2).strip()
            if for_min_comparison:
                # For min comparison, use the END of the range
                end_result = _parse_partial_date_for_range_check(
                    range_end_str, for_min_comparison=True, filtername=filtername
                )
                logger.debug("Parsed bracket-range date '%s' as %s (end of range for min comparison)",
                           date_str, end_result)
                return end_result
            else:
                # For max comparison, use the START of the range
                start_result = _parse_partial_date_for_range_check(
                    range_start_str, for_min_comparison=False, filtername=filtername
                )
                logger.debug("Parsed bracket-range date '%s' as %s (start of range for max comparison)",
                           date_str, start_result)
                return start_result

        elif year_range_match:
            # Year range like "2021/2022" — collection spans multiple years
            year_start = int(year_range_match.group(1))
            year_end = int(year_range_match.group(2))
            if for_min_comparison:
                # For min comparison, use end of the range (Dec 31 of end year)
                result = datetime(year_end, 12, 31)
                logger.debug("Parsed year-range date '%s' as %s (end of range for min comparison)", 
                           date_str, result)
            else:
                # For max comparison, use start of the range (Jan 1 of start year)
                result = datetime(year_start, 1, 1)
                logger.debug("Parsed year-range date '%s' as %s (start of range for max comparison)", 
                           date_str, result)
            return result

        elif year_match:
            # Year-only date like "2015"
            year = int(year_match.group(1))
            if for_min_comparison:
                # For min comparison, use end of year (Dec 31)
                result = datetime(year, 12, 31)
                logger.debug("Parsed year-only date '%s' as %s (end of year for min comparison)", 
                           date_str, result)
            else:
                # For max comparison, use start of year (Jan 1)
                result = datetime(year, 1, 1)
                logger.debug("Parsed year-only date '%s' as %s (start of year for max comparison)", 
                           date_str, result)
            return result
            
        elif year_month_match:
            # Year-month date like "2015-06"
            year = int(year_month_match.group(1))
            month = int(year_month_match.group(2))
            if for_min_comparison:
                # For min comparison, use end of month
                _, last_day = calendar.monthrange(year, month)
                result = datetime(year, month, last_day)
                logger.debug("Parsed year-month date '%s' as %s (end of month for min comparison)", 
                           date_str, result)
            else:
                # For max comparison, use start of month
                result = datetime(year, month, 1)
                logger.debug("Parsed year-month date '%s' as %s (start of month for max comparison)", 
                           date_str, result)
            return result
        else:
            # Full date - use standard parsing
            return _parse_date(date_str, filtername=filtername)
            
    except (ValueError, TypeError) as exc:
        error_msg = (
            f"Invalid date detected for argument {filtername}: '{date_str}'.\n"
            "Note: Please check for errors such as incorrect day values "
            "(e.g., June 31st does not exist) or typos in the date format."
        )
        logger.error("❌ Date parsing failed: %s", error_msg)
        raise ValueError(error_msg) from exc


def _write_fasta_record(handle, record):
    """
    Write a single FASTA record to an open file handle.
    
    Args:
        handle: Open file handle for writing.
        record: FastaRecord object with id, description, and seq attributes.
    """
    if hasattr(record, 'description') and record.description:
        handle.write(f">{record.id} {record.description}\n")
    else:
        handle.write(f">{record.id}\n")
    seq_str = str(record.seq)
    for i in range(0, len(seq_str), 70):
        handle.write(seq_str[i:i+70] + '\n')


def _stream_copy_fasta(input_path, output_path, accession_set=None):
    """
    Stream-copy FASTA records from input to output, optionally filtering by accession set.
    
    This avoids loading all sequences into RAM — only one record at a time is in memory.
    For large datasets (millions of sequences), this is critical to avoid out-of-memory errors.
    
    Args:
        input_path (str): Path to input FASTA file.
        output_path (str): Path to output FASTA file.
        accession_set (set, optional): If provided, only copy records whose ID is in this set.
        
    Returns:
        int: Number of records written.
    """
    count = 0
    skipped = 0
    with open(output_path, 'w', encoding='utf-8') as out_handle:
        for record in FastaIO.parse(input_path, "fasta"):
            if accession_set is not None and record.id not in accession_set:
                skipped += 1
                continue
            _write_fasta_record(out_handle, record)
            count += 1
            if count % FASTA_STREAM_LOG_INTERVAL == 0:
                logger.debug("Streamed %d FASTA records so far...", count)
    
    if accession_set is not None:
        logger.info("Stream-copied %d FASTA records (%d skipped by accession filter)", count, skipped)
    else:
        logger.info("Stream-copied %d FASTA records", count)
    return count


def _load_metadata_dict_from_temp_jsonl(temp_file_path):
    """
    Stream metadata records from a temporary JSONL file and build metadata_dict directly.
    
    This function reads the JSONL file line-by-line, converting each raw API report to the internal metadata format. This avoids loading the entire raw API response list into memory at once.
    
    The conversion logic mirrors load_metadata_from_api_reports() but processes
    records one at a time from disk.
    
    Args:
        temp_file_path (str): Path to the temporary JSONL file containing raw API reports.
        
    Returns:
        dict: Dictionary mapping accession numbers to metadata dictionaries.
              Same format as load_metadata_from_api_reports().
    """
    metadata_dict = {}
    processed_count = 0
    skipped_count = 0
    
    if not temp_file_path or not os.path.exists(temp_file_path):
        logger.warning("Temporary metadata file not found: %s", temp_file_path)
        return metadata_dict
    
    file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
    logger.info("Loading metadata from temp file: %s (%.2f MB)", temp_file_path, file_size_mb)
    
    with open(temp_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                report = json.loads(line)
            except json.JSONDecodeError:
                skipped_count += 1
                logger.debug("Skipping malformed JSON at line %d", line_num)
                continue
            
            # Extract the accession number
            accession = report.get("accession")
            
            if accession:
                processed_count += 1
                
                # Transform API report format to internal format (same as load_metadata_from_api_reports)
                metadata = {
                    "accession": accession,
                    "length": report.get("length"),
                    "geneCount": report.get("gene_count"),
                    "completeness": (report.get("completeness") or "").lower(),
                    "host": report.get("host", {}),
                    "hostName": report.get("host", {}).get("organism_name", ""),
                    "hostTaxId": report.get("host", {}).get("tax_id", None),
                    "isLabHost": report.get("is_lab_host", False),
                    "labHost": report.get("is_lab_host", False),
                    "location": report.get("location", {}).get("geographic_location", None),
                    "region": report.get("location", {}).get("geographic_region", None),
                    "submitter": report.get("submitters", [{}])[0] if report.get("submitters") else {},
                    "sourceDatabase": report.get("source_database", ""),
                    "isolateName": report.get("isolate", {}).get("name", ""),
                    "isolate": {
                        'collectionDate': report.get("isolate", {}).get("collection_date", ""),
                        'source': report.get("isolate", {}).get("source", ""),
                    },
                    "virusTaxId": report.get("virus", {}).get("tax_id", None),
                    "virusName": report.get("virus", {}).get("organism_name", ""),
                    "isAnnotated": report.get("is_annotated", False),
                    "releaseDate": report.get("release_date", ""),
                    "proteinCount": report.get("protein_count"),
                    "maturePeptideCount": report.get("mature_peptide_count"),
                    "segment": report.get("segment"),
                    "isVaccineStrain": report.get("is_vaccine_strain", False),
                    "virusPangolinClassification": report.get("virus", {}).get("pangolin_classification", {}),
                    "submitterName": report.get("submitter", {}).get("names", ""),
                    "submitterCountry": report.get("submitter", {}).get("country", ""),
                    "submitterInstitution": report.get("submitter", {}).get("affiliation", ""),
                }
                
                metadata_dict[accession] = metadata
            else:
                skipped_count += 1
            
            # Log progress for large files
            if processed_count > 0 and processed_count % 500000 == 0:
                logger.info("  ... processed %d records from temp file", processed_count)
    
    logger.info("Loaded %d metadata records from temp file (skipped %d)", 
                processed_count, skipped_count)
    
    return metadata_dict


def _load_cached_metadata_from_jsonl(jsonl_path):
    """
    Load cached metadata from a JSONL file where records are already in internal format.
    
    Unlike _load_metadata_dict_from_temp_jsonl (which transforms raw API format), this function loads records that are already transformed (from process_cached_download). Each line is a JSON object with 'accession' key and all metadata fields directly.
    
    Args:
        jsonl_path (str): Path to the cached metadata JSONL file.
        
    Returns:
        dict: Dictionary mapping accession numbers to metadata dictionaries.
    """
    metadata_dict = {}
    processed_count = 0
    
    if not jsonl_path or not os.path.exists(jsonl_path):
        logger.warning("Cached metadata JSONL file not found: %s", jsonl_path)
        return metadata_dict
    
    file_size_mb = os.path.getsize(jsonl_path) / (1024 * 1024)
    logger.info("Loading cached metadata from JSONL: %s (%.2f MB)", jsonl_path, file_size_mb)
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                metadata = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            accession = metadata.get("accession")
            if accession:
                metadata_dict[accession] = metadata
                processed_count += 1
                
                if processed_count % 500000 == 0:
                    logger.info("  ... loaded %d cached metadata records", processed_count)
    
    logger.info("Loaded %d cached metadata records from JSONL", processed_count)
    return metadata_dict


def _stream_filter_cached_metadata_from_jsonl(
    jsonl_path,
    host=None,
    complete_only=None,
    annotated=None,
    lineage=None,
    geographic_location=None,
    refseq_only=None,
    min_release_date=None,
    applied_strategy_filters=None,
):
    """
    Stream cached metadata from a JSONL file, applying filters on-the-fly.
    
    This is the memory-efficient equivalent of loading ALL records into a dict
    and then calling filter_cached_metadata_for_unused_filters(). Only records
    that pass ALL filters are kept in memory.
    
    Args:
        jsonl_path (str): Path to the cached metadata JSONL file.
        host (str, optional): Host organism filter.
        complete_only (bool, optional): Complete genome filter.
        annotated (bool, optional): Annotation filter.
        lineage (str, optional): Lineage filter.
        geographic_location (str, optional): Geographic location filter.
        refseq_only (bool, optional): RefSeq only filter.
        min_release_date (str, optional): Minimum release date filter.
        applied_strategy_filters (list, optional): Filters already applied server-side.
        
    Returns:
        tuple: (metadata_dict, total_records, filter_stats)
            - metadata_dict: dict mapping accession to metadata (only passing records)
            - total_records: total number of records scanned
            - filter_stats: dict with counts of records filtered by each category
    """
    if applied_strategy_filters is None:
        applied_strategy_filters = []
    
    # Determine which filters to actually apply
    filters_active = {}
    if 'host' not in applied_strategy_filters and host:
        filters_active['host'] = host
    if 'complete-only' not in applied_strategy_filters and complete_only:
        filters_active['complete_only'] = True
    if 'annotated' not in applied_strategy_filters and annotated:
        filters_active['annotated'] = True
    if 'lineage' not in applied_strategy_filters and lineage:
        filters_active['lineage'] = lineage
    if geographic_location:
        filters_active['geographic_location'] = geographic_location
    if refseq_only:
        filters_active['refseq_only'] = True
    if min_release_date:
        filters_active['min_release_date'] = min_release_date
    
    # Parse min_release_date once
    min_release_date_parsed = None
    if 'min_release_date' in filters_active:
        min_release_date_parsed = _parse_date(min_release_date, filtername="min_release_date")
    
    metadata_dict = {}
    total_records = 0
    filter_stats = {
        'host': 0,
        'complete_only': 0,
        'annotated': 0,
        'lineage': 0,
        'geographic_location': 0,
        'refseq_only': 0,
        'min_release_date': 0,
    }
    
    if not jsonl_path or not os.path.exists(jsonl_path):
        logger.warning("Cached metadata JSONL not found for streaming filter: %s", jsonl_path)
        return metadata_dict, 0, filter_stats
    
    file_size_mb = os.path.getsize(jsonl_path) / (1024 * 1024)
    logger.info("Stream-filtering cached metadata from JSONL: %s (%.2f MB)", jsonl_path, file_size_mb)
    if filters_active:
        logger.info("Active filters: %s", list(filters_active.keys()))
    else:
        logger.info("No filters to apply — loading all records")
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                metadata = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            accession = metadata.get("accession")
            if not accession:
                continue
            
            total_records += 1
            
            # Apply filters — skip record if any filter fails
            skip = False
            
            # Host filter
            if not skip and 'host' in filters_active:
                host_name = metadata.get('hostName', '')
                if not host_name or host.lower() not in host_name.lower():
                    filter_stats['host'] += 1
                    skip = True
            
            # Complete-only filter
            if not skip and 'complete_only' in filters_active:
                completeness = metadata.get('completeness', '')
                if not completeness or completeness.lower() != 'complete':
                    filter_stats['complete_only'] += 1
                    skip = True
            
            # Annotated filter
            if not skip and 'annotated' in filters_active:
                is_annotated = metadata.get('isAnnotated', False)
                if not is_annotated:
                    filter_stats['annotated'] += 1
                    skip = True
            
            # Lineage filter
            if not skip and 'lineage' in filters_active:
                virus_pangolin = metadata.get('virusPangolinClassification', '')
                if not virus_pangolin or lineage.lower() not in str(virus_pangolin).lower():
                    filter_stats['lineage'] += 1
                    skip = True
            
            # Geographic location filter
            if not skip and 'geographic_location' in filters_active:
                geo_loc = metadata.get('location', '') or ''
                geo_region = metadata.get('region', '') or ''
                virus_name = metadata.get('virusName', '') or ''
                geo_filter = geographic_location.lower()
                loc_matches = geo_loc and geo_filter in geo_loc.lower()
                region_matches = geo_region and geo_filter in geo_region.lower()
                virus_name_matches = virus_name and geo_filter in virus_name.lower()
                if not loc_matches and not region_matches and not virus_name_matches:
                    filter_stats['geographic_location'] += 1
                    skip = True
            
            # RefSeq only filter
            if not skip and 'refseq_only' in filters_active:
                is_refseq = metadata.get('sourceDatabase', '').lower() == 'refseq'
                if not is_refseq:
                    filter_stats['refseq_only'] += 1
                    skip = True
            
            # Minimum release date filter
            if not skip and 'min_release_date' in filters_active and min_release_date_parsed:
                release_date_str = metadata.get('releaseDate', '')
                if not release_date_str:
                    filter_stats['min_release_date'] += 1
                    skip = True
                else:
                    try:
                        release_date = _parse_date(release_date_str, filtername="releaseDate")
                        if release_date and release_date < min_release_date_parsed:
                            filter_stats['min_release_date'] += 1
                            skip = True
                    except (ValueError, TypeError):
                        filter_stats['min_release_date'] += 1
                        skip = True
            
            if not skip:
                metadata_dict[accession] = metadata
            
            # Log progress every 1M records
            if total_records % 1000000 == 0:
                logger.info("  ... scanned %d records, %d passing filters so far", 
                           total_records, len(metadata_dict))
    
    logger.info("Stream-filter complete: scanned %d records, %d passed all filters",
               total_records, len(metadata_dict))
    if any(v > 0 for v in filter_stats.values()):
        logger.info("Filter statistics: %s", 
                   {k: v for k, v in filter_stats.items() if v > 0})
    
    return metadata_dict, total_records, filter_stats


def load_metadata_from_api_reports(api_reports):
    """
    Load metadata from API response reports into a dictionary.
    
    This function transforms the raw API response format into a standardized
    internal metadata format that can be used by the filtering functions.
    It maps API field names to the expected internal field names and handles
    missing or null values appropriately.
    
    Args:
        api_reports (list): List of virus metadata reports from the NCBI API.
        
    Returns:
        dict: Dictionary mapping accession numbers to metadata dictionaries
              Key: accession number (str)
              Value: metadata dictionary with standardized field names
    """
    metadata_dict = {}
    processed_count = 0
    skipped_count = 0
    
    logger.debug("Processing %d API reports into metadata dictionary", len(api_reports))
    
    for report in api_reports:
        # Extract the accession number - this serves as our unique identifier
        accession = report.get("accession")
        
        if accession:
            processed_count += 1
            
            # Transform API report format to match expected internal metadata format
            # Map API fields to expected internal field names with appropriate defaults
            metadata = {
                "accession": accession,
                "length": report.get("length"),  # Sequence length in nucleotides
                # "source": "NCBI_REST_API",
                "geneCount": report.get("gene_count"),  # Number of genes annotated
                "completeness": (report.get("completeness") or "").lower(), # Completeness status (e.g., complete, partial)
                "host": report.get("host", {}),  # Host organism details
                "hostName": report.get("host", {}).get("organism_name", ""),  # Host organism name
                "hostTaxId": report.get("host", {}).get("tax_id", None),  # Host taxonomy ID
                "isLabHost": report.get("is_lab_host", False),  # Lab-passaged flag (top-level field)
                "labHost": report.get("is_lab_host", False),  # Alternative field name (top-level field)
                "location": report.get("location", {}).get("geographic_location", None),  # Geographic location details
                "region": report.get("location", {}).get("geographic_region", None),  # Broad region
                "submitter": report.get("submitters", [{}])[0] if report.get("submitters") else {},
                "sourceDatabase": report.get("source_database", ""),  # GenBank, RefSeq, etc.
                # "isolate_info": report.get("isolate", {}),  # Sample/isolate details
                "isolateName": report.get("isolate", {}).get("name", ""),  # Isolate name
                "isolate": {
                    # 'name': report.get("isolate", {}).get("name", ""),
                    'collectionDate': report.get("isolate", {}).get("collection_date", ""),
                    'source': report.get("isolate", {}).get("source", ""),
                },
                "virusTaxId": report.get("virus", {}).get("tax_id", None),  # Virus taxonomy and classification
                "virusName": report.get("virus", {}).get("organism_name", ""),  # Virus name
                "isAnnotated": report.get("is_annotated", False),  # Whether sequence is annotated
                "releaseDate": report.get("release_date", ""),  # When sequence was released
                # "sraAccessions": report.get("sra_accessions", []),  # SRA read data accessions 
                # "bioprojects": report.get("bioprojects", []),  # Associated BioProject IDs 
                # "biosample": report.get("biosample"),  # BioSample ID 
                "proteinCount": report.get("protein_count"),  # Number of proteins
                "maturePeptideCount": report.get("mature_peptide_count"),  # Number of mature peptides
                "segment": report.get("segment"),  # Virus segment identifier (e.g., 'HA', 'NA', 'PB1')
                "isVaccineStrain": report.get("is_vaccine_strain", False),  # Whether this is a vaccine strain
                "virusPangolinClassification" : report.get("virus", {}).get("pangolin_classification", {}),  # Pangolin lineage classification
                "submitterName" : report.get("submitter", {}).get("names", ""),  # Submitter names
                "submitterCountry" : report.get("submitter", {}).get("country", ""),  # Submitter country
                "submitterInstitution" : report.get("submitter", {}).get("affiliation", "")  # Submitter institution
            }
            
            # Store the metadata using accession as the key
            metadata_dict[accession] = metadata
            # logger.debug("Processed metadata for accession: %s (length: %s, host: %s)", 
            #             accession, 
            #             metadata.get("length"), 
            #             metadata.get("host", {}).get("organism_name", "Unknown"))
            
        else:
            # Skip reports without accession numbers
            skipped_count += 1
            logger.warning("Skipping API report without accession number: %s", report)
    
    logger.info("Processed %d metadata records, skipped %d records without accessions", 
                processed_count, skipped_count)
    
    return metadata_dict




def _check_protein_requirements(record, metadata, has_proteins, proteins_complete):
    """
    Check if a sequence meets protein/gene requirements based on FASTA header.
    
    This function validates whether a virus sequence contains required proteins
    or genes by checking the FASTA header. For segmented viruses (like influenza),
    this checks segment/protein labels in the sequence description.
    
    The function extracts the protein/segment portion of the header by:
    1. Splitting the description on the isolate name (if available in metadata)
    2. Splitting by semicolons to get individual protein/segment parts
    3. Using regex to match protein names (case-insensitive, handles quotes/parentheses)
    
    Args:
        record: FastaRecord object containing the sequence and description
        metadata (dict): Metadata dictionary for this accession
        has_proteins (str/list/None): Required protein(s)/gene(s) to check for
                                      Can be a single string or list of strings
        proteins_complete (bool): Whether proteins must be marked as "complete" in header
        
    Returns:
        bool: True if protein requirements are met, False otherwise
        
    Example:
        >>> # Check for HA segment
        >>> _check_protein_requirements(record, metadata, "HA", False)
        True
        >>> # Check for multiple segments, requiring complete
        >>> _check_protein_requirements(record, metadata, ["HA", "NA"], True)
        True  # Only if both HA and NA are present AND marked "complete"
    """
    
    # If no protein filter specified and proteins_complete is False, pass through
    if has_proteins is None and not proteins_complete:
        return True
    
    # If only proteins_complete is True but no specific proteins required,
    # we can't check completion status without knowing which proteins to look for
    if has_proteins is None and proteins_complete:
        # Fall back to checking if sequence has any protein annotations in metadata
        protein_count = metadata.get("proteinCount", 0)
        gene_count = metadata.get("geneCount", 0)
        if protein_count is None or protein_count == 0:
            if gene_count is None or gene_count == 0:
                logger.debug("Sequence %s has no protein/gene annotations", record.id)
                return False
        return True
    
    # Convert single string to list for uniform processing
    if isinstance(has_proteins, str):
        has_proteins = [has_proteins]
    
    try:
        # Extract the protein/segment portion of the header
        # If isolate name exists in metadata, split on it to get just the protein info
        isolate_name = metadata.get("isolate", {}).get("name")
        if isolate_name:
            prot_header = record.description.split(isolate_name)[-1]
        else:
            # If sample name was not added to metadata,
            # whole header will be searched for protein/segment names
            prot_header = record.description
        
        # Split header into parts by semicolon for checking individual annotations
        prot_parts = prot_header.split(";")
        
        # Check that ALL required proteins are present
        for protein in has_proteins:
            # Dynamically create regex for each protein with case insensitivity
            # Handles optional quotes, parentheses around protein names
            regex = rf"(?i)\b['\",]?\(?{re.escape(protein)}\)?['\",]?\b"
            
            if proteins_complete:
                # Only keeping sequences for which proteins are marked as "complete"
                if not any(
                    re.search(regex, part) and "complete" in part.lower()
                    for part in prot_parts
                ):
                    logger.debug("Sequence %s: protein '%s' not found or not complete",
                               record.id, protein)
                    return False
            else:
                # Just check if protein name appears anywhere in header parts
                if not any(re.search(regex, part) for part in prot_parts):
                    logger.debug("Sequence %s: required protein '%s' not found in header",
                               record.id, protein)
                    return False
        
        logger.debug("Sequence %s passed protein requirements: %s (complete=%s)",
                   record.id, has_proteins, proteins_complete)
        return True
        
    except Exception as e:
        logger.warning(
            f"The 'has_proteins' filter could not be applied to sequence {record.id} "
            f"due to the following error:\n{e}"
        )
        # On error, exclude the sequence (conservative approach)
        return False


def _extract_protein_info_from_header(description, metadata=None):
    """
    Extract protein/segment information from FASTA header.
    
    This function extracts the protein/segment portion of the FASTA description
    by splitting on the isolate name (if available in metadata). This is particularly
    important for segmented viruses like influenza.
    
    The extraction logic matches the original Laura_OG implementation:
    1. If isolate name exists in metadata, split description on it and take the last part
    2. Otherwise, use the entire description as the protein/segment info
    
    Args:
        description (str): FASTA header/description line
        metadata (dict, optional): Metadata dictionary that may contain isolate name
        
    Returns:
        str: Extracted protein/segment information, or pd.NA if extraction fails
        
    Example:
        >>> _extract_protein_info_from_header(
        ...     "NC_001234 A/California/07/2009 HA; complete cds",
        ...     {"isolate": {"name": "A/California/07/2009"}}
        ... )
        " HA; complete cds"
    """
    
    if not description:
        return pd.NA
    
    try:
        # If isolate name exists in metadata, split on it to get just the protein info
        if metadata is not None:
            isolate_name = metadata.get("isolate", {}).get("name")
            if isolate_name:
                prot_header = description.split(isolate_name)[-1]
                return prot_header
        
        # If sample name was not added to metadata,
        # whole header will be added as protein/segment description
        return description
        
    except Exception:
        return pd.NA


def filter_sequences(
    fna_file,
    metadata_dict,
    max_ambiguous_chars=None,
    # has_proteins=None,
    proteins_complete=False,
    output_fasta_path=None,
):
    """
    Apply sequence-dependent filters to downloaded sequences.
    
    Applies filters requiring actual sequence data (ambiguous character counting,
    protein/feature analysis). Metadata-only filters should be applied by
    filter_metadata_only before downloading sequences.
    
    When output_fasta_path is provided, filtered sequences are streamed directly
    to the output file instead of accumulating in memory. This is critical for
    large datasets (millions of sequences) that would otherwise exhaust system RAM.
    
    Args:
        fna_file (str): Path to FASTA file containing sequences.
        metadata_dict (dict): Dictionary mapping accession numbers to metadata.
        max_ambiguous_chars (int, optional): Maximum ambiguous nucleotides allowed.
        has_proteins (str/list, optional): Required proteins/genes filter.
        proteins_complete (bool): Whether proteins must be complete.
        output_fasta_path (str, optional): Path to write filtered sequences directly.
            When provided, sequences are streamed to disk instead of held in memory.
        
    Returns:
        tuple: (filtered_count, filtered_metadata, protein_headers)
            - filtered_count (int): Number of sequences that passed all filters.
            - filtered_metadata (list): Metadata dicts for sequences passing filters.
            - protein_headers (list): Protein/segment info from FASTA headers.
    """
    logger.info("Applying sequence-dependent filters...")
    logger.debug("Sequence filters: max_ambiguous=%s, complete=%s, streaming=%s",
                max_ambiguous_chars, proteins_complete, output_fasta_path is not None)
    
    # Initialize lists to store filtered results (metadata is small, kept in memory)
    filtered_metadata = []     # Will store corresponding metadata dictionaries
    protein_headers = []       # Will store protein/segment information from FASTA headers
    filtered_count = 0         # Count of sequences passing all filters
    
    # Counters for logging filter statistics
    total_sequences = 0
    filter_stats = {
        'seq_length': 0,
        'ambiguous_chars': 0,
        'proteins': 0
    }

    # Read and process sequences from the FASTA file
    # When output_fasta_path is set, write passing records directly to disk
    logger.info("Reading sequences from FASTA file: %s", fna_file)
    output_handle = None
    try:
        if output_fasta_path:
            output_handle = open(output_fasta_path, 'w', encoding='utf-8')
            logger.info("Streaming filtered sequences directly to: %s", output_fasta_path)
        
        for record in FastaIO.parse(fna_file, "fasta"):
            total_sequences += 1
            record_passes = True
            
            # Normalize accession by taking only the first part (before space)
            record_accession = record.id.split()[0] if hasattr(record, 'id') else str(record)
                
            # Count ambiguous characters (N's)
            if max_ambiguous_chars is not None:
                ambiguous_count = record.seq.upper().count('N')
                if ambiguous_count > max_ambiguous_chars:
                    filter_stats['ambiguous_chars'] += 1
                    record_passes = False
                    continue
            
            # Get metadata for this record to check protein information
            record_metadata = metadata_dict.get(record_accession, {})
            
            if proteins_complete:
                protein_count = record_metadata.get("proteinCount", 0)
                gene_count = record_metadata.get("geneCount", 0)
                if protein_count is None or protein_count == 0:
                    if gene_count is None or gene_count == 0:
                        logger.debug("Sequence %s has no protein/gene annotations", record.id)
                        record_passes = False
                        filter_stats['proteins'] += 1
                        continue
            
            # If sequence passed all filters, keep it and its metadata
            if record_passes:
                filtered_count += 1
                filtered_metadata.append(record_metadata)
                
                # Write directly to output file if streaming (memory-efficient)
                if output_handle:
                    _write_fasta_record(output_handle, record)
                
                if filtered_count % FASTA_STREAM_LOG_INTERVAL == 0:
                    logger.debug("Processed %d sequences, %d passed filters so far...",
                                total_sequences, filtered_count)
    finally:
        if output_handle:
            output_handle.close()

    # Log filtering results
    logger.info("Sequence filter results:")
    logger.info("- Total sequences processed: %d", total_sequences)
    logger.info("- Filtered out because of sequence length: %d", filter_stats['seq_length'])
    logger.info("- Filtered out because of number of ambiguous characters: %d", filter_stats['ambiguous_chars'])
    logger.info("- Filtered out because of protein requirements: %d", filter_stats['proteins'])
    logger.info("- Sequences passing all filters: %d", filtered_count)
    
    return filtered_count, filtered_metadata, protein_headers, filter_stats


def save_command_summary(
    outfolder,
    command_line,
    total_api_records,
    total_after_metadata_filter,
    total_final_sequences,
    output_files,
    filtered_metadata,
    datasets_version,
    success=True,
    error_message=None,
    failed_commands=None,
    genbank_error=None,
    gget_version=None,
    baseline_file=None,
    baseline_accession_count=None,
    baseline_skipped_count=None,
    partial_metadata_file=None,
    recovery_command=None,
    runtime_seconds=None,
    memory_info=None,
    metadata_filter_stats=None,
    genbank_filter_stats=None,
    sequence_filter_stats=None,
    total_after_genbank_filter=None,
    total_after_sequence_filter=None,
):
    """
    Save a summary file documenting the command execution and results.
    
    Creates a comprehensive summary including command line, statistics,
    output files, and any errors encountered.
    """
    
    # Get versions if not provided
    if gget_version is None:
        gget_version = _get_gget_version()
    
    summary_file = os.path.join(outfolder, "command_summary.txt")
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("GGET VIRUS COMMAND SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            # Timestamp
            f.write(f"Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Output Folder: {outfolder}\n\n")
            
            # Version information
            f.write("-" * 80 + "\n")
            f.write("SOFTWARE VERSIONS\n")
            f.write("-" * 80 + "\n")
            f.write(f"gget version: {gget_version}\n")
            if datasets_version is not None:
                f.write(f"{datasets_version}\n")
            f.write("\n")
            
            # Command line
            f.write("-" * 80 + "\n")
            f.write("COMMAND LINE\n")
            f.write("-" * 80 + "\n")
            f.write(f"{command_line}\n\n")
            
            # Execution status
            f.write("-" * 80 + "\n")
            f.write("EXECUTION STATUS\n")
            f.write("-" * 80 + "\n")
            if success:
                if genbank_error:
                    f.write("Command completed with warnings\n")
                    f.write(f"⚠️ GenBank metadata retrieval failed: {genbank_error}\n\n")
                else:
                    f.write("✅ Command completed successfully\n\n")
            else:
                f.write("✗ Command failed\n")
                if error_message:
                    f.write(f"Error: {error_message}\n\n")
            
            # Runtime
            if runtime_seconds is not None:
                f.write("-" * 80 + "\n")
                f.write("RUNTIME\n")
                f.write("-" * 80 + "\n")
                hours, remainder = divmod(int(runtime_seconds), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    f.write(f"Total wall-clock time: {hours}h {minutes}m {seconds}s ({runtime_seconds:.1f} seconds)\n\n")
                elif minutes > 0:
                    f.write(f"Total wall-clock time: {minutes}m {seconds}s ({runtime_seconds:.1f} seconds)\n\n")
                else:
                    f.write(f"Total wall-clock time: {runtime_seconds:.1f} seconds\n\n")
            
            # Memory usage
            if memory_info:
                f.write("-" * 80 + "\n")
                f.write("MEMORY USAGE\n")
                f.write("-" * 80 + "\n")
                if memory_info.get('rss_mb') is not None:
                    f.write(f"Process RSS (resident memory): {memory_info['rss_mb']:.1f} MB\n")
                if memory_info.get('vms_mb') is not None:
                    f.write(f"Process VMS (virtual memory): {memory_info['vms_mb']:.1f} MB\n")
                if memory_info.get('percent') is not None:
                    f.write(f"Process memory percent: {memory_info['percent']:.1f}%\n")
                if memory_info.get('total_mb') is not None:
                    f.write(f"System total memory: {memory_info['total_mb']:.0f} MB\n")
                if memory_info.get('available_mb') is not None:
                    f.write(f"System available memory: {memory_info['available_mb']:.0f} MB\n")
                if memory_info.get('system_percent') is not None:
                    f.write(f"System memory used: {memory_info['system_percent']:.1f}%\n")
                f.write("\n")
            
            # Statistics
            f.write("-" * 80 + "\n")
            f.write("SEQUENCE STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total records from API: {total_api_records}\n")
            if baseline_file:
                f.write(f"Baseline file: {baseline_file}\n")
                if baseline_accession_count is not None:
                    f.write(f"Baseline accessions: {baseline_accession_count}\n")
                if baseline_skipped_count is not None:
                    f.write(f"Skipped (already in baseline): {baseline_skipped_count}\n")
                f.write(f"New accessions processed: {total_after_metadata_filter}\n")
            f.write(f"After metadata filtering: {total_after_metadata_filter}\n")
            if total_after_genbank_filter is not None:
                f.write(f"After GenBank metadata filtering: {total_after_genbank_filter}\n")
            if total_after_sequence_filter is not None:
                f.write(f"After sequence filtering: {total_after_sequence_filter}\n")
            f.write(f"Final sequences (after all filters): {total_final_sequences}\n\n")
            
            # Filter breakdown by stage
            any_filter_stats = (metadata_filter_stats or genbank_filter_stats or sequence_filter_stats)
            if any_filter_stats:
                f.write("-" * 80 + "\n")
                f.write("FILTER BREAKDOWN BY STAGE\n")
                f.write("-" * 80 + "\n")
                
                if metadata_filter_stats:
                    active_meta = {k: v for k, v in metadata_filter_stats.items() if v > 0}
                    if active_meta:
                        f.write("\nMetadata filtering (records excluded):\n")
                        for filter_name, count in sorted(active_meta.items(), key=lambda x: -x[1]):
                            f.write(f"  {filter_name}: {count}\n")
                    else:
                        f.write("\nMetadata filtering: no records excluded\n")
                
                if genbank_filter_stats:
                    active_gb = {k: v for k, v in genbank_filter_stats.items() if v > 0}
                    if active_gb:
                        f.write("\nGenBank metadata filtering (records excluded):\n")
                        for filter_name, count in sorted(active_gb.items(), key=lambda x: -x[1]):
                            f.write(f"  {filter_name}: {count}\n")
                    else:
                        f.write("\nGenBank metadata filtering: no records excluded\n")
                
                if sequence_filter_stats:
                    active_seq = {k: v for k, v in sequence_filter_stats.items() if v > 0}
                    if active_seq:
                        f.write("\nSequence filtering (records excluded):\n")
                        for filter_name, count in sorted(active_seq.items(), key=lambda x: -x[1]):
                            f.write(f"  {filter_name}: {count}\n")
                    else:
                        f.write("\nSequence filtering: no records excluded\n")
                
                f.write("\n")
            
            # Partial metadata recovery information
            if partial_metadata_file:
                f.write("-" * 80 + "\n")
                f.write("💾 PARTIAL METADATA RECOVERY\n")
                f.write("-" * 80 + "\n")
                f.write(f"Partial metadata saved: {partial_metadata_file}\n")
                if recovery_command:
                    f.write(f"\nRecovery command:\n")
                    f.write(f"  {recovery_command}\n")
                f.write("\n")
            
            # Detailed statistics from metadata
            if filtered_metadata and len(filtered_metadata) > 0:
                f.write("-" * 80 + "\n")
                f.write("DETAILED STATISTICS\n")
                f.write("-" * 80 + "\n")
                
                # Unique hosts
                hosts = set()
                for meta in filtered_metadata:
                    host_name = meta.get('host', {}).get('organism_name') if isinstance(meta.get('host'), dict) else None
                    if host_name:
                        hosts.add(host_name)
                f.write(f"Unique hosts: {len(hosts)}\n")
                if hosts and len(hosts) <= 20:
                    for host in sorted(hosts):
                        f.write(f"  - {host}\n")
                elif hosts:
                    f.write(f"  (Top 20 of {len(hosts)} hosts)\n")
                    for host in sorted(hosts)[:20]:
                        f.write(f"  - {host}\n")
                f.write("\n")
                
                # Unique geographic locations
                locations = set()
                for meta in filtered_metadata:
                    location = meta.get('location')
                    if location:
                        locations.add(location)
                f.write(f"Unique geographic locations: {len(locations)}\n")
                if locations and len(locations) <= 20:
                    for loc in sorted(locations):
                        f.write(f"  - {loc}\n")
                elif locations:
                    f.write(f"  (Top 20 of {len(locations)} locations)\n")
                    for loc in sorted(locations)[:20]:
                        f.write(f"  - {loc}\n")
                f.write("\n")
                
                # Sequence length statistics
                lengths = [meta.get('length') for meta in filtered_metadata if meta.get('length')]
                if lengths:
                    f.write(f"Sequence length range: {min(lengths)} - {max(lengths)} bp\n")
                    f.write(f"Average sequence length: {sum(lengths) / len(lengths):.0f} bp\n\n")
                
                # Completeness breakdown
                completeness_counts = {}
                for meta in filtered_metadata:
                    comp = meta.get('completeness', 'unknown')
                    completeness_counts[comp] = completeness_counts.get(comp, 0) + 1
                f.write("Completeness breakdown:\n")
                for comp, count in sorted(completeness_counts.items()):
                    f.write(f"  - {comp}: {count}\n")
                f.write("\n")
                
                # Source database breakdown
                source_counts = {}
                for meta in filtered_metadata:
                    source = meta.get('sourceDatabase', 'unknown')
                    source_counts[source] = source_counts.get(source, 0) + 1
                f.write("Source database breakdown:\n")
                for source, count in sorted(source_counts.items()):
                    f.write(f"  - {source}: {count}\n")
                f.write("\n")
                
                # Submitter countries
                countries = set()
                for meta in filtered_metadata:
                    country = meta.get('submitterCountry')
                    if country:
                        countries.add(country)
                f.write(f"Unique submitter countries: {len(countries)}\n")
                if countries and len(countries) <= 20:
                    for country in sorted(countries):
                        f.write(f"  - {country}\n")
                elif countries:
                    f.write(f"  (Top 20 of {len(countries)} countries)\n")
                    for country in sorted(countries)[:20]:
                        f.write(f"  - {country}\n")
                f.write("\n")
            
            # Output files
            f.write("-" * 80 + "\n")
            f.write("OUTPUT FILES\n")
            f.write("-" * 80 + "\n")
            if output_files:
                for file_type, file_path in output_files.items():
                    if file_path and os.path.exists(file_path):
                        file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                        f.write(f"{file_type}: {os.path.basename(file_path)} ({file_size:.2f} MB)\n")
                    elif file_path:
                        f.write(f"{file_type}: {os.path.basename(file_path)} (not created)\n")
            else:
                f.write("No output files generated\n")
            f.write("\n")
            
            # Failed operations - if any occurred
            if failed_commands:
                has_failures = False
                
                # Check for API timeouts
                if failed_commands.get('api_timeout'):
                    if not has_failures:
                        f.write("-" * 80 + "\n")
                        f.write("⚠️ FAILED OPERATIONS - MANUAL RETRY REQUIRED\n")
                        f.write("-" * 80 + "\n")
                    has_failures = True
                    timeout_info = failed_commands['api_timeout']
                    f.write(f"\n📍 API TIMEOUT:\n")
                    f.write(f"   Error: {timeout_info.get('error', 'Unknown')}\n")
                    f.write(f"   URL: {timeout_info.get('url', 'Unknown')}\n")
                    f.write(f"   Recommendation: Try again later or use different filters\n\n")
                
                # Check for empty API response
                if failed_commands.get('empty_response'):
                    if not has_failures:
                        f.write("-" * 80 + "\n")
                        f.write("⚠️ FAILED OPERATIONS - MANUAL RETRY REQUIRED\n")
                        f.write("-" * 80 + "\n")
                    has_failures = True
                    empty_resp_info = failed_commands['empty_response']
                    f.write(f"\n📍 EMPTY API RESPONSE:\n")
                    f.write(f"   Error: {empty_resp_info.get('error', 'Unknown')}\n")
                    f.write(f"   Recommendation: Check your virus identifier or try different filter parameters\n\n")
                
                # Check for failed API batches
                if failed_commands.get('api_batches'):
                    if not has_failures:
                        f.write("-" * 80 + "\n")
                        f.write("⚠️ FAILED OPERATIONS - MANUAL RETRY REQUIRED\n")
                        f.write("-" * 80 + "\n")
                    has_failures = True
                    f.write(f"\n📍 FAILED METADATA BATCHES ({len(failed_commands['api_batches'])} batches):\n")
                    for batch_info in failed_commands['api_batches'][:5]:  # Show first 5
                        f.write(f"\n   Batch {batch_info.get('batch_num', '?')}: {batch_info.get('accession_count', '?')} accessions\n")
                        f.write(f"   Error: {batch_info.get('error', 'Unknown')}\n")
                        f.write(f"   API URL: {batch_info.get('api_url', 'Unknown')}\n")
                    if len(failed_commands['api_batches']) > 5:
                        f.write(f"\n   ... and {len(failed_commands['api_batches']) - 5} more failed batches\n")
                    f.write("\n")
                
                # Check for pagination errors/timeouts
                if failed_commands.get('pagination_timeouts') or failed_commands.get('pagination_errors'):
                    has_failures = True
                    if not (failed_commands.get('api_batches') or failed_commands.get('api_timeout')):
                        f.write("-" * 80 + "\n")
                        f.write("⚠️ FAILED OPERATIONS - PARTIAL RESULTS OBTAINED\n")
                        f.write("-" * 80 + "\n")
                    
                    if failed_commands.get('pagination_timeouts'):
                        f.write(f"\n📍 PAGINATION TIMEOUTS ({len(failed_commands['pagination_timeouts'])} pages):\n")
                        for page_info in failed_commands['pagination_timeouts'][:3]:
                            f.write(f"   Page {page_info.get('page', '?')}: {page_info.get('records_retrieved', 0)} records retrieved\n")
                            f.write(f"   Error: {page_info.get('error', 'Unknown')}\n")
                    
                    if failed_commands.get('pagination_errors'):
                        f.write(f"\n📍 PAGINATION ERRORS ({len(failed_commands['pagination_errors'])} pages):\n")
                        for page_info in failed_commands['pagination_errors'][:3]:
                            f.write(f"   Page {page_info.get('page', '?')}: {page_info.get('error_type', 'Unknown')} error\n")
                            f.write(f"   Error: {page_info.get('error', 'Unknown')}\n")
                
                # Check for sequence download failures
                if failed_commands.get('sequence_batches'):
                    has_failures = True
                    if not (failed_commands.get('api_batches') or failed_commands.get('api_timeout') or 
                           failed_commands.get('pagination_timeouts') or failed_commands.get('pagination_errors')):
                        f.write("-" * 80 + "\n")
                        f.write("⚠️ FAILED OPERATIONS - MANUAL RETRY AVAILABLE\n")
                        f.write("-" * 80 + "\n")
                    
                    f.write(f"\n📍 FAILED SEQUENCE DOWNLOAD BATCHES ({len(failed_commands['sequence_batches'])} batches):\n")
                    for batch_info in failed_commands['sequence_batches'][:5]:
                        f.write(f"\n   Batch {batch_info.get('batch_num', '?')}\n")
                        f.write(f"   Error: {batch_info.get('error', 'Unknown')}\n")
                        f.write(f"   Retry URL: {batch_info.get('retry_url', 'Unknown')}\n")
                    if len(failed_commands['sequence_batches']) > 5:
                        f.write(f"\n   ... and {len(failed_commands['sequence_batches']) - 5} more failed batches\n")
                
                # Check for single sequence fetch failures
                if failed_commands.get('sequence_fetch'):
                    has_failures = True
                    f.write(f"\n📍 SEQUENCE FETCH FAILURES ({len(failed_commands['sequence_fetch'])} operations):\n")
                    for fetch_info in failed_commands['sequence_fetch'][:3]:
                        f.write(f"\n   Operation: {fetch_info.get('operation', 'Unknown')}\n")
                        f.write(f"   Accessions: {fetch_info.get('accession_count', '?')}\n")
                        f.write(f"   Error: {fetch_info.get('error', 'Unknown')}\n")
                        f.write(f"   Retry URL: {fetch_info.get('retry_url', 'Unknown')}\n")
                    if len(failed_commands['sequence_fetch']) > 3:
                        f.write(f"\n   ... and {len(failed_commands['sequence_fetch']) - 3} more failures\n")
                
                if has_failures:
                    f.write("\n💡 RECOVERY INSTRUCTIONS:\n")
                    f.write("   1. Copy the URL from above and paste it into your browser\n")
                    f.write("   2. Save the downloaded file manually\n")
                    f.write("   3. Retry the command with updated filters (e.g., stricter date ranges)\n")
                    f.write("   4. If the issue persists, NCBI servers may be temporarily unavailable\n")
                    if partial_metadata_file:
                        f.write(f"\n   5. RESUME with baseline deduplication:\n")
                        f.write(f"      {recovery_command}\n")
                    f.write("\n")
            
            # Footer
            f.write("=" * 80 + "\n")
            f.write("END OF SUMMARY\n")
            f.write("=" * 80 + "\n")

        logger.info("=" * 60)
        logger.info("✅ Command summary saved: %s", summary_file)
        return summary_file
        
    except Exception as e:
        logger.error("Failed to save command summary: %s", e)
        logger.error("Traceback: %s", traceback.format_exc())
        return None


def merge_metadata_csvs(genbank_csv_path, standard_csv_path):
    """
    Merge standard metadata CSV into GenBank metadata CSV.
    
    Where GenBank data is missing, fills in values from the standard metadata CSV.
    Does not overwrite any existing data in the GenBank CSV.
    
    Args:
        genbank_csv_path (str): Path to the GenBank metadata CSV file
        standard_csv_path (str): Path to the standard metadata CSV file
        
    Returns:
        bool: True if merge was successful, False otherwise
    """
    try:
        if not os.path.exists(standard_csv_path):
            logger.debug("Standard metadata CSV not found, skipping merge: %s", standard_csv_path)
            return False
        
        logger.info("Merging standard metadata into GenBank metadata...")
        
        # Read both CSV files - use dtype=str to avoid type conversion issues
        genbank_df = pd.read_csv(genbank_csv_path, dtype=str)
        standard_df = pd.read_csv(standard_csv_path, dtype=str)
        
        logger.debug("GenBank CSV: %d rows × %d columns", len(genbank_df), len(genbank_df.columns))
        logger.debug("Standard CSV: %d rows × %d columns", len(standard_df), len(standard_df.columns))
        
        # Create a mapping from accession to standard metadata for quick lookup
        standard_by_accession = {}
        if 'accession' in standard_df.columns:
            for _, row in standard_df.iterrows():
                acc = row['accession']
                if pd.notna(acc) and str(acc).strip() and str(acc) != 'nan':
                    standard_by_accession[str(acc)] = row
        
        logger.debug("Indexed %d accessions from standard metadata", len(standard_by_accession))
        
        # Fill missing values in genbank_df from standard_df
        rows_updated = 0
        columns_updated = 0
        
        for idx, row in genbank_df.iterrows():
            accession = str(row['accession']).strip() if pd.notna(row['accession']) else None
            
            if accession and accession != 'nan' and accession in standard_by_accession:
                standard_row = standard_by_accession[accession]
                
                # For each column in genbank_df, if the value is NaN/empty, fill from standard
                for col in genbank_df.columns:
                    if col in standard_row.index:
                        genbank_val = str(row[col]).strip() if pd.notna(row[col]) else None
                        standard_val = str(standard_row[col]).strip() if pd.notna(standard_row[col]) else None
                        
                        # Fill if genbank is empty but standard has data
                        if (not genbank_val or genbank_val == 'nan') and standard_val and standard_val != 'nan':
                            genbank_df.at[idx, col] = standard_val
                            columns_updated += 1
                
                if columns_updated > 0:
                    rows_updated += 1
        
        # Save the merged dataframe back to the genbank CSV
        genbank_df.to_csv(genbank_csv_path, index=False, encoding='utf-8')
        
        logger.info("✅ Metadata merge complete: updated %d cells across %d rows", 
                    columns_updated, rows_updated)
        logger.debug("Merged GenBank CSV: %d rows × %d columns", len(genbank_df), len(genbank_df.columns))
        
        return True
        
    except Exception as e:
        logger.warning("❌ Failed to merge metadata CSVs: %s", e)
        logger.debug("Exception details:", exc_info=True)
        return False


def save_metadata_to_csv(filtered_metadata, protein_headers, output_metadata_file):
    """
    Save filtered metadata to a CSV file with a specific column order.
    
    This function creates a comprehensive CSV file containing all relevant metadata
    for the filtered virus sequences. The output format is designed to be compatible
    with downstream analysis tools like Delphy.
    
    Args:
        filtered_metadata (list): List of metadata dictionaries for filtered sequences
        protein_headers (list): List of protein/segment information extracted from headers
        output_metadata_file (str): Path to the output CSV file
        
    Note:
        The column order is specifically designed to match requirements for
        phylogenetic analysis tools and provides a standardized format.
    """

    logger.info("Preparing metadata for CSV output...")
    logger.debug("Processing %d metadata records with %d protein headers", 
                len(filtered_metadata), len(protein_headers))

    # Define the column order for the output CSV
    # This order prioritizes the most commonly used fields and matches
    # the format expected by downstream analysis tools
    columns = [
        "accession",           # Primary identifier (lowercase for Delphy compatibility)
        "Organism Name",       # Virus species/strain name
        "GenBank/RefSeq",      # Source database (GenBank or RefSeq)
        "Submitters",          # Names of sequence submitters
        "Organization",        # Submitting organization/institution
        "Submitter Country",   # Country of submitting organization
        "Release date",        # Date when sequence was released to public databases
        "Isolate",            # Isolate/sample identifier
        "Virus Lineage",      # Taxonomic lineage of the virus
        "Length",             # Sequence length in base pairs
        "Nuc Completeness",   # Completeness status (complete/partial)
        "Proteins/Segments",  # Protein/segment information from FASTA headers
        "Segment",            # Virus segment identifier (e.g., 'HA', 'NA', '4', '6')
        "Is Vaccine Strain",  # Whether this sequence is from a vaccine strain
        "Geographic Region",  # Geographic region where sample was collected
        "Geographic Location",# Specific geographic location
        "Host",               # Host organism name
        "Host Lineage",       # Taxonomic lineage of host organism
        "Lab Host",           # Whether sample was lab-passaged
        "Tissue/Specimen/Source", # Sample source/tissue type
        "Collection Date",    # Date when sample was collected
        "Sample Name",        # Sample identifier
        "Annotated",          # Whether sequence has annotation data
        "SRA Accessions",     # Associated SRA (sequencing) accessions
        "Bioprojects",        # Associated BioProject identifiers
        "Biosample",          # BioSample identifier
        "Protein count",      # Number of proteins annotated
        "Gene count",         # Number of genes annotated
        "Mature Peptide Count", # Number of mature peptides annotated
        # Additional GenBank columns
        "definition",         # GenBank sequence definition
        "strain",             # Strain information
        "isolation_source",   # Source of isolation
        "create_date",        # GenBank creation date
        "update_date",        # GenBank update date
        "assembly_name",      # Assembly name
        "authors",            # Publication authors
        "title",              # Publication title
        "journal",            # Publication journal
        "pubmed_id",          # PubMed ID
        "reference_count",    # Number of references
        "comment",            # Additional comments
    ]

    logger.debug("Using column order: %s", columns)

    # Process metadata in chunks for memory efficiency on large datasets
    total_records = len(filtered_metadata)
    chunk_size = METADATA_CSV_CHUNK_SIZE
    
    logger.info("Processing %d metadata records (chunk_size=%d)...", total_records, chunk_size)
    
    def _build_row(i, metadata):
        """Build a single row dictionary from metadata."""
        return {
            # Primary identifiers
            "accession": metadata.get("accession", pd.NA),
            "Organism Name": metadata.get("virus", {}).get("organism_name", pd.NA),
            
            # Database and submission information
            "GenBank/RefSeq": metadata.get("sourceDatabase", pd.NA),
            "Submitters": ", ".join(metadata.get("submitter", {}).get("names", [])) if metadata.get("submitter", {}).get("names") else pd.NA,
            "Organization": metadata.get("submitter", {}).get("affiliation", pd.NA),
            "Submitter Country": metadata.get("submitter", {}).get("country", pd.NA),
            "Release date": metadata.get("releaseDate", "").split("T")[0] if metadata.get("releaseDate") else pd.NA,
            
            # Sample and isolate information
            "Isolate": metadata.get("isolate", {}).get("name", pd.NA),
            "Sample Name": metadata.get("isolate", {}).get("name", pd.NA),
            
            # Virus classification
            "Virus Lineage": metadata.get("virus", {}).get("lineage", []),
            
            # Sequence characteristics
            "Length": metadata.get("length", pd.NA),
            "Nuc Completeness": metadata.get("completeness", pd.NA),
            "Proteins/Segments": protein_headers[i] if i < len(protein_headers) else pd.NA,
            "Segment": metadata.get("segment", pd.NA), 
            "Is Vaccine Strain": metadata.get("isVaccineStrain", metadata.get("is_vaccine_strain", pd.NA)),
            
            # Geographic information
            "Geographic Region": metadata.get("region", pd.NA),
            "Geographic Location": metadata.get("location", pd.NA),
            
            # Host information
            "Host": metadata.get("host", {}).get("organism_name", pd.NA),
            "Host Lineage": metadata.get("host", {}).get("lineage", []),
            "Lab Host": metadata.get("labHost", pd.NA),
            
            # Sample source information
            "Tissue/Specimen/Source": metadata.get("isolate", {}).get("source", pd.NA),
            "Collection Date": metadata.get("isolate", {}).get("collection_date", pd.NA),
            
            # Annotation and quality information
            "Annotated": metadata.get("isAnnotated", pd.NA),
            
            # Associated database records
            "SRA Accessions": metadata.get("sraAccessions", []),
            "Bioprojects": metadata.get("bioprojects", []),
            "Biosample": metadata.get("biosample", pd.NA),
            
            # Counts
            "Gene count": metadata.get("geneCount"),
            "Protein count": metadata.get("proteinCount"),
            "Mature Peptide Count": metadata.get("maturePeptideCount"),
            
            # GenBank-specific columns (not available from NCBI API metadata)
            "definition": pd.NA,
            "strain": pd.NA,
            "isolation_source": pd.NA,
            "create_date": pd.NA,
            "update_date": pd.NA,
            "assembly_name": pd.NA,
            "authors": pd.NA,
            "title": pd.NA,
            "journal": pd.NA,
            "pubmed_id": pd.NA,
            "reference_count": pd.NA,
            "comment": pd.NA,
        }

    # Write CSV in chunks to avoid building a single massive DataFrame
    try:
        first_chunk = True
        rows_written = 0
        
        for chunk_start in range(0, total_records, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_records)
            chunk_data = []
            
            for i in range(chunk_start, chunk_end):
                chunk_data.append(_build_row(i, filtered_metadata[i]))
            
            df_chunk = pd.DataFrame(chunk_data, columns=columns)
            
            # First chunk writes header, subsequent chunks append without header
            if first_chunk:
                df_chunk.to_csv(output_metadata_file, index=False, mode='w')
                first_chunk = False
            else:
                df_chunk.to_csv(output_metadata_file, index=False, mode='a', header=False)
            
            rows_written += len(df_chunk)
            
            # Free chunk memory
            del chunk_data
            del df_chunk
            
            if total_records > chunk_size:
                logger.debug("CSV progress: %d/%d rows written", rows_written, total_records)
        
        logger.info("Successfully saved metadata CSV to: %s", output_metadata_file)
        logger.debug("CSV file contains %d rows and %d columns", rows_written, len(columns))
    except Exception as e:
        logger.error("❌ Failed to save CSV file: %s", e)
        raise


def check_min_max(min_val, max_val, filtername, date=False):
    """
    Validate that minimum and maximum values are in the correct order.
    
    Args:
        min_val: Minimum value (can be numeric or date string).
        max_val: Maximum value (can be numeric or date string).
        filtername (str): Name of the filter for error reporting.
        date (bool): Whether the values are dates that need parsing.
        
    Raises:
        ValueError: If minimum value is greater than maximum value
        
    Example:
        check_min_max(100, 50, "sequence length")  # Raises ValueError
        check_min_max(100, 200, "sequence length")  # No error
    """
    # Only perform validation if both values are provided
    if min_val is not None and max_val is not None:
        logger.debug("Validating min/max values for %s: min=%s, max=%s", 
                    filtername, min_val, max_val)
        
        if date:
            try:
                min_val = _parse_date(min_val)
                max_val = _parse_date(max_val)
                logger.debug("Parsed date values: min=%s, max=%s", min_val, max_val)
            except Exception as e:
                logger.error("❌ Failed to parse dates for validation: %s", e)
                raise ValueError(f"Invalid date format in {filtername} filters") from e
        
        if min_val > max_val:
            error_msg = f"Min value ({min_val}) cannot be greater than max value ({max_val}) for {filtername}."
            logger.error("❌ Validation failed: %s", error_msg)
            raise ValueError(error_msg)
        
        logger.debug("Min/max validation passed for %s", filtername)


# =============================================================================
# ESEARCH PRE-FILTERING 
# =============================================================================

def _esearch_prefilter_genbank(
    virus_taxid,
    metadata_filtered_accessions,
    provirus=None,
    has_proteins=None,
    genotype=None,
    gen_mol_type=None,
    min_seq_length=None,
    max_seq_length=None,
    api_key=None,
):
    """
    Use NCBI ESearch to pre-filter accessions BEFORE fetching full GenBank XML.
    
    Instead of fetching full GenBank XML for ALL metadata-filtered accessions, we use ESearch to find only the subset that might pass the GenBank-    dependent filters. This typically reduces the set from hundreds of thousands to a few hundred, making the GenBank fetch near-instant.
    
    Strategy: Build an ESearch query that is a SUPERSET of what the exact GenBank XML parsing will select. Use broad matching to avoid false negatives. Then intersect with the metadata-filtered accessions and fetch GenBank XML only for the intersection.
    
    Args:
        virus_taxid (str/int): NCBI taxonomy ID for the virus (e.g. 11676 for HIV-1).
        metadata_filtered_accessions (list): Accessions that passed metadata filters.
        provirus (bool, optional): If True, search for proviral sequences.
        has_proteins (str, optional): Protein name to search for (e.g. "gag polyprotein").
        genotype (str, optional): Genotype/subtype to search for.
        gen_mol_type (str, optional): Molecule type qualifier.
        min_seq_length (int, optional): Minimum sequence length.
        max_seq_length (int, optional): Maximum sequence length.
        api_key (str, optional): NCBI API key for higher rate limits.
        
    Returns:
        set: Set of accession numbers that might pass GenBank filters,
             or None if pre-filtering couldn't be performed (fall back to full fetch).
    """
    # Build ESearch query terms
    query_parts = []
    
    # Always include organism constraint
    if virus_taxid:
        query_parts.append(f"txid{virus_taxid}[Organism]")
    
    # NOTE: We deliberately do NOT use "proviral" as an ESearch term here.
    # ESearch free-text "proviral" only matches sequences that contain the WORD
    # "proviral" in their GenBank text (title, comment, keywords). Many sequences that ARE proviral (especially complete genomes like AF004394.1, U69593.1) do NOT contain this word in their text. The NCBI Virus web interface uses a different mechanism (structured metadata/mol_type qualifier) to identify proviral sequences. 
    # The provirus filter is correctly applied later in filter_genbank_metadata() by checking the actual GenBank XML features/qualifiers.
    
    # Has_proteins filter: search for protein name
    if has_proteins:
        # Use broad "All Fields" matching for protein name to ensure superset
        # The exact filtering will happen later on the GenBank XML
        query_parts.append(f'"{has_proteins}"')
    
    # Genotype filter: search for genotype string
    if genotype:
        query_parts.append(f'"{genotype}"')
    
    # Molecule type filter
    if gen_mol_type:
        query_parts.append(f'"{gen_mol_type}"[Molecule Type]')
    
    # Sequence length filter
    if min_seq_length and max_seq_length:
        query_parts.append(f"{min_seq_length}:{max_seq_length}[SLEN]")
    elif min_seq_length:
        query_parts.append(f"{min_seq_length}:99999999[SLEN]")
    elif max_seq_length:
        query_parts.append(f"1:{max_seq_length}[SLEN]")
    
    # Need at least organism + one GenBank filter for pre-filtering to be useful
    if len(query_parts) < 2:
        logger.info("ESearch pre-filter: not enough filter criteria for useful pre-filtering")
        return None
    
    search_query = " AND ".join(query_parts)
    logger.info("ESearch pre-filter query: %s", search_query)
    
    try:
        # Step 1: ESearch to get count and WebEnv
        params = {
            'db': 'nucleotide',
            'term': search_query,
            'retmax': 0,
            'usehistory': 'y',
        }
        if api_key:
            params['api_key'] = api_key
        
        response = requests.get(NCBI_EUTILS_BASE_ESEARCH, params=params, timeout=60,
                               headers={'User-Agent': 'gget/1.0'})
        response.raise_for_status()
        root = ET.fromstring(response.text)
        
        count_elem = root.find('.//Count')
        web_env_elem = root.find('.//WebEnv')
        query_key_elem = root.find('.//QueryKey')
        
        if count_elem is None or web_env_elem is None:
            logger.warning("ESearch pre-filter: could not parse response")
            return None
        
        total_count = int(count_elem.text)
        web_env = web_env_elem.text
        query_key = query_key_elem.text
        
        logger.info("ESearch pre-filter: found %d accessions matching GenBank criteria", total_count)
        
        # If the pre-filter results are TOO large (>50K), it's not useful
        # Fall back to the full fetch method
        if total_count > 50000:
            logger.info("ESearch pre-filter: %d results is too large for effective pre-filtering (>50K), skipping", total_count)
            return None
        
        if total_count == 0:
            logger.info("ESearch pre-filter: NO accessions match the GenBank criteria")
            return set()
        
        # Step 2: Fetch all matching accessions using EFetch rettype=acc (lightweight!)
        all_esearch_accessions = []
        batch_size = 10000
        
        for retstart in range(0, total_count, batch_size):
            time.sleep(0.35 if not api_key else 0.1)
            
            fetch_params = {
                'db': 'nucleotide',
                'WebEnv': web_env,
                'query_key': query_key,
                'retmax': batch_size,
                'retstart': retstart,
                'rettype': 'acc',
                'retmode': 'text',
            }
            if api_key:
                fetch_params['api_key'] = api_key
            
            resp = requests.get(NCBI_EUTILS_BASE_EFETCH, params=fetch_params, timeout=120,
                               headers={'User-Agent': 'gget/1.0'})
            resp.raise_for_status()
            
            batch_accs = [a.strip() for a in resp.text.strip().split('\n') if a.strip()]
            all_esearch_accessions.extend(batch_accs)
            logger.debug("ESearch pre-filter: fetched %d accessions (retstart=%d)", 
                        len(batch_accs), retstart)
        
        logger.info("ESearch pre-filter: retrieved %d accession numbers total", len(all_esearch_accessions))
        
        # Step 3: Intersect with our metadata-filtered accessions
        esearch_set = set(all_esearch_accessions)
        metadata_set = set(metadata_filtered_accessions)
        intersection = esearch_set & metadata_set
        
        logger.info("ESearch pre-filter RESULTS:")
        logger.info("  ESearch matches: %d", len(esearch_set))
        logger.info("  Metadata-filtered: %d", len(metadata_set))
        logger.info("  Intersection (candidates): %d", len(intersection))
        logger.info("  Reduction: %.1f%% (from %d to %d accessions for GenBank fetch)",
                   (1 - len(intersection) / len(metadata_set)) * 100 if metadata_set else 0,
                   len(metadata_set), len(intersection))
        
        return intersection
        
    except requests.exceptions.RequestException as e:
        logger.warning("ESearch pre-filter failed (network error): %s. Falling back to full fetch.", e)
        return None
    except ET.ParseError as e:
        logger.warning("ESearch pre-filter failed (parse error): %s. Falling back to full fetch.", e)
        return None
    except Exception as e:
        logger.warning("ESearch pre-filter failed (unexpected): %s. Falling back to full fetch.", e)
        return None


# =============================================================================
# EPOST + EFETCH HELPER FUNCTIONS (NCBI-recommended for large datasets)
# =============================================================================

def _epost_accessions(accessions, api_key=None):
    """
    Upload accession numbers to NCBI History Server using EPost.
    
    EPost allows uploading large numbers of UIDs to the server, which assigns
    them a WebEnv and query_key for subsequent EFetch requests. This avoids
    URL length limitations that restrict direct efetch calls to ~200 accessions.
    
    Args:
        accessions (list): List of accession numbers to upload.
        api_key (str, optional): NCBI API key for higher rate limits.
        
    Returns:
        tuple: (web_env, query_key) for use in subsequent EFetch calls,
               or (None, None) if upload failed.
    """
    logger.info("Uploading %d accessions to NCBI History Server via EPost...", len(accessions))
    
    epost_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/epost.fcgi"
    
    # For EPost, we send IDs in the POST body to avoid URL length limits
    # Can handle tens of thousands of accessions in one request
    accession_string = ",".join(accessions)
    
    params = {
        'db': 'nucleotide',
    }
    if api_key:
        params['api_key'] = api_key
    
    # POST body contains the accession list
    data = {
        'id': accession_string
    }
    
    headers = {'User-Agent': 'gget/1.0'}
    
    try:
        # Make POST request with accessions in body
        response = requests.post(
            epost_url,
            params=params,
            data=data,
            headers=headers,
            timeout=EUTILS_TIMEOUT
        )
        response.raise_for_status()
        
        # Parse the XML response to extract WebEnv and query_key
        # Example response:
        # <ePostResult>
        #   <QueryKey>1</QueryKey>
        #   <WebEnv>NCID_01_...</WebEnv>
        # </ePostResult>
        
        root = ET.fromstring(response.text)
        
        query_key_elem = root.find('.//QueryKey')
        web_env_elem = root.find('.//WebEnv')
        
        if query_key_elem is not None and web_env_elem is not None:
            query_key = query_key_elem.text
            web_env = web_env_elem.text
            logger.info("✅ EPost successful: QueryKey=%s, WebEnv=%s...", 
                       query_key, web_env[:30] if len(web_env) > 30 else web_env)
            return web_env, query_key
        else:
            # Check for error message
            error_elem = root.find('.//ERROR')
            if error_elem is not None:
                logger.error("❌ EPost error: %s", error_elem.text)
            else:
                logger.error("❌ EPost failed: Could not parse WebEnv/QueryKey from response")
                logger.debug("Response: %s", response.text[:500])
            return None, None
            
    except requests.exceptions.RequestException as e:
        logger.error("❌ EPost request failed: %s", e)
        return None, None
    except ET.ParseError as e:
        logger.error("❌ Failed to parse EPost response: %s", e)
        return None, None


def _efetch_with_history(web_env, query_key, retstart, retmax, api_key=None, failed_log_path=None):
    """
    Fetch GenBank records using History Server reference (WebEnv/query_key).
    
    This is the NCBI-recommended method for large datasets. After uploading UIDs
    via EPost, use this function to retrieve records in batches using pagination
    (retstart/retmax).
    
    Args:
        web_env (str): WebEnv string from EPost.
        query_key (str): Query key from EPost.
        retstart (int): Starting index for retrieval (0-based).
        retmax (int): Maximum number of records to retrieve in this batch.
        api_key (str, optional): NCBI API key for higher rate limits.
        failed_log_path (str, optional): Path to log failed requests.
        
    Returns:
        tuple: (metadata_dict, xml_text) where metadata_dict maps accessions to
               parsed metadata, and xml_text is the raw XML response.
    """
    
    params = {
        'db': 'nucleotide',
        'WebEnv': web_env,
        'query_key': query_key,
        'retstart': retstart,
        'retmax': retmax,
        'rettype': 'gb',
        'retmode': 'xml',
        'complexity': GENBANK_COMPLEXITY,
    }
    if api_key:
        params['api_key'] = api_key
    
    # Create a requests.Session with retry logic
    session = requests.Session()
    try:
        retry_strategy = Retry(
            total=GENBANK_RETRY_ATTEMPTS,
            backoff_factor=HTTP_INITIAL_BACKOFF,
            status_forcelist=HTTP_RETRY_STATUS_CODES,
            allowed_methods=frozenset(['GET', 'POST'])
        )
    except TypeError:
        # Fallback for older urllib3 versions
        retry_strategy = Retry(
            total=GENBANK_RETRY_ATTEMPTS,
            backoff_factor=HTTP_INITIAL_BACKOFF,
            status_forcelist=HTTP_RETRY_STATUS_CODES,
            method_whitelist=frozenset(['GET', 'POST'])
        )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    headers = {'Connection': 'close', 'User-Agent': 'gget/1.0'}
    
    max_attempts = HTTP_MAX_LOCAL_RETRIES
    attempt = 0
    backoff = HTTP_INITIAL_BACKOFF
    
    while attempt < max_attempts:
        try:
            logger.debug("EFetch with history: retstart=%d, retmax=%d (attempt %d)", 
                        retstart, retmax, attempt + 1)
            
            response = session.get(NCBI_EUTILS_BASE_EFETCH, params=params, timeout=EUTILS_TIMEOUT, headers=headers)
            response.raise_for_status()
            
            # Verify we got XML data
            if not response.text.strip().startswith('<?xml') and not response.text.strip().startswith('<'):
                raise RuntimeError(f"Invalid XML response: {response.text[:200]}")
            
            logger.debug("Received XML response: %d characters", len(response.text))
            
            # Parse the GenBank XML
            metadata_dict = _parse_genbank_xml(response.text)
            
            logger.debug("✅ Parsed metadata for %d records", len(metadata_dict))
            return metadata_dict, response.text
            
        except (requests.exceptions.ChunkedEncodingError,
                urllib3.exceptions.ProtocolError,
                http.client.IncompleteRead,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout) as e:
            attempt += 1
            logger.warning("Transient network error (attempt %d/%d): %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                logger.warning("Max retry attempts reached for retstart=%d", retstart)
                break
        
        except requests.exceptions.RequestException as e:
            logger.error("❌ EFetch request failed: %s", e)
            break
        
        except Exception as e:
            logger.error("❌ EFetch parsing failed: %s", e)
            break
    
    # Log failure
    if failed_log_path:
        try:
            with open(failed_log_path, 'a') as f:
                f.write(f"FAILED_BATCH: retstart={retstart}, retmax={retmax}\n")
                f.write(f"WebEnv: {web_env[:50]}...\n")
                f.write(f"QueryKey: {query_key}\n\n")
        except Exception:
            pass
    
    return {}, ""


def fetch_genbank_metadata(accessions, genbank_full_xml_path, genbank_full_csv_path, batch_size=200, delay=0.5, failed_log_path=None, api_key=None):
    """
    Fetch detailed GenBank metadata for a list of accession numbers using NCBI E-utilities.
    
    Uses the NCBI-recommended EPost + EFetch workflow for large datasets:
    1. EPost: Upload all accessions to History Server (avoids URL length limits)
    2. EFetch: Retrieve data using WebEnv/query_key with pagination (retmax)
    
    This approach allows batch sizes of 500+ per request (vs 200 with direct URL method). Writes XML to disk incrementally instead of accumulating in memory.
    
    Args:
        accessions (list): List of accession numbers to fetch GenBank data for.
        genbank_full_xml_path (str): Path to save the full XML output.
        genbank_full_csv_path (str): Path to save the full CSV output.
        batch_size (int): Maximum accessions per EFetch request (default: 200, can use 500 with EPost method).
        delay (float): Delay in seconds between batch requests (default: 0.5).
        failed_log_path (str, optional): Path to log file for failed batches.
        api_key (str, optional): NCBI API key for higher rate limits (10 req/sec vs 3). Falls back to NCBI_API_KEY env var if not provided.
        
    Returns:
        tuple: (metadata_dict, failed_log_path) where metadata_dict maps accession
               numbers to their GenBank metadata.
    """
    # Use module-level API_KEY (from NCBI_API_KEY env var) if not provided directly
    if api_key is None:
        api_key = API_KEY
        if api_key:
            logger.debug("Using NCBI API key from environment for higher rate limits (10 req/sec)")
    
    if failed_log_path is None:
        failed_log_path = os.path.join(os.path.dirname(genbank_full_xml_path), "genbank_failed_batches.log")
    if os.path.exists(failed_log_path):
        os.remove(failed_log_path)

    if not accessions:
        raise ValueError("No accessions provided for GenBank metadata retrieval")
    
    logger.info("Fetching GenBank metadata for %d accessions using E-utilities (EPost+EFetch method)", len(accessions))
    logger.debug("First 5 accessions: %s", accessions[:5])
    
    # Log initial memory state
    _log_memory_usage("GenBank fetch start")
    
    # Initialize tracking variables
    all_metadata = {}  # Only used for final return; populated from temp JSONL at end
    failed_batches = []
    total_metadata_written = 0  # Counter for metadata records streamed to disk
    
    # Create a temp file to write XML incrementally (saves memory)
    temp_xml_path = genbank_full_xml_path + ".tmp"
    xml_file = None
    xml_written = False
    
    # Create a temp JSONL file to write parsed GenBank metadata incrementally
    temp_metadata_jsonl_path = genbank_full_xml_path + ".metadata.jsonl.tmp"
    metadata_jsonl_file = None
    seen_accessions = set()  # Lightweight set to track which accessions have been fetched
    
    # For large datasets, use the EPost+EFetch workflow which allows larger batch sizes
    # EPost uploads IDs to history server, then EFetch retrieves using WebEnv/query_key
    use_epost_method = len(accessions) > 100  # Use EPost for any significant number
    optimized_batch_size = 500 if use_epost_method else batch_size  # EPost method allows larger batches
    
    # Optimize delay based on API key: 10 req/sec with key vs 3 req/sec without
    # With API key: 0.1s delay allows ~10 req/sec
    # Without API key: 0.35s delay allows ~3 req/sec
    effective_delay = 0.1 if api_key else delay
    logger.info("Using delay of %.2fs between requests (API key: %s)", 
               effective_delay, "yes" if api_key else "no")
    
    try:
        # Open temp file for incremental XML writing
        xml_file = open(temp_xml_path, 'w', encoding='utf-8')
        xml_file.write("<AllGBSets>\n")
        
        # Open temp JSONL file for incremental metadata writing
        metadata_jsonl_file = open(temp_metadata_jsonl_path, 'w', encoding='utf-8')
        
        if use_epost_method:
            # ===== EPost + EFetch with History Server =====
            EPOST_CHUNK_SIZE = 2000  # Tuned to avoid History Server session timeout
            
            if len(accessions) > EPOST_CHUNK_SIZE:
                epost_chunks = [accessions[i:i + EPOST_CHUNK_SIZE] 
                               for i in range(0, len(accessions), EPOST_CHUNK_SIZE)]
            else:
                epost_chunks = [accessions]
            
            logger.info("Using optimized EPost+EFetch workflow (efetch_batch=%d, epost_chunks=%d of up to %d each)",
                        optimized_batch_size, len(epost_chunks), EPOST_CHUNK_SIZE)
            
            # Calculate total EFetch batches across all EPost chunks for progress tracking
            overall_batch_num = 0
            total_batches_all_chunks = sum(
                (len(chunk) + optimized_batch_size - 1) // optimized_batch_size 
                for chunk in epost_chunks
            )
            
            # Determine GC and memory logging frequency based on total batches
            gc_frequency = max(20, total_batches_all_chunks // 20)
            memory_log_frequency = max(50, total_batches_all_chunks // 10)
            
            epost_failures = []  # Track chunks that fail EPost for direct-URL fallback
            
            for chunk_idx, chunk_accessions in enumerate(epost_chunks):
                logger.info("EPost chunk %d/%d: uploading %d accessions to History Server...",
                           chunk_idx + 1, len(epost_chunks), len(chunk_accessions))
                
                # Step 1: Upload this chunk to NCBI History Server via EPost
                web_env, query_key = _epost_accessions(chunk_accessions, api_key=api_key)
                
                if web_env and query_key:
                    logger.info("✅ EPost chunk %d/%d successful: uploaded %d accessions",
                               chunk_idx + 1, len(epost_chunks), len(chunk_accessions))
                    
                    # Step 2: Fetch data for this chunk using WebEnv/query_key with pagination
                    chunk_total = len(chunk_accessions)
                    num_batches = (chunk_total + optimized_batch_size - 1) // optimized_batch_size
                    
                    for batch_num in range(num_batches):
                        overall_batch_num += 1
                        retstart = batch_num * optimized_batch_size
                        logger.info("Processing GenBank batch %d/%d (chunk %d/%d, retstart=%d, retmax=%d)",
                                   overall_batch_num, total_batches_all_chunks,
                                   chunk_idx + 1, len(epost_chunks),
                                   retstart, optimized_batch_size)
                        
                        try:
                            batch_metadata, batch_xml_text = _efetch_with_history(
                                web_env=web_env,
                                query_key=query_key,
                                retstart=retstart,
                                retmax=optimized_batch_size,
                                api_key=api_key,
                                failed_log_path=failed_log_path
                            )
                            
                            if batch_metadata:
                                # Stream parsed metadata to temp JSONL (not held in RAM)
                                for acc, meta in batch_metadata.items():
                                    metadata_jsonl_file.write(json.dumps({"accession": acc, "metadata": meta}) + "\n")
                                    total_metadata_written += 1
                                    seen_accessions.add(acc)
                                metadata_jsonl_file.flush()
                                batch_count = len(batch_metadata)
                                del batch_metadata
                            else:
                                batch_count = 0
                            
                            if batch_xml_text:
                                cleaned_xml = _clean_xml_declarations(batch_xml_text)
                                xml_file.write(cleaned_xml + "\n")
                                xml_file.flush()
                                xml_written = True
                                del batch_xml_text
                                del cleaned_xml
                                logger.info("Batch %d/%d: Successfully retrieved metadata for %d accessions",
                                           overall_batch_num, total_batches_all_chunks,
                                           batch_count)
                            else:
                                logger.warning("Batch %d/%d returned no data", 
                                              overall_batch_num, total_batches_all_chunks)
                                # Track failed accessions for potential retry
                                batch_start = batch_num * optimized_batch_size
                                batch_end = min(batch_start + optimized_batch_size, chunk_total)
                                failed_batches.append(chunk_accessions[batch_start:batch_end])
                            
                            # Periodic garbage collection
                            if overall_batch_num % gc_frequency == 0:
                                _force_garbage_collection(f"after batch {overall_batch_num}/{total_batches_all_chunks}")
                            
                            # Periodic memory logging
                            if overall_batch_num % memory_log_frequency == 0:
                                _log_memory_usage(f"GenBank batch {overall_batch_num}/{total_batches_all_chunks}")
                            
                            # Delay between requests (respect NCBI rate limits)
                            if overall_batch_num < total_batches_all_chunks and effective_delay > 0:
                                time.sleep(effective_delay)
                                
                        except Exception as e:
                            logger.error("⚠️ Batch %d/%d failed: %s", 
                                        overall_batch_num, total_batches_all_chunks, e)
                            batch_start = batch_num * optimized_batch_size
                            batch_end = min(batch_start + optimized_batch_size, chunk_total)
                            failed_batches.append(chunk_accessions[batch_start:batch_end])
                            continue
                    
                    # Brief delay between EPost chunks to be respectful to NCBI
                    if chunk_idx < len(epost_chunks) - 1:
                        time.sleep(1.0)
                        
                else:
                    logger.warning("EPost chunk %d/%d failed, will use direct fetch for %d accessions",
                                  chunk_idx + 1, len(epost_chunks), len(chunk_accessions))
                    epost_failures.extend(chunk_accessions)
            
            # If any EPost chunks failed entirely, fall back to direct URL method for those
            if epost_failures:
                logger.info("Falling back to direct URL method for %d accessions from failed EPost chunks", 
                           len(epost_failures))
                direct_batches = [epost_failures[i:i + batch_size] 
                                 for i in range(0, len(epost_failures), batch_size)]
                for dbatch_num, dbatch_accessions in enumerate(direct_batches, 1):
                    try:
                        batch_metadata, batch_xml_text = _fetch_genbank_batch(
                            dbatch_accessions, failed_log_path=failed_log_path)
                        if batch_metadata:
                            for acc, meta in batch_metadata.items():
                                metadata_jsonl_file.write(json.dumps({"accession": acc, "metadata": meta}) + "\n")
                                total_metadata_written += 1
                                seen_accessions.add(acc)
                            metadata_jsonl_file.flush()
                            del batch_metadata
                        if batch_xml_text:
                            cleaned_xml = _clean_xml_declarations(batch_xml_text)
                            xml_file.write(cleaned_xml + "\n")
                            xml_file.flush()
                            xml_written = True
                            del batch_xml_text
                            del cleaned_xml
                        if dbatch_num < len(direct_batches) and effective_delay > 0:
                            time.sleep(effective_delay)
                    except Exception as e:
                        logger.error("⚠️ Direct fallback batch %d failed: %s", dbatch_num, e)
                        failed_batches.append(dbatch_accessions)
                        continue
            
            # Check if we got ANY data from EPost method
            if total_metadata_written == 0 and not epost_failures:
                logger.warning("EPost method returned no data, falling back to direct fetch method")
                use_epost_method = False  # Fall through to traditional method
        
        if not use_epost_method:
            # ===== FALLBACK METHOD: Traditional direct URL batching =====
            logger.info("Using traditional direct URL method (batch_size=%d)", batch_size)
            
            # Split accessions into batches to avoid URL length limits
            if len(accessions) > batch_size:
                batches = [accessions[i:i + batch_size] for i in range(0, len(accessions), batch_size)]
                logger.info("Processing %d accessions in %d batches of size %d", 
                           len(accessions), len(batches), batch_size)
            else:
                batches = [accessions]
                logger.info("Processing %d accessions in 1 batch", len(accessions))
            
            # Determine GC and memory logging frequency based on total batches
            gc_frequency = max(50, len(batches) // 20)  # GC roughly every 5% of batches
            memory_log_frequency = max(100, len(batches) // 10)  # Log memory every 10%
            
            # Process each batch
            for batch_num, batch_accessions in enumerate(batches, 1):
                logger.info("Processing GenBank batch %d/%d (%d accessions)", 
                           batch_num, len(batches), len(batch_accessions))
                
                try:
                    # Fetch GenBank XML data using E-utilities efetch
                    batch_metadata, batch_xml_text = _fetch_genbank_batch(batch_accessions, failed_log_path=failed_log_path)
                    
                    if batch_metadata:
                        # Stream parsed metadata to temp JSONL (not held in RAM)
                        for acc, meta in batch_metadata.items():
                            metadata_jsonl_file.write(json.dumps({"accession": acc, "metadata": meta}) + "\n")
                            total_metadata_written += 1
                            seen_accessions.add(acc)
                        metadata_jsonl_file.flush()
                        batch_count = len(batch_metadata)
                        del batch_metadata
                    else:
                        batch_count = 0

                    if batch_xml_text:
                        # Clean XML and write directly to file (not accumulating in memory)
                        cleaned_xml = _clean_xml_declarations(batch_xml_text)
                        xml_file.write(cleaned_xml + "\n")
                        xml_file.flush()  # Ensure data is written to disk
                        xml_written = True
                        
                        # Clear batch_xml_text from memory
                        del batch_xml_text
                        del cleaned_xml
                        
                        logger.info("Batch %d: Successfully retrieved metadata for %d accessions", 
                                   batch_num, batch_count)
                    else:
                        # Batch failed, add to failed_batches for retry
                        logger.warning("Batch %d returned no data, will retry later", batch_num)
                        failed_batches.append(batch_accessions)
                    
                    # Periodic garbage collection to prevent memory buildup
                    if batch_num % gc_frequency == 0:
                        _force_garbage_collection(f"after batch {batch_num}/{len(batches)}")
                    
                    # Periodic memory logging
                    if batch_num % memory_log_frequency == 0:
                        _log_memory_usage(f"GenBank batch {batch_num}/{len(batches)}")
                    
                    # Add delay between requests to be respectful to NCBI servers
                    if batch_num < len(batches) and effective_delay > 0:
                        logger.debug("Adding %.1f second delay before next batch", effective_delay)
                        time.sleep(effective_delay)
                    
                except Exception as e:
                    logger.error("⚠️ Batch %d failed: %s", batch_num, e)
                    failed_batches.append(batch_accessions)
                    logger.info("Added batch %d to retry list", batch_num)
                    continue
        
        # Retry failed batches at the end
        if failed_batches:
            logger.info("Retrying %d failed batches", len(failed_batches))
            _log_memory_usage("before retry")
            retry_success = []
            for batch_accessions in failed_batches:
                try:
                    meta, xml = _fetch_genbank_batch(batch_accessions, failed_log_path=failed_log_path)
                    if meta:
                        for acc, m in meta.items():
                            metadata_jsonl_file.write(json.dumps({"accession": acc, "metadata": m}) + "\n")
                            total_metadata_written += 1
                            seen_accessions.add(acc)
                        metadata_jsonl_file.flush()
                        retry_success.append(batch_accessions)
                        del meta
                    if xml:
                        cleaned_xml = _clean_xml_declarations(xml)
                        xml_file.write(cleaned_xml + "\n")
                        xml_file.flush()
                        xml_written = True
                        del xml
                        del cleaned_xml
                        logger.info("Successfully retried batch with %d accessions", len(batch_accessions))
                except Exception as e:
                    logger.warning("Final retry failed for batch: %s", batch_accessions)
            
            if retry_success:
                logger.info("Successfully recovered %d/%d failed batches on retry", len(retry_success), len(failed_batches))

        # ===== DETECT AND RETRY SILENTLY DROPPED ACCESSIONS =====
        # The NCBI history server sometimes silently drops individual accessions from batch responses without raising errors. Detect these and retry them individually with direct URL fetch to maximize completeness.
        # This also catches accessions lost due to EPost/EFetch position mismatch (server internal ordering differs from posting order) after batch retries.
        silently_dropped = set(accessions) - seen_accessions
        if silently_dropped:
            logger.info("🔄 Detected %d accessions silently dropped by NCBI history server — retrying with direct fetch",
                       len(silently_dropped))
            dropped_list = sorted(silently_dropped)
            # Use batch size of 200 for direct URL retry (efficient for large sets, small enough to avoid URL length limits ~8KB for 200 accessions)
            direct_batch_size = min(200, len(dropped_list))
            direct_batches = [dropped_list[i:i + direct_batch_size] 
                             for i in range(0, len(dropped_list), direct_batch_size)]
            recovered_count = 0
            for dbatch_num, dbatch_accessions in enumerate(direct_batches, 1):
                try:
                    meta, xml = _fetch_genbank_batch(dbatch_accessions, failed_log_path=failed_log_path)
                    if meta:
                        for acc, m in meta.items():
                            metadata_jsonl_file.write(json.dumps({"accession": acc, "metadata": m}) + "\n")
                            total_metadata_written += 1
                            seen_accessions.add(acc)
                        metadata_jsonl_file.flush()
                        recovered_count += len(meta)
                        del meta
                    if xml:
                        cleaned_xml = _clean_xml_declarations(xml)
                        xml_file.write(cleaned_xml + "\n")
                        xml_file.flush()
                        xml_written = True
                        del xml
                        del cleaned_xml
                    if dbatch_num < len(direct_batches) and effective_delay > 0:
                        time.sleep(effective_delay)
                except Exception as e:
                    logger.warning("Direct retry failed for dropped accessions %s: %s", 
                                  dbatch_accessions, e)
            if recovered_count:
                logger.info("✅ Recovered %d/%d silently dropped accessions via direct fetch",
                           recovered_count, len(silently_dropped))
            else:
                logger.warning("Could not recover any of the %d silently dropped accessions",
                              len(silently_dropped))

        # Close XML wrapper
        xml_file.write("</AllGBSets>\n")
        xml_file.close()
        xml_file = None
        
        # Close metadata JSONL file
        if metadata_jsonl_file is not None:
            metadata_jsonl_file.close()
            metadata_jsonl_file = None
        
        # Move temp file to final location
        if xml_written:
            shutil.move(temp_xml_path, genbank_full_xml_path)
            logger.debug("Saved full GenBank XML to: %s", genbank_full_xml_path)
            
            # Convert XML to CSV (memory-efficient chunked processing)
            _log_memory_usage("before XML to CSV conversion")
            _genbank_xml_to_csv(genbank_full_xml_path, genbank_full_csv_path)
            _log_memory_usage("after XML to CSV conversion")
        else:
            logger.warning("No GenBank XML content retrieved to save")
            if os.path.exists(temp_xml_path):
                os.remove(temp_xml_path)
                
    except Exception as e:
        logger.error("Error during GenBank metadata fetch: %s", e)
        raise
    finally:
        # Clean up file handles if still open
        if xml_file is not None:
            try:
                xml_file.close()
            except OSError as e:
                logger.debug("Failed to clean up xml_file: %s", e)
        if metadata_jsonl_file is not None:
            try:
                metadata_jsonl_file.close()
            except OSError as e:
                logger.debug("Failed to clean up metadata_jsonl_file: %s", e)
        # Clean up temp XML file if it exists
        if os.path.exists(temp_xml_path):
            try:
                os.remove(temp_xml_path)
            except OSError as e:
                logger.debug("Failed to clean up temp_xml_path (os.remove): %s", e)

    logger.info("GenBank metadata retrieval complete: %d/%d accessions processed", 
                total_metadata_written, len(accessions))
    
    # Load all metadata from temp JSONL file into dict for return
    # This is fine because GenBank metadata is fetched only for the post-filter subset
    # (typically 1K-50K records, not millions)
    all_metadata = {}
    if os.path.exists(temp_metadata_jsonl_path) and total_metadata_written > 0:
        try:
            with open(temp_metadata_jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    acc = record.get("accession")
                    meta = record.get("metadata")
                    if acc and meta:
                        all_metadata[acc] = meta
            logger.info("Loaded %d GenBank metadata records from temp file", len(all_metadata))
        except Exception as e:
            logger.error("Failed to load GenBank metadata from temp JSONL: %s", e)
    
    # Clean up temp JSONL file
    if os.path.exists(temp_metadata_jsonl_path):
        try:
            os.remove(temp_metadata_jsonl_path)
        except OSError as e:
            logger.debug("Failed to clean up temp_metadata_jsonl_path (os.remove): %s", e)
    
    # Final memory log and GC
    _force_garbage_collection("GenBank fetch complete")
    _log_memory_usage("GenBank fetch complete")

    if not all_metadata:
        logger.warning("No GenBank metadata was successfully retrieved")
    
    missing_accessions = set(accessions) - set(all_metadata.keys())
    if missing_accessions:
        logger.info("❌ The following accessions could not be downloaded:")
        for acc in list(missing_accessions)[:10]:  # Only log first 10
            efetch_url = f"{NCBI_EUTILS_BASE_EFETCH}?db=nucleotide&id={acc}&rettype=gb&retmode=xml"
            logger.info(f"  {acc}: {efetch_url}")
        if len(missing_accessions) > 10:
            logger.info(f"  ... and {len(missing_accessions) - 10} more")
        logger.info(f"A log of failed batches and efetch URLs is saved at: {failed_log_path}")
    
    # Return both metadata and the path to the failed batches log for summary tracking
    return all_metadata, failed_log_path if os.path.exists(failed_log_path) else None


def _fetch_genbank_batch(accessions, failed_log_path=None):
    """
    Fetch GenBank metadata for a single batch of accessions.
    
    Includes retry logic with exponential backoff and automatic batch splitting
    for problematic requests.
    
    Args:
        accessions (list): List of accession numbers for this batch.
        failed_log_path (str, optional): Path to log file for failed batches.
        
    Returns:
        tuple: (metadata_dict, xml_text) where metadata_dict maps accessions to
               parsed metadata, and xml_text is the raw XML response.
    """
    
    # Build E-utilities efetch URL for GenBank XML format
    # base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    accession_string = ",".join(accessions)
    
    params = {
        'db': 'nucleotide',           # Nucleotide database (includes virus sequences)
        'id': accession_string,       # Comma-separated accession numbers
        'rettype': 'gb',              # GenBank format
        'retmode': 'xml',             # XML output for structured parsing
        'complexity': GENBANK_COMPLEXITY,              
    }
    
    # Create a requests.Session with urllib3 Retry/HTTPAdapter for robust retries
    session = requests.Session()
    try:
        retry_strategy = Retry(
            total=GENBANK_RETRY_ATTEMPTS,
            backoff_factor=HTTP_INITIAL_BACKOFF,
            status_forcelist=HTTP_RETRY_STATUS_CODES,
            allowed_methods=frozenset(['GET', 'POST'])
        )
    except TypeError:
        # Fallback for older urllib3 versions that use method_whitelist
        retry_strategy = Retry(
            total=GENBANK_RETRY_ATTEMPTS,
            backoff_factor=HTTP_INITIAL_BACKOFF,
            status_forcelist=HTTP_RETRY_STATUS_CODES,
            method_whitelist=frozenset(['GET', 'POST'])
        )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {'Connection': 'close', 'User-Agent': 'gget/1.0'}
    # Local retry loop for transient chunk/connection errors with exponential backoff
    max_attempts = HTTP_MAX_LOCAL_RETRIES
    attempt = 0
    backoff = HTTP_INITIAL_BACKOFF
    efetch_url = None  # Initialize to track the URL for logging

    while attempt < max_attempts:
        try:
            logger.debug("Making E-utilities request for %d accessions (attempt %d)", len(accessions), attempt + 1)
            logger.debug("Request URL: %s", NCBI_EUTILS_BASE_EFETCH)
            logger.debug("Request parameters: %s", {k: (v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v) for k, v in params.items()})

            # Use POST instead of GET for EFetch to avoid 414 URI Too Long errors.
            # NCBI E-utilities supports POST for all requests, and POST puts the
            # accession list in the request body instead of the URL.
            response = session.post(NCBI_EUTILS_BASE_EFETCH, data=params, timeout=EUTILS_TIMEOUT, headers=headers)
            efetch_url = response.url  # Capture the full URL for logging
            logger.debug("POST request sent to: %s", NCBI_EUTILS_BASE_EFETCH)
            response.raise_for_status()

            # Verify we got XML data
            if not response.text.strip().startswith('<?xml') and not response.text.strip().startswith('<'):
                raise RuntimeError(f"Invalid XML response: {response.text[:200]}")

            logger.debug("Received XML response: %d characters", len(response.text))

            # Parse the GenBank XML and extract metadata
            metadata_dict = _parse_genbank_xml(response.text)

            logger.debug("✅ Successfully parsed metadata for %d records", len(metadata_dict))
            return metadata_dict, response.text

        except (requests.exceptions.ChunkedEncodingError,
                urllib3.exceptions.ProtocolError,
                http.client.IncompleteRead,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout) as e:
            attempt += 1
            logger.warning("Transient network error during E-utilities request (attempt %d/%d): %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                logger.debug("Backing off for %.1f seconds before retrying", backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            else:
                logger.warning("Maximum local retry attempts reached for this batch (%d). Will attempt to split batch if possible.", max_attempts)
                break

        except requests.exceptions.RequestException as e:
            # Non-recoverable requests error (HTTP error status etc.)
            logger.error("❌ E-utilities request failed: %s", e)
            if hasattr(e, 'response') and e.response is not None:
                efetch_url = e.response.url
            break  # Exit retry loop

        except Exception as e:
            logger.error("❌ GenBank XML parsing failed: %s", e)
            break  # Exit retry loop

    # If local retries failed, try splitting into smaller sub-batches
    if len(accessions) > 1:
        logger.info("Attempting to split failing batch of %d accessions into smaller sub-batches", len(accessions))
        mid = len(accessions) // 2
        left_acc = accessions[:mid]
        right_acc = accessions[mid:]

        try:
            left_meta, left_xml = _fetch_genbank_batch(left_acc, failed_log_path=failed_log_path)
            right_meta, right_xml = _fetch_genbank_batch(right_acc, failed_log_path=failed_log_path)

            combined_meta = {}
            combined_meta.update(left_meta if left_meta else {})
            combined_meta.update(right_meta if right_meta else {})

            combined_xml = (left_xml or "") + "\n" + (right_xml or "")
            return combined_meta, combined_xml
        except Exception as split_error:
            logger.error("Failed to split batch: %s", split_error)

    # Cannot split further, log failed batch
    if failed_log_path:
        # Build the URL for manual download
        if efetch_url is None:
            # Construct URL if we never got a response
            base_url = f"{NCBI_EUTILS_BASE_EFETCH}?db=nucleotide&id={accession_string}&rettype=gb&retmode=xml"
            efetch_url = base_url
        
        with open(failed_log_path, "a") as flog:
            flog.write(f"FAILED_BATCH: {accessions}\n")
            flog.write(f"URL: {efetch_url}\n")
            flog.write(f"Individual URLs:\n")
            for acc in accessions:
                individual_url = f"{NCBI_EUTILS_BASE_EFETCH}?db=nucleotide&id={acc}&rettype=gb&retmode=xml"
                flog.write(f"  {acc}: {individual_url}\n")
            flog.write("\n")
        logger.error(f"Failed to fetch GenBank metadata for batch: {accessions[:5]}... Logged to {failed_log_path}")
    
    return {}, None


def _clean_xml_declarations(xml_text):
    """
    Remove XML and DOCTYPE declarations from XML text for concatenation.
    
    Args:
        xml_text (str): Raw XML text with declarations.
        
    Returns:
        str: Cleaned XML text without declarations
        
    Example:
        >>> xml = '<?xml version="1.0"?>\n<!DOCTYPE GBSet>\n<GBSet>...</GBSet>'
        >>> _clean_xml_declarations(xml)
        '<GBSet>...</GBSet>'
    """
    cleaned_lines = []
    for line in xml_text.splitlines():
        # Skip XML declarations and DOCTYPE declarations
        if line.strip().startswith("<?xml") or line.strip().startswith("<!DOCTYPE"):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _local_name(tag):
    """
    Return the local name of an XML tag (strip namespace if present).
    
    XML tags may include namespace prefixes (e.g., '{http://namespace}TagName').
    This helper function extracts just the tag name without the namespace.
    
    Args:
        tag (str): XML tag string, potentially with namespace.
        
    Returns:
        str: Tag name without namespace prefix.
        
    Example:
        >>> _local_name('{http://www.ncbi.nlm.nih.gov}GBSeq')
        'GBSeq'
        >>> _local_name('GBSeq')
        'GBSeq'
    """
    return tag.split('}')[-1] if '}' in tag else tag


def _genbank_xml_to_csv(xml_path, csv_path, chunk_size=None):
    """
    Convert GenBank XML to CSV with streaming and dynamic qualifier columns.
    
    Args:
        xml_path (str): Path to input GenBank XML file.
        csv_path (str): Path to output CSV file.
        chunk_size (int, optional): Rows to process before writing to disk.
    """
    # Apply default chunk size if not specified
    if chunk_size is None:
        chunk_size = GENBANK_XML_CHUNK_SIZE
    
    qualifier_names = set()
    rows = []
    header_written = False

    csv_file = open(csv_path, "w", newline='', encoding='utf-8')
    writer = None

    # Stream-parse XML
    for event, elem in ET.iterparse(xml_path, events=("end",)):
        if _local_name(elem.tag) == "GBSeq":
            # # Skip protein sequences (AA type) - we only want nucleotide sequences
            # moltype_elem = elem.findtext(".//GBSeq_moltype", "").strip()
            # if moltype_elem == "AA":
            #     logger.debug("Skipping protein sequence (AA type) in XML to CSV conversion")
            #     elem.clear()
            #     continue
            
            accession = elem.findtext(".//GBSeq_accession-version", "").strip()
            sequence = elem.findtext(".//GBSeq_sequence", "").strip()
            features = elem.findall(".//GBFeature")

            seq_rows = []  # rows for this GBSeq

            for feature in features:
                feature_key = feature.findtext("GBFeature_key", "").strip()
                feature_location = feature.findtext("GBFeature_location", "").strip()
                feature_operator = feature.findtext("GBFeature_operator", "").strip()

                intervals = feature.findall(".//GBInterval")
                quals = feature.findall(".//GBQualifier")

                qualifiers = {}
                for q in quals:
                    name = q.findtext("GBQualifier_name", "").strip()
                    value = q.findtext("GBQualifier_value", "").strip()
                    if name:
                        qualifiers[name] = value
                        qualifier_names.add(name)

                if not intervals:
                    intervals = [None]

                for interval in intervals:
                    interval_from = (interval.findtext("GBInterval_from") if interval is not None else "") or ""
                    interval_to = (interval.findtext("GBInterval_to") if interval is not None else "") or ""
                    interval_acc = (interval.findtext("GBInterval_accession") if interval is not None else "") or ""

                    interval_from = interval_from.strip()
                    interval_to = interval_to.strip()
                    interval_acc = interval_acc.strip()

                    order_flag = feature_operator if feature_operator.startswith("order(") else ""

                    row = {
                        "accession": accession,
                        "Feature_key": feature_key,
                        "Feature_location": feature_location,
                        "Interval_from": interval_from,
                        "Interval_to": interval_to,
                        "Interval_accession": interval_acc,
                        "order": order_flag,
                        "sequence": ""  # leave blank for now
                    }

                    for qn in qualifier_names:
                        row[qn] = qualifiers.get(qn, "")

                    seq_rows.append(row)

            # Add sequence only to the last row for this GBSeq
            if seq_rows:
                seq_rows[-1]["sequence"] = sequence

            rows.extend(seq_rows)

            # Write chunk
            if len(rows) >= chunk_size:
                df = pd.DataFrame(rows)
                if not header_written:
                    df.to_csv(csv_file, index=False)
                    header_written = True
                else:
                    df.to_csv(csv_file, index=False, header=False)
                rows.clear()

            elem.clear()

    # Write remaining rows
    if rows:
        df = pd.DataFrame(rows)
        if not header_written:
            df.to_csv(csv_file, index=False)
        else:
            df.to_csv(csv_file, index=False, header=False)

    csv_file.close()
    logger.debug(f"✅ Finished writing {csv_path}")


def _save_genbank_xml_and_csv(xml_content, xml_file_name, csv_file_name):
    """
    Save GenBank XML content and convert to CSV.
    
    Args:
        xml_content (str): Raw XML content from E-utilities.
        xml_file_name (str): Path for XML output file.
        csv_file_name (str): Path for CSV output file.
    """
    try:
        root = ET.fromstring(xml_content)
        logger.debug("✅ XML parsing successful, root element: %s", root.tag)

        logger.debug("Saving GenBank XML content to file: %s", xml_file_name)
        with open(xml_file_name, "w", encoding="utf-8") as f:
            f.write(xml_content)
        logger.debug("✅ Saved GenBank XML content to: %s", xml_file_name)

        logger.debug("Saving the loss-less genbank information into a CSV if the flag is set.")
        logger.debug("Reformatting to extract important data from GenBank XML to save as CSV: %s", csv_file_name)
        _genbank_xml_to_csv(xml_file_name, csv_file_name)
        logger.debug("✅ Saved GenBank data in a csv file to: %s", csv_file_name)

    except ET.ParseError as e:
        logger.error("❌ XML parsing failed: %s", e)
        logger.debug("XML content preview: %s", xml_content[:500])
        raise RuntimeError(f"Invalid XML format in GenBank response: {e}") from e


def _parse_genbank_xml(xml_content):
    """
    Parse GenBank XML response and extract high-level metadata fields.
    This function processes the GenBank XML format returned by E-utilities efetch
    and extracts key metadata including collection dates, geographic information,
    host details, publication references, and sequence features.
    
    Args:
        xml_content (str): Raw XML content from E-utilities efetch.
        
    Returns:
        dict: Dictionary mapping accession numbers to metadata dictionaries
        
    Note:
        Uses xml.etree.ElementTree for parsing to avoid external dependencies.
        The GenBank XML schema is documented by NCBI and contains structured
        information about sequence records.
    """
    
    # Parse the XML content
    try:
        root = ET.fromstring(xml_content)
        logger.debug("✅ XML parsing successful, root element: %s", root.tag)

    except ET.ParseError as e:
        logger.error("❌ XML parsing failed: %s", e)
        logger.debug("XML content preview: %s", xml_content[:500])
        raise RuntimeError(f"Invalid XML format in GenBank response: {e}") from e
    
    metadata_dict = {}
    
    # Process each GenBank sequence record in the XML
    for gbseq in root.findall('.//GBSeq'):
        try:
            # # Skip protein sequences (AA type) - we only want nucleotide sequences
            # moltype_elem = gbseq.find('GBSeq_moltype')
            # if moltype_elem is not None and moltype_elem.text == 'AA':
            #     logger.debug("Skipping protein sequence (AA type)")
            #     continue
            
            # Extract accession number as the primary key
            accession_elem = gbseq.find('GBSeq_accession-version')
            if accession_elem is None:
                accession_elem = gbseq.find('GBSeq_primary-accession')
            
            if accession_elem is None:
                logger.warning("Skipping GenBank record without accession number")
                continue
                
            accession = accession_elem.text
            logger.debug("Processing GenBank record: %s", accession)
            
            # Initialize metadata dictionary for this record
            metadata = {
                'accession': accession,
                'genbank_data': {}  # Store GenBank-specific fields
            }
            
            # Extract basic sequence information
            length_elem = gbseq.find('GBSeq_length')
            metadata['genbank_data']['sequence_length'] = int(length_elem.text) if length_elem is not None else None
            
            organism_elem = gbseq.find('GBSeq_organism')
            metadata['genbank_data']['organism'] = organism_elem.text if organism_elem is not None else ""
            
            definition_elem = gbseq.find('GBSeq_definition')
            metadata['genbank_data']['definition'] = definition_elem.text if definition_elem is not None else ""
            
            # Extract taxonomy information
            taxonomy_elem = gbseq.find('GBSeq_taxonomy')
            metadata['genbank_data']['taxonomy'] = taxonomy_elem.text if taxonomy_elem is not None else ""
            
            # Extract creation and update dates
            create_date_elem = gbseq.find('GBSeq_create-date')
            metadata['genbank_data']['create_date'] = create_date_elem.text if create_date_elem is not None else ""
            
            update_date_elem = gbseq.find('GBSeq_update-date')
            metadata['genbank_data']['update_date'] = update_date_elem.text if update_date_elem is not None else ""
            
            # Extract references (publications)
            references = []
            for ref in gbseq.findall('.//GBReference'):
                ref_data = {}
                
                title_elem = ref.find('GBReference_title')
                ref_data['title'] = title_elem.text if title_elem is not None else ""
                
                authors_elem = ref.find('GBReference_authors')
                if authors_elem is not None:
                    authors = [a.text for a in authors_elem.findall('GBAuthor') if a.text]
                    ref_data['authors'] = ', '.join(authors)
                else:
                    ref_data['authors'] = ""
                # ref_data['authors'] = authors_elem.text if authors_elem is not None else ""
                
                journal_elem = ref.find('GBReference_journal')
                ref_data['journal'] = journal_elem.text if journal_elem is not None else ""
                
                pubmed_elem = ref.find('GBReference_pubmed')
                ref_data['pubmed_id'] = pubmed_elem.text if pubmed_elem is not None else ""
                
                if any(ref_data.values()):  # Only add if we got some reference data
                    references.append(ref_data)
            
            metadata['genbank_data']['references'] = references
            
            # Extract features (collection_date, geographic location, host, etc.)
            features_data = {}
            gene_count = 0
            mature_peptide_count = 0
            products = []
            
            for feature in gbseq.findall('.//GBFeature'):
                feature_key_elem = feature.find('GBFeature_key')
                if feature_key_elem is None:
                    continue
                    
                feature_key = feature_key_elem.text
                
                # Count genes and mature peptides
                if feature_key == 'gene':
                    gene_count += 1
                elif feature_key == 'mat_peptide':
                    mature_peptide_count += 1
                
                # Extract qualifiers for this feature
                feature_qualifiers = {}
                has_proviral = False
                for qual in feature.findall('.//GBQualifier'):
                    qual_name_elem = qual.find('GBQualifier_name')
                    qual_value_elem = qual.find('GBQualifier_value')
                    
                    if qual_name_elem is not None:
                        qual_name = qual_name_elem.text
                        # Handle qualifiers without values (e.g., proviral)
                        qual_value = qual_value_elem.text if qual_value_elem is not None else ""
                        feature_qualifiers[qual_name] = qual_value
                        
                        # Track proviral flag (presence indicates proviral)
                        if qual_name == 'proviral':
                            has_proviral = True
                        
                        # Collect product names for has_proteins filter
                        if qual_name == 'product' and qual_value:
                            products.append(qual_value)
                
                if has_proviral:
                    feature_qualifiers['_has_proviral'] = True
                
                if feature_qualifiers:
                    # Store multiple features of same type (e.g., multiple CDS)
                    if feature_key not in features_data:
                        features_data[feature_key] = feature_qualifiers
                    elif isinstance(features_data[feature_key], list):
                        features_data[feature_key].append(feature_qualifiers)
                    else:
                        features_data[feature_key] = [features_data[feature_key], feature_qualifiers]
            
            # Extract specific fields of interest from source feature
            source_feature = features_data.get('source', {})
            if isinstance(source_feature, list):
                source_feature = source_feature[0]  # Use first source if multiple
            
            metadata['genbank_data']['collection_date'] = source_feature.get('collection_date', '')
            metadata['genbank_data']['geographic_location'] = source_feature.get('geo_loc_name', '')
            metadata['genbank_data']['host'] = source_feature.get('host', '')
            metadata['genbank_data']['isolation_source'] = source_feature.get('isolation_source', '')
            metadata['genbank_data']['strain'] = source_feature.get('strain', '')
            metadata['genbank_data']['isolate'] = source_feature.get('isolate', '')
            # metadata['genbank_data']['collected_by'] = source_feature.get('collected_by', '')
            # metadata['genbank_data']['specimen_voucher'] = source_feature.get('specimen_voucher', '')
            
            # Extract additional GenBank-specific fields for filtering
            metadata['genbank_data']['proviral'] = source_feature.get('_has_proviral', False) or 'proviral' in source_feature
            metadata['genbank_data']['mol_type'] = source_feature.get('mol_type', '')
            metadata['genbank_data']['serotype'] = source_feature.get('serotype', '')
            metadata['genbank_data']['gene_count'] = gene_count
            metadata['genbank_data']['mature_peptide_count'] = mature_peptide_count
            metadata['genbank_data']['products'] = products
            
            # Extract genotype from note field or serotype
            genotype = ''
            note_value = source_feature.get('note', '')
            if note_value:
                # Look for genotype pattern in note (e.g., "genotype: IV" or "genotype=H5N1")
                genotype_match = re.search(r'genotype[:\s=]+([^\s;,]+)', note_value, re.IGNORECASE)
                if genotype_match:
                    genotype = genotype_match.group(1).strip()
            if not genotype and source_feature.get('serotype'):
                genotype = source_feature.get('serotype', '')
            metadata['genbank_data']['genotype'] = genotype
            
            # Store all features for potential future use
            metadata['genbank_data']['all_features'] = features_data
            
            # Extract comment field (often contains additional metadata)
            comment_elem = gbseq.find('GBSeq_comment')
            comment_text = comment_elem.text if comment_elem is not None else ""
            metadata['genbank_data']['comment'] = comment_text
            
            # Parse assembly name from comment if present (used in some studies)
            assembly_name = ""
            if comment_text:
                assembly_match = re.search(r'Assembly Name :: (\S+)', comment_text)
                if assembly_match:
                    assembly_name = assembly_match.group(1)
            metadata['genbank_data']['assembly_name'] = assembly_name
            
            # Store the metadata for this accession
            metadata_dict[accession] = metadata
            
            logger.debug("Extracted GenBank metadata for %s: organism=%s, collection_date=%s, geographic_location=%s", 
                        accession, 
                        metadata['genbank_data']['organism'],
                        metadata['genbank_data']['collection_date'],
                        metadata['genbank_data']['geographic_location'])
            
        except Exception as e:
            logger.warning("❌ Failed to parse GenBank record %s: %s", 
                          accession if 'accession' in locals() else 'unknown', e)
            continue
    
    logger.info("✅ Successfully parsed GenBank metadata for %d records", len(metadata_dict))
    return metadata_dict


def save_genbank_metadata_to_csv(genbank_metadata, output_file, virus_metadata=None):
    """
    Save GenBank metadata to a CSV file with the same column headers as the standard metadata CSV.
    
    Args:
        genbank_metadata (dict): Dictionary mapping accessions to GenBank metadata
        output_file (str): Path to the output CSV file
        virus_metadata (list, optional): List of virus metadata dictionaries to merge
        
    Note:
        The CSV format uses the same column headers as save_metadata_to_csv to ensure
        consistency between the two output files, making them directly comparable.
    """
    
    logger.info("Preparing GenBank metadata for CSV output...")
    logger.debug("Processing %d GenBank records", len(genbank_metadata))
    
    # Use the same column order as save_metadata_to_csv for consistency
    columns = [
        "accession",           # Primary identifier (lowercase for Delphy compatibility)
        "Organism Name",       # Virus species/strain name
        "GenBank/RefSeq",      # Source database (GenBank or RefSeq)
        "Submitters",          # Names of sequence submitters
        "Organization",        # Submitting organization/institution
        "Submitter Country",   # Country of submitting organization
        "Release date",        # Date when sequence was released to public databases
        "Isolate",            # Isolate/sample identifier
        "Virus Lineage",      # Taxonomic lineage of the virus
        "Length",             # Sequence length in base pairs
        "Nuc Completeness",   # Completeness status (complete/partial)
        "Proteins/Segments",  # Protein/segment information from FASTA headers
        "Segment",            # Virus segment identifier (e.g., 'HA', 'NA', '4', '6')
        "Is Vaccine Strain",  # Whether this sequence is from a vaccine strain
        "Geographic Region",  # Geographic region where sample was collected
        "Geographic Location",# Specific geographic location
        "Host",               # Host organism name
        "Host Lineage",       # Taxonomic lineage of host organism
        "Lab Host",           # Whether sample was lab-passaged
        "Tissue/Specimen/Source", # Sample source/tissue type
        "Collection Date",    # Date when sample was collected
        "Sample Name",        # Sample identifier
        "Annotated",          # Whether sequence has annotation data
        "SRA Accessions",     # Associated SRA (sequencing) accessions
        "Bioprojects",        # Associated BioProject identifiers
        "Biosample",          # BioSample identifier
        "Protein count",      # Number of proteins annotated
        "Gene count",         # Number of genes annotated
        "Mature Peptide Count", # Number of mature peptides annotated
        # Additional GenBank columns
        "definition",         # GenBank sequence definition
        "strain",             # Strain information
        "isolation_source",   # Source of isolation
        "create_date",        # GenBank creation date
        "update_date",        # GenBank update date
        "assembly_name",      # Assembly name
        "authors",            # Publication authors
        "title",              # Publication title
        "journal",            # Publication journal
        "pubmed_id",          # PubMed ID
        "reference_count",    # Number of references
        "comment",            # Additional comments
    ]
    
    logger.debug("Using column order: %s", columns)
    
    # Prepare data for DataFrame creation
    data_for_df = []
    
    for accession, metadata in genbank_metadata.items():
        logger.debug("Processing GenBank metadata for accession: %s", accession)
        
        genbank_data = metadata.get('genbank_data', {})
        
        # Extract publication information (use first reference if available)
        references = genbank_data.get('references', [])
        first_ref = references[0] if references else {}
        
        # Build the row dictionary with the same column structure as save_metadata_to_csv
        row = {
            # Primary identifier
            "accession": accession,
            
            # Organism and database information
            "Organism Name": genbank_data.get('organism', pd.NA),
            "GenBank/RefSeq": metadata.get('sourceDatabase', pd.NA),
            
            # Submission information
            "Submitters": metadata.get('submitter', {}).get('names', []) if metadata.get('submitter', {}).get('names') else pd.NA,
            "Organization": metadata.get('submitter', {}).get('affiliation', pd.NA),
            "Submitter Country": metadata.get('submitter', {}).get('country', pd.NA),
            "Release date": metadata.get('releaseDate', '').split('T')[0] if metadata.get('releaseDate') else pd.NA,
            
            # Sample and isolate information
            "Isolate": genbank_data.get('isolate', pd.NA),
            "Sample Name": genbank_data.get('isolate', pd.NA),
            
            # Virus classification
            "Virus Lineage": genbank_data.get('taxonomy', pd.NA),
            
            # Sequence characteristics
            "Length": genbank_data.get('sequence_length', pd.NA),
            "Nuc Completeness": metadata.get('completeness', pd.NA),
            "Proteins/Segments": pd.NA,  # Not available from GenBank XML parsing
            "Segment": metadata.get('segment', pd.NA),  # Virus segment identifier
            "Is Vaccine Strain": metadata.get('isVaccineStrain', metadata.get('is_vaccine_strain', pd.NA)),
            
            # Geographic information
            "Geographic Region": metadata.get('region', pd.NA),
            "Geographic Location": genbank_data.get('geographic_location', pd.NA),
            
            # Host information
            "Host": genbank_data.get('host', pd.NA),
            "Host Lineage": metadata.get('host', {}).get('lineage', []) if isinstance(metadata.get('host'), dict) else pd.NA,
            "Lab Host": metadata.get('labHost', pd.NA),
            
            # Sample source information
            "Tissue/Specimen/Source": genbank_data.get('isolation_source', pd.NA),
            "Collection Date": genbank_data.get('collection_date', pd.NA),
            
            # Annotation and quality information
            "Annotated": metadata.get('isAnnotated', pd.NA),
            
            # Associated database records
            "SRA Accessions": metadata.get('sraAccessions', pd.NA),
            "Bioprojects": metadata.get('bioprojects', pd.NA),
            "Biosample": metadata.get('biosample', pd.NA),
            
            # Counts
            "Gene count": metadata.get('geneCount', pd.NA),
            "Protein count": metadata.get('proteinCount', pd.NA),
            "Mature Peptide Count": metadata.get('maturePeptideCount', pd.NA),
            
            # GenBank-specific columns
            "definition": genbank_data.get('definition', pd.NA),
            "strain": genbank_data.get('strain', pd.NA),
            "isolation_source": genbank_data.get('isolation_source', pd.NA),
            "create_date": genbank_data.get('create_date', pd.NA),
            "update_date": genbank_data.get('update_date', pd.NA),
            "assembly_name": genbank_data.get('assembly_name', pd.NA),
            "authors": first_ref.get('authors', pd.NA),
            "title": first_ref.get('title', pd.NA),
            "journal": first_ref.get('journal', pd.NA),
            "pubmed_id": first_ref.get('pubmed_id', pd.NA),
            "reference_count": len(references) if references else pd.NA,
            "comment": genbank_data.get('comment', pd.NA),
        }
        
        data_for_df.append(row)
    
    logger.info("Creating DataFrame with %d rows and %d columns", len(data_for_df), len(columns))
    
    # Create DataFrame with the specified column order
    df = pd.DataFrame(data_for_df, columns=columns)

    # Write DataFrame to CSV file
    try:
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info("✅ GenBank metadata successfully saved to: %s", output_file)
        logger.info("CSV file contains %d rows and %d columns", len(df), len(df.columns)) 
    except Exception as e:
        logger.error("❌ Failed to save GenBank metadata CSV: %s", e)
        raise RuntimeError(f"❌ Failed to save GenBank metadata to {output_file}: {e}") from e
    

def filter_cached_metadata_for_unused_filters(
    metadata_dict,
    host=None,
    complete_only=None,
    annotated=None,
    lineage=None,
    geographic_location=None,
    refseq_only=None,
    min_release_date=None,
    applied_strategy_filters=None,
):
    """
    Apply filters that were not used in the cached download strategy.
    
    This is Step 3 of the cached download pipeline. It applies:
    1. Server-side filters not used in the successful cached strategy: host, complete_only, annotated, lineage
    2. API-only filters that couldn't be applied server-side: geographic_location, refseq_only, min_release_date
    
    Args:
        metadata_dict (dict): Dictionary mapping accession numbers to metadata from cached download.
        host (str, optional): Host organism filter (not applied if in applied_strategy_filters).
        complete_only (bool, optional): Complete genome filter (not applied if in applied_strategy_filters).
        annotated (bool, optional): Annotation filter (not applied if in applied_strategy_filters).
        lineage (str, optional): Lineage filter for SARS-CoV-2 (not applied if in applied_strategy_filters).
        geographic_location (str, optional): Geographic location filter (API-only, always applied if specified).
        refseq_only (bool, optional): RefSeq only filter (API-only, always applied if specified).
        min_release_date (str, optional): Minimum release date filter (API-only, always applied if specified).
        applied_strategy_filters (list, optional): List of filter names that were applied during cached strategy.
            Includes: 'host', 'complete-only', 'annotated', 'lineage'
        
    Returns:
        tuple: (filtered_accessions, filtered_metadata_list)
    """

    if applied_strategy_filters is None and geographic_location is None and refseq_only is None and min_release_date is None:
        logger.debug("No filters specified for post-cached-download filtering. Returning all metadata unchanged.")
        return list(metadata_dict.keys()), list(metadata_dict.values())
    
    if applied_strategy_filters is None:
        applied_strategy_filters = []
    
    logger.info("="*60)
    logger.info("STEP 3b: Applying post-cached-download filters")
    logger.info("="*60)
    logger.debug("Filters applied during cached strategy: %s", applied_strategy_filters)
    
    # Determine which filters to apply based on what wasn't used in strategy
    filters_to_apply = {}
    
    # Server-side filters (only apply if not already applied in strategy)
    if 'host' not in applied_strategy_filters and host:
        filters_to_apply['host'] = host
        logger.debug("Will apply host filter: %s (not used in cached strategy)", host)
    
    if 'complete-only' not in applied_strategy_filters and complete_only:
        filters_to_apply['complete_only'] = complete_only
        logger.debug("Will apply complete-only filter (not used in cached strategy)")
    
    if 'annotated' not in applied_strategy_filters and annotated:
        filters_to_apply['annotated'] = annotated
        logger.debug("Will apply annotated filter (not used in cached strategy)")
    
    if 'lineage' not in applied_strategy_filters and lineage:
        filters_to_apply['lineage'] = lineage
        logger.debug("Will apply lineage filter: %s (not used in cached strategy)", lineage)
    
    # API-only filters (always apply if specified since they're never in cached strategy)
    if geographic_location:
        filters_to_apply['geographic_location'] = geographic_location
        logger.debug("Will apply geographic_location filter: %s (API-only)", geographic_location)
    
    if refseq_only:
        filters_to_apply['refseq_only'] = refseq_only
        logger.debug("Will apply refseq_only filter (API-only)")
    
    if min_release_date:
        filters_to_apply['min_release_date'] = min_release_date
        logger.debug("Will apply min_release_date filter: %s (API-only)", min_release_date)
    
    # If no filters to apply, return all metadata unchanged
    if not filters_to_apply:
        logger.debug("No post-cached-download filters to apply. All %d records will proceed.", len(metadata_dict))
        return list(metadata_dict.keys()), list(metadata_dict.values())
    
    logger.info("Applying post-cached-download filters: %s", list(filters_to_apply.keys()))
    
    # Parse min_release_date once for efficiency
    min_release_date_parsed = None
    if 'min_release_date' in filters_to_apply:
        min_release_date_parsed = _parse_date(min_release_date, filtername="min_release_date")
    
    # Apply filters to each metadata record
    filtered_accessions = []
    filtered_metadata_list = []
    filter_stats = {
        'host': 0,
        'complete_only': 0,
        'annotated': 0,
        'lineage': 0,
        'geographic_location': 0,
        'refseq_only': 0,
        'min_release_date': 0,
    }
    
    for accession, metadata in metadata_dict.items():
        # Apply each filter - if any fails, skip this record
        
        # Host filter
        if 'host' in filters_to_apply:
            host_name = metadata.get('hostName', '')
            if not host_name:
                logger.debug("Skipping %s: missing host metadata", accession)
                filter_stats['host'] += 1
                continue
            if host.lower() not in host_name.lower():
                logger.debug("Skipping %s: host '%s' does not match '%s'", accession, host_name, host)
                filter_stats['host'] += 1
                continue
        
        # Complete-only filter
        if 'complete_only' in filters_to_apply:
            nuc_completeness = metadata.get('completeness', '')
            if not nuc_completeness or nuc_completeness.lower() != 'complete':
                logger.debug("Skipping %s: completeness '%s' != 'complete'", accession, nuc_completeness)
                filter_stats['complete_only'] += 1
                continue
        
        # Annotated filter
        if 'annotated' in filters_to_apply:
            is_annotated = metadata.get('isAnnotated', False)
            if not is_annotated:
                logger.debug("Skipping %s: not annotated", accession)
                filter_stats['annotated'] += 1
                continue
        
        # Lineage filter (SARS-CoV-2 specific)
        if 'lineage' in filters_to_apply:
            virus_pangolin = metadata.get('virusPangolinClassification', '')
            if not virus_pangolin or lineage.lower() not in virus_pangolin.lower():
                logger.debug("Skipping %s: lineage '%s' does not match '%s'", accession, virus_pangolin, lineage)
                filter_stats['lineage'] += 1
                continue
        
        # Geographic location filter (API-only)
        if 'geographic_location' in filters_to_apply:
            geo_loc = metadata.get('location', '') or ''
            geo_region = metadata.get('region', '') or ''
            virus_name = metadata.get('virusName', '') or ''
            # Only skip if ALL location sources are empty
            if not geo_loc and not geo_region and not virus_name:
                logger.debug("Skipping %s: missing location, region, and virusName metadata", accession)
                filter_stats['geographic_location'] += 1
                continue
            # Check if filter matches location, region, or virusName (fallback for older records)
            geo_filter = geographic_location.lower()
            loc_matches = geo_loc and geo_filter in geo_loc.lower()
            region_matches = geo_region and geo_filter in geo_region.lower()
            # Also check virusName as fallback (e.g., "B/USA/65/2002" contains location in name)
            virus_name_matches = virus_name and geo_filter in virus_name.lower()
            if not loc_matches and not region_matches and not virus_name_matches:
                logger.debug("Skipping %s: geo_location '%s', region '%s', virusName '%s' do not match '%s'", accession, geo_loc, geo_region, virus_name, geographic_location)
                filter_stats['geographic_location'] += 1
                continue
        
        # RefSeq only filter (API-only)
        if 'refseq_only' in filters_to_apply:
            is_refseq = metadata.get('sourceDatabase', '').lower() == 'refseq'
            if not is_refseq:
                logger.debug("Skipping %s: not RefSeq (refseq_only=True)", accession)
                filter_stats['refseq_only'] += 1
                continue
        
        # Minimum release date filter (API-only)
        if 'min_release_date' in filters_to_apply:
            release_date_str = metadata.get('releaseDate', '')
            if not release_date_str:
                logger.debug("Skipping %s: missing release date metadata", accession)
                filter_stats['min_release_date'] += 1
                continue
            release_date = _parse_date(release_date_str.split("T")[0], filtername="release_date")
            if not release_date or (min_release_date_parsed and release_date < min_release_date_parsed):
                logger.debug("Skipping %s: release date %s < min %s", accession, release_date, min_release_date_parsed)
                filter_stats['min_release_date'] += 1
                continue
        
        # All filters passed
        filtered_accessions.append(accession)
        filtered_metadata_list.append(metadata)
    
    # Log comprehensive filtering statistics
    logger.info("✅ Post-cached-download filtering complete: %d -> %d records",
                len(metadata_dict), len(filtered_accessions))
    
    total_filtered = sum(filter_stats.values())
    if total_filtered > 0:
        logger.info("Filter statistics (records excluded):")
        for filter_name, count in filter_stats.items():
            if count > 0:
                logger.info("  %s: %d records", filter_name, count)
    
    return filtered_accessions, filtered_metadata_list


def filter_metadata_only(
    metadata_dict,
    min_seq_length=None,
    max_seq_length=None,
    # min_gene_count=None,
    # max_gene_count=None,
    nuc_completeness=None,
    lab_passaged=None,
    submitter_country=None,
    min_collection_date=None,
    max_collection_date=None,
    source_database=None,
    max_release_date=None,
    # min_mature_peptide_count=None,
    # max_mature_peptide_count=None,
    min_protein_count=None,
    max_protein_count=None,
    annotated=None,
    segment=None,
    vaccine_strain=None,
    submitter_name=None,
    submitter_institution=None,
    isolate=None,
    isolation_source=None,
    geographic_location=None,
    host=None,
):
    """
    Filter metadata records based on metadata-only criteria.
    
    Applies filters that can be evaluated using only metadata, reducing the
    number of accessions before downloading sequences. Sequence-dependent
    filters are deferred to post-download filtering.
    
    Args:
        metadata_dict (dict): Dictionary mapping accession numbers to metadata.
        (other args): Filter criteria - same as filter_sequences.
        
    Returns:
        tuple: (filtered_accessions, filtered_metadata_list)
    """
    
    logger.info("Starting metadata-only filtering process...")
    logger.debug("Applying metadata-only filters: seq_length(%s-%s), completeness(%s), lab_passaged(%s), annotated(%s), submitter_country(%s), collection_date(%s-%s), source_database(%s), max_release_date(%s), protein_count(%s-%s), segment(%s), vaccine_strain(%s), submitter_name(%s), submitter_institution(%s), isolate(%s)", min_seq_length, max_seq_length, nuc_completeness, lab_passaged, annotated, submitter_country, min_collection_date, max_collection_date, source_database, max_release_date, min_protein_count, max_protein_count, segment, vaccine_strain, submitter_name, submitter_institution, isolate)

    # Convert date filters to datetime objects for proper comparison
    # Parse user-provided filter dates with appropriate partial date handling:
    # - min dates: use START of range (e.g., "2015" -> 2015-01-01)
    # - max dates: use END of range (e.g., "2024" -> 2024-12-31)
    min_collection_date = (
        _parse_partial_date_for_range_check(
            min_collection_date, for_min_comparison=False, filtername="min_collection_date"
        ) if min_collection_date else None
    )
    max_collection_date = (
        _parse_partial_date_for_range_check(
            max_collection_date, for_min_comparison=True, filtername="max_collection_date"
        ) if max_collection_date else None
    )
    max_release_date = (
        _parse_partial_date_for_range_check(
            max_release_date, for_min_comparison=True, filtername="max_release_date"
        ) if max_release_date else None
    )
    
    if min_collection_date:
        logger.debug("Parsed min_collection_date: %s", min_collection_date)
    if max_collection_date:
        logger.debug("Parsed max_collection_date: %s", max_collection_date)
    if max_release_date:
        logger.debug("Parsed max_release_date: %s", max_release_date)

    # Initialize lists to store filtered results
    filtered_accessions = []
    filtered_metadata_list = []
    
    # Counters for logging filter statistics
    total_sequences = len(metadata_dict)
    filter_stats = {
        'seq_length': 0,
        # 'gene_count': 0,
        'completeness': 0,
        'lab_passaged': 0,
        'annotated': 0,
        'submitter_country': 0,
        'collection_date': 0,
        'source_database': 0,
        'release_date': 0,
        # 'mature_peptide_count': 0,
        'protein_count': 0,
        'segment': 0,
        'vaccine_strain': 0,
        'submitter_name': 0,
        'submitter_institution': 0,
        'isolate': 0,
        'isolation_source': 0,
        'geographic_location': 0,
        'host': 0,
    }

    logger.info("Processing %d metadata records...", total_sequences)
    
    for accession, metadata in metadata_dict.items():
        # logger.debug("Processing metadata for: %s", accession)
        
        # Apply filters sequentially - each filter can exclude the record
        # If any filter fails, we continue to the next record
        
        # FILTER 1: Sequence length filters
        if min_seq_length is not None or max_seq_length is not None:
            sequence_length = metadata.get("length")
            if sequence_length is None:
                logger.debug("Skipping %s: missing length metadata", accession)
                filter_stats['seq_length'] += 1
                continue
                
            if min_seq_length is not None and sequence_length < min_seq_length:
                logger.debug("Skipping %s: length %d < min %d", accession, sequence_length, min_seq_length)
                filter_stats['seq_length'] += 1
                continue
                
            if max_seq_length is not None and sequence_length > max_seq_length:
                logger.debug("Skipping %s: length %d > max %d", accession, sequence_length, max_seq_length)
                filter_stats['seq_length'] += 1
                continue

        # FILTER 2: Gene count filters
        # if min_gene_count is not None or max_gene_count is not None:
        #     gene_count = metadata.get("geneCount")
        #     if gene_count is None:
        #         logger.debug("Skipping %s: missing gene count metadata", accession)
        #         filter_stats['gene_count'] += 1
        #         continue
                
        #     if min_gene_count is not None and gene_count < min_gene_count:
        #         logger.debug("Skipping %s: gene count %d < min %d", accession, gene_count, min_gene_count)
        #         filter_stats['gene_count'] += 1
        #         continue
                
        #     if max_gene_count is not None and gene_count > max_gene_count:
        #         logger.debug("Skipping %s: gene count %d > max %d", accession, gene_count, max_gene_count)
        #         filter_stats['gene_count'] += 1
        #         continue

        # FILTER 3: Nucleotide completeness filter
        if nuc_completeness is not None and not nuc_completeness.lower() == "complete":
            completeness_status = metadata.get("completeness")
            if completeness_status is None:
                logger.debug("Skipping %s: missing completeness metadata", accession)
                filter_stats['completeness'] += 1
                continue
                
            if completeness_status.lower() != nuc_completeness.lower():
                logger.debug("Skipping %s: completeness '%s' != required '%s'", 
                           accession, completeness_status, nuc_completeness)
                filter_stats['completeness'] += 1
                continue

        # FILTER 4: Lab passaging status filter
        if lab_passaged is True:
            from_lab = metadata.get("isLabHost")
            if not from_lab:
                logger.debug("Skipping %s: not lab-passaged (required)", accession)
                filter_stats['lab_passaged'] += 1
                continue

        if lab_passaged is False:
            from_lab = metadata.get("isLabHost")
            if from_lab:
                logger.debug("Skipping %s: is lab-passaged (excluded)", accession)
                filter_stats['lab_passaged'] += 1
                continue

        # FILTER 5: Annotation status filter
        # Note: annotated=True is handled server-side via API filter.annotated_only=true
        # annotated=False must be handled client-side by excluding annotated sequences
        if annotated is False:
            is_annotated = metadata.get("isAnnotated")
            if is_annotated:
                logger.debug("Skipping %s: is annotated (excluded when annotated=False)", accession)
                filter_stats['annotated'] += 1
                continue

        # FILTER 6: Submitter country filter
        if submitter_country is not None:
            submitter_country_value = "_".join(
                (metadata.get("submitterCountry") or "").split(" ")
            ).lower()
            
            if not submitter_country_value:
                logger.debug("Skipping %s: missing submitter country", accession)
                filter_stats['submitter_country'] += 1
                continue
                
            if submitter_country_value != submitter_country.lower():
                logger.debug("Skipping %s: submitter country '%s' != required '%s'", 
                           accession, submitter_country_value, submitter_country.lower())
                filter_stats['submitter_country'] += 1
                continue

        # FILTER 7: Submitter name filter
        if submitter_name is not None:
            # Convert submitter_name to list if it's a string
            submitter_name_list = [submitter_name] if isinstance(submitter_name, str) else submitter_name
            
            # Get submitter name from metadata
            metadata_submitter_name = metadata.get("submitterName", "")

            if not metadata_submitter_name:
                filter_stats['submitter_name'] += 1
                continue
            
            # Build set of acceptable submitter name values (case-insensitive)
            acceptable_names = {s.lower().strip() for s in submitter_name_list}
            
            # Check if metadata submitter name matches any acceptable value (case-insensitive)
            metadata_submitter_name_lower = str(metadata_submitter_name).lower().strip()
            if metadata_submitter_name_lower not in acceptable_names:
                logger.debug("Skipping %s: submitter name '%s' not in required list %s", 
                           accession, metadata_submitter_name, submitter_name_list)
                filter_stats['submitter_name'] += 1
                continue

        # FILTER 8: Submitter institution filter
        if submitter_institution is not None:
            # Convert submitter_institution to list if it's a string
            submitter_institution_list = [submitter_institution] if isinstance(submitter_institution, str) else submitter_institution
            
            # Get submitter institution from metadata
            metadata_submitter_institution = metadata.get("submitterInstitution", "")

            if not metadata_submitter_institution:
                filter_stats['submitter_institution'] += 1
                continue
            
            # Build set of acceptable submitter institution values (case-insensitive)
            acceptable_institutions = {s.lower().strip() for s in submitter_institution_list}
            
            # Check if metadata submitter institution matches any acceptable value (case-insensitive)
            metadata_submitter_institution_lower = str(metadata_submitter_institution).lower().strip()
            if metadata_submitter_institution_lower not in acceptable_institutions:
                logger.debug("Skipping %s: submitter institution '%s' not in required list %s", 
                           accession, metadata_submitter_institution, submitter_institution_list)
                filter_stats['submitter_institution'] += 1
                continue

        # FILTER 9: isolate filter
        if isolate is not None:
            # Convert isolate to list if it's a string
            isolate_list = [isolate] if isinstance(isolate, str) else isolate
            
            # Get isolate from metadata
            metadata_isolate = metadata.get("isolateName", "")

            if not metadata_isolate:
                filter_stats['isolate'] += 1
                continue
            
            # Build set of acceptable isolate values (case-insensitive)
            acceptable_isolates = {s.lower().strip() for s in isolate_list}
            
            # Check if metadata isolate matches any acceptable value (case-insensitive)
            metadata_isolate_lower = str(metadata_isolate).lower().strip()
            if metadata_isolate_lower not in acceptable_isolates:
                logger.debug("Skipping %s: isolate '%s' not in required list %s", 
                           accession, metadata_isolate, isolate_list)
                filter_stats['isolate'] += 1
                continue

        # FILTER 10: isolation source filter
        if isolation_source is not None:
            # Convert isolation_source to list if it's a string
            isolation_source_list = [isolation_source] if isinstance(isolation_source, str) else isolation_source
            
            # Get isolation source from metadata
            metadata_isolation_source = metadata.get("isolate", {}).get("source", "")

            if not metadata_isolation_source:
                filter_stats['isolation_source'] += 1
                continue
            
            # Build set of acceptable isolation source values (case-insensitive)
            acceptable_isolation_sources = {s.lower().strip() for s in isolation_source_list}
            
            # Check if metadata isolation source matches any acceptable value (case-insensitive)
            metadata_isolation_source_lower = str(metadata_isolation_source).lower().strip()
            if metadata_isolation_source_lower not in acceptable_isolation_sources:
                logger.debug("Skipping %s: isolation source '%s' not in required list %s", 
                           accession, metadata_isolation_source, isolation_source_list)
                filter_stats['isolation_source'] += 1
                continue


        # FILTER 11: Collection date range filter
        if min_collection_date is not None or max_collection_date is not None:
            date_str = metadata.get("isolate", {}).get("collectionDate", "")
            
            # Skip records with empty or missing collection date
            if not date_str:
                logger.debug("Skipping %s: missing or empty collection date", accession)
                filter_stats['collection_date'] += 1
                continue
            
            # Handle partial dates (year-only or year-month) appropriately for range checks
            # For min_collection_date: use end of partial range (record COULD be >= min)
            # For max_collection_date: use start of partial range (record COULD be <= max)
            
            skip_record = False
            
            if min_collection_date:
                try:
                    # Parse with for_min_comparison=True to use end of range for partial dates
                    date_for_min = _parse_partial_date_for_range_check(
                        date_str, for_min_comparison=True, filtername="collection_date"
                    )
                except ValueError:
                    logger.debug("Skipping %s: invalid collection date format '%s'", accession, date_str)
                    filter_stats['collection_date'] += 1
                    continue
                    
                if date_for_min is None:
                    logger.debug("Skipping %s: missing or invalid collection date '%s'", accession, date_str)
                    filter_stats['collection_date'] += 1
                    continue
                    
                if date_for_min < min_collection_date:
                    logger.debug("Skipping %s: collection date %s (from '%s') < min %s", 
                               accession, date_for_min, date_str, min_collection_date)
                    filter_stats['collection_date'] += 1
                    skip_record = True
                    
            if not skip_record and max_collection_date:
                try:
                    # Parse with for_min_comparison=False to use start of range for partial dates
                    date_for_max = _parse_partial_date_for_range_check(
                        date_str, for_min_comparison=False, filtername="collection_date"
                    )
                except ValueError:
                    logger.debug("Skipping %s: invalid collection date format '%s'", accession, date_str)
                    filter_stats['collection_date'] += 1
                    continue
                    
                if date_for_max is None:
                    logger.debug("Skipping %s: missing or invalid collection date '%s'", accession, date_str)
                    filter_stats['collection_date'] += 1
                    continue
                    
                if date_for_max > max_collection_date:
                    logger.debug("Skipping %s: collection date %s (from '%s') > max %s", 
                               accession, date_for_max, date_str, max_collection_date)
                    filter_stats['collection_date'] += 1
                    skip_record = True
            
            if skip_record:
                continue

        # FILTER 12: Maximum release date filter
        if max_release_date is not None:
            release_date_str = metadata.get("releaseDate")
            
            if not release_date_str:
                logger.debug("Skipping %s: missing release date", accession)
                filter_stats['release_date'] += 1
                continue
            
            # Strip time portion if present (e.g., "2024-02-14T00:00:00Z" -> "2024-02-14")
            release_date_str_clean = release_date_str.split("T")[0]
            
            try:
                # For max comparison, use START of range for partial dates
                # so that records that COULD be within range are included
                release_date_value = _parse_partial_date_for_range_check(
                    release_date_str_clean, for_min_comparison=False, filtername="release_date"
                )
            except ValueError:
                logger.debug("Skipping %s: invalid release date format '%s'", accession, release_date_str)
                filter_stats['release_date'] += 1
                continue
            
            if release_date_value is None:
                logger.debug("Skipping %s: invalid release date '%s'", accession, release_date_str)
                filter_stats['release_date'] += 1
                continue
                
            if release_date_value > max_release_date:
                logger.debug("Skipping %s: release date %s (from '%s') > max %s", 
                           accession, release_date_value, release_date_str, max_release_date)
                filter_stats['release_date'] += 1
                continue

        # FILTER 13: Mature peptide count filters
        # if min_mature_peptide_count is not None or max_mature_peptide_count is not None:
        #     mature_peptide_count = metadata.get("maturePeptideCount")
            
        #     if mature_peptide_count is None:
        #         logger.debug("Skipping %s: missing mature peptide count", accession)
        #         filter_stats['mature_peptide_count'] += 1
        #         continue
                
        #     if (min_mature_peptide_count is not None and 
        #         mature_peptide_count < min_mature_peptide_count):
        #         logger.debug("Skipping %s: mature peptide count %d < min %d", 
        #                    accession, mature_peptide_count, min_mature_peptide_count)
        #         filter_stats['mature_peptide_count'] += 1
        #         continue
                
        #     if (max_mature_peptide_count is not None and 
        #         mature_peptide_count > max_mature_peptide_count):
        #         logger.debug("Skipping %s: mature peptide count %d > max %d", 
        #                    accession, mature_peptide_count, max_mature_peptide_count)
        #         filter_stats['mature_peptide_count'] += 1
        #         continue

        # FILTER 14: Protein count filters
        if min_protein_count is not None or max_protein_count is not None:
            protein_count = metadata.get("proteinCount")
            
            if protein_count is None:
                logger.debug("Skipping %s: missing protein count", accession)
                filter_stats['protein_count'] += 1
                continue
                
            if min_protein_count is not None and protein_count < min_protein_count:
                logger.debug("Skipping %s: protein count %d < min %d", 
                           accession, protein_count, min_protein_count)
                filter_stats['protein_count'] += 1
                continue
                
            if max_protein_count is not None and protein_count > max_protein_count:
                logger.debug("Skipping %s: protein count %d > max %d", 
                           accession, protein_count, max_protein_count)
                filter_stats['protein_count'] += 1
                continue

        # FILTER 15: Segment filter - simple case-insensitive matching
        if segment is not None:
            # Convert segment to list if it's a string
            segment_list = [segment] if isinstance(segment, str) else segment
            
            # Get segment from metadata
            metadata_segment = metadata.get("segment")
            
            if not metadata_segment:
                filter_stats['segment'] += 1
                continue
            
            # Build set of acceptable segment values (case-insensitive)
            acceptable_segments = {s.lower().strip() for s in segment_list}
            
            # Check if metadata segment matches any acceptable value (case-insensitive)
            metadata_segment_lower = str(metadata_segment).lower().strip()
            if metadata_segment_lower not in acceptable_segments:
                logger.debug("Skipping %s: segment '%s' not in required list %s", 
                           accession, metadata_segment, segment_list)
                filter_stats['segment'] += 1
                continue

        # FILTER 16: Vaccine strain filter
        if vaccine_strain is not None:
            is_vaccine = metadata.get("isVaccineStrain", metadata.get("is_vaccine_strain", False))
            if vaccine_strain:
                if not is_vaccine:
                    logger.debug("Skipping %s: not a vaccine strain (required)", accession)
                    filter_stats['vaccine_strain'] += 1
                    continue
            if vaccine_strain == False:
                if is_vaccine:
                    logger.debug("Skipping %s: is a vaccine strain (not allowed)", accession)
                    filter_stats['vaccine_strain'] += 1
                    continue

        # FILTER 17: Source database filter
        if source_database is not None:
            source_db = (metadata.get("sourceDatabase") or "").lower()
            if not source_db:
                logger.debug("Skipping %s: missing source database", accession)
                filter_stats['source_database'] += 1
                continue
                
            if source_db != source_database.lower():
                logger.debug("Skipping %s: source database '%s' != required '%s'", 
                           accession, source_db, source_database.lower())
                filter_stats['source_database'] += 1
                continue

        # FILTER 18: Geographic location filter (deferred from API when server-side filter fails)
        if geographic_location is not None:
            # Convert geographic_location to list if it's a string
            geo_location_list = [geographic_location] if isinstance(geographic_location, str) else geographic_location
            
            # Get geographic location from metadata - stored in "location", "region", and "virusName" fields
            metadata_location = metadata.get("location", "") or ""
            metadata_region = metadata.get("region", "") or ""
            metadata_virus_name = metadata.get("virusName", "") or ""
            
            # Only skip if ALL location sources are empty
            if not metadata_location and not metadata_region and not metadata_virus_name:
                logger.debug("Skipping %s: missing location, region, and virusName", accession)
                filter_stats['geographic_location'] += 1
                continue
            
            # Build set of acceptable location values (case-insensitive)
            # Normalize the filter values: remove special chars and create variations
            acceptable_locations = set()
            for loc in geo_location_list:
                loc_normalized = loc.lower().strip()
                # Remove common separators and create variations
                loc_normalized = loc_normalized.replace('-', ' ').replace('_', ' ').replace('+', ' ')
                acceptable_locations.add(loc_normalized)
                # Also add version without spaces for matching
                acceptable_locations.add(loc_normalized.replace(' ', ''))
            
            # Normalize metadata location and region for comparison
            metadata_location_lower = str(metadata_location).lower().strip()
            metadata_location_normalized = metadata_location_lower.replace('-', ' ').replace('_', ' ')
            metadata_location_no_spaces = metadata_location_normalized.replace(' ', '')
            
            metadata_region_lower = str(metadata_region).lower().strip()
            metadata_region_normalized = metadata_region_lower.replace('-', ' ').replace('_', ' ')
            metadata_region_no_spaces = metadata_region_normalized.replace(' ', '')
            metadata_virus_name_lower = str(metadata_virus_name).lower().strip()
            
            # Check for partial/substring match in location, region, OR virusName
            location_match = False
            for acceptable_loc in acceptable_locations:
                # Check location field
                if metadata_location_normalized and (acceptable_loc in metadata_location_normalized or acceptable_loc in metadata_location_no_spaces):
                    location_match = True
                    break
                # Also check if metadata location is contained in acceptable location
                if metadata_location_normalized and (metadata_location_normalized in acceptable_loc or metadata_location_no_spaces in acceptable_loc):
                    location_match = True
                    break
                # Check region field
                if metadata_region_normalized and (acceptable_loc in metadata_region_normalized or acceptable_loc in metadata_region_no_spaces):
                    location_match = True
                    break
                # Also check if metadata region is contained in acceptable location
                if metadata_region_normalized and (metadata_region_normalized in acceptable_loc or metadata_region_no_spaces in acceptable_loc):
                    location_match = True
                    break
                # Check virusName as fallback (for older records where location is in the name)
                if metadata_virus_name_lower and acceptable_loc in metadata_virus_name_lower:
                    location_match = True
                    break
            
            if not location_match:
                logger.debug("Skipping %s: location '%s', region '%s', virusName '%s' do not match required '%s'", 
                           accession, metadata_location, metadata_region, metadata_virus_name, geo_location_list)
                filter_stats['geographic_location'] += 1
                continue

        # FILTER 19: Host filter (deferred from API when server-side filter fails)
        if host is not None:
            # Convert host to list if it's a string
            host_list = [host] if isinstance(host, str) else host
            
            # Get host from metadata - stored in "hostName" field
            metadata_host = metadata.get("hostName", "") or ""
            
            if not metadata_host:
                logger.debug("Skipping %s: missing hostName", accession)
                filter_stats['host'] += 1
                continue
            
            # Build set of acceptable host values (case-insensitive)
            acceptable_hosts = set()
            for h in host_list:
                h_normalized = h.lower().strip()
                acceptable_hosts.add(h_normalized)
            
            # Normalize metadata host for comparison
            metadata_host_lower = str(metadata_host).lower().strip()
            
            # Check for partial/substring match in host
            host_match = False
            for acceptable_host in acceptable_hosts:
                # Check if acceptable host is in metadata host or vice versa
                if acceptable_host in metadata_host_lower or metadata_host_lower in acceptable_host:
                    host_match = True
                    break
            
            if not host_match:
                logger.debug("Skipping %s: hostName '%s' does not match required '%s'", 
                           accession, metadata_host, host_list)
                filter_stats['host'] += 1
                continue

        # If we reach this point, the metadata record has passed all filters
        filtered_accessions.append(accession)
        filtered_metadata_list.append(metadata)
        
        logger.debug("Metadata %s passed all filters", accession)

    # Log comprehensive filtering statistics
    num_filtered = len(filtered_accessions)
    
    if num_filtered == 0:
        # Simplified output when nothing passes filters
        logger.info("=================================")
        logger.info("Metadata-only filtering complete: 0 of %d records passed filters", total_sequences)
        total_filtered = sum(filter_stats.values())
        if total_filtered > 0:
            logger.info("Filter statistics (records excluded):")
            for filter_name, count in filter_stats.items():
                if count > 0:
                    logger.info("  %s: %d records", filter_name, count)
    else:
        # Normal output when some records pass filters
        logger.info("✅ Metadata-only filtering process complete.")
        logger.info("=================================")
        logger.info("Metadata-only filtering complete:")
        logger.info("  Total metadata records: %d", total_sequences)
        logger.info("  Records passing filters: %d", num_filtered)
        
        # Log detailed filter statistics if any records were filtered out
        total_filtered = sum(filter_stats.values())
        if total_filtered > 0:
            logger.info("Filter statistics (records excluded):")
            for filter_name, count in filter_stats.items():
                if count > 0:
                    logger.info("  %s: %d records", filter_name, count)
    
    return filtered_accessions, filtered_metadata_list, filter_stats


def filter_genbank_metadata(
    genbank_metadata,
    min_gene_count=None,
    max_gene_count=None,
    min_mature_peptide_count=None,
    max_mature_peptide_count=None,
    provirus=None,
    genotype=None,
    has_proteins=None,
    gen_mol_type=None,
    env_source=None,
):
    """
    Filter accessions based on GenBank-specific metadata fields.
    
    This function filters accessions using metadata extracted from GenBank XML
    that is not available in the standard NCBI Datasets API. These fields require
    fetching full GenBank records via E-utilities.
    
    Filtering is done using the parsed genbank_metadata dictionary where each
    accession maps to metadata containing a 'genbank_data' sub-dictionary with:
        - gene_count: Number of gene features
        - mature_peptide_count: Number of mat_peptide features
        - proviral: Boolean indicating proviral annotation
        - genotype: From serotype or note qualifier (determines virus subtype)
        - products: List of product names from CDS/mat_peptide features
        - mol_type: Molecule type (e.g., 'genomic RNA', 'genomic DNA')
        - isolation_source: Sample isolation source (for env_source filter)
        - host: Host information (used to determine env_source when empty)
        - comment: GenBank comment field (may contain env_source keywords)
    
    Args:
        genbank_metadata (dict): Dictionary mapping accession numbers to metadata
            with 'genbank_data' sub-dictionary from _parse_genbank_xml.
        min_gene_count (int, optional): Minimum number of gene features required.
        max_gene_count (int, optional): Maximum number of gene features allowed.
        min_mature_peptide_count (int, optional): Minimum mat_peptide features.
        max_mature_peptide_count (int, optional): Maximum mat_peptide features.
        provirus (bool, optional): If True, keep only proviral sequences.
            If False, exclude proviral sequences. None means no filtering.
        genotype (str or list, optional): Required genotype(s) to match.
            Can be single string (e.g., 'H5N1') or list (e.g., ['H5N1', 'H3N2']).
        has_proteins (str or list, optional): Required protein/product name(s).
            Filters for sequences containing at least one of the specified proteins.
        gen_mol_type (str, optional): Required molecule type (e.g., 'genomic RNA').
        env_source (str or list, optional): Environmental source keywords to match.
            Searches isolation_source and note fields for keywords like 'sewage',
            'ocean water', 'sea', etc. when host is empty or not human.
        
    Returns:
        list: List of accession numbers that passed all GenBank-based filters.
        
    Example:
        >>> genbank_filtered = filter_genbank_metadata(
        ...     genbank_metadata=genbank_data,
        ...     min_gene_count=5,
        ...     provirus=False,
        ...     genotype=['H5N1', 'H5N8'],
        ...     has_proteins='hemagglutinin',
        ... )
    """
    
    logger.info("Starting GenBank metadata filtering...")
    logger.debug("GenBank filters: gene_count(%s-%s), mature_peptide(%s-%s), provirus=%s, genotype=%s, has_proteins=%s, mol_type=%s, env_source=%s",
                min_gene_count, max_gene_count, min_mature_peptide_count, max_mature_peptide_count,
                provirus, genotype, has_proteins, gen_mol_type, env_source)
    
    if not genbank_metadata:
        logger.warning("No GenBank metadata provided for filtering")
        return []
    
    # Convert single string filters to lists for uniform processing
    if isinstance(genotype, str):
        genotype = [genotype]
    if isinstance(has_proteins, str):
        has_proteins = [has_proteins]
    if isinstance(env_source, str):
        env_source = [env_source]
    
    # Environmental source keywords to search for
    env_keywords = ['sewage', 'wastewater', 'ocean', 'sea', 'river', 'lake', 
                    'pond', 'water', 'soil', 'environment', 'feces', 'fecal',
                    'stool', 'manure', 'avian', 'bird', 'poultry', 'swine', 'pig']
    
    # Filter statistics
    filter_stats = {
        'gene_count': 0,
        'mature_peptide_count': 0,
        'provirus': 0,
        'genotype': 0,
        'has_proteins': 0,
        'mol_type': 0,
        'env_source': 0,
        'no_genbank_data': 0,
    }
    
    filtered_accessions = []
    total_sequences = len(genbank_metadata)
    
    for accession, metadata in genbank_metadata.items():
        # Get genbank_data sub-dictionary
        gb_data = metadata.get('genbank_data', {})
        if not gb_data:
            logger.debug("Skipping %s: no genbank_data", accession)
            filter_stats['no_genbank_data'] += 1
            continue
        
        # FILTER 1: Gene count
        if min_gene_count is not None or max_gene_count is not None:
            gene_count = gb_data.get('gene_count', 0)
            
            if min_gene_count is not None and gene_count < min_gene_count:
                logger.debug("Skipping %s: gene count %d < min %d", accession, gene_count, min_gene_count)
                filter_stats['gene_count'] += 1
                continue
                
            if max_gene_count is not None and gene_count > max_gene_count:
                logger.debug("Skipping %s: gene count %d > max %d", accession, gene_count, max_gene_count)
                filter_stats['gene_count'] += 1
                continue
        
        # FILTER 2: Mature peptide count
        if min_mature_peptide_count is not None or max_mature_peptide_count is not None:
            mat_count = gb_data.get('mature_peptide_count', 0)
            
            if min_mature_peptide_count is not None and mat_count < min_mature_peptide_count:
                logger.debug("Skipping %s: mature peptide count %d < min %d", accession, mat_count, min_mature_peptide_count)
                filter_stats['mature_peptide_count'] += 1
                continue
                
            if max_mature_peptide_count is not None and mat_count > max_mature_peptide_count:
                logger.debug("Skipping %s: mature peptide count %d > max %d", accession, mat_count, max_mature_peptide_count)
                filter_stats['mature_peptide_count'] += 1
                continue
        
        # FILTER 3: Proviral status
        if provirus is not None:
            is_proviral = gb_data.get('proviral', False)
            
            if provirus and not is_proviral:
                logger.debug("Skipping %s: not proviral (required)", accession)
                filter_stats['provirus'] += 1
                continue
            
            if provirus is False and is_proviral:
                logger.debug("Skipping %s: is proviral (excluded)", accession)
                filter_stats['provirus'] += 1
                continue
        
        # FILTER 4: Genotype (from serotype or note field)
        if genotype is not None:
            record_genotype = (gb_data.get('genotype', '') or '').lower().strip()
            
            if not record_genotype:
                logger.debug("Skipping %s: missing genotype", accession)
                filter_stats['genotype'] += 1
                continue
            
            # Check if any requested genotype matches (case-insensitive, partial match)
            genotype_match = False
            for g in genotype:
                g_lower = g.lower().strip()
                if g_lower in record_genotype or record_genotype in g_lower:
                    genotype_match = True
                    break
            
            if not genotype_match:
                logger.debug("Skipping %s: genotype '%s' not in required %s", accession, record_genotype, genotype)
                filter_stats['genotype'] += 1
                continue
        
        # FILTER 5: Has proteins (check product names)
        if has_proteins is not None:
            products = gb_data.get('products', [])
            products_lower = [p.lower() for p in products]
            
            # Check that AT LEAST ONE required protein is present
            any_protein_found = False
            for protein in has_proteins:
                protein_lower = protein.lower().strip()
                for prod in products_lower:
                    if protein_lower in prod or prod in protein_lower:
                        any_protein_found = True
                        break
                if any_protein_found:
                    break
            
            if not any_protein_found:
                logger.debug("Skipping %s: none of required proteins %s found in %s", 
                           accession, has_proteins, products[:5])
                filter_stats['has_proteins'] += 1
                continue
        
        # FILTER 6: Molecule type (gen_mol_type)
        if gen_mol_type is not None:
            mol_type = (gb_data.get('mol_type', '') or '').lower().strip()
            
            if not mol_type:
                logger.debug("Skipping %s: missing mol_type", accession)
                filter_stats['mol_type'] += 1
                continue
            
            gen_mol_type_lower = gen_mol_type.lower().strip()
            
            # Define molecule type mappings for common aliases
            # dsDNA/ssRNA etc are structural classifications while GenBank uses "genomic DNA/RNA"
            mol_type_mappings = {
                'dsdna': ['genomic dna', 'dna'],
                'ssdna': ['genomic dna', 'dna'],
                'dsrna': ['genomic rna', 'rna'],
                'ssrna': ['genomic rna', 'rna', 'mrna', 'viral crna'],
                'dna': ['genomic dna', 'dna'],
                'rna': ['genomic rna', 'rna', 'mrna', 'viral crna'],
                'genomic dna': ['genomic dna', 'dna'],
                'genomic rna': ['genomic rna', 'rna'],
            }
            
            # Check if the filter matches directly or via mapping
            mol_type_match = False
            
            # First check direct/partial match
            if gen_mol_type_lower in mol_type or mol_type in gen_mol_type_lower:
                mol_type_match = True
            else:
                # Check via mappings
                mapped_values = mol_type_mappings.get(gen_mol_type_lower, [])
                for mapped_val in mapped_values:
                    if mapped_val in mol_type:
                        mol_type_match = True
                        break
            
            if not mol_type_match:
                logger.debug("Skipping %s: mol_type '%s' != required '%s'", accession, mol_type, gen_mol_type)
                filter_stats['mol_type'] += 1
                continue
        
        # FILTER 7: Environmental source (env_source)
        if env_source is not None:
            # Get isolation_source, note, and check host
            isolation_source = (gb_data.get('isolation_source', '') or '').lower()
            host = (gb_data.get('host', '') or '').lower()
            comment = (gb_data.get('comment', '') or '').lower()
            all_features = gb_data.get('all_features', {})
            
            # Get note from source feature
            source_feature = all_features.get('source', {})
            if isinstance(source_feature, list):
                source_feature = source_feature[0]
            note = (source_feature.get('note', '') or '').lower()
            
            # Combine all text to search
            search_text = f"{isolation_source} {note} {comment}"
            
            # If host is specified and is human, skip env_source filtering
            # (env_source is for non-human/environmental samples)
            is_human_host = 'human' in host or 'homo sapiens' in host
            
            env_match = False
            for env_term in env_source:
                env_term_lower = env_term.lower().strip()
                if env_term_lower in search_text:
                    env_match = True
                    break
                # Also check against common environmental keywords
                for keyword in env_keywords:
                    if keyword in env_term_lower and keyword in search_text:
                        env_match = True
                        break
                if env_match:
                    break
            
            # Only filter out if explicitly looking for environmental and not found
            if not env_match and not is_human_host:
                logger.debug("Skipping %s: env_source '%s' not found in isolation_source/note", 
                           accession, env_source)
                filter_stats['env_source'] += 1
                continue
        
        # If we reach here, the record passed all filters
        filtered_accessions.append(accession)
        logger.debug("GenBank metadata %s passed all filters", accession)
    
    # Log filtering summary
    num_filtered = len(filtered_accessions)
    
    if num_filtered == 0:
        logger.info("=================================")
        logger.info("GenBank filtering complete: 0 of %d records passed filters", total_sequences)
        total_excluded = sum(filter_stats.values())
        if total_excluded > 0:
            logger.info("Filter statistics (records excluded):")
            for filter_name, count in filter_stats.items():
                if count > 0:
                    logger.info("  %s: %d records", filter_name, count)
    else:
        logger.info("✅ GenBank metadata filtering complete.")
        logger.info("=================================")
        logger.info("GenBank filtering complete:")
        logger.info("  Total GenBank records: %d", total_sequences)
        logger.info("  Records passing filters: %d", num_filtered)
        
        total_excluded = sum(filter_stats.values())
        if total_excluded > 0:
            logger.info("Filter statistics (records excluded):")
            for filter_name, count in filter_stats.items():
                if count > 0:
                    logger.info("  %s: %d records", filter_name, count)
    
    return filtered_accessions, filter_stats


def virus(
    virus,
    is_accession=False,
    outfolder=None,
    host=None,
    min_seq_length=None,
    max_seq_length=None,
    min_gene_count=None,
    max_gene_count=None,
    nuc_completeness=None,
    has_proteins=None,
    proteins_complete=False,
    lab_passaged=None,
    geographic_location=None,
    submitter_country=None,
    min_collection_date=None,
    max_collection_date=None,
    source_database=None,
    annotated=None,
    # refseq_only=False,
    keep_temp=False,
    min_release_date=None,
    max_release_date=None,
    min_mature_peptide_count=None,
    max_mature_peptide_count=None,
    min_protein_count=None,
    max_protein_count=None,
    max_ambiguous_chars=None,
    is_sars_cov2=False,
    is_alphainfluenza=False,
    segment=None,
    vaccine_strain=None,
    lineage=None,
    genbank_metadata=False,
    genbank_batch_size=GENBANK_DEFAULT_BATCH_SIZE,
    download_all_accessions=False,
    _skip_cache=False,
    provirus=None,
    isolate=None,
    genotype=None,
    isolation_source=None,
    env_source=None,  
    submitter_name=None,
    submitter_institution=None,
    gen_mol_type=None, 
    # assembly_completeness=None,
    api_key=None,
    baseline_metadata=None,
    merge_results=True,
    verbose=True,
    ):
    """
    Download a virus genome dataset from the NCBI Virus database (https://www.ncbi.nlm.nih.gov/labs/virus/).

    This is the main function that orchestrates the entire virus data retrieval process,
    now optimized to download sequences only after all metadata-based filtering:
    1) Validate inputs
    2) Fetch and save API metadata (server-side filters applied)
    3) Apply metadata-only filters locally
    4) Download sequences for the filtered accession list only
    5) Apply sequence-dependent filters and save outputs
    6) Optionally fetch detailed GenBank metadata and save to CSV
    """
    # Resolve NCBI API key: argument > environment variable.
    # NCBI E-utilities allows 10 requests/sec with an API key vs 3/sec without.
    # Users can provide a key via:
    #   1. api_key argument (highest priority)
    #   2. NCBI_API_KEY environment variable (standard NCBI convention)
    # If no key is provided, the process continues at the lower rate limit.
    if api_key is None:
        api_key = os.environ.get("NCBI_API_KEY")
    if api_key:
        logger.info("Using NCBI API key for higher rate limits (10 req/sec)")
    else:
        logger.info("No NCBI API key provided. Using default rate limit (3 req/sec). "
                    "Set NCBI_API_KEY env var or pass --api_key for faster requests.")

    # Save the original logger level and set it based on verbose parameter
    original_logger_level = logger.level
    if not verbose:
        logger.setLevel(logging.CRITICAL)
    
    logger.info("Starting virus data retrieval process...")
    
    # Capture the command line for summary
    command_line = " ".join(sys.argv) if len(sys.argv) > 0 else "virus (called programmatically)"
    
    # Track wall-clock runtime
    _virus_start_time = time.time()
    
    # Initialize variables for tracking results
    total_api_records = 0
    total_after_metadata_filter = 0
    total_final_sequences = 0
    output_files_dict = {}
    final_metadata_for_summary = []
    filtered_sequences = []  
    refseq_only = False

    # Initialize filter stats for each stage (populated by filter functions)
    metadata_filter_stats = {}
    genbank_filter_stats = {}
    sequence_filter_stats = {}
    total_after_genbank_filter = None
    total_after_sequence_filter = None
    
    # Initialize failed commands tracker for tracking all types of failures
    failed_commands = {
        'api_timeout': None,
        'empty_response': None,
        'sequence_batches': [],
        'genbank_batches': [],
        'api_batches': [],
        'pagination_timeouts': [],
        'pagination_errors': [],
        'sequence_fetch': [],
    }
    
    # Track if GenBank metadata was successfully retrieved
    genbank_success = False
    genbank_error_msg = None

    if download_all_accessions:
        logger.info("ATTENTION: Download all accessions mode is active.")
        logger.info("This will download ALL virus accessions from NCBI, which can be a very large dataset and take a long time.")
        virus = NCBI_ALL_VIRUSES_TAXID # NCBI taxonomy ID for all Viruses
        is_accession = False
        logger.info("Overriding virus query and accession tag to fetch all viruses using taxon ID: %s. Filters remain unchanged.", virus)

    logger.info("Query parameters: virus='%s', is_accession=%s, outfolder='%s'",
                virus, is_accession, outfolder)
    logger.debug("Applied filters: host=%s, seq_length=(%s-%s), gene_count=(%s-%s), completeness=%s, annotated=%s, source_db(%s), keep_temp=%s, lab_passaged=%s, geographic_location=%s, submitter_country=%s, submitter_name=%s, submitter_institution=%s, collection_date=(%s-%s), release_date=(%s-%s), protein_count=(%s-%s), mature_peptide_count=(%s-%s), max_ambiguous=%s, has_proteins=%s, proteins_complete=%s, segment=%s, vaccine_strain=%s, lineage=%s, provirus=%s, isolate=%s, genotype=%s, isolation_source=%s, env_source=%s, gen_mol_type=%s, genbank_metadata=%s, genbank_batch_size=%s",
    host, min_seq_length, max_seq_length, min_gene_count, max_gene_count, nuc_completeness, annotated, source_database, keep_temp, lab_passaged, geographic_location, submitter_country, submitter_name, submitter_institution, min_collection_date, max_collection_date, min_release_date, max_release_date, min_protein_count, max_protein_count, min_mature_peptide_count, max_mature_peptide_count, max_ambiguous_chars, has_proteins, proteins_complete, segment, vaccine_strain, lineage, provirus, isolate, genotype, isolation_source, env_source, gen_mol_type, genbank_metadata, genbank_batch_size)

    # SECTION 1: INPUT VALIDATION AND OUTPUT DIRECTORY SETUP
    # Validate and normalize input arguments before proceeding
    logger.info("=" * 60)
    logger.info("STEP 1: VALIDATING INPUT ARGUMENTS AND OUTPUT DIRECTORY SETUP...")
    logger.info("=" * 60)
    
    # Validate virus parameter
    if virus is None or (isinstance(virus, str) and virus.strip() == ""):
        raise ValueError(
            "Argument 'virus' must be a non-empty string (virus name, taxon ID, or accession number)."
        )
    
    # Validate that both host and env_source filters are not used together, as they are mutually exclusive
    if host is not None and env_source is not None:
        raise ValueError("Both 'host' and 'env_source' filters are specified. If there is a host, there is no environmental source. Use only one of these filters for results.")
    
    # Normalize host parameter: convert "human" to "Homo sapiens" for NCBI API compatibility
    if host is not None and host.strip().lower() == "human":
        logger.debug("Normalizing host 'human' to 'Homo sapiens' for NCBI API compatibility")
        host = "Homo sapiens"
    
    # Validate nucleotide completeness argument
    if nuc_completeness is not None:
        nuc_completeness = nuc_completeness.lower()  # Normalize to lowercase
        if nuc_completeness not in ["partial", "complete"]:
            raise ValueError(
                "Argument 'nuc_completeness' must be 'partial', 'complete', or None."
            )
        logger.debug("Nucleotide completeness filter set to: %s", nuc_completeness)

    # Validate source database argument
    if source_database is not None:
        source_database = source_database.lower()  # Normalize to lowercase
        if source_database not in ["refseq", "genbank"]:
            raise ValueError(
                "Argument 'source_database' must be 'refseq', 'genbank', or None."
            )
        elif source_database == "refseq":
            refseq_only = True
            logger.debug("Source database filter set to RefSeq only")
        logger.debug("Source database filter set to: %s", source_database)
    
    # Validate boolean arguments with proper type checking
    if annotated is not None and not isinstance(annotated, bool):
        raise TypeError(
            "Argument 'annotated' must be a boolean (True or False) or None."
        )
        
    if lab_passaged is not None and not isinstance(lab_passaged, bool):
        raise TypeError(
            "Argument 'lab_passaged' must be a boolean (True or False) or None."
        )
        
    if proteins_complete is not None and not isinstance(proteins_complete, bool):
        raise TypeError(
            "Argument 'proteins_complete' must be a boolean (True or False)."
        )

    # if refseq_only is not None and not isinstance(refseq_only, bool):
    #     raise TypeError(
    #         "Argument 'refseq_only' must be a boolean (True or False)."
        # )
    
    if keep_temp is not None and not isinstance(keep_temp, bool):
        raise TypeError(
            "Argument 'keep_temp' must be a boolean (True or False)."
        )

    if is_accession is not None and not isinstance(is_accession, bool):
        raise TypeError(
            "Argument 'is_accession' must be a boolean (True or False)."
        )
    
    if genbank_metadata is not None and not isinstance(genbank_metadata, bool):
        raise TypeError(
            "Argument 'genbank_metadata' must be a boolean (True or False)."
        )

    if vaccine_strain is not None and not isinstance(vaccine_strain, bool):
        raise TypeError(
            "Argument 'vaccine_strain' must be a boolean (True or False) or None."
        )

    if provirus is not None and not isinstance(provirus, bool):
        raise TypeError(
            "Argument 'provirus' must be a boolean (True or False) or None."
        )
    
    if genbank_batch_size is not None:
        if not isinstance(genbank_batch_size, int) or genbank_batch_size <= 0:
            raise ValueError(
                "Argument 'genbank_batch_size' must be a positive integer."
            )
        if genbank_batch_size > GENBANK_MAX_BATCH_SIZE_WARNING:
            logger.warning("Large genbank_batch_size (%d) may cause API timeouts. Consider using smaller batches.", genbank_batch_size)
    
    if genbank_metadata:
        logger.info("GenBank metadata retrieval enabled (batch_size=%d)", genbank_batch_size)
    else:
        # Check if any GenBank-dependent filters are specified
        genbank_dependent_filters = {
            'provirus': provirus,
            'genotype': genotype,
            'has_proteins': has_proteins,
            'gen_mol_type': gen_mol_type,
            'env_source': env_source,
            'min_gene_count': min_gene_count,
            'max_gene_count': max_gene_count,
            'min_mature_peptide_count': min_mature_peptide_count,
            'max_mature_peptide_count': max_mature_peptide_count,
        }
        active_genbank_filters = [k for k, v in genbank_dependent_filters.items() if v is not None]
        
        if active_genbank_filters:
            logger.info("GenBank-dependent filters detected: %s", ', '.join(active_genbank_filters))
            logger.info("Automatically enabling GenBank metadata retrieval (-g flag)")
            genbank_metadata = True
        else:
            logger.debug("GenBank metadata retrieval disabled")

    
    # Convert integer virus identifiers to strings for API compatibility
    if isinstance(virus, int):
        virus = str(virus)
        logger.debug("Converted integer virus ID to string: %s", virus)

    if isinstance(host, int):
        host = str(host)
        logger.debug("Converted integer host ID to string: %s", host)

    # Validate min/max argument pairs to ensure logical consistency
    logger.debug("Validating min/max argument pairs...")
    check_min_max(
        min_seq_length,
        max_seq_length,
        "sequence length (arguments: min_seq_length and max_seq_length)",
    )
    check_min_max(
        min_gene_count,
        max_gene_count,
        "gene count (arguments: min_gene_count and max_gene_count)",
    )
    check_min_max(
        min_mature_peptide_count,
        max_mature_peptide_count,
        "mature peptide count (arguments: min_mature_peptide_count and max_mature_peptide_count)",
    )
    check_min_max(
        min_protein_count,
        max_protein_count,
        "protein count (arguments: min_protein_count and max_protein_count)",
    )
    check_min_max(
        min_collection_date,
        max_collection_date,
        "collection date (arguments: min_collection_date and max_collection_date)",
        date=True,
    )
    check_min_max(
        min_release_date,
        max_release_date,
        "release date (arguments: min_release_date and max_release_date)",
        date=True,
    )

    logger.info("Input validation completed successfully")

    ##############
    # Prepare output directory and all used file paths
    virus_clean = virus.replace(' ', '_').replace('/', '_').replace('-', '_')

    # Create and prepare output directory structure
    if outfolder is None:
        currentfolder = os.getcwd()
        outfolder = os.path.join(currentfolder, "gget_virus_output" , f"{virus_clean}_{timestamp}")
        logger.info("No output folder specified, creating a subdirectory in current directory named 'gget_virus_output' and placing results in a folder named: %s", outfolder)
    else:
        logger.info("Using specified output folder: %s", outfolder)
    
    # Ensure output folder exists
    os.makedirs(outfolder, exist_ok=True)
    logger.debug("Output folder ready: %s", outfolder)
    
    # Create temporary directory for intermediate processing
    # This will be cleaned up at the end regardless of success or failure
    temp_dir = os.path.join(outfolder, f"tmp_{timestamp}_{random_suffix}")
    os.makedirs(temp_dir, exist_ok=True)
    logger.debug("Created temporary processing directory: %s", temp_dir)

    # File names which will be referenced later
    genbank_csv_path = os.path.join(outfolder, f"{virus_clean}_genbank_metadata.csv")
    genbank_full_xml_path = os.path.join(outfolder, f"{virus_clean}_genbank_metadata_full.xml")
    genbank_full_csv_path = os.path.join(outfolder, f"{virus_clean}_genbank_metadata_full.csv")
    output_api_metadata_jsonl = os.path.join(outfolder, f"{virus_clean}_api_metadata.jsonl")
    
    # SECTION 1b: BASELINE METADATA LOADING FOR DEDUPLICATION
    # If a baseline file is provided, load accessions for deduplication
    baseline_accessions = None
    baseline_skipped_count = 0
    partial_metadata_file = None  # Will be set if API fails and partial metadata is saved
    
    if baseline_metadata is not None:
        logger.info("=" * 60)
        logger.info("STEP 1b: LOADING BASELINE METADATA FOR DEDUPLICATION")
        logger.info("=" * 60)
        try:
            baseline_accessions = _parse_baseline_file(baseline_metadata)
            logger.info("Baseline loaded: %d accessions from %s", len(baseline_accessions), baseline_metadata)
            if merge_results:
                logger.info("Output mode: --merge-results (combined baseline + new)")
            else:
                logger.info("Output mode: --no-merge (new sequences only)")
        except FileNotFoundError:
            logger.warning("⚠️ Baseline file not found: %s", baseline_metadata)
            logger.warning("Continuing without baseline deduplication.")
            baseline_accessions = None
        except ValueError as e:
            logger.warning("⚠️ Could not parse baseline file: %s", e)
            logger.warning("Continuing without baseline deduplication.")
            baseline_accessions = None

    # SECTION 2: CHECKING FOR CACHED DATA PROCESSING
    logger.info("=" * 60)
    logger.info("STEP 2: CHECKING FOR SARS-CoV-2 AND INFLUENZA A QUERIES TO APPLY OPTIMIZED CACHED PATHWAY")  
    logger.info("=" * 60)
    # Initialize variables to track cached download results
    cached_fasta_file = None  # Path to cached FASTA file (sequences streamed on-demand)
    cached_metadata_dict = None
    used_cached_download = False
    cached_zip_file = None  # Track zip file path for cleanup
    datasets_version = None  # Track datasets version for logging and summary

    # For SARS-CoV-2 queries, use cached data packages with hierarchical fallback
    if _skip_cache:
        logger.info("⏭️  SKIPPING CACHED PATHWAY - Using API method directly (via _skip_cache flag)")
    elif (is_sars_cov2 or is_sars_cov2_query(virus, is_accession)):
        logger.info("DETECTED SARS-CoV-2 QUERY - USING CACHED DATA PACKAGE PATHWAY")
        logger.info("SARS-CoV-2 queries will use NCBI's optimized cached data packages")
        logger.info("with hierarchical fallback from specific to general cached files.")
        
        # Use the download_sars_cov2_optimized function which handles fallback strategies internally
        params = {
            'host': host,
            'complete_only': (nuc_completeness == "complete"),
            'annotated': annotated,
            'outdir': outfolder,
            'lineage': lineage,
            'accession': virus,
            'use_accession': is_accession
        }
                    
        try:
            download_result = download_sars_cov2_optimized(**params)
            # Unpack tuple: (zip_path, applied_filters, missing_filters)
            zip_file = download_result[0]
            applied_filters = download_result[1]
            missing_filters = download_result[2]
            cached_zip_file = zip_file  # Track for cleanup
            datasets_version = _get_datasets_version()
            
            cached_fasta_file, cached_metadata_dict, used_cached_download = process_cached_download(
                zip_file, virus_type="SARS-CoV-2"
            )
            if used_cached_download:
                logger.info("Cached download completed. Server-side filters (host, complete_only, annotated, lineage) applied.")
                logger.info("All other filters will be applied in the unified filtering pipeline.")
                logger.debug("Applied filters: %s", applied_filters)
                logger.debug("Missing filters (to apply in Step 3b): %s", missing_filters)
        except Exception as cache_error:
            logger.warning("SARS-CoV-2 cached download failed after all strategies: %s", cache_error)
            logger.info("🔄 Retrying with normal API download method (_skip_cache=True)...")
            # Retry the entire virus() call with _skip_cache=True to use the normal API pathway
            _virus_func = globals()['virus']
            return _virus_func(
                virus=virus,
                is_accession=is_accession,
                outfolder=outfolder,
                host=host,
                min_seq_length=min_seq_length,
                max_seq_length=max_seq_length,
                min_gene_count=min_gene_count,
                max_gene_count=max_gene_count,
                nuc_completeness=nuc_completeness,
                has_proteins=has_proteins,
                proteins_complete=proteins_complete,
                lab_passaged=lab_passaged,
                geographic_location=geographic_location,
                submitter_country=submitter_country,
                min_collection_date=min_collection_date,
                max_collection_date=max_collection_date,
                source_database=source_database,
                annotated=annotated,
                keep_temp=keep_temp,
                min_release_date=min_release_date,
                max_release_date=max_release_date,
                min_mature_peptide_count=min_mature_peptide_count,
                max_mature_peptide_count=max_mature_peptide_count,
                min_protein_count=min_protein_count,
                max_protein_count=max_protein_count,
                max_ambiguous_chars=max_ambiguous_chars,
                is_sars_cov2=is_sars_cov2,
                is_alphainfluenza=is_alphainfluenza,
                segment=segment,
                vaccine_strain=vaccine_strain,
                lineage=lineage,
                genbank_metadata=genbank_metadata,
                genbank_batch_size=genbank_batch_size,
                download_all_accessions=download_all_accessions,
                _skip_cache=True,
                provirus=provirus,
                isolate=isolate,
                genotype=genotype,
                isolation_source=isolation_source,
                env_source=env_source,
                submitter_name=submitter_name,
                submitter_institution=submitter_institution,
                gen_mol_type=gen_mol_type,
                verbose=verbose,
            )
    else:
        logger.info("No SARS-CoV-2 query detected.")

    
    # SECTION 2b: ALPHAINFLUENZA CACHED DATA PROCESSING
    # For Alphainfluenza queries, use cached data packages with hierarchical fallback
    if _skip_cache:
        logger.info("⏭️  SKIPPING CACHED PATHWAY - Using API method directly (via _skip_cache flag)")
    elif (is_alphainfluenza or is_alphainfluenza_query(virus, is_accession)):
        logger.info("DETECTED ALPHAINFLUENZA QUERY - USING CACHED DATA PACKAGES")
        logger.info("Alphainfluenza queries will use NCBI's optimized cached data packages")
        logger.info("with hierarchical fallback from specific to general cached files.")
        
        # Use the download_alphainfluenza_optimized function which handles fallback strategies internally
        params = {
            'host': host,
            'complete_only': (nuc_completeness == "complete"),
            'annotated': annotated,
            'outdir': outfolder,
            'accession': virus,
            'use_accession': is_accession
        }
                    
        try:
            download_result = download_alphainfluenza_optimized(**params)
            # Unpack tuple: (zip_path, applied_filters, missing_filters)
            zip_file = download_result[0]
            applied_filters = download_result[1]
            missing_filters = download_result[2]
            cached_zip_file = zip_file  # Track for cleanup
            datasets_version = _get_datasets_version()
            
            cached_fasta_file, cached_metadata_dict, used_cached_download = process_cached_download(
                zip_file, virus_type="Alphainfluenza"
            )
            if used_cached_download:
                logger.info("Cached download completed. Server-side filters (host, complete_only, annotated) applied.")
                logger.info("All other filters will be applied in the unified filtering pipeline.")
                logger.debug("Applied filters: %s", applied_filters)
                logger.debug("Missing filters (to apply in Step 3b): %s", missing_filters)
        except Exception as cache_error:
            logger.warning("Alphainfluenza cached download failed after all strategies: %s", cache_error)
            logger.info("🔄 Retrying with normal API download method (_skip_cache=True)...")
            # Retry the entire virus() call with _skip_cache=True to use the normal API pathway
            # Note: We use globals()['virus'] because the local parameter 'virus' (a string)
            # shadows the function name in this scope.
            _virus_func = globals()['virus']
            return _virus_func(
                virus=virus,
                is_accession=is_accession,
                outfolder=outfolder,
                host=host,
                min_seq_length=min_seq_length,
                max_seq_length=max_seq_length,
                min_gene_count=min_gene_count,
                max_gene_count=max_gene_count,
                nuc_completeness=nuc_completeness,
                has_proteins=has_proteins,
                proteins_complete=proteins_complete,
                lab_passaged=lab_passaged,
                geographic_location=geographic_location,
                submitter_country=submitter_country,
                min_collection_date=min_collection_date,
                max_collection_date=max_collection_date,
                source_database=source_database,
                annotated=annotated,
                keep_temp=keep_temp,
                min_release_date=min_release_date,
                max_release_date=max_release_date,
                min_mature_peptide_count=min_mature_peptide_count,
                max_mature_peptide_count=max_mature_peptide_count,
                min_protein_count=min_protein_count,
                max_protein_count=max_protein_count,
                max_ambiguous_chars=max_ambiguous_chars,
                is_sars_cov2=is_sars_cov2,
                is_alphainfluenza=is_alphainfluenza,
                segment=segment,
                vaccine_strain=vaccine_strain,
                lineage=lineage,
                genbank_metadata=genbank_metadata,
                genbank_batch_size=genbank_batch_size,
                download_all_accessions=download_all_accessions,
                _skip_cache=True,
                provirus=provirus,
                isolate=isolate,
                genotype=genotype,
                isolation_source=isolation_source,
                env_source=env_source,
                submitter_name=submitter_name,
                submitter_institution=submitter_institution,
                gen_mol_type=gen_mol_type,
                verbose=verbose,
            )
    else:
        logger.info("No Alphainfluenza query detected.")
    
    # Initialize deferred_filters for tracking filters that couldn't be applied server-side
    deferred_filters = None

    try:
    # SECTION 3: METADATA RETRIEVAL AND FILTERING
        # Check if we're using cached download data
        if used_cached_download and cached_metadata_dict:
            logger.info("=" * 60)
            logger.info("STEP 3: Applying metadata filters for cached download")
            logger.info("=" * 60)
            logger.info("Using metadata from cached download (skipping API metadata fetch)")
            
            # cached_metadata_dict is now a file path (not a dict)
            # Use streaming filter to load only records passing filters into memory
            if isinstance(cached_metadata_dict, str) and os.path.isfile(cached_metadata_dict):
                logger.info("Memory-efficient path: streaming cached metadata JSONL with on-the-fly filtering")
                
                metadata_dict, total_api_records, cache_filter_stats = _stream_filter_cached_metadata_from_jsonl(
                    cached_metadata_dict,
                    host=host,
                    complete_only=(nuc_completeness == "complete"),
                    annotated=annotated,
                    lineage=lineage,
                    geographic_location=geographic_location,
                    refseq_only=refseq_only,
                    min_release_date=min_release_date,
                    applied_strategy_filters=applied_filters,
                )
                logger.info("Loaded %d records passing filters (from %d total in cache)", 
                           len(metadata_dict), total_api_records)
                
                # Copy the cached JSONL to the output API metadata location for consistency
                try:
                    shutil.copy(cached_metadata_dict, output_api_metadata_jsonl)
                    logger.info("✅ Saved cached metadata JSONL: %s", output_api_metadata_jsonl)
                except Exception as e:
                    logger.warning("❌ Failed to copy cached metadata JSONL: %s", e)
            else:
                # Fallback: cached_metadata_dict is already a dict (legacy path)
                metadata_dict = cached_metadata_dict
                total_api_records = len(metadata_dict)
                logger.info("Loaded %d metadata records from cached download", total_api_records)
                
                # Save metadata JSONL for consistency
                try:
                    with open(output_api_metadata_jsonl, "w", encoding="utf-8") as f:
                        for md in metadata_dict.values():
                            f.write(json.dumps(md) + "\n")
                    logger.info("✅ Saved cached metadata JSONL: %s", output_api_metadata_jsonl)
                except Exception as e:
                    logger.warning("❌ Failed to save cached metadata JSONL: %s", e)
                
                # Apply post-cached-download filters (legacy in-memory path)
                logger.debug("Using applied_filters from cached strategy: %s", applied_filters)
                filtered_accessions_step3, filtered_metadata_step3 = filter_cached_metadata_for_unused_filters(
                    metadata_dict,
                    host=host,
                    complete_only=(nuc_completeness == "complete"),
                    annotated=annotated,
                    lineage=lineage,
                    geographic_location=geographic_location,
                    refseq_only=refseq_only,
                    min_release_date=min_release_date,
                    applied_strategy_filters=applied_filters,
                )
                metadata_dict = {acc: md for acc, md in zip(filtered_accessions_step3, filtered_metadata_step3)}
            
            logger.info("After post-cached-download filtering: %d records remain", len(metadata_dict))
            
            # Baseline deduplication for cached path
            baseline_skipped_count = 0
            if baseline_accessions is not None and metadata_dict:
                logger.info("Deduplicating cached metadata against baseline (%d accessions)...", len(baseline_accessions))
                metadata_dict, baseline_skipped_count = _deduplicate_metadata_against_baseline(
                    metadata_dict, baseline_accessions
                )
                logger.info("After baseline deduplication: %d new records (skipped %d)", 
                           len(metadata_dict), baseline_skipped_count)
            
        else:
            # Regular API metadata fetch
            logger.info("=" * 60)
            logger.info("STEP 3: Fetching virus metadata from NCBI API")
            logger.info("=" * 60)
            api_annotated_filter = annotated if annotated is True else None
            api_complete_filter = True if nuc_completeness=="complete" else False

            logger.debug("Applying server-side filters: host=%s, geo_location=%s, annotated=%s, complete_only=%s, min_release_date=%s, refseq_only=%s", host, geographic_location, annotated, api_complete_filter, min_release_date, refseq_only)
            
            # Track deferred filters that couldn't be applied server-side
            deferred_filters = None
            
            try:
                # Check if this is a multi-accession query (list or file)
                use_batched_fetch = False
                if is_accession:
                    parsed_accessions = _parse_accession_input(virus)
                    if parsed_accessions['type'] in ('list', 'file'):
                        use_batched_fetch = True
                        accession_list = parsed_accessions['accessions']
                        logger.info("Detected %d accessions from %s input", 
                                   len(accession_list), parsed_accessions['type'])
                
                if use_batched_fetch:
                    # Multiple accessions - use batched fetching
                    api_result = _fetch_metadata_for_accession_list(
                        accessions=accession_list,
                        host=host,
                        geographic_location=geographic_location,
                        annotated=api_annotated_filter,
                        complete_only=api_complete_filter,
                        min_release_date=min_release_date,
                        refseq_only=refseq_only,
                        failed_commands=failed_commands,
                        temp_output_dir=temp_dir,
                    )
                    # Unpack tuple result
                    if isinstance(api_result, tuple):
                        api_reports, deferred_filters = api_result
                    else:
                        api_reports = api_result
                else:
                    # Single accession or taxon-based query - use standard fetch
                    api_result = fetch_virus_metadata(
                        virus,
                        accession=is_accession,
                        host=host,
                        geographic_location=geographic_location,
                        annotated=api_annotated_filter,
                        complete_only=api_complete_filter,
                        min_release_date=min_release_date,
                        refseq_only=refseq_only,
                        failed_commands=failed_commands,
                        temp_output_dir=temp_dir,
                    )
                    # Unpack tuple result
                    if isinstance(api_result, tuple):
                        api_reports, deferred_filters = api_result
                    else:
                        api_reports = api_result

                # If fetch_virus_metadata returns None, it means the dataset is too large
                # and we need to use the chunked download strategy
                if api_reports is None:
                    logger.info("Standard download failed due to dataset size - switching to chunked download")
                    api_result = fetch_virus_metadata_chunked(
                        virus,
                        accession=is_accession,
                        host=host,
                        geographic_location=geographic_location,
                        annotated=api_annotated_filter,
                        complete_only=api_complete_filter,
                        min_release_date=min_release_date,
                        max_release_date=max_release_date,
                        refseq_only=refseq_only,
                        failed_commands=failed_commands,
                        temp_output_dir=temp_dir,
                    )
                    # Unpack tuple result
                    if isinstance(api_result, tuple):
                        api_reports, deferred_filters = api_result
                    else:
                        api_reports = api_result
                
                # Log deferred filters if any
                if deferred_filters:
                    logger.info("=" * 60)
                    logger.info("⚠️ DEFERRED FILTERS: Some server-side filters could not be applied")
                    logger.info("   The following filters will be applied during metadata filtering:")
                    for filter_name, filter_value in deferred_filters.items():
                        logger.info("   - %s: %s", filter_name, filter_value)
                    logger.info("=" * 60)
            except RuntimeError as e:
                # Error has already been logged nicely by fetch_virus_metadata
                # Ensure output folder exists for summary file
                os.makedirs(outfolder, exist_ok=True)
                logger.debug("Ensured output folder exists for error summary: %s", outfolder)
                
                # Save partial metadata if any was collected before the failure
                # Check for streaming temp file from fetch_virus_metadata
                partial_metadata_dict = {}
                temp_metadata_glob = os.path.join(temp_dir, "gget_metadata_*.jsonl")
                import glob as _glob
                temp_metadata_files = _glob.glob(temp_metadata_glob)
                for tmf in temp_metadata_files:
                    try:
                        with open(tmf, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        record = json.loads(line)
                                        acc = record.get('accession', {})
                                        if isinstance(acc, dict):
                                            acc = acc.get('accession', '')
                                        if acc:
                                            partial_metadata_dict[str(acc)] = record
                                    except json.JSONDecodeError:
                                        continue
                    except Exception:
                        continue
                
                if partial_metadata_dict:
                    # Convert raw API reports to internal format
                    try:
                        partial_internal = load_metadata_from_api_reports(list(partial_metadata_dict.values()))
                    except Exception:
                        partial_internal = {acc: {'accession': acc} for acc in partial_metadata_dict}
                    
                    partial_metadata_file = _save_partial_metadata(partial_internal, outfolder, virus_clean, reason="api_failure")
                    if partial_metadata_file:
                        logger.info("=" * 60)
                        logger.info("💾 PARTIAL METADATA SAVED FOR RECOVERY")
                        logger.info("   File: %s", partial_metadata_file)
                        logger.info("   Records: %d", len(partial_internal))
                        logger.info("")
                        logger.info("   Recovery command:")
                        logger.info("   gget virus %s --baseline %s --merge-results -o %s", 
                                   virus, partial_metadata_file, outfolder)
                        logger.info("=" * 60)
                
                # Save a summary file documenting the failure, then exit gracefully
                logger.error("Failed to fetch virus metadata from NCBI API")
                save_command_summary(
                    outfolder=outfolder,
                    command_line=command_line,
                    total_api_records=len(partial_metadata_dict) if partial_metadata_dict else 0,
                    total_after_metadata_filter=0,
                    total_final_sequences=0,
                    output_files={},
                    filtered_metadata=[],
                    datasets_version=datasets_version,
                    success=False,
                    error_message=str(e),
                    failed_commands=failed_commands,
                    partial_metadata_file=partial_metadata_file if partial_metadata_dict else None,
                    recovery_command=f"gget virus {virus} --baseline {partial_metadata_file} --merge-results -o {outfolder}" if partial_metadata_dict and partial_metadata_file else None,
                )
                return None

            if not api_reports:
                logger.warning("No virus records found matching the specified criteria.")
                logger.info("Consider relaxing your filter criteria or checking your virus identifier.")
                # Save command summary documenting zero results
                save_command_summary(
                    outfolder=outfolder,
                    command_line=command_line,
                    total_api_records=0,
                    total_after_metadata_filter=0,
                    total_final_sequences=0,
                    output_files={},
                    filtered_metadata=[],
                    datasets_version=datasets_version,
                    success=True,
                    error_message="No virus records found matching the specified criteria (API returned 0 records)",
                    failed_commands=failed_commands
                )
                return

            # Convert API metadata to internal format
            # api_reports can be either:
            #   - A string (file path to JSONL) when streaming was used for large datasets
            #   - A list of report dicts for smaller/accession-based queries
            _log_memory_usage("after API fetch")
            logger.debug("Converting API metadata to internal format...")
            
            if isinstance(api_reports, str) and os.path.isfile(api_reports):
                # Stream from temp JSONL file - avoids loading raw API reports into RAM
                logger.info("Loading metadata from streamed temp file (memory-efficient path)...")
                metadata_dict = _load_metadata_dict_from_temp_jsonl(api_reports)
                total_api_records = len(metadata_dict)
                # Check if file was actually empty
                if not metadata_dict:
                    logger.warning("No virus records found matching the specified criteria.")
                    logger.info("Consider relaxing your filter criteria or checking your virus identifier.")
                    save_command_summary(
                        outfolder=outfolder,
                        command_line=command_line,
                        total_api_records=0,
                        total_after_metadata_filter=0,
                        total_final_sequences=0,
                        output_files={},
                        filtered_metadata=[],
                        datasets_version=datasets_version,
                        success=True,
                        error_message="No virus records found matching the specified criteria (API returned 0 records)",
                        failed_commands=failed_commands
                    )
                    return
            else:
                # api_reports is a list (accession-based or small queries)
                total_api_records = len(api_reports)
                metadata_dict = load_metadata_from_api_reports(api_reports)
                # Delete api_reports after conversion - no longer needed
                del api_reports
            
            _force_garbage_collection("after api_reports conversion")
            _log_memory_usage("after api_reports cleanup")

            # Save the raw API metadata (server-side filtered) before local filtering
            logger.debug("Writing API metadata to JSONL file: %s", output_api_metadata_jsonl)
            try:
                with open(output_api_metadata_jsonl, "w", encoding="utf-8") as f:
                    for md in metadata_dict.values():
                        f.write(json.dumps(md) + "\n")
                logger.info("✅ Saved API metadata JSONL: %s", output_api_metadata_jsonl)
            except Exception as e:
                logger.warning("❌ Failed to save API metadata JSONL: %s", e)

    # SECTION 3b: BASELINE DEDUPLICATION
        # If baseline accessions were loaded, remove them from the metadata
        baseline_skipped_count = 0
        if baseline_accessions is not None and metadata_dict:
            logger.info("=" * 60)
            logger.info("STEP 3b: DEDUPLICATING AGAINST BASELINE")
            logger.info("=" * 60)
            logger.info("API returned %d records. Comparing against %d baseline accessions...",
                        len(metadata_dict), len(baseline_accessions))
            
            metadata_dict, baseline_skipped_count = _deduplicate_metadata_against_baseline(
                metadata_dict, baseline_accessions
            )
            
            logger.info("Deduplication complete:")
            logger.info("  - Total from API: %d", total_api_records)
            logger.info("  - Already in baseline (skipped): %d", baseline_skipped_count)
            logger.info("  - New accessions to process: %d", len(metadata_dict))
            
            if not metadata_dict:
                logger.warning("All API records already exist in the baseline file.")
                logger.info("No new sequences to download.")
                
                if merge_results and baseline_metadata:
                    # Copy baseline to output as the merged result
                    merged_output = os.path.join(outfolder, f"{virus_clean}_merged.csv")
                    import shutil as _shutil
                    _shutil.copy2(baseline_metadata, merged_output)
                    logger.info("✅ Baseline copied as merged output: %s", merged_output)
                    output_files_dict['Merged Metadata'] = merged_output
                
                save_command_summary(
                    outfolder=outfolder,
                    command_line=command_line,
                    total_api_records=total_api_records,
                    total_after_metadata_filter=0,
                    total_final_sequences=0,
                    output_files=output_files_dict,
                    filtered_metadata=[],
                    datasets_version=datasets_version,
                    success=True,
                    error_message="All records already exist in baseline (0 new sequences)",
                    failed_commands=failed_commands,
                    baseline_file=baseline_metadata,
                    baseline_accession_count=len(baseline_accessions),
                    baseline_skipped_count=baseline_skipped_count,
                )
                return

    # SECTION 4: METADATA-ONLY FILTERING
        logger.info("=" * 60)
        logger.info("STEP 4: Applying metadata-only filters")
        logger.info("=" * 60)

        filters = {
            "min_seq_length": min_seq_length,
            "max_seq_length": max_seq_length,
            # "min_gene_count": min_gene_count,
            # "max_gene_count": max_gene_count,
            "nuc_completeness": nuc_completeness if nuc_completeness and nuc_completeness.lower() == 'partial' else None, #only for partial cases
            "lab_passaged": lab_passaged,
            "submitter_country": submitter_country,
            "min_collection_date": min_collection_date,
            "max_collection_date": max_collection_date,
            "source_database": source_database if source_database and source_database.lower() == 'genbank' else None,
            "max_release_date": max_release_date,
            # "min_mature_peptide_count": min_mature_peptide_count,
            # "max_mature_peptide_count": max_mature_peptide_count,
            "min_protein_count": min_protein_count,
            "max_protein_count": max_protein_count,
            # annotated=False needs client-side filtering (annotated=True is handled server-side)
            "annotated": annotated if annotated is False else None,
            "segment": segment,
            "vaccine_strain": vaccine_strain,
            "submitter_name": submitter_name,
            "submitter_institution": submitter_institution,
            "isolate": isolate,
            "isolation_source": isolation_source,
            # Add deferred filters if server-side filter failed
            "geographic_location": deferred_filters.get('geographic_location') if deferred_filters else None,
            "host": deferred_filters.get('host') if deferred_filters else None,
        }

        all_metadata_filters_none = all(v is None for k, v in filters.items())

        # Prepare output file paths (defined early for use in cleanup even if filters return early)
        output_fasta_file = os.path.join(outfolder, f"{virus_clean}_sequences.fasta")
        output_metadata_csv = os.path.join(outfolder, f"{virus_clean}_metadata.csv")
        output_metadata_jsonl = os.path.join(outfolder, f"{virus_clean}_metadata.jsonl")

        if all_metadata_filters_none:
            logger.info("No metadata-only filters specified, skipping this step.")
            filtered_accessions = list(metadata_dict.keys())
            filtered_metadata = list(metadata_dict.values())
            logger.info("All %d sequences will proceed to sequence download", len(filtered_accessions))
        else:
            filtered_accessions, filtered_metadata, metadata_filter_stats = filter_metadata_only(metadata_dict, **filters)
            if not filtered_accessions:
                pass  # No sequences passed metadata filters
                total_after_metadata_filter = 0
                total_final_sequences = 0
                # Save command summary even if no sequences passed filters
                save_command_summary(
                    outfolder=outfolder,
                    command_line=command_line,
                    total_api_records=total_api_records,
                    total_after_metadata_filter=0,
                    total_final_sequences=0,
                    output_files=output_files_dict,
                    filtered_metadata=[],
                    datasets_version=datasets_version,
                    success=True,
                    error_message="No sequences passed the metadata filters",
                    failed_commands=failed_commands,
                    runtime_seconds=time.time() - _virus_start_time,
                    memory_info=_get_memory_usage(),
                    metadata_filter_stats=metadata_filter_stats,
                )
                return
        
        total_after_metadata_filter = len(filtered_accessions)
        _log_memory_usage("after metadata filtering")

        # Save filtered metadata immediately (before sequence-dependent fields)
        logger.debug("Writing filtered metadata (pre-sequence) to JSONL: %s", output_metadata_jsonl)
        try:
            with open(output_metadata_jsonl, "w", encoding="utf-8") as f:
                for md in filtered_metadata:
                    f.write(json.dumps(md) + "\n")
            logger.info("✅ Saved filtered metadata JSONL: %s", output_metadata_jsonl)
        except Exception as e:
            logger.warning("❌ Failed to save filtered metadata JSONL: %s", e)

    # SECTION 4.5: EARLY GENBANK METADATA FETCHING AND FILTERING
    # This step fetches GenBank metadata and applies GenBank-dependent filters BEFORE downloading sequences, dramatically reducing the number of sequences to download.
        
        # Track GenBank data for later steps (saving to CSV)
        genbank_data_prefetch = None
        genbank_prefetch_done = False
        
        # Check if any GenBank-dependent filters are specified
        genbank_dependent_filters_active = any([
            provirus is not None,
            genotype is not None,
            has_proteins is not None,
            gen_mol_type is not None,
            env_source is not None,
            min_gene_count is not None,
            max_gene_count is not None,
            min_mature_peptide_count is not None,
            max_mature_peptide_count is not None,
        ])
        
        if genbank_dependent_filters_active and filtered_accessions:
            logger.info("=" * 60)
            logger.info("STEP 4.5: Early GenBank metadata fetch and filtering (OPTIMIZATION)")
            logger.info("=" * 60)
            logger.info("GenBank-dependent filters detected. Fetching GenBank metadata BEFORE")
            logger.info("sequence download to reduce the number of sequences to download.")
            logger.info("This can dramatically speed up processing for large datasets.")
            _log_memory_usage("before early GenBank fetch")
            
            try:
                # Create temp paths for GenBank data
                genbank_prefetch_xml = os.path.join(temp_dir, f"{virus_clean}_genbank_prefetch.xml")
                genbank_prefetch_csv = os.path.join(temp_dir, f"{virus_clean}_genbank_prefetch.csv")
            
                # ESearch pre-filtering
                accessions_to_fetch = list(set(filtered_accessions))
                
                # Get virus taxid from metadata for ESearch query
                virus_taxid_for_esearch = None
                if filtered_metadata:
                    virus_taxid_for_esearch = filtered_metadata[0].get('virusTaxId')
                    if not virus_taxid_for_esearch:
                        # Try to get from nested virus dict
                        virus_dict = filtered_metadata[0].get('virus', {})
                        if isinstance(virus_dict, dict):
                            virus_taxid_for_esearch = virus_dict.get('tax_id')
                
                # Only attempt ESearch pre-filtering if we have enough accessions
                # to make it worthwhile (>1000) and we have GenBank-dependent filters
                esearch_prefilter_threshold = 1000
                if len(accessions_to_fetch) > esearch_prefilter_threshold and virus_taxid_for_esearch:
                    logger.info("=" * 60)
                    logger.info("ESearch PRE-FILTERING: Narrowing %d accessions to likely candidates",
                               len(accessions_to_fetch))
                    logger.info("This avoids fetching full GenBank XML for all %d accessions",
                               len(accessions_to_fetch))
                    logger.info("=" * 60)
                    
                    esearch_candidates = _esearch_prefilter_genbank(
                        virus_taxid=virus_taxid_for_esearch,
                        metadata_filtered_accessions=accessions_to_fetch,
                        provirus=provirus,
                        has_proteins=has_proteins,
                        genotype=genotype,
                        gen_mol_type=gen_mol_type,
                        min_seq_length=min_seq_length,
                        max_seq_length=max_seq_length,
                        api_key=api_key,
                    )
                    
                    if esearch_candidates is not None:
                        if len(esearch_candidates) == 0:
                            # ESearch says NO accessions match
                            logger.warning("ESearch pre-filter: NO accessions match GenBank criteria.")
                            logger.warning("No sequences will pass the GenBank-based filters.")
                            filtered_accessions = []
                            filtered_metadata = []
                            genbank_data_prefetch = {}
                            
                            save_command_summary(
                                outfolder=outfolder,
                                command_line=command_line,
                                total_api_records=total_api_records,
                                total_after_metadata_filter=total_after_metadata_filter,
                                total_final_sequences=0,
                                output_files=output_files_dict,
                                filtered_metadata=[],
                                datasets_version=datasets_version,
                                success=True,
                                error_message="ESearch pre-filter: No accessions match GenBank criteria (provirus/has_proteins/genotype)",
                                failed_commands=failed_commands,
                                runtime_seconds=time.time() - _virus_start_time,
                                memory_info=_get_memory_usage(),
                                metadata_filter_stats=metadata_filter_stats,
                                genbank_filter_stats={},
                                total_after_genbank_filter=0,
                            )
                            if not keep_temp and os.path.isdir(temp_dir):
                                try:
                                    shutil.rmtree(temp_dir)
                                except Exception:
                                    pass
                            return
                        else:
                            # Narrow to only the candidates
                            accessions_to_fetch = list(esearch_candidates)
                            logger.info("✅ ESearch pre-filter successful: narrowed from %d to %d accessions",
                                       len(filtered_accessions), len(accessions_to_fetch))
                    else:
                        logger.info("ESearch pre-filter: could not pre-filter, using full accession list")
                
                logger.info("Fetching GenBank metadata for %d accessions...", len(accessions_to_fetch))
                
                # Fetch GenBank metadata
                genbank_data_prefetch, genbank_failed_log = fetch_genbank_metadata(
                    accessions=accessions_to_fetch,
                    genbank_full_xml_path=genbank_prefetch_xml,
                    genbank_full_csv_path=genbank_prefetch_csv,
                    batch_size=genbank_batch_size,
                    delay=GENBANK_INTER_BATCH_DELAY,
                    api_key=api_key
                )
                
                if genbank_data_prefetch:
                    genbank_prefetch_done = True
                    logger.info("Successfully retrieved GenBank metadata for %d accessions", len(genbank_data_prefetch))
                    _log_memory_usage("after early GenBank fetch")
                    
                    # Apply GenBank-dependent filters
                    logger.info("Applying GenBank-dependent filters...")
                    filters_genbank_early = {
                        "provirus": provirus,
                        "has_proteins": has_proteins,
                        "genotype": genotype,
                        "gen_mol_type": gen_mol_type,
                        "env_source": env_source,
                        "min_gene_count": min_gene_count,
                        "max_gene_count": max_gene_count,
                        "min_mature_peptide_count": min_mature_peptide_count,
                        "max_mature_peptide_count": max_mature_peptide_count,
                    }
                    
                    genbank_filtered_accessions_early, genbank_filter_stats = filter_genbank_metadata(
                        genbank_metadata=genbank_data_prefetch,
                        **filters_genbank_early,
                    )
                    
                    if genbank_filtered_accessions_early:
                        # Calculate reduction
                        before_count = len(filtered_accessions)
                        after_count = len(genbank_filtered_accessions_early)
                        reduction_pct = ((before_count - after_count) / before_count) * 100 if before_count > 0 else 0
                        
                        logger.info("=" * 60)
                        logger.info("🎯 EARLY GENBANK FILTERING RESULTS:")
                        logger.info("   Before GenBank filters: %d accessions", before_count)
                        logger.info("   After GenBank filters:  %d accessions", after_count)
                        logger.info("   Reduction: %.1f%% (%d accessions filtered out)", reduction_pct, before_count - after_count)
                        logger.info("   This means we'll download %d sequences instead of %d!", after_count, before_count)
                        logger.info("=" * 60)
                        
                        # Update filtered_accessions and filtered_metadata
                        genbank_filtered_set_early = set(genbank_filtered_accessions_early)
                        filtered_accessions = [acc for acc in filtered_accessions if acc in genbank_filtered_set_early]
                        filtered_metadata = [md for md in filtered_metadata if md['accession'] in genbank_filtered_set_early]
                        
                        # Also filter genbank_data_prefetch to only include passing accessions
                        genbank_data_prefetch = {acc: genbank_data_prefetch[acc] for acc in genbank_filtered_accessions_early if acc in genbank_data_prefetch}
                        
                        # Update total_after_metadata_filter to reflect GenBank filtering
                        # Note: This is now total after BOTH metadata + GenBank filtering
                        total_after_genbank_filter = len(filtered_accessions)
                        
                        _force_garbage_collection("after early GenBank filtering")
                        _log_memory_usage("after early GenBank filtering cleanup")
                    else:
                        logger.warning("No sequences passed the GenBank-based filters.")
                        # Clear outputs - no sequences to process
                        filtered_accessions = []
                        filtered_metadata = []
                        genbank_data_prefetch = {}
                        
                        # Save command summary and return early
                        save_command_summary(
                            outfolder=outfolder,
                            command_line=command_line,
                            total_api_records=total_api_records,
                            total_after_metadata_filter=total_after_metadata_filter,
                            total_final_sequences=0,
                            output_files=output_files_dict,
                            filtered_metadata=[],
                            datasets_version=datasets_version,
                            success=True,
                            error_message="No sequences passed the GenBank-based filters (provirus/has_proteins/genotype/etc.)",
                            failed_commands=failed_commands,
                            runtime_seconds=time.time() - _virus_start_time,
                            memory_info=_get_memory_usage(),
                            metadata_filter_stats=metadata_filter_stats,
                            genbank_filter_stats=genbank_filter_stats,
                            total_after_genbank_filter=0,
                        )
                        # Cleanup before return
                        if not keep_temp and os.path.isdir(temp_dir):
                            try:
                                shutil.rmtree(temp_dir)
                            except Exception:
                                pass
                        return
                else:
                    logger.warning("Failed to retrieve GenBank metadata. Proceeding without early filtering.")
                    logger.warning("GenBank-dependent filters will be applied after sequence download (slower).")
                    genbank_prefetch_done = False
                    
            except Exception as e:
                logger.warning("Early GenBank fetch failed: %s", e)
                logger.warning("Proceeding without early GenBank filtering. Filters will be applied after sequence download.")
                genbank_prefetch_done = False
                genbank_data_prefetch = None

    # SECTION 5: DOWNLOAD SEQUENCES FOR FILTERED ACCESSIONS ONLY
        logger.info("=" * 60)
        logger.info("STEP 5: Downloading sequences for filtered accessions")
        logger.info("=" * 60)

        # Check if we're using cached sequences
        if used_cached_download and cached_fasta_file:
            logger.info("Using sequences from cached download (skipping sequence download)")
            logger.info("Streaming and filtering cached FASTA file on-demand...")
            
            # Create filtered accessions set for faster lookup
            filtered_acc_set = set(filtered_accessions)
            
            # Stream through cached FASTA and write only filtered sequences
            # This avoids loading the entire file into RAM
            fna_file = os.path.join(temp_dir, f"{virus_clean}_cached_sequences.fasta")
            filtered_count = 0
            
            try:
                # Generator expression: yields only sequences in filtered_accessions
                filtered_records = (r for r in FastaIO.parse(cached_fasta_file, "fasta") if r.id in filtered_acc_set)
                FastaIO.write(filtered_records, fna_file, "fasta")
                
                # Count the written sequences
                for _ in FastaIO.parse(fna_file, "fasta"):
                    filtered_count += 1
                
                logger.info("✅ Streamed and wrote %d filtered sequences from cached FASTA", filtered_count)
                logger.info("   Output: %s", fna_file)
            except Exception as e:
                logger.error("❌ Failed to filter and write cached FASTA: %s", e)
                raise RuntimeError(f"Failed to process cached FASTA file: {e}") from e
        else:
            # Regular sequence download
            fna_file = download_sequences_by_accessions(filtered_accessions, outdir=temp_dir, failed_commands=failed_commands, api_key=api_key)
            if not os.path.exists(fna_file):
                raise RuntimeError(f"❌ Download failed: FASTA file not found at {fna_file}")
            logger.info("Downloaded FASTA file: %s (%.2f MB)", fna_file, os.path.getsize(fna_file) / 1024 / 1024)

    # SECTION 6: SEQUENCE-DEPENDENT FILTERING
        logger.info("=" * 60)
        logger.info("STEP 6: Applying sequence-dependent filters and saving results")
        logger.info("=" * 60)

        filters_seq={
            "max_ambiguous_chars": max_ambiguous_chars,
            # "has_proteins": has_proteins,
            "proteins_complete": proteins_complete,
        }

        if filters_seq["max_ambiguous_chars"] is None and not filters_seq["proteins_complete"]:
            logger.info("No sequence-dependent filters specified, skipping this step.")
            # Stream-copy FASTA directly to output instead of loading all into RAM
            # For large datasets (millions of sequences), this avoids OOM errors
            total_final_sequences = _stream_copy_fasta(fna_file, output_fasta_file)
            filtered_metadata_final = filtered_metadata  # No change to metadata
            protein_headers = []
            logger.info("All %d downloaded sequences were streamed to output", total_final_sequences)
            _log_memory_usage("after streaming sequences to output")
        else:
            # Restrict metadata to filtered accessions only
            filtered_metadata_dict = {acc: metadata_dict[acc] for acc in filtered_accessions}

            # Stream filtered sequences directly to output file
            # instead of accumulating them in a list in RAM
            total_final_sequences, filtered_metadata_final, protein_headers, sequence_filter_stats = filter_sequences(
                fna_file,
                filtered_metadata_dict,
                output_fasta_path=output_fasta_file,
                **filters_seq,
            )
            # Clean up filtered_metadata_dict after use
            del filtered_metadata_dict
        
        # metadata_dict is no longer needed after this point
        # filtered_metadata_final and filtered_accessions contain all we need
        try:
            del metadata_dict
        except NameError:
            pass  # Already deleted in some code paths
        _force_garbage_collection("after sequence filtering")
        _log_memory_usage("after sequence filtering cleanup")

    # SECTION 7: SAVING FINAL OUTPUT FILES
        logger.info("=" * 60)
        logger.info("STEP 7: Saving final output files")
        logger.info("=" * 60)
        if total_final_sequences > 0:
            logger.info("Saving metadata for %d filtered sequences...", total_final_sequences)

            # FASTA was already written during Section 6 (streaming to output_fasta_file)
            if os.path.exists(output_fasta_file):
                logger.info("✅ FASTA file saved: %s (%.2f MB)", output_fasta_file, os.path.getsize(output_fasta_file) / 1024 / 1024)
                output_files_dict['FASTA Sequences'] = output_fasta_file
            else:
                logger.error("❌ FASTA file not found at expected location: %s", output_fasta_file)
            
            # Track final metadata for summary
            final_metadata_for_summary = filtered_metadata_final

            # Overwrite JSONL with final filtered metadata (includes only sequences that passed all filters)
            try:
                with open(output_metadata_jsonl, "w", encoding="utf-8") as file:
                    for metadata in filtered_metadata_final:
                        file.write(json.dumps(metadata) + "\n")
                logger.info("✅ JSONL metadata file saved: %s (%.2f MB)", output_metadata_jsonl, os.path.getsize(output_metadata_jsonl) / 1024 / 1024)
                output_files_dict['JSONL Metadata'] = output_metadata_jsonl
            except Exception as e:
                logger.error("❌ Failed to save JSONL metadata file: %s", e)
                raise

            # CSV
            try:
                save_metadata_to_csv(filtered_metadata_final, protein_headers, output_metadata_csv)
                if os.path.exists(output_metadata_csv):
                    logger.info("✅ CSV metadata file saved: %s (%.2f MB)", output_metadata_csv, os.path.getsize(output_metadata_csv) / 1024 / 1024)
                    output_files_dict['CSV Metadata'] = output_metadata_csv
                else:
                    logger.error("❌ Failed to create CSV file: %s", output_metadata_csv)
            except Exception as e:
                logger.error("❌ Failed to save CSV metadata file: %s", e)
                raise
            
            # SECTION 7b: BASELINE MERGE/NO-MERGE OUTPUT
            if baseline_accessions is not None and baseline_metadata:
                logger.info("=" * 60)
                logger.info("STEP 7b: Baseline merge/split output")
                logger.info("=" * 60)
                
                if merge_results:
                    # Merge new results with baseline into a single file
                    merged_csv_path = os.path.join(outfolder, f"{virus_clean}_merged.csv")
                    merge_success = _merge_baseline_with_new(
                        baseline_metadata, filtered_metadata_final, merged_csv_path
                    )
                    if merge_success:
                        output_files_dict['Merged Metadata (CSV)'] = merged_csv_path
                        logger.info("✅ Merged CSV: %s", merged_csv_path)
                    else:
                        logger.warning("⚠️ Merge failed. New-only output is available at: %s", output_metadata_csv)
                else:
                    # No-merge mode: label the new-only output clearly
                    new_csv_path = os.path.join(outfolder, f"{virus_clean}_new.csv")
                    baseline_ref_path = os.path.join(outfolder, f"{virus_clean}_baseline_provided.csv")
                    
                    # Rename existing CSV to _new
                    if os.path.exists(output_metadata_csv):
                        shutil.copy2(output_metadata_csv, new_csv_path)
                        output_files_dict['New Metadata (CSV)'] = new_csv_path
                        logger.info("✅ New-only CSV: %s (%d sequences)", new_csv_path, len(filtered_metadata_final))
                    
                    # Copy baseline as reference
                    shutil.copy2(baseline_metadata, baseline_ref_path)
                    output_files_dict['Baseline Provided (CSV)'] = baseline_ref_path
                    logger.info("✅ Baseline reference: %s", baseline_ref_path)

        else:
            logger.info("Skipping this step since no sequences passed all filters")
        
        # Clean up before GenBank fetch
        # filtered_metadata_final contains all we need - clear other references
        # Note: filtered_metadata may still reference same objects, but that's okay
        _force_garbage_collection("before GenBank fetch")

    # SECTION 8: GENBANK METADATA RETRIEVAL (OPTIONAL)
        logger.info("=" * 60)
        logger.info("STEP 8: Fetching detailed GenBank metadata")
        logger.info("=" * 60)
        _log_memory_usage("STEP 8 start")
        if genbank_metadata and total_final_sequences > 0:
            logger.info("GenBank metadata retrieval requested...")
            
            # Check if we already have GenBank data from early pre-fetch (Step 4.5)
            if genbank_prefetch_done and genbank_data_prefetch:
                logger.info("Using pre-fetched GenBank data from Step 4.5 (no re-fetch needed)")
                genbank_data = genbank_data_prefetch
                
                # Save GenBank metadata to final output location
                try:
                    # Copy temp XML to final location if it exists
                    genbank_prefetch_xml = os.path.join(temp_dir, f"{virus_clean}_genbank_prefetch.xml")
                    genbank_prefetch_csv = os.path.join(temp_dir, f"{virus_clean}_genbank_prefetch.csv")
                    
                    if os.path.exists(genbank_prefetch_xml):
                        shutil.copy(genbank_prefetch_xml, genbank_full_xml_path)
                    if os.path.exists(genbank_prefetch_csv):
                        shutil.copy(genbank_prefetch_csv, genbank_full_csv_path)
                    
                    # Save GenBank metadata to CSV
                    save_genbank_metadata_to_csv(
                        genbank_metadata=genbank_data,
                        output_file=genbank_csv_path,
                        virus_metadata=filtered_metadata_final
                    )
                    logger.info("✅ GenBank metadata CSV saved: %s (%.2f MB)", 
                                genbank_csv_path, os.path.getsize(genbank_csv_path) / 1024 / 1024)
                    
                    # Merge with standard metadata CSV if it exists
                    if os.path.exists(output_metadata_csv):
                        merge_metadata_csvs(genbank_csv_path, output_metadata_csv)
                    
                    output_files_dict['GenBank CSV Metadata'] = genbank_csv_path
                    if os.path.exists(genbank_full_xml_path):
                        output_files_dict['GenBank Full XML'] = genbank_full_xml_path
                    if os.path.exists(genbank_full_csv_path):
                        output_files_dict['GenBank Full CSV'] = genbank_full_csv_path
                    genbank_success = True
                    
                except Exception as e:
                    logger.error("❌ Failed to save pre-fetched GenBank data: %s", e)
                    genbank_error_msg = str(e)
            else:
                # No pre-fetch available - fetch GenBank data now
                logger.info("Fetching GenBank metadata (no pre-fetch available)...")
                try:
                    # Use filtered_accessions (from metadata) instead of iterating
                    # in-memory sequences - avoids loading all sequences into RAM
                    final_accessions = list(filtered_accessions)
                    
                    if final_accessions:
                        logger.info("Fetching GenBank metadata for %d sequences...", len(final_accessions))

                        # Fetch GenBank metadata
                        genbank_data, genbank_failed_log = fetch_genbank_metadata(
                            accessions=list(set(final_accessions)),  # Remove duplicates
                            genbank_full_xml_path=genbank_full_xml_path, genbank_full_csv_path=genbank_full_csv_path,
                            batch_size=genbank_batch_size,
                            delay=GENBANK_INTER_BATCH_DELAY,
                            api_key=api_key
                        )
                        
                        # Parse GenBank failed batches log if it exists
                        if genbank_failed_log and os.path.exists(genbank_failed_log):
                            try:
                                with open(genbank_failed_log, 'r') as flog:
                                    content = flog.read()
                                    # Parse the log file to extract failed batch information
                                    batch_pattern = r'FAILED_BATCH: \[([^\]]+)\][\s\S]*?URL: ([^\n]+)'
                                    matches = re.findall(batch_pattern, content)
                                    for accessions_str, url in matches:
                                        # Clean up accessions string
                                        batch_accessions = [acc.strip().strip("'").strip('"') for acc in accessions_str.split(',')]
                                        failed_commands['genbank_batches'].append({
                                            'accessions': batch_accessions,
                                            'retry_url': url.strip()
                                        })
                            except Exception as parse_error:
                                logger.debug("Could not parse GenBank failed batches log: %s", parse_error)
                        
                        if genbank_data and not genbank_dependent_filters_active:
                            # No GenBank filters - just save the data
                            save_genbank_metadata_to_csv(
                                genbank_metadata=genbank_data,
                                output_file=genbank_csv_path,
                                virus_metadata=filtered_metadata_final
                            )
                            logger.info("✅ GenBank metadata CSV saved: %s (%.2f MB)", 
                                        genbank_csv_path, os.path.getsize(genbank_csv_path) / 1024 / 1024)
                            
                            # Merge with standard metadata CSV if it exists
                            if os.path.exists(output_metadata_csv):
                                merge_metadata_csvs(genbank_csv_path, output_metadata_csv)
                            
                            output_files_dict['GenBank CSV Metadata'] = genbank_csv_path
                            if os.path.exists(genbank_full_xml_path):
                                output_files_dict['GenBank Full XML'] = genbank_full_xml_path
                            if os.path.exists(genbank_full_csv_path):
                                output_files_dict['GenBank Full CSV'] = genbank_full_csv_path
                            genbank_success = True
                        elif genbank_data and genbank_dependent_filters_active:
                            # GenBank filters needed - this is the fallback path when pre-fetch failed
                            logger.info("GenBank metadata retrieved. Applying filters (fallback path)...")
                            _log_memory_usage("before fallback GenBank filtering")
                            _force_garbage_collection("before fallback filtering")
                            
                            filters_genbank={
                                "provirus": provirus,
                                "has_proteins": has_proteins,
                                "genotype": genotype,
                                "gen_mol_type": gen_mol_type,
                                "env_source": env_source,
                                "min_gene_count": min_gene_count,
                                "max_gene_count": max_gene_count,
                                "min_mature_peptide_count": min_mature_peptide_count,
                                "max_mature_peptide_count": max_mature_peptide_count,
                            }

                            try:
                                genbank_filtered_accessions, genbank_filter_stats = filter_genbank_metadata(
                                    genbank_metadata=genbank_data,
                                    **filters_genbank,
                                )

                                if genbank_filtered_accessions:
                                    logger.info("After applying GenBank-based filters, %d sequences remain", len(genbank_filtered_accessions))
                                    
                                    genbank_filtered_set = set(genbank_filtered_accessions)
                                    total_after_genbank_filter = len(genbank_filtered_accessions)
                                    # Re-filter FASTA by streaming from output
                                    # file through accession filter, instead of holding all sequences in RAM
                                    temp_refiltered_fasta = output_fasta_file + ".tmp"
                                    refiltered_count = _stream_copy_fasta(output_fasta_file, temp_refiltered_fasta, genbank_filtered_set)
                                    shutil.move(temp_refiltered_fasta, output_fasta_file)
                                    total_final_sequences = refiltered_count
                                    
                                    filtered_metadata_final = [md for md in filtered_metadata_final if md['accession'] in genbank_filtered_set]
                                    genbank_data_filtered = {acc: genbank_data[acc] for acc in genbank_filtered_accessions if acc in genbank_data}
                                    
                                    del genbank_data
                                    _force_garbage_collection("after fallback GenBank filtering")

                                    save_metadata_to_csv(filtered_metadata_final, protein_headers, output_metadata_csv)
                                    
                                    try:
                                        with open(output_metadata_jsonl, "w", encoding="utf-8") as f:
                                            for md in filtered_metadata_final:
                                                f.write(json.dumps(md) + "\n")
                                    except Exception as e:
                                        logger.warning("❌ Failed to update JSONL metadata file: %s", e)
                                    
                                    save_genbank_metadata_to_csv(
                                        genbank_metadata=genbank_data_filtered,
                                        output_file=genbank_csv_path,
                                        virus_metadata=filtered_metadata_final
                                    )
                                    logger.info("✅ GenBank metadata CSV saved: %s (%.2f MB)", 
                                                genbank_csv_path, os.path.getsize(genbank_csv_path) / 1024 / 1024)
                                    
                                    if os.path.exists(output_metadata_csv):
                                        merge_metadata_csvs(genbank_csv_path, output_metadata_csv)
                                    
                                    output_files_dict['FASTA Sequences'] = output_fasta_file
                                    output_files_dict['CSV Metadata'] = output_metadata_csv
                                    output_files_dict['GenBank CSV Metadata'] = genbank_csv_path
                                    if os.path.exists(genbank_full_xml_path):
                                        output_files_dict['GenBank Full XML'] = genbank_full_xml_path
                                    if os.path.exists(genbank_full_csv_path):
                                        output_files_dict['GenBank Full CSV'] = genbank_full_csv_path

                                    final_metadata_for_summary = filtered_metadata_final
                                    genbank_success = True
                                    
                                    del genbank_data_filtered
                                    del genbank_filtered_accessions
                                    del genbank_filtered_set
                                else:
                                    logger.warning("No sequences passed the GenBank-based filters.")
                                    del genbank_data
                                    filtered_metadata_final = []
                                    total_final_sequences = 0
                                    if os.path.exists(output_fasta_file):
                                        os.remove(output_fasta_file)
                                    if os.path.exists(output_metadata_csv):
                                        os.remove(output_metadata_csv)
                                    if os.path.exists(output_metadata_jsonl):
                                        os.remove(output_metadata_jsonl)
                            except Exception as e:
                                logger.error("❌ Failed to apply GenBank-based filters: %s", e)
                                logger.warning("Continuing with previously filtered results without GenBank-based filtering.")
                        else:
                            logger.warning("No GenBank metadata was retrieved")
                            genbank_error_msg = "No GenBank metadata was retrieved"
                    else:
                        logger.warning("No accession numbers found for GenBank metadata lookup")
                        genbank_error_msg = "No accession numbers found for GenBank metadata lookup"
                        
                except Exception as genbank_error:
                    logger.error("❌ GenBank metadata retrieval failed: %s", genbank_error)
                    logger.warning("Continuing without GenBank metadata - standard output files are still available")
                    genbank_error_msg = str(genbank_error)
            
            _log_memory_usage("GenBank processing complete")
            _force_garbage_collection("after GenBank processing")
            logger.info("GenBank metadata processing completed")
        else:
            logger.info("Skipping this step since GenBank metadata retrieval was not requested.")

    # SECTION 9: FINAL SUMMARY
        # Provide comprehensive summary of the results
        if total_final_sequences > 0:
            logger.info("=" * 60)
            logger.info("PROCESS COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info("Results summary:")
            logger.info("  Total sequences (API metadata): %d", total_api_records)
            logger.info("  After metadata-only filtering: %d", len(filtered_accessions))
            logger.info("  After all filters (final): %d", total_final_sequences)
            logger.info("")
            logger.info("Output files saved to: %s", outfolder)
            logger.info("  📄 Sequences (FASTA): %s", os.path.basename(output_fasta_file))
            if not os.path.exists(genbank_csv_path):
                logger.info("  📊 Metadata (CSV):    %s", os.path.basename(output_metadata_csv))
            logger.info("  🔧 Metadata (JSONL):  %s", os.path.basename(output_metadata_jsonl))

            # Check if GenBank metadata CSV was created
            if genbank_metadata:
                if genbank_success and os.path.exists(genbank_csv_path):
                    logger.info("  📊 Metadata (including Genbank information):  %s", os.path.basename(genbank_csv_path))
                    if os.path.exists(genbank_full_xml_path):
                        logger.info("  🧬 GenBank-only full XML:      %s", os.path.basename(genbank_full_xml_path))
                    if os.path.exists(genbank_full_csv_path):
                        logger.info("  🧬 GenBank-only full CSV (readable XML format):      %s", os.path.basename(genbank_full_csv_path))
                else:
                    logger.warning("")
                    logger.warning("⚠️  GenBank metadata was requested but NOT saved due to errors:")
                    logger.warning("    %s", genbank_error_msg)
                    logger.warning("    Standard metadata files are still available.")

            logger.info("=" * 60)
            
            # Save command summary
            save_command_summary(
                outfolder=outfolder,
                command_line=command_line,
                total_api_records=total_api_records,
                total_after_metadata_filter=total_after_metadata_filter,
                total_final_sequences=total_final_sequences,
                output_files=output_files_dict,
                filtered_metadata=final_metadata_for_summary,
                datasets_version=datasets_version,
                success=True,
                error_message=None,
                failed_commands=failed_commands,
                genbank_error=genbank_error_msg if genbank_metadata and not genbank_success else None,
                baseline_file=baseline_metadata,
                baseline_accession_count=len(baseline_accessions) if baseline_accessions else None,
                baseline_skipped_count=baseline_skipped_count if baseline_accessions is not None else None,
                runtime_seconds=time.time() - _virus_start_time,
                memory_info=_get_memory_usage(),
                metadata_filter_stats=metadata_filter_stats,
                genbank_filter_stats=genbank_filter_stats,
                sequence_filter_stats=sequence_filter_stats,
                total_after_genbank_filter=total_after_genbank_filter,
                total_after_sequence_filter=total_after_sequence_filter,
            )
        else:
            logger.warning("=" * 60)
            logger.warning("NO SEQUENCES PASSED THE FILTERS")
            logger.warning("=" * 60)
            logger.warning("No sequences met all the specified filter criteria.")
            logger.warning("Consider:")
            logger.warning("  - Relaxing some filter parameters")
            logger.warning("  - Checking filter values for typos or incorrect formats")
            logger.warning("  - Trying a broader virus query term")
            logger.warning("  - Removing some of the more restrictive filters")
            logger.warning("=" * 60)
            
            # Save command summary even when no sequences pass
            save_command_summary(
                outfolder=outfolder,
                command_line=command_line,
                total_api_records=total_api_records,
                total_after_metadata_filter=total_after_metadata_filter,
                total_final_sequences=0,
                output_files=output_files_dict,
                filtered_metadata=[],
                datasets_version=datasets_version,
                success=True,
                error_message="No sequences passed all filters",
                failed_commands=failed_commands,
                runtime_seconds=time.time() - _virus_start_time,
                memory_info=_get_memory_usage(),
                metadata_filter_stats=metadata_filter_stats,
                genbank_filter_stats=genbank_filter_stats,
                sequence_filter_stats=sequence_filter_stats,
            )

    except Exception as e:
        # Handle any unexpected errors during processing
        error_msg = str(e)
        
        # Check if this is a server-side issue that we can provide guidance for
        if any(indicator in error_msg.lower() for indicator in ['timeout', '500 server error', 'internal server error']):
            logger.error("=" * 80)
            logger.error("SERVER-SIDE ERROR DETECTED")
            logger.error("=" * 80)
            logger.error("The NCBI API is experiencing server-side issues.")
            logger.error("This is not a problem with your query or parameters.")
            logger.error("")
            logger.error("Error details: %s", e)
            logger.error("")
            
            # Provide alternative commands based on the problematic parameters
            if geographic_location:
                logger.error("🔧 SUGGESTED SOLUTION:")
                logger.error("The geographic location filter may be causing server issues.")
                logger.error("Try running without the geographic filter and filter manually afterward:")
                logger.error("")
                
                # Build alternative command
                cmd_parts = [f"gget.virus('{virus}'"]
                
                # Add all non-problematic filters
                if host:
                    cmd_parts.append(f"host='{host}'")
                if min_seq_length:
                    cmd_parts.append(f"min_seq_length={min_seq_length}")
                if max_seq_length:
                    cmd_parts.append(f"max_seq_length={max_seq_length}")
                if min_gene_count:
                    cmd_parts.append(f"min_gene_count={min_gene_count}")
                if max_gene_count:
                    cmd_parts.append(f"max_gene_count={max_gene_count}")
                if nuc_completeness:
                    cmd_parts.append(f"nuc_completeness='{nuc_completeness}'")
                if annotated is not None:
                    cmd_parts.append(f"annotated={annotated}")
                if lab_passaged is not None:
                    cmd_parts.append(f"lab_passaged={lab_passaged}")
                if min_collection_date:
                    cmd_parts.append(f"min_collection_date='{min_collection_date}'")
                if max_collection_date:
                    cmd_parts.append(f"max_collection_date='{max_collection_date}'")
                if source_database:
                    cmd_parts.append(f"source_database='{source_database}'")
                if min_release_date:
                    cmd_parts.append(f"min_release_date='{min_release_date}'")
                if max_release_date:
                    cmd_parts.append(f"max_release_date='{max_release_date}'")
                if max_ambiguous_chars is not None:
                    cmd_parts.append(f"max_ambiguous_chars={max_ambiguous_chars}")
                if has_proteins:
                    if isinstance(has_proteins, list):
                        cmd_parts.append(f"has_proteins={has_proteins}")
                    else:
                        cmd_parts.append(f"has_proteins='{has_proteins}'")
                
                cmd_parts.append(f"outfolder='{virus_clean}_data'")
                
                alternative_cmd = ", ".join(cmd_parts) + ")"
                logger.error("📋 ALTERNATIVE COMMAND:")
                logger.error("  %s", alternative_cmd)
                logger.error("")
                logger.error("After download completes, filter the output CSV file by the")
                logger.error("'Geographic Location' column to get sequences from '%s'.", geographic_location)
            
            elif any(x in virus.lower() for x in ['sars-cov-2', 'covid', 'influenza']) and not host:
                logger.error("🔧 SUGGESTED SOLUTION:")
                logger.error("Large datasets like '%s' may cause server timeouts.", virus)
                logger.error("Try adding a host filter to reduce the dataset size:")
                logger.error("")
                
                # Build alternative command with host filter
                cmd_parts = [f"gget.virus('{virus}'", "host='human'"]
                
                # Add existing filters
                if min_seq_length:
                    cmd_parts.append(f"min_seq_length={min_seq_length}")
                if max_seq_length:
                    cmd_parts.append(f"max_seq_length={max_seq_length}")
                if nuc_completeness:
                    cmd_parts.append(f"nuc_completeness='{nuc_completeness}'")
                if annotated is not None:
                    cmd_parts.append(f"annotated={annotated}")
                
                cmd_parts.append(f"outfolder='{virus_clean}_data'")
                
                alternative_cmd = ", ".join(cmd_parts) + ")"
                logger.error("📋 ALTERNATIVE COMMAND:")
                logger.error("  %s", alternative_cmd)
            
            else:
                logger.error("🔧 SUGGESTED SOLUTIONS:")
                logger.error("1. Wait a few minutes and try again (server issues are often temporary)")
                logger.error("2. Try using more specific filters to reduce dataset size")
                logger.error("3. Use host='human' filter if studying human pathogens")
                logger.error("4. Add date range filters to limit the time period")
            
            logger.error("=" * 80)
        else:
            # For non-server errors, show the original error message
            logger.error("An error occurred during virus data processing: %s", e)
            logger.error("Error type: %s", type(e).__name__)
            if logger.getEffectiveLevel() <= logging.DEBUG:
                logger.debug("Full traceback:\n%s", traceback.format_exc())
        
        # Save command summary with error information
        save_command_summary(
            outfolder=outfolder if outfolder else os.getcwd(),
            command_line=command_line,
            total_api_records=total_api_records,
            total_after_metadata_filter=total_after_metadata_filter,
            total_final_sequences=total_final_sequences,
            output_files=output_files_dict,
            filtered_metadata=final_metadata_for_summary,
            datasets_version=datasets_version,
            success=False,
            error_message=str(e),
            failed_commands=failed_commands,
            runtime_seconds=time.time() - _virus_start_time,
            memory_info=_get_memory_usage(),
            metadata_filter_stats=metadata_filter_stats,
            genbank_filter_stats=genbank_filter_stats,
            sequence_filter_stats=sequence_filter_stats,
        )
        
        raise
        
    # SECTION 10: CLEANUP
    finally:
        # Always clean up temporary files, regardless of success or failure
        logger.debug("Performing cleanup...")
        if os.path.exists(temp_dir) and keep_temp is False:
            try:
                shutil.rmtree(temp_dir)
                if os.path.exists(output_api_metadata_jsonl):
                    os.remove(output_api_metadata_jsonl)
                # Only remove metadata CSV if GenBank was successfully retrieved (as it's superseded by GenBank CSV)
                if genbank_metadata and genbank_success and os.path.exists(output_metadata_csv):
                    os.remove(output_metadata_csv)
                logger.debug("✅ Cleaned up temporary directory: %s", temp_dir)
            except Exception as e:
                logger.warning("Failed to clean up temporary directory %s: %s", temp_dir, e)
        
        # Clean up cached download files (zip file and extracted directory)
        # This ensures the folder structure is identical whether using cached or API-based downloads
        logger.debug("Checking for cached download files to clean up...")
        if cached_zip_file and keep_temp is False:
            logger.debug("in cached zip file and not keep_temp case")
            try:
                # Remove the zip file
                if os.path.exists(cached_zip_file):
                    logger.debug("Removing cached zip file: %s", cached_zip_file)
                    os.remove(cached_zip_file)
                    logger.debug("✅ Cleaned up cached zip file: %s", cached_zip_file)
                # Remove the extracted directory (same path without .zip extension)
                cached_extract_dir = os.path.splitext(cached_zip_file)[0]
                if os.path.exists(cached_extract_dir) and os.path.isdir(cached_extract_dir):
                    shutil.rmtree(cached_extract_dir)
                    logger.debug("✅ Cleaned up cached extracted directory: %s", cached_extract_dir)
            except Exception as e:
                logger.warning("Failed to clean up cached download files: %s", e)
        elif cached_zip_file and keep_temp:
            logger.debug("Preserving cached download files as per user request: %s", cached_zip_file)
        
        if keep_temp and os.path.exists(output_api_metadata_jsonl):
            logger.debug("Preserving temporary directory as per user request: %s", temp_dir)
            shutil.move(output_api_metadata_jsonl, os.path.join(temp_dir, os.path.basename(output_api_metadata_jsonl)))
            if genbank_metadata and genbank_success and os.path.exists(genbank_csv_path):
                shutil.move(output_metadata_csv, os.path.join(temp_dir, os.path.basename(output_metadata_csv)))

        if total_final_sequences == 0 and os.path.exists(output_api_metadata_jsonl):
            try:
                os.remove(output_api_metadata_jsonl)
                logger.debug("Removed filtered metadata JSONL due to no passing sequences: %s", output_api_metadata_jsonl)
            except Exception as e:
                logger.warning("Failed to remove filtered metadata JSONL even though no sequence passed all filters: %s", e)

                
                
        
        logger.info("NCBI virus data retrieval process completed.")
    
    # Restore the original logger level
    logger.setLevel(original_logger_level)


if __name__ == "__main__":
    # Main module entry point
    pass
