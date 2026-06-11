[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/seq.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
## gget seq 🧬
Obtenga la(s) secuencia(s) nucleótidos o aminoácidos de un gen (y todas sus isoformas) con su ID de Ensembl.  
Regresa: Archivo de tipo FASTA.  

**Parámetro posicional**  
`ens_ids`  
One or more Ensembl IDs.

**Parámetros optionales**  
`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ruta/al/directorio/resultados.fa. Por defecto: salida estándar (STDOUT).  
Para Python, usa `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-t` `--translate`  
Regresa secuencias de aminoácidos (en lugar de nucleótidos).  
Las secuencias de nucleótidos se obtienen de [Ensembl](https://www.ensembl.org/).  
Las secuencias de aminoácidos se obtienen de [UniProt](https://www.uniprot.org/).  

`-iso` `--isoforms`  
Regresa las secuencias de todas las transcripciones conocidas.  
(Solo para IDs de genes).  

`-q` `--quiet`  
Solo para la Terminal. Impide la informacion de progreso de ser exhibida durante la corrida.  
Para Python, usa `verbose=False` para imipidir la informacion de progreso de ser exhibida durante la corrida.  


### Por ejemplo  
```bash
gget seq ENSG00000034713 ENSG00000104853 ENSG00000170296
```
```python
# Python
gget.seq(["ENSG00000034713", "ENSG00000104853", "ENSG00000170296"])
```
&rarr; Regresa las secuencias de nucleótidos de ENSG00000034713, ENSG00000104853, y ENSG00000170296 en formato FASTA.  

<br/><br/>

```bash
gget seq -t -iso ENSG00000034713
```
```python
# Python
gget.seq("ENSG00000034713", translate=True, isoforms=True)
```
&rarr; Regresa las secuencias de aminoácidos de todas las transcripciones conocidas de ENSG00000034713 en formato FASTA.  

#### [Más ejemplos](https://github.com/pachterlab/gget_examples)

# Citar  
Si utiliza `gget seq` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Martin FJ, Amode MR, Aneja A, Austine-Orimoloye O, Azov AG, Barnes I, Becker A, Bennett R, Berry A, Bhai J, Bhurji SK, Bignell A, Boddu S, Branco Lins PR, Brooks L, Ramaraju SB, Charkhchi M, Cockburn A, Da Rin Fiorretto L, Davidson C, Dodiya K, Donaldson S, El Houdaigui B, El Naboulsi T, Fatima R, Giron CG, Genez T, Ghattaoraya GS, Martinez JG, Guijarro C, Hardy M, Hollis Z, Hourlier T, Hunt T, Kay M, Kaykala V, Le T, Lemos D, Marques-Coelho D, Marugán JC, Merino GA, Mirabueno LP, Mushtaq A, Hossain SN, Ogeh DN, Sakthivel MP, Parker A, Perry M, Piližota I, Prosovetskaia I, Pérez-Silva JG, Salam AIA, Saraiva-Agostinho N, Schuilenburg H, Sheppard D, Sinha S, Sipos B, Stark W, Steed E, Sukumaran R, Sumathipala D, Suner MM, Surapaneni L, Sutinen K, Szpak M, Tricomi FF, Urbina-Gómez D, Veidenberg A, Walsh TA, Walts B, Wass E, Willhoft N, Allen J, Alvarez-Jarreta J, Chakiachvili M, Flint B, Giorgetti S, Haggerty L, Ilsley GR, Loveland JE, Moore B, Mudge JM, Tate J, Thybert D, Trevanion SJ, Winterbottom A, Frankish A, Hunt SE, Ruffier M, Cunningham F, Dyer S, Finn RD, Howe KL, Harrison PW, Yates AD, Flicek P. Ensembl 2023. Nucleic Acids Res. 2023 Jan 6;51(D1):D933-D941. doi: [10.1093/nar/gkac958](https://doi.org/10.1093/nar/gkac958). PMID: 36318249; PMCID: PMC9825606

- The UniProt Consortium , UniProt: the Universal Protein Knowledgebase in 2023, Nucleic Acids Research, Volume 51, Issue D1, 6 January 2023, Pages D523–D531, [https://doi.org/10.1093/nar/gkac1052](https://doi.org/10.1093/nar/gkac1052)
