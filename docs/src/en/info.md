[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/info.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget info 💡
Fetch extensive gene and transcript metadata from [Ensembl](https://www.ensembl.org/), [UniProt](https://www.uniprot.org/), and [NCBI](https://www.ncbi.nlm.nih.gov/) using Ensembl IDs.  
Return format: JSON (command-line) or data frame/CSV (Python).

**Positional argument**  
`ens_ids`  
One or more Ensembl IDs (WormBase and Flybase IDs are also supported).  
NOTE: Providing a list of more than 1,000 Ensembl IDs at once might result in a server error (to process more than 1,000 IDs, split the list of IDs into chunks of 1,000 IDs and run these separately).  

**Optional arguments**  
`-o` `--out`  
Path to the file the results will be saved in, e.g. path/to/directory/results.csv (or .json). Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
`-n` `--ncbi`  
TURN OFF results from [NCBI](https://www.ncbi.nlm.nih.gov/).  
Python: `ncbi=False` prevents data retrieval from NCBI (default: True).  

`-u` `--uniprot`  
TURN OFF results from [UniProt](https://www.uniprot.org/).  
Python: `uniprot=False` prevents data retrieval from UniProt (default: True).  

`-pdb` `--pdb`  
INCLUDE [PDB](https://www.ebi.ac.uk/pdbe/) IDs in output (might increase runtime).  
Python: `pdb=True` includes PDB IDs in the results (default: False).  

`-csv` `--csv`  
Command-line only. Returns results in CSV format.  
Python: Use `json=True` to return output in JSON format.

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.  

`wrap_text`  
Python only. `wrap_text=True` displays data frame with wrapped text for easy reading (default: False).  


### Example
```bash
gget info ENSG00000034713 ENSG00000104853 ENSG00000170296
```
```python
# Python
gget.info(["ENSG00000034713", "ENSG00000104853", "ENSG00000170296"])
```
&rarr; Returns extensive information about each requested Ensembl ID:  

|      | uniprot_id     | ncbi_gene_id     | primary_gene_name | synonyms | protein_names | ensembl_description | uniprot_description | ncbi_description | biotype | canonical_transcript | ... |
| -------------- |-------------------------| ------------------------| -------------- | ----------|-----|----|----|----|----|----|----|
| ENSG00000034713| P60520 | 11345 | GABARAPL2 | [ATG8, ATG8C, FLC3A, GABARAPL2, GATE-16, GATE16, GEF-2, GEF2] | Gamma-aminobutyric acid receptor-associated protein like 2 (GABA(A) receptor-associated protein-like 2)... | GABA type A receptor associated protein like 2 [Source:HGNC Symbol;Acc:HGNC:13291] | FUNCTION: Ubiquitin-like modifier involved in intra- Golgi traffic (By similarity). Modulates intra-Golgi transport through coupling between NSF activity and ... | Enables ubiquitin protein ligase binding activity. Involved in negative regulation of proteasomal protein catabolic process and protein... | protein_coding | ENST00000037243.7 |... |
| . . .            | . . .                     | . . .                     | . . .            | . . .       | . . . | . . . | . . . | . . . | . . . | . . . | ... |

#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget info` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Martin FJ, Amode MR, Aneja A, Austine-Orimoloye O, Azov AG, Barnes I, Becker A, Bennett R, Berry A, Bhai J, Bhurji SK, Bignell A, Boddu S, Branco Lins PR, Brooks L, Ramaraju SB, Charkhchi M, Cockburn A, Da Rin Fiorretto L, Davidson C, Dodiya K, Donaldson S, El Houdaigui B, El Naboulsi T, Fatima R, Giron CG, Genez T, Ghattaoraya GS, Martinez JG, Guijarro C, Hardy M, Hollis Z, Hourlier T, Hunt T, Kay M, Kaykala V, Le T, Lemos D, Marques-Coelho D, Marugán JC, Merino GA, Mirabueno LP, Mushtaq A, Hossain SN, Ogeh DN, Sakthivel MP, Parker A, Perry M, Piližota I, Prosovetskaia I, Pérez-Silva JG, Salam AIA, Saraiva-Agostinho N, Schuilenburg H, Sheppard D, Sinha S, Sipos B, Stark W, Steed E, Sukumaran R, Sumathipala D, Suner MM, Surapaneni L, Sutinen K, Szpak M, Tricomi FF, Urbina-Gómez D, Veidenberg A, Walsh TA, Walts B, Wass E, Willhoft N, Allen J, Alvarez-Jarreta J, Chakiachvili M, Flint B, Giorgetti S, Haggerty L, Ilsley GR, Loveland JE, Moore B, Mudge JM, Tate J, Thybert D, Trevanion SJ, Winterbottom A, Frankish A, Hunt SE, Ruffier M, Cunningham F, Dyer S, Finn RD, Howe KL, Harrison PW, Yates AD, Flicek P. Ensembl 2023. Nucleic Acids Res. 2023 Jan 6;51(D1):D933-D941. doi: [10.1093/nar/gkac958](https://doi.org/10.1093/nar/gkac958). PMID: 36318249; PMCID: PMC9825606.

- Sayers EW, Beck J, Bolton EE, Brister JR, Chan J, Comeau DC, Connor R, DiCuccio M, Farrell CM, Feldgarden M, Fine AM, Funk K, Hatcher E, Hoeppner M, Kane M, Kannan S, Katz KS, Kelly C, Klimke W, Kim S, Kimchi A, Landrum M, Lathrop S, Lu Z, Malheiro A, Marchler-Bauer A, Murphy TD, Phan L, Prasad AB, Pujar S, Sawyer A, Schmieder E, Schneider VA, Schoch CL, Sharma S, Thibaud-Nissen F, Trawick BW, Venkatapathi T, Wang J, Pruitt KD, Sherry ST. Database resources of the National Center for Biotechnology Information. Nucleic Acids Res. 2024 Jan 5;52(D1):D33-D43. doi: [10.1093/nar/gkad1044](https://doi.org/10.1093/nar/gkad1044). PMID: 37994677; PMCID: PMC10767890.

- The UniProt Consortium , UniProt: the Universal Protein Knowledgebase in 2023, Nucleic Acids Research, Volume 51, Issue D1, 6 January 2023, Pages D523–D531, [https://doi.org/10.1093/nar/gkac1052](https://doi.org/10.1093/nar/gkac1052)
