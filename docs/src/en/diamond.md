[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/diamond.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget diamond 💎
Align multiple protein or translated DNA sequences using [DIAMOND](https://www.nature.com/articles/nmeth.3176) (DIAMOND is similar to BLAST, but this is a local computation).  
Return format: JSON (command-line) or data frame/CSV (Python).  

**Positional argument**  
`query`  
Sequences (str or list) or path to FASTA file containing sequences to be aligned against the reference.  

**Required arguments**  
`-ref` `--reference`  
Reference sequences (str or list) or path to FASTA file containing reference sequences.  
Add the `--translated` flag (Python: `translated=True`) if reference sequences are amino acid sequences and query sequences are nucleotide sequences.  

**Optional arguments**  
`-db` `--diamond_db`  
Path to save DIAMOND database created from `reference` (str).  
Default: None -> Temporary db file will be deleted after alignment or saved in `out` if `out` is provided.  

`-s` `--sensitivity`  
Sensitivity of alignment (str). Default: "very-sensitive".  
One of the following: fast, mid-sensitive, sensitive, more-sensitive, very-sensitive, or ultra-sensitive.  

`-t` `--threads`  
Number of threads used (int). Default: 1.  

`-db` `--diamond_binary`  
Path to DIAMOND binary (str). Default: None -> Uses DIAMOND binary installed with `gget`.  

`-o` `--out`  
Path to the folder to save results in (str), e.g. "path/to/directory". Default: Standard out; temporary files are deleted.  

**Flags**  
`-x` `--translated`  
Perform translated alignment of nucleotide sequences to amino acid reference sequences.  

`-csv` `--csv`  
Command-line only. Returns results in CSV format.  
Python: Use `json=True` to return output in JSON format.  

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

### Example
```bash
# !!! Make sure to list the positional argument first here so it is not added as a reference sequence
gget diamond GGETISAWESQME ELVISISALIVE LQVEFRANKLIN PACHTERLABRQCKS -ref GGETISAWESQMEELVISISALIVELQVEFRANKLIN PACHTERLABRQCKS
```
```python
# Python
gget.diamond(["GGETISAWESQME", "ELVISISALIVE", "LQVEFRANKLIN", "PACHTERLABRQCKS"], reference=["GGETISAWESQMEELVISISALIVELQVEFRANKLIN", "PACHTERLABRQCKS"])
```
&rarr; Returns results in JSON (command-line) or data frame/CSV (Python) format:  

|query_accession|subject_accession|identity_percentage|query_seq_length|subject_seq_length|length|mismatches|gap_openings|query_start|query_end|subject_start|subject_end|e-value |bit_score|
|---------------|-----------------|-------------------|----------------|------------------|------|----------|------------|-----------|---------|-------------|-----------|--------|---------|
|Seq0           |Seq0             |100                |13              |37                |13    |0         |0           |1          |13       |1            |13         |2.82e-09|30.8     |
|Seq2           |Seq0             |100                |12              |37                |12    |0         |0           |1          |12       |26           |37         |4.35e-08|27.7     |
|Seq3           |Seq1             |100                |15              |15                |15    |0         |0           |1          |15       |1            |15         |2.01e-11|36.2     |

#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget diamond` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Buchfink, B., Xie, C. & Huson, D. Fast and sensitive protein alignment using DIAMOND. Nat Methods 12, 59–60 (2015). [https://doi.org/10.1038/nmeth.3176](https://doi.org/10.1038/nmeth.3176)
