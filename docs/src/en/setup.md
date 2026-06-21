[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/setup.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget setup 🔧

Function to install/download third-party dependencies for a specified gget module.

> **Note:** Some dependencies (e.g., `cellxgene-census`) may not support the latest Python versions. If you encounter installation errors try using an environment with an earlier Python version.

**Positional argument**  
`module`  
gget module for which dependencies should be installed.  

**Optional arguments**  
`-o` `--out`  
Path to the folder downloaded files will be saved in (currently only applies to module = 'elm').  
NOTE: Do NOT use this argument when downloading the files for use with `gget.elm`.  
Default: None (downloaded files are saved inside the `gget` package installation folder).  

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
