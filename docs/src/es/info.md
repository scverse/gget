[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/info.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget info 💡
Obtenga información detallada sobre genes y transcripciones de [Ensembl](https://www.ensembl.org/), [UniProt](https://www.uniprot.org/) y [NCBI](https://www.ncbi.nlm.nih.gov/) utilizando sus IDs del tipo Ensembl.  
Regresa: Resultados en formato JSON (Terminal) o Dataframe/CSV (Python).  

**Parámetro posicional**  
`ens_ids`  
Uno o más ID del tipo Ensembl.  
NOTA: Proporcionar una lista de más de 1000 ID de Ensembl a la vez puede provocar un error del servidor (para procesar más de 1000 ID, divida la lista de ID en fragmentos de 1000 ID y ejecútelos por separado).

**Parámetros optionales**  
`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.csv (o .json). Por defecto: salida estándar (STDOUT).  
Para Python, usa `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-n` `--ncbi`  
DESACTIVA los resultados de [NCBI](https://www.ncbi.nlm.nih.gov/).  
Para Python: `ncbi=False` evita la incluida de datos de NCBI (por defecto: True).  

`-u` `--uniprot`  
DESACTIVA los resultados de [UniProt](https://www.uniprot.org/).  
Para Python: `uniprot=False` evita la incluida de datos de UniProt (por defecto: True).  

`-pdb` `--pdb`  
INCLUYE [PDB](https://www.ebi.ac.uk/pdbe/) IDs en los resultados (podría aumentar el tiempo de ejecución).  
Para Python: `pdb=True` incluye IDs de PDB en los resultados (por defecto: False).

`-csv` `--csv`  
Solo para la Terminal. Regresa los resultados en formato CSV.  
Para Python, usa `json=True` para regresar los resultados en formato JSON.  

`-q` `--quiet`  
Solo para la Terminal. Impide la informacion de progreso de ser exhibida durante la corrida.  
Para Python, usa `verbose=False` para imipidir la informacion de progreso de ser exhibida durante la corrida.  

`wrap_text`  
Solo para Python. `wrap_text=True` muestra los resultados con texto envuelto para facilitar la lectura (por defecto: False).  


### Por ejemplo
```bash
gget info ENSG00000034713 ENSG00000104853 ENSG00000170296
```
```python
# Python
gget.info(["ENSG00000034713", "ENSG00000104853", "ENSG00000170296"])
```
&rarr; Regresa información detallada sobre cada ID de Ensembl ingresada:

|      | uniprot_id     | ncbi_gene_id     | primary_gene_name | synonyms | protein_names | ensembl_description | uniprot_description | ncbi_description | biotype | canonical_transcript | ... |
| -------------- |-------------------------| ------------------------| -------------- | ----------|-----|----|----|----|----|----|----|
| ENSG00000034713| P60520 | 11345 | GABARAPL2 | [ATG8, ATG8C, FLC3A, GABARAPL2, GATE-16, GATE16, GEF-2, GEF2] | Gamma-aminobutyric acid receptor-associated protein like 2 (GABA(A) receptor-associated protein-like 2)... | GABA type A receptor associated protein like 2 [Source:HGNC Symbol;Acc:HGNC:13291] | FUNCTION: Ubiquitin-like modifier involved in intra- Golgi traffic (By similarity). Modulates intra-Golgi transport through coupling between NSF activity and ... | Enables ubiquitin protein ligase binding activity. Involved in negative regulation of proteasomal protein catabolic process and protein... | protein_coding | ENST00000037243.7 |... |
| . . .            | . . .                     | . . .                     | . . .            | . . .       | . . . | . . . | . . . | . . . | . . . | . . . | ... |

#### [More examples](https://github.com/pachterlab/gget_examples)

# Citar  
Si utiliza `gget info` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Martin FJ, Amode MR, Aneja A, Austine-Orimoloye O, Azov AG, Barnes I, Becker A, Bennett R, Berry A, Bhai J, Bhurji SK, Bignell A, Boddu S, Branco Lins PR, Brooks L, Ramaraju SB, Charkhchi M, Cockburn A, Da Rin Fiorretto L, Davidson C, Dodiya K, Donaldson S, El Houdaigui B, El Naboulsi T, Fatima R, Giron CG, Genez T, Ghattaoraya GS, Martinez JG, Guijarro C, Hardy M, Hollis Z, Hourlier T, Hunt T, Kay M, Kaykala V, Le T, Lemos D, Marques-Coelho D, Marugán JC, Merino GA, Mirabueno LP, Mushtaq A, Hossain SN, Ogeh DN, Sakthivel MP, Parker A, Perry M, Piližota I, Prosovetskaia I, Pérez-Silva JG, Salam AIA, Saraiva-Agostinho N, Schuilenburg H, Sheppard D, Sinha S, Sipos B, Stark W, Steed E, Sukumaran R, Sumathipala D, Suner MM, Surapaneni L, Sutinen K, Szpak M, Tricomi FF, Urbina-Gómez D, Veidenberg A, Walsh TA, Walts B, Wass E, Willhoft N, Allen J, Alvarez-Jarreta J, Chakiachvili M, Flint B, Giorgetti S, Haggerty L, Ilsley GR, Loveland JE, Moore B, Mudge JM, Tate J, Thybert D, Trevanion SJ, Winterbottom A, Frankish A, Hunt SE, Ruffier M, Cunningham F, Dyer S, Finn RD, Howe KL, Harrison PW, Yates AD, Flicek P. Ensembl 2023. Nucleic Acids Res. 2023 Jan 6;51(D1):D933-D941. doi: [10.1093/nar/gkac958](https://doi.org/10.1093/nar/gkac958). PMID: 36318249; PMCID: PMC9825606.

- Sayers EW, Beck J, Bolton EE, Brister JR, Chan J, Comeau DC, Connor R, DiCuccio M, Farrell CM, Feldgarden M, Fine AM, Funk K, Hatcher E, Hoeppner M, Kane M, Kannan S, Katz KS, Kelly C, Klimke W, Kim S, Kimchi A, Landrum M, Lathrop S, Lu Z, Malheiro A, Marchler-Bauer A, Murphy TD, Phan L, Prasad AB, Pujar S, Sawyer A, Schmieder E, Schneider VA, Schoch CL, Sharma S, Thibaud-Nissen F, Trawick BW, Venkatapathi T, Wang J, Pruitt KD, Sherry ST. Database resources of the National Center for Biotechnology Information. Nucleic Acids Res. 2024 Jan 5;52(D1):D33-D43. doi: [10.1093/nar/gkad1044](https://doi.org/10.1093/nar/gkad1044). PMID: 37994677; PMCID: PMC10767890.

- The UniProt Consortium , UniProt: the Universal Protein Knowledgebase in 2023, Nucleic Acids Research, Volume 51, Issue D1, 6 January 2023, Pages D523–D531, [https://doi.org/10.1093/nar/gkac1052](https://doi.org/10.1093/nar/gkac1052)
