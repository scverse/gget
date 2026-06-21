[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/blat.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget blat 🎯
Find the genomic location of a nucleotide or amino acid sequence using [BLAT](https://genome.ucsc.edu/cgi-bin/hgBlat).  
Return format: JSON (command-line) or data frame/CSV (Python).

**Positional argument**  
`sequence`  
Nucleotide or amino acid sequence, or path to FASTA or .txt file.

**Optional arguments**  
`-st` `--seqtype`  
'DNA', 'protein', 'translated%20RNA', or 'translated%20DNA'.  
Default: 'DNA' for nucleotide sequences; 'protein' for amino acid sequences.  

`-a` `--assembly`  
'human' (hg38) (default), 'mouse' (mm39), 'zebrafinch' (taeGut2),  
or any of the species assemblies available [here](https://genome.ucsc.edu/cgi-bin/hgBlat) (use short assembly name).

`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.csv (or .json). Default: Standard out.  
Python: `save=True` will save the output in the current working directory.  

**Flags**  
`-csv` `--csv`  
Command-line only. Returns results in CSV format.  
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.


### Example
```bash
gget blat -a taeGut2 MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR
```
```python
# Python
gget.blat("MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR", assembly="taeGut2")
```
&rarr; Returns BLAT results for assembly taeGut2 (zebra finch). In the above example, `gget blat` automatically detects this sequence as an amino acid sequence and therefore sets the BLAT seqtype to *protein*.

| genome     | query_size     | aligned_start     | aligned_end        | matches | mismatches | %_aligned | ... |
| -------------- |-------------------------| ------------------------| -------------- | ----------|-----|---|---|
| taeGut2| 88 | 	12 | 88 | 77 | 0 | 87.5 | ... |

#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget blat` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Kent WJ. BLAT--the BLAST-like alignment tool. Genome Res. 2002 Apr;12(4):656-64. doi: 10.1101/gr.229202. PMID: 11932250; PMCID: PMC187518.
