[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/mutate.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python.  The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget mutate 🧟
Takes in nucleotide sequences and mutations (in [standard mutation annotation](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1867422/) and returns mutated versions of the input sequences according to the provided mutations.  
Return format: Saves mutated sequences in FASTA format (or returns a list containing the mutated sequences if `out=None`).  

This module was written by [Joseph Rich](https://github.com/josephrich98).

** Update: The more complex functionality of gget mutate has been ported to https://github.com/pachterlab/kvar. kvar expands on this functionality in the context of screening for variants/mutations in sequencing data. If this sounds interesting to you, please check it out! **

**Positional argument**  
`sequences`  
Path to the FASTA file containing the sequences to be mutated, e.g., 'path/to/seqs.fa'.  
Sequence identifiers following the '>' character must correspond to the identifiers in the seq_ID column of `mutations`.  

Example format of the FASTA file:  
```
>seq1 (or ENSG00000106443)  
ACTGCGATAGACT  
>seq2  
AGATCGCTAG
```

Alternatively: Input sequence(s) as a string or list, e.g. 'AGCTAGCT'.

NOTE: Only the letters until the first space or dot will be used as sequence identifiers - Version numbers of Ensembl IDs will be ignored.  
NOTE: When the `sequences` input is a genome fasta file, also see the `gtf` argument below.

**Required arguments**  
`-m` `--mutations`  
Path to the csv or tsv file (e.g., 'path/to/mutations.csv') or data frame (DataFrame object) containing information about the mutations in the following format (the 'notes' and 'mut_ID' columns are optional):  

| mutation         | mut_ID | seq_ID | notes |
|------------------|--------|--------|-------|
| c.2C>T           | mut1   | seq1   | -> Apply mutation 1 to sequence 1 |
| c.9_13inv        | mut2   | seq2   | -> Apply mutation 2 to sequence 2 |
| c.9_13inv        | mut2   | seq4   | -> Apply mutation 2 to sequence 4 |
| c.9_13delinsAAT  | mut3   | seq4   | -> Apply mutation 3 to sequence 4 |
| ...              | ...    | ...    |                                   |

'mutation' = Column containing the mutations to be performed written in standard mutation annotation  
'mut_ID' = Column containing the identifier for each mutation  
'seq_ID' = Column containing the identifiers of the sequences to be mutated (must correspond to the string following the '>' character in the 'sequences' FASTA file; do NOT include spaces or dots)  

Alternatively: Input mutation(s) as a string or list, e.g., 'c.2C>T'.  
If a list is provided, the number of mutations must equal the number of input sequences.  

For use from the terminal (bash): Enclose individual mutation annotations in quotation marks to prevent parsing errors.  

**Optional input-related arguments**  
`-mc` `--mut_column`  
Name of the column containing the mutations to be performed in `mutations`. Default: 'mutation'.  

`-sic` `--seq_id_column`  
Name of the column containing the IDs of the sequences to be mutated in `mutations`. Default: 'seq_ID'.

`-mic` `--mut_id_column`  
Name of the column containing the IDs of each mutation in `mutations`. Default: Same as `mut_column`.

**Optional mutant sequence generation/filtering arguments**  
`-k` `--k`  
Length of sequences flanking the mutation. Default: 30.  
If k > total length of the sequence, the entire sequence will be kept.  

**Optional general arguments**  
`-o` `--out`  
Path to output FASTA file containing the mutated sequences, e.g., 'path/to/output_fasta.fa'.  
Default: None -> returns a list of the mutated sequences to standard out.  
The identifiers (following the '>') of the mutated sequences in the output FASTA will be '>[seq_ID]_[mut_ID]'.

**Optional general flags**  
`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

### Examples
```bash
gget mutate ATCGCTAAGCT -m 'c.4G>T'
```
```python
# Python
gget.mutate("ATCGCTAAGCT", "c.4G>T")
```
&rarr; Returns ATCTCTAAGCT.  

<br/><br/>

**List of sequences with a mutation for each sequence provided in a list:**  
```bash
gget mutate ATCGCTAAGCT TAGCTA -m 'c.4G>T' 'c.1_3inv' -o mut_fasta.fa
```
```python
# Python
gget.mutate(["ATCGCTAAGCT", "TAGCTA"], ["c.4G>T", "c.1_3inv"], out="mut_fasta.fa")
```
&rarr; Saves 'mut_fasta.fa' file containing:
```
>seq1_mut1  
ATCTCTAAGCT  
>seq2_mut2  
GATCTA
```

<br/><br/>

**One mutation applied to several sequences with adjusted `k`:**  
```bash
gget mutate ATCGCTAAGCT TAGCTA -m 'c.1_3inv' -k 3
```
```python
# Python
gget.mutate(["ATCGCTAAGCT", "TAGCTA"], "c.1_3inv", k=3)
```
&rarr; Returns ['CTAGCT', 'GATCTA'].  


# References
If you use `gget mutate` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
