[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/mutate.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget mutate 🧟
Recibe secuencias de nucleótidos y mutaciones (en [anotación de mutación estándar](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1867422/)) y devuelve versiones mutadas de las secuencias según las mutaciones proporcionadas.  
Resultado: Guarda las secuencias mutadas en formato FASTA (o devuelve una lista que contiene las secuencias mutadas si `out=None`).  

Este módulo fue coescrito por [Joseph Rich](https://github.com/josephrich98).

**Argumento posicional**  
`sequences`  
Ruta al archivo FASTA que contiene las secuencias a ser mutadas, por ejemplo, 'path/to/seqs.fa'.  
Los identificadores de las secuencias que siguen al carácter '>' deben corresponder a los identificadores en la columna seq_ID de `mutations`.  

Formato de ejemplo del archivo FASTA:  
```
>seq1 (or ENSG00000106443)  
ACTGCGATAGACT  
>seq2  
AGATCGCTAG
```

Alternativamente: Secuencia(s) de entrada como una cadena o lista, por ejemplo, 'AGCTAGCT'.

NOTA: Solo se utilizarán las letras hasta el primer espacio o punto como identificadores de secuencias; se ignorarán los números de versión de los IDs de Ensembl.  
NOTA: Cuando la entrada `sequences` es un archivo fasta de genoma, consulte también el argumento `gtf` a continuación.

**Argumentos requeridos**  
`-m` `--mutations`  
Ruta al archivo csv o tsv (por ejemplo, 'path/to/mutations.csv') o marco de datos (objeto DataFrame) que contiene información sobre las mutaciones en el siguiente formato (las columnas 'notes' y 'mut_ID' son opcionales):  

| mutation         | mut_ID | seq_ID | notes |
|------------------|--------|--------|-------|
| c.2C>T           | mut1   | seq1   | -> Aplicar mutación 1 a la secuencia 1 |
| c.9_13inv        | mut2   | seq2   | -> Aplicar mutación 2 a la secuencia 2 |
| c.9_13inv        | mut2   | seq4   | -> Aplicar mutación 2 a la secuencia 4 |
| c.9_13delinsAAT  | mut3   | seq4   | -> Aplicar mutación 3 a la secuencia 4 |
| ...              | ...    | ...    |                                   |

'mutation' = Columna que contiene las mutaciones a realizar escritas en la anotación estándar de mutaciones  
'mut_ID' = Columna que contiene el identificador para cada mutación  
'seq_ID' = Columna que contiene los identificadores de las secuencias a ser mutadas (deben corresponder a la cadena que sigue al carácter '>' en el archivo FASTA 'sequences'; NO incluya espacios ni puntos)  

Alternativamente: Mutación(es) de entrada como una cadena o lista, por ejemplo, 'c.2C>T'.  
Si se proporciona una lista, el número de mutaciones debe ser igual al número de secuencias de entrada.  

Para usar desde la terminal (bash): Enciérrale las anotaciones de mutación individuales entre comillas para evitar errores de análisis.  

**Argumentos opcionales relacionados con la entrada**  
`-mc` `--mut_column`  
Nombre de la columna que contiene las mutaciones a realizar en `mutations`. Predeterminado: 'mutation'.  

`-sic` `--seq_id_column`  
Nombre de la columna que contiene los ID de las secuencias a ser mutadas en `mutations`. Predeterminado: 'seq_ID'.

`-mic` `--mut_id_column`  
Nombre de la columna que contiene los IDs de cada mutación en `mutations`. Predeterminado: Igual que `mut_column`.

`-gtf` `--gtf`  
Ruta a un archivo .gtf. Al proporcionar un archivo fasta de genoma como entrada para 'sequences', puede proporcionar un archivo .gtf aquí y las secuencias de entrada se definirán de acuerdo con los límites de los transcritos, por ejemplo, 'path/to/genome_annotation.gtf'. Predeterminado: Ninguno

`-gtic` `--gtf_transcript_id_column`  
Nombre de la columna en el archivo de entrada `mutations` que contiene el ID del transcrito. En este caso, la columna `seq_id_column` debe contener el número de cromosoma.  
Requerido cuando se proporciona `gtf`. Predeterminado: Ninguno  

**Argumentos opcionales para la generación/filtrado de secuencias mutantes**  
`-k` `--k`  
Longitud de las secuencias que flanquean la mutación. Predeterminado: 30.  
Si k > longitud total de la secuencia, se mantendrá toda la secuencia.  

`-msl` `--min_seq_len`  
Longitud mínima de la secuencia de salida mutante, por ejemplo, 100. Las secuencias mutantes más pequeñas que esto serán descartadas. Predeterminado: Ninguno

`-ma` `--max_ambiguous`  
Número máximo de caracteres 'N' (o 'n') permitidos en la secuencia de salida, por ejemplo, 10. Predeterminado: Ninguno (no se aplicará filtro de caracteres ambiguos)

**Banderas opcionales para la generación/filtrado de secuencias mutantes**  
`-ofr` `--optimize_flanking_regions`  
Elimina nucleótidos de cualquiera de los extremos de la secuencia mutante para asegurar (cuando sea posible) que la secuencia mutante no contenga ningún k-mer que también se encuentre en la secuencia de tipo salvaje/entrada.

`-rswk` `--remove_seqs_with_wt_kmers`  
Elimina las secuencias de salida donde al menos un k-mer también está presente en la secuencia de tipo salvaje/entrada en la misma región.  
Cuando se utiliza con `--optimize_flanking_regions`, solo se eliminarán las secuencias para las cuales un k-mer de tipo salvaje aún está presente después de la optimización.

`-mio` `--merge_identical_off`  
No fusionar secuencias mutantes idénticas en la salida (por defecto, las secuencias idénticas se fusionarán concatenando los encabezados de secuencia para todas las secuencias idénticas).

**Argumentos opcionales para generar salida adicional**  
Esta salida se activa utilizando la bandera `--update_df` y se almacenará en una copia del DataFrame `mutations`.  

`-udf_o` `--update_df_out`  
Ruta al archivo csv de salida que contiene el DataFrame actualizado, por ejemplo, 'path/to/mutations_updated.csv'. Solo válido cuando se usa con `--update_df`.  
Predeterminado: Ninguno -> el nuevo archivo csv se guardará en el mismo directorio que el DataFrame `mutations` con el apéndice '_updated'  

`-ts` `--translate_start`  
(int o str) La posición en la secuencia de nucleótidos de entrada para comenzar a traducir, por ejemplo, 5. Si se proporciona una cadena, debe corresponder a un nombre de columna en `mutations` que contenga las posiciones de inicio del marco de lectura abierto para cada secuencia/mutación. Solo válido cuando se usa con `--translate`.  
Predeterminado: traduce desde el principio de cada secuencia  

`-te` `--translate_end`  
(int o str) La posición en la secuencia de nucleótidos de entrada para finalizar la traducción, por ejemplo, 35. Si se proporciona una cadena, debe corresponder a un nombre de columna en `mutations` que contenga las posiciones de fin del marco de lectura abierto para cada secuencia/mutación. Solo válido cuando se usa con `--translate`.  
Predeterminado: traduce hasta el final de cada secuencia  

**Banderas opcionales para modificar salida adicional**  
`-udf` `--update_df`  
Actualiza el DataFrame de entrada `mutations` para incluir columnas adicionales con el tipo de mutación, la secuencia de nucleótidos de tipo salvaje y la secuencia de nucleótidos mutante (solo válido si `mutations` es un archivo .csv o .tsv).  

`-sfs` `--store_full_sequences`  
Incluye las secuencias completas de tipo salvaje y mutantes en el DataFrame actualizado `mutations` (no solo la sub-secuencia con flancos de longitud k). Solo válido cuando se usa con `--update_df`.  

`-tr` `--translate`  
Agrega columnas adicionales al DataFrame actualizado `mutations` que contienen las secuencias de aminoácidos de tipo salvaje y mutantes. Solo válido cuando se usa con `--store_full_sequences`.  

**Argumentos generales opcionales**  
`-o` `--out`  
Ruta al archivo FASTA de salida que contiene las secuencias mutadas, por ejemplo, 'path/to/output_fasta.fa'.  
Predeterminado: Ninguno -> devuelve una lista de las secuencias mutadas a la salida estándar.  
Los identificadores (que siguen al '>') de las secuencias mutadas en el FASTA de salida serán '>[seq_ID]_[mut_ID]'.

**Banderas generales opcionales**  
`-q` `--quiet`  
Solo en línea de comandos. Previene que se muestre información de progreso.  
Python: Usa `verbose=False` para prevenir que se muestre información de progreso.  


### Ejemplos
```bash
gget mutate ATCGCTAAGCT -m 'c.4G>T'
```
```python
# Python
gget.mutate("ATCGCTAAGCT", "c.4G>T")
```
&rarr; Devuelve ATCTCTAAGCT.  

<br/><br/>

**Lista de secuencias con una mutación para cada secuencia proporcionada en una lista:**  
```bash
gget mutate ATCGCTAAGCT TAGCTA -m 'c.4G>T' 'c.1_3inv' -o mut_fasta.fa
```
```python
# Python
gget.mutate(["ATCGCTAAGCT", "TAGCTA"], ["c.4G>T", "c.1_3inv"], out="mut_fasta.fa")
```
&rarr; Guarda el archivo 'mut_fasta.fa' que contiene:  
```
>seq1_mut1  
ATCTCTAAGCT  
>seq2_mut2  
GATCTA
```

<br/><br/>

**Una mutación aplicada a varias secuencias con k ajustado:**  
```bash
gget mutate ATCGCTAAGCT TAGCTA -m 'c.1_3inv' -k 3
```
```python
# Python
gget.mutate(["ATCGCTAAGCT", "TAGCTA"], "c.1_3inv", k=3)
```
&rarr; Devuelve ['CTAGCT', 'GATCTA'].  

<br/><br/>

**Agregar mutaciones a un genoma completo con salida extendida**  
Entrada principal:  
- información de mutación como un CSV de `mutations` (teniendo `seq_id_column` que contenga información de cromosoma, y `mut_column` que contenga información de mutación con respecto a las coordenadas del genoma)  
- el genoma como el archivo `sequences`  

Dado que estamos pasando la ruta a un archivo gtf al argumento `gtf`, se respetarán los límites de los transcritos (el genoma se dividirá en transcritos). `gtf_transcript_id_column` especifica el nombre de la columna en `mutations` que contiene los IDs de los transcritos correspondientes a los IDs de transcritos en el archivo `gtf`.  

El argumento `optimize_flanking_regions` maximiza la longitud de las secuencias resultantes que contienen la mutación manteniendo la especificidad (ningún k-mer de tipo salvaje se mantendrá).

`update_df` activa la creación de un nuevo archivo CSV con información actualizada sobre cada secuencia de entrada y salida. Este nuevo archivo CSV se guardará como `update_df_out`. Dado que `store_full_sequences` está activado, este nuevo archivo CSV no solo contendrá las secuencias de salida (restringidas en tamaño por las regiones flanqueantes de tamaño `k`), sino también las secuencias completas de entrada y salida. Esto nos permite observar la mutación en el contexto de la secuencia completa. Por último, también estamos agregando las versiones traducidas de las secuencias completas mediante la activación de la bandera `translate`, para que podamos observar cómo cambia la secuencia de aminoácidos resultante. Los argumentos `translate_start` y `translate_end` especifican los nombres de las columnas en `mutations` que contienen las posiciones de inicio y fin del marco de lectura abierto (posiciones de inicio y fin para traducir la secuencia de nucleótidos a una secuencia de aminoácidos), respectivamente.  


```bash
gget mutate \
  -m mutations_input.csv \
  -o mut_fasta.fa \
  -k 4 \
  -sic Chromosome \
  -mic Mutation \
  -gtf genome_annotation.gtf \
  -gtic Ensembl_Transcript_ID \
  -ofr \
  -update_df \
  -udf_o mutations_updated.csv \
  -sfs \
  -tr \
  -ts Translate_Start \
  -te Translate_End \
  genome_reference.fa
```
```python
# Python
gget.mutate(
  sequences="genome_reference.fa",
  mutations="mutations_input.csv",
  out="mut_fasta.fa",
  k=4,
  seq_id_column="Chromosome",
  mut_column="Mutation",
  gtf="genome_annotation.gtf",
  gtf_transcript_id_column="Ensembl_Transcript_ID",
  optimize_flanking_regions=True,
  update_df=True,
  update_df_out="mutations_updated.csv",
  store_full_sequences=True,
  translate=True,
  translate_start="Translate_Start",
  translate_end="Translate_End"
)
```
&rarr; Toma un genoma fasta ('genome_reference.fa') y un archivo gtf ('genome_annotation.gtf') (estos se pueden descargar usando [`gget ref`](ref.md)), así como un archivo 'mutations_input.csv' que contiene:  
```
| Chromosome | Mutation          | Ensembl_Transcript_ID  | Translate_Start | Translate_End |
|------------|-------------------|------------------------|-----------------|---------------|
| 1          | g.224411A>C       | ENST00000193812        | 0               | 100           |
| 8          | g.25111del        | ENST00000174411        | 0               | 294           |
| X          | g.1011_1012insAA  | ENST00000421914        | 9               | 1211          |
```
&rarr; Guarda el archivo 'mut_fasta.fa' que contiene:  
```
>1:g.224411A>C  
TGCTCTGCT  
>8:g.25111del  
GAGTCGAT
>X:g.1011_1012insAA
TTAGAACTT
```
&rarr; Guarda el archivo 'mutations_updated.csv' que contiene:  
```

| Chromosome | Mutation          | Ensembl_Transcript_ID  | mutation_type | wt_sequence | mutant_sequence | wt_sequence_full  | mutant_sequence_full | wt_sequence_aa_full | mutant_sequence_aa_full |
|------------|-------------------|------------------------|---------------|-------------|-----------------|-------------------|----------------------|---------------------|-------------------------|
| 1          | g.224411A>C       | ENSMUST00000193812     | Substitution  | TGCTATGCT   | TGCTCTGCT       | ...TGCTATGCT...   | ...TGCTCTGCT...      | ...CYA...           | ...CSA...               |
| 8          | g.25111del        | ENST00000174411        | Deletion      | GAGTCCGAT   | GAGTCGAT        | ...GAGTCCGAT...   | ...GAGTCGAT...       | ...ESD...           | ...ES...                |
| X          | g.1011_1012insAA  | ENST00000421914        | Insertion     | TTAGCTT     | TTAGAACTT       | ...TTAGCTT...     | ...TTAGAACTT...      | ...A...             | ...EL...                |

```

# Citar  
Si utiliza `gget mutate` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)
