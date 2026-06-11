[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/search.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget search 🔎
Fetch genes and transcripts from [Ensembl](https://www.ensembl.org/) using free-form search terms.  
Results are matched based on the "gene name" and "description" sections in the Ensembl database. `gget` version >= 0.27.9 also includes results that match the Ensembl "synonym" section.  
Return format: JSON (command-line) or data frame/CSV (Python).

**Positional argument**  
`searchwords`  
One or more free form search words, e.g. gaba nmda. (Note: Search is not case-sensitive.)

**Other required arguments**  
`-s` `--species`  
Species or database to be searched.  
A species can be passed in the format 'genus_species', e.g. 'homo_sapiens' or 'arabidopsis_thaliana'.  
To pass a specific database, pass the name of the CORE database, e.g. 'mus_musculus_dba2j_core_105_1'.  

All available core databases can be found here:  
Vertebrates: [http://ftp.ensembl.org/pub/current/mysql/](http://ftp.ensembl.org/pub/current/mysql/)  
Invertebrates: [http://ftp.ensemblgenomes.org/pub/current/](http://ftp.ensemblgenomes.org/pub/current/) + select kingdom + go to mysql/  

Supported shortcuts: 'human', 'mouse'  

**Optional arguments**  
`-r` `--release`  
Defines the Ensembl release number from which the files are fetched, e.g. 104. Default: None -> latest Ensembl release is used.  

Note: *The release argument does not apply to invertebrate species* (you can pass a specific core database (which includes a release number) to the `species` argument instead). For invertebrate species, Ensembl only stores databases from 10 releases prior to the current release.  

This argument is overwritten if a specific database (which includes a release number) is passed to the species argument.  

`-t` `--id_type`  
'gene' (default) or 'transcript'  
Returns genes or transcripts, respectively.

`-ao` `--andor`  
'or' (default) or 'and'  
'or': Returns all genes that INCLUDE AT LEAST ONE of the searchwords in their name/description.  
'and': Returns only genes that INCLUDE ALL of the searchwords in their name/description.

`-l` `--limit`  
Limits the number of search results, e.g. 10. Default: None.  

`-o` `--out`  
Path to the csv the results will be saved in, e.g. path/to/directory/results.csv (or .json). Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
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
gget search -s human gaba gamma-aminobutyric
```
```python
# Python
gget.search(["gaba", "gamma-aminobutyric"], "homo_sapiens")
```
&rarr; Returns all genes that contain at least one of the search words in their name or Ensembl/external reference description:

| ensembl_id     | gene_name     | ensembl_description     | ext_ref_description        | biotype | url |
| -------------- |-------------------------| ------------------------| -------------- | ----------|-----|
| ENSG00000034713| GABARAPL2 | 	GABA type A receptor associated protein like 2 [Source:HGNC Symbol;Acc:HGNC:13291] | GABA type A receptor associated protein like 2 | protein_coding | https://uswest.ensembl.org/homo_sapiens/Gene/Summary?g=ENSG00000034713 |
| . . .            | . . .                     | . . .                     | . . .            | . . .       | . . . |

#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget search` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Martin FJ, Amode MR, Aneja A, Austine-Orimoloye O, Azov AG, Barnes I, Becker A, Bennett R, Berry A, Bhai J, Bhurji SK, Bignell A, Boddu S, Branco Lins PR, Brooks L, Ramaraju SB, Charkhchi M, Cockburn A, Da Rin Fiorretto L, Davidson C, Dodiya K, Donaldson S, El Houdaigui B, El Naboulsi T, Fatima R, Giron CG, Genez T, Ghattaoraya GS, Martinez JG, Guijarro C, Hardy M, Hollis Z, Hourlier T, Hunt T, Kay M, Kaykala V, Le T, Lemos D, Marques-Coelho D, Marugán JC, Merino GA, Mirabueno LP, Mushtaq A, Hossain SN, Ogeh DN, Sakthivel MP, Parker A, Perry M, Piližota I, Prosovetskaia I, Pérez-Silva JG, Salam AIA, Saraiva-Agostinho N, Schuilenburg H, Sheppard D, Sinha S, Sipos B, Stark W, Steed E, Sukumaran R, Sumathipala D, Suner MM, Surapaneni L, Sutinen K, Szpak M, Tricomi FF, Urbina-Gómez D, Veidenberg A, Walsh TA, Walts B, Wass E, Willhoft N, Allen J, Alvarez-Jarreta J, Chakiachvili M, Flint B, Giorgetti S, Haggerty L, Ilsley GR, Loveland JE, Moore B, Mudge JM, Tate J, Thybert D, Trevanion SJ, Winterbottom A, Frankish A, Hunt SE, Ruffier M, Cunningham F, Dyer S, Finn RD, Howe KL, Harrison PW, Yates AD, Flicek P. Ensembl 2023. Nucleic Acids Res. 2023 Jan 6;51(D1):D933-D941. doi: [10.1093/nar/gkac958](https://doi.org/10.1093/nar/gkac958). PMID: 36318249; PMCID: PMC9825606.
