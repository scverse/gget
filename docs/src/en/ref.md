[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/ref.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget ref 📖
Fetch download links and metadata for [Ensembl](https://www.ensembl.org/) reference genomes.  
Return format: dictionary/JSON.

**Positional argument**  
`species`  
Species for which the FTPs will be fetched in the format genus_species, e.g. homo_sapiens.  
Supports all available vertebrate and invertebrate (plants, fungi, protists, and invertebrate metazoa) genomes from Ensembl, except bacteria.  
Note: Not required when using flags `--list_species` or `--list_iv_species`.  
Supported shortcuts: 'human', 'mouse', 'human_grch37' (accesses the GRCh37 genome assembly)  
When using the `--assembly_report` flag, this is instead an NCBI assembly accession, e.g. GCF_000001405.40. The version suffix is optional; if omitted (e.g. GCF_000001405), the latest available version is used.

**Optional arguments**  
`-w` `--which`  
Defines which results to return. Default: 'all' -> Returns all available results.  
Possible entries are one or a combination (as comma-separated list) of the following:  
'gtf' - Returns the annotation (GTF).  
'cdna' - Returns the trancriptome (cDNA).  
'dna' - Returns the genome (DNA).  
'cds' - Returns the coding sequences corresponding to Ensembl genes. (Does not contain UTR or intronic sequence.)  
'cdrna' - Returns transcript sequences corresponding to non-coding RNA genes (ncRNA).  
'pep' - Returns the protein translations of Ensembl genes.  

`-r` `--release`  
Defines the Ensembl release number from which the files are fetched, e.g. 104. Default: latest Ensembl release.  

`-od` `--out_dir`  
Path to the directory where the FTPs will be saved, e.g. path/to/directory/. Default: Current working directory.

`-o` `--out`  
Path to the JSON file the results will be saved in, e.g. path/to/directory/results.json. Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
`-l` `--list_species`  
Lists all available vertebrate species. (Python: combine with `species=None`.)  

`-liv` `--list_iv_species`  
Lists all available invertebrate species. (Python: combine with `species=None`.)  

`-ftp` `--ftp`  
Returns only the requested FTP links.  

`-ar` `--assembly_report`  
Returns the [NCBI assembly report](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/troubleshooting/faq/#what-is-an-assembly-report) for the NCBI assembly accession passed as the positional argument (instead of Ensembl FTP links). The report maps sequence/chromosome names across the Ensembl/short, GenBank, RefSeq, and UCSC naming conventions, which is useful for translating chromosome names between databases.  
Python: returns a `pandas` DataFrame (use `assembly_report=True`).  

`-csv` `--csv`  
Command-line only. Only used with `--assembly_report`: returns the report in csv format instead of json.  
Python: Use `json=True` to return a list of dictionaries instead of a DataFrame.  

`-d` `--download`  
Command-line only. Downloads the requested FTPs to the directory specified by `out_dir` (requires [curl](https://curl.se/docs/) to be installed).

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.


### Examples

**Get the genome reference for a specific species:**  
```bash
gget ref -w gtf,dna homo_sapiens
```
```python
# Python
gget.ref("homo_sapiens", which=["gtf", "dna"])
```
&rarr; Returns a JSON with the latest human GTF and FASTA FTPs, and their respective metadata, in the format:
```
{
    "homo_sapiens": {
        "annotation_gtf": {
            "ftp": "http://ftp.ensembl.org/pub/release-106/gtf/homo_sapiens/Homo_sapiens.GRCh38.106.gtf.gz",
            "ensembl_release": 106,
            "release_date": "28-Feb-2022",
            "release_time": "23:27",
            "bytes": "51379459"
        },
        "genome_dna": {
            "ftp": "http://ftp.ensembl.org/pub/release-106/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
            "ensembl_release": 106,
            "release_date": "21-Feb-2022",
            "release_time": "09:35",
            "bytes": "881211416"
        }
    }
}
```

<br/><br/>

**List all available genomes from Ensembl release 103:**  
```bash
gget ref --list_species -r 103
```
```python
# Python
gget.ref(species=None, list_species=True, release=103)
```
&rarr; Returns a list with all available genomes (checks if GTF and FASTAs are available) from Ensembl release 103.  
(If no release is specified, `gget ref` will always return information from the latest Ensembl release.)  

<br/><br/>

**Get the NCBI assembly report to translate chromosome names between conventions:**  
```bash
gget ref GCF_000001405.40 --assembly_report
```
```python
# Python
gget.ref("GCF_000001405.40", assembly_report=True)
```
&rarr; Returns the NCBI assembly report for the human GRCh38.p14 assembly, mapping each sequence across the Ensembl/short (`Sequence-Name`), GenBank (`GenBank-Accn`), RefSeq (`RefSeq-Accn`), and UCSC (`UCSC-style-name`) naming conventions:

| Sequence-Name | Sequence-Role | Assigned-Molecule | ... | GenBank-Accn | RefSeq-Accn | ... | UCSC-style-name |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | assembled-molecule | 1 | ... | CM000663.2 | NC_000001.11 | ... | chr1 |
| 2 | assembled-molecule | 2 | ... | CM000664.2 | NC_000002.12 | ... | chr2 |

<br/><br/>

**Use `gget ref` in combination with [kallisto | bustools](https://www.kallistobus.tools/kb_usage/kb_ref/) to build a reference index:**
```bash
kb ref \
    -i index.idx \
    -g t2g.txt \
    -f1 fasta.fa \
    $(gget ref --ftp -w dna,gtf homo_sapiens)
```
&rarr; kb ref builds a reference index using the latest DNA and GTF files of species **Homo sapiens** passed to it by `gget ref`.  

#### [More examples](https://github.com/pachterlab/gget_examples)

# References
If you use `gget ref` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Martin FJ, Amode MR, Aneja A, Austine-Orimoloye O, Azov AG, Barnes I, Becker A, Bennett R, Berry A, Bhai J, Bhurji SK, Bignell A, Boddu S, Branco Lins PR, Brooks L, Ramaraju SB, Charkhchi M, Cockburn A, Da Rin Fiorretto L, Davidson C, Dodiya K, Donaldson S, El Houdaigui B, El Naboulsi T, Fatima R, Giron CG, Genez T, Ghattaoraya GS, Martinez JG, Guijarro C, Hardy M, Hollis Z, Hourlier T, Hunt T, Kay M, Kaykala V, Le T, Lemos D, Marques-Coelho D, Marugán JC, Merino GA, Mirabueno LP, Mushtaq A, Hossain SN, Ogeh DN, Sakthivel MP, Parker A, Perry M, Piližota I, Prosovetskaia I, Pérez-Silva JG, Salam AIA, Saraiva-Agostinho N, Schuilenburg H, Sheppard D, Sinha S, Sipos B, Stark W, Steed E, Sukumaran R, Sumathipala D, Suner MM, Surapaneni L, Sutinen K, Szpak M, Tricomi FF, Urbina-Gómez D, Veidenberg A, Walsh TA, Walts B, Wass E, Willhoft N, Allen J, Alvarez-Jarreta J, Chakiachvili M, Flint B, Giorgetti S, Haggerty L, Ilsley GR, Loveland JE, Moore B, Mudge JM, Tate J, Thybert D, Trevanion SJ, Winterbottom A, Frankish A, Hunt SE, Ruffier M, Cunningham F, Dyer S, Finn RD, Howe KL, Harrison PW, Yates AD, Flicek P. Ensembl 2023. Nucleic Acids Res. 2023 Jan 6;51(D1):D933-D941. doi: [10.1093/nar/gkac958](https://doi.org/10.1093/nar/gkac958). PMID: 36318249; PMCID: PMC9825606.
