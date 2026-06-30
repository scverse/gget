[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/pineapple.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget pineapple 🍍
List and download curated bio-imaging datasets and pre-trained model weights from [Pineapple](https://github.com/tomouellette/pineapple).  
[Pineapple](https://github.com/tomouellette/pineapple) (by Tom Ouellette) is a tool for image-based cell profiling that also curates and standardizes a collection of annotated bio-imaging datasets (segmentation and benchmark) and self-supervised model weights, hosted on Google Drive. `gget pineapple` lets you browse this catalog and download the resources directly — no Rust binary required.  
Return format: JSON (command-line) or data frame/CSV (Python).

> **Scope:** `gget pineapple` wraps only Pineapple's data download. It does not reimplement Pineapple's image-processing features (`process`, `profile`, `neural`, `measure`) — use the [Pineapple](https://github.com/tomouellette/pineapple) tool directly for those.

> ⚠️ Please check each dataset's original reference and license (shown in the catalog) before use. Some datasets are non-commercial only.

**Positional argument**  
`name`  
Name of the dataset/weights to fetch, e.g. `vicar_2021` or `dino_vit_small`. Omit to list the full catalog for the chosen category.

**Optional arguments**  
`-c` `--category`  
Resource category: `segmentation`, `benchmark`, or `weights`. Default: `segmentation`.  

`-od` `--out_dir`  
Directory to download the resource into (used with `--download`). Default: current directory.  

`-o` `--out`  
Path to the file the catalog table will be saved in, e.g. path/to/directory/results.csv (or .json). Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
`-d` `--download`  
Download the resource (requires a specific `name`) into `--out_dir`. Datasets are large (up to several GB); see the `size_gb` column.  

`-csv` `--csv`  
Command-line only. Returns results in CSV format.  
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

### Examples
**List the available segmentation datasets:**
```bash
gget pineapple --category segmentation
```
```python
# Python
gget.pineapple(category="segmentation")
```
&rarr; Returns the catalog of curated segmentation datasets.

| name | category | data_authors | size_gb | license | filename | google_drive_id |
| --- | --- | --- | --- | --- | --- | --- |
| vicar_2021 | segmentation | Vicar et al. 2021 | 0.113 | CC BY 4.0 | vicar-2021.tar.gz | 12tJOlIHZPFqp8GLek_jV__Uhhgsa530_ |
| . . . | . . . | . . . | . . . | . . . | . . . | . . . |

<br/><br/>
**Download a specific dataset:**
```bash
gget pineapple vicar_2021 --download --out_dir ./pineapple_data
```
```python
# Python
gget.pineapple("vicar_2021", download=True, out_dir="./pineapple_data")
```
&rarr; Downloads `vicar-2021.tar.gz` into `./pineapple_data` and returns the catalog entry.

<br/><br/>
**List the pre-trained model weights:**
```bash
gget pineapple --category weights
```
```python
# Python
gget.pineapple(category="weights")
```
&rarr; Returns the catalog of pre-trained self-supervised model weights (e.g. `dino_vit_small`, `subcell_vit_base`).

# References
If you use `gget pineapple` in a publication, please cite the following article and the original dataset references (listed in the catalog `data_authors` column):  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Pineapple: scalable processing for image-based cell profiling. [https://github.com/tomouellette/pineapple](https://github.com/tomouellette/pineapple)
