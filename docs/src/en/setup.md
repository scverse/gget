[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/setup.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget setup 🔧

Function to install/download third-party dependencies for a specified gget module.

> **Note:** Some dependencies (e.g., `cellxgene-census`) may not support the latest Python versions. If you encounter installation errors try using an environment with an earlier Python version.

**Positional argument**  
`module`  
gget module for which dependencies should be installed.  
Choose from: "alphafold", "gpt", "cellxgene", "elm", or "cbio"

**Optional arguments**  
`-o` `--out`  
Only applies when `module='elm'`. Path to a folder where the raw ELM database files (`elm_instances.fasta`, `elms_classes.tsv`, `elm_instances.tsv`, `elm_interaction_domains.tsv`) will be downloaded — useful if you want a local copy of the ELM data for your own scripts or inspection, separately from running [`gget elm`](elm.md).  
NOTE: To set up the files so that [`gget elm`](elm.md) can use them, **omit this argument** — [`gget elm`](elm.md) only reads from the default location inside the `gget` package installation folder. Files downloaded to a custom `--out` path will not be picked up by [`gget elm`](elm.md).  
Default: None (downloaded files are saved inside the `gget` package installation folder where [`gget elm`](elm.md) can find them).  

**Flags**  
`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.


### Example
```bash
gget setup alphafold
```
```python
# Python
gget.setup("alphafold")
```
&rarr; Installs all (modified) third-party dependencies and downloads model parameters (~4GB) required to run [`gget alphafold`](alphafold.md).
