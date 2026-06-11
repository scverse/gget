[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/seq.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget seq 🧬
Fetch nucleotide or amino acid sequence(s) of a gene (and all its isoforms) or a transcript by Ensembl ID.  
Return format: FASTA.

**Positional argument**  
`ens_ids`  
One or more Ensembl IDs.

**Optional arguments**  
`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.fa. Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
`-t` `--translate`  
Returns amino acid (instead of nucleotide) sequences.  
Nucleotide sequences are fetched from [Ensembl](https://www.ensembl.org/).  
Amino acid sequences are fetched from [UniProt](https://www.uniprot.org/).

`-iso` `--isoforms`  
Returns the sequences of all known transcripts.  
(Only for gene IDs.)

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.


### Examples  
```bash
gget seq ENSG00000034713 ENSG00000104853 ENSG00000170296
```
```python
# Python
gget.seq(["ENSG00000034713", "ENSG00000104853", "ENSG00000170296"])
```
&rarr; Returns the nucleotide sequences of ENSG00000034713, ENSG00000104853, and ENSG00000170296 in FASTA format.  


```bash
gget seq -t -iso ENSG00000034713
```
```python
# Python
gget.seq("ENSG00000034713", translate=True, isoforms=True)
```
&rarr; Returns the amino acid sequences of all known transcripts of ENSG00000034713 in FASTA format.

#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget seq` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Martin FJ, Amode MR, Aneja A, Austine-Orimoloye O, Azov AG, Barnes I, Becker A, Bennett R, Berry A, Bhai J, Bhurji SK, Bignell A, Boddu S, Branco Lins PR, Brooks L, Ramaraju SB, Charkhchi M, Cockburn A, Da Rin Fiorretto L, Davidson C, Dodiya K, Donaldson S, El Houdaigui B, El Naboulsi T, Fatima R, Giron CG, Genez T, Ghattaoraya GS, Martinez JG, Guijarro C, Hardy M, Hollis Z, Hourlier T, Hunt T, Kay M, Kaykala V, Le T, Lemos D, Marques-Coelho D, Marugán JC, Merino GA, Mirabueno LP, Mushtaq A, Hossain SN, Ogeh DN, Sakthivel MP, Parker A, Perry M, Piližota I, Prosovetskaia I, Pérez-Silva JG, Salam AIA, Saraiva-Agostinho N, Schuilenburg H, Sheppard D, Sinha S, Sipos B, Stark W, Steed E, Sukumaran R, Sumathipala D, Suner MM, Surapaneni L, Sutinen K, Szpak M, Tricomi FF, Urbina-Gómez D, Veidenberg A, Walsh TA, Walts B, Wass E, Willhoft N, Allen J, Alvarez-Jarreta J, Chakiachvili M, Flint B, Giorgetti S, Haggerty L, Ilsley GR, Loveland JE, Moore B, Mudge JM, Tate J, Thybert D, Trevanion SJ, Winterbottom A, Frankish A, Hunt SE, Ruffier M, Cunningham F, Dyer S, Finn RD, Howe KL, Harrison PW, Yates AD, Flicek P. Ensembl 2023. Nucleic Acids Res. 2023 Jan 6;51(D1):D933-D941. doi: [10.1093/nar/gkac958](https://doi.org/10.1093/nar/gkac958). PMID: 36318249; PMCID: PMC9825606

- The UniProt Consortium , UniProt: the Universal Protein Knowledgebase in 2023, Nucleic Acids Research, Volume 51, Issue D1, 6 January 2023, Pages D523–D531, [https://doi.org/10.1093/nar/gkac1052](https://doi.org/10.1093/nar/gkac1052)
