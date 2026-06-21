[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/blast.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Las banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget blast 💥
BLAST una secuencia de nucleótidos o aminoácidos a cualquier base de datos [BLAST](https://blast.ncbi.nlm.nih.gov/Blast.cgi).  
Produce: Resultados en formato JSON (Terminal) o Dataframe/CSV (Python).  

**Parámetro posicional**  
`sequence`  
Secuencia de nucleótidos o aminoácidos, o una ruta a un archivo tipo FASTA o .txt.  

**Parámetros optionales**  
`-p` `--program`  
'blastn', 'blastp', 'blastx', 'tblastn', o 'tblastx'.  
Por defecto: 'blastn' para secuencias de nucleótidos; 'blastp' para secuencias de aminoácidos.  

`-db` `--database`  
'nt', 'nr', 'refseq_rna', 'refseq_protein', 'swissprot', 'pdbaa', o 'pdbnt'.  
Por defecto: 'nt' para secuencias de nucleótidos; 'nr' para secuencias de aminoácidos.  
[Más información sobre los bases de datos BLAST](https://ncbi.github.io/blast-cloud/blastdb/available-blastdbs.html)  

`-l` `--limit`  
Limita el número de resultados producidos. Por defecto: 50.  

`-e` `--expect`  
Define el umbral de ['expect value'](https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs&DOC_TYPE=FAQ#expect). Por defecto: 10.0.  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.csv (o .json). Por defecto: salida estándar (STDOUT).  
Para Python, usa `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-lcf` `--low_comp_filt`  
Activa el ['low complexity filter'](https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Web&PAGE_TYPE=BlastDocs&DOC_TYPE=FAQ#LCR) (filtro de baja complejidad).  

`-mbo` `--megablast_off`  
Desactiva el algoritmo MegaBLAST. Por defecto: MegaBLAST esta activado (solo aplicable para blastn).  

`-csv` `--csv`  
Solo para Terminal. Produce los resultados en formato CSV.  
Para Python, usa `json=True` para producir los resultados en formato JSON.  

`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para imipidir la informacion de progreso de ser exhibida durante la ejecución del programa.  

`wrap_text`  
Solo para Python. `wrap_text=True` muestra los resultados con texto envuelto para facilitar la lectura (por defecto: False).  

### Por ejemplo
```bash
gget blast MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR
```
```python
# Python
gget.blast("MKWMFKEDHSLEHRCVESAKIRAKYPDRVPVIVEKVSGSQIVDIDKRKYLVPSDITVAQFMWIIRKRIQLPSEKAIFLFVDKTVPQSR")
```
&rarr; Produce los resultados BLAST de la secuencia de interés. `gget blast` automáticamente detecta esta secuencia como una secuencia de aminoácidos y, por lo tanto, establece el programa BLAST en *blastp* con la base de datos *nr*.  

| Description     | Scientific Name	     | Common Name     | Taxid        | Max Score | Total Score | Query Cover | ... |
| -------------- |-------------------------| ------------------------| -------------- | ----------|-----|---|---|
| PREDICTED: gamma-aminobutyric acid receptor-as...| Colobus angolensis palliatus	 | 	NaN | 336983 | 180	 | 180 | 100% | ... |
| . . . | . . . | . . . | . . . | . . . | . . . | . . . | ... |


**BLAST desde un archivo .fa o .txt:**  
```bash
gget blast fasta.fa
```
```python
# Python
gget.blast("fasta.fa")
```
&rarr; Produce los resultados BLAST de la primera secuencia contenida en el archivo 'fasta.fa'.  

#### [Más ejemplos](https://github.com/pachterlab/gget_examples)

# Citar  
Si utiliza `gget blast` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Altschul SF, Gish W, Miller W, Myers EW, Lipman DJ. Basic local alignment search tool. J Mol Biol. 1990 Oct 5;215(3):403-10. doi: 10.1016/S0022-2836(05)80360-2. PMID: 2231712.
