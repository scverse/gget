[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/virus.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget virus 🦠  

Descargue secuencias nucleotídicas virales, junto con metadatos ricos y vinculados, de toda la International Nucleotide Sequence Database Collaboration ([INSDC](https://www.insdc.org/)), incluyendo NCBI, [ENA](https://www.ebi.ac.uk/ena/browser/) y [DDBJ](https://www.ddbj.nig.ac.jp/index-e.html) (a través de [NCBI Virus](https://www.ncbi.nlm.nih.gov/labs/virus/)), con la opción de enriquecer adicionalmente los resultados usando metadatos de NCBI GenBank (por ejemplo, anotaciones de genes y proteínas, secuencias de aminoácidos y más). `gget virus` aplica filtros secuenciales tanto del lado del servidor como locales para descargar de forma eficiente conjuntos de datos personalizados.

Formato de salida: archivos FASTA, CSV y JSONL guardados en una carpeta de salida.  

[Cuaderno de Google Colab sin código y compartible para descargar secuencias virales.](https://colab.research.google.com/github/pachterlab/gget_examples/blob/main/gget_virus/gget_virus_colab.ipynb)

Este módulo fue escrito por [Ferdous Nasri](https://github.com/ferbsx).

**Nota**: Para consultas de SARS-CoV-2 y Alphainfluenza (Influenza A), `gget virus` utiliza los paquetes de datos optimizados en caché de NCBI mediante la [NCBI datasets CLI](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/download-and-install/). El binario de la CLI de datasets se incluye con gget para las principales plataformas—no se requiere instalación adicional. Si ya tienes la CLI `datasets` instalada en tu sistema, gget usará automáticamente tu instalación existente.

**Argumento posicional**  
`virus`
Nombre del taxón viral (p. ej., 'Zika virus'), ID de taxón (p. ej., '2697049'), número de acceso de NCBI (p. ej., 'NC_045512.2'), lista de números de acceso separados por espacios (p. ej., 'NC_045512.2 MN908947.3 MT020781.1') o ruta a un archivo de texto que contenga números de acceso (uno por línea) (p. ej., 'path/to/text.txt').

Añada `--is_accession` al proporcionar un número de acceso de NCBI. Añada `--is_sars_cov2` o `--is_alphainfluenza` para la descarga optimizada de secuencias de SARS-CoV-2 o Alphainfluenza, respectivamente.

Para descargas en caché de SARS-CoV-2 y Alphainfluenza, se admite:

* Acceso único: `NC_045512.2`
* Lista separada por espacios: `NC_045512.2 MN908947.3 MT020781.1`
* Ruta a archivo de texto: `accessions.txt` (un número de acceso por línea)

Use la opción `--download_all_accessions` para aplicar filtros sin buscar un virus específico.

**Argumentos opcionales**  

_Filtros de hospedador_  

`--host`  
Filtra por nombre del organismo hospedador o ID de Taxonomía de NCBI (p. ej. 'human', 'Aedes aegypti', `1335626`).

_Filtros de Secuencia y Gen_  

`--nuc_completeness`  
Filtrar por integridad del nucleótido. Una de las siguientes opciones: 'complete' o 'partial'.  
Establezca 'complete' para devolver únicamente secuencias de nucleótidos marcadas como completas; establezca 'partial' para devolver únicamente secuencias marcadas como parciales.

`--min_seq_length`  
Filtra por longitud mínima de secuencia.

`--max_seq_length`  
Filtra por longitud máxima de secuencia.

`--min_gene_count`  
Filtra por número mínimo de genes.  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

`--max_gene_count`  
Filtra por número máximo de genes.  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

`--min_protein_count`  
Filtra por número mínimo de proteínas.

`--max_protein_count`  
Filtra por número máximo de proteínas.

`--min_mature_peptide_count`  
Filtra por número mínimo de péptidos maduros.  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

`--max_mature_peptide_count`  
Filtra por número máximo de péptidos maduros.  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

`--max_ambiguous_chars`  
Filtra por número máximo de caracteres nucleotídicos ambiguos (N).

`--has_proteins`  
Filtra por secuencias que contengan proteínas o genes específicos (p. ej. 'spike', 'ORF1ab'). Puede ser un solo nombre de proteína o una lista de nombres de proteínas. Cualquier proteína que coincida mantendrá la secuencia.  
Línea de comandos: `--has_proteins spike` o `--has_proteins hemagglutinin,neuraminidase` (separados por comas, sin espacios)  
Python: `has_proteins="spike"` o `has_proteins=["spike", "ORF1ab"]`  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

`--segment`  
Filtra por secuencias con segmento(s) específico(s) (p. ej. 'HA', 'NA'). Puede ser un solo nombre de segmento o una lista de nombres de segmentos. Cualquier segmento que coincida mantendrá la secuencia.  
Línea de comandos: `--segment HA` o `--segment HA,NA,PB1` (separados por comas, sin espacios)  
Python: `segment="HA"` o `segment=["HA", "NA", "PB1"]`

`--annotated`  
`'true'` o `'false'`. Filtra por secuencias que han sido anotadas con información de genes/proteínas.  
Línea de comandos: `--annotated true` para obtener únicamente secuencias anotadas con información de genes/proteínas, o `--annotated false` para excluirlas.  
Python: `annotated=True` o `annotated=False` (`annotated=None` para no aplicar ningún filtro).  

`--lab_passaged`  
`'true'` o `'false'`. Filtra a favor o en contra de muestras pasadas por laboratorio (*lab-passaged*).  
Línea de comandos: `--lab_passaged true` para obtener únicamente muestras pasadas por laboratorio, o `--lab_passaged false` para excluirlas.  
Python: `lab_passaged=True` o `lab_passaged=False` (`lab_passaged=None` para no aplicar ningún filtro).

`--vaccine_strain`  
Filtra a favor o en contra de secuencias de cepas de vacunas.  
Línea de comandos: `--vaccine_strain true` para obtener solo cepas de vacunas, o `--vaccine_strain false` para excluirlas.  
Python: `vaccine_strain=True` o `vaccine_strain=False` (`vaccine_strain=None` para no aplicar ningún filtro).

`--provirus`  
Filtra a favor o en contra de secuencias provirales/integradas.  
Línea de comandos: `--provirus true` para obtener solo secuencias provirales, o `--provirus false` para excluirlas.  
Python: `provirus=True` o `provirus=False` (`provirus=None` para no aplicar ningún filtro).  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).


_Filtros de fecha_  

`--min_collection_date`  
Filtra por fecha mínima de recolección de la muestra (YYYY-MM-DD).

`--max_collection_date`  
Filtra por fecha máxima de recolección de la muestra (YYYY-MM-DD).

`--min_release_date`  
Filtra por fecha mínima de liberación de la secuencia (YYYY-MM-DD).

`--max_release_date`  
Filtra por fecha máxima de liberación de la secuencia (YYYY-MM-DD).

_Filtros de ubicación y remitente_

`--geographic_location`  
Filtra por ubicación geográfica de la recolección de la muestra (p. ej. 'USA', 'Asia').

`--submitter_name`  
Filtra por el nombre del autor remitente. Puede ser un solo nombre o una lista de nombres. Cualquier nombre que coincida mantendrá la secuencia.  
Línea de comandos: `--submitter_name "John Doe"` o `--submitter_name "John Doe,Jane Smith"` (separados por comas)  
Python: `submitter_name="John Doe"` o `submitter_name=["John Doe", "Jane Smith"]`

`--submitter_institution`  
Filtra por la institución del remitente. Puede ser una sola institución o una lista de instituciones. Cualquier institución que coincida mantendrá la secuencia.  
Línea de comandos: `--submitter_institution CDC` o `--submitter_institution CDC,NIH,WHO` (separados por comas, sin espacios)  
Python: `submitter_institution="CDC"` o `submitter_institution=["CDC", "NIH", "WHO"]`

`--submitter_country`  
Filtra por el país del remitente de la secuencia. Puede ser un solo país o una lista de países.  
Línea de comandos: `--submitter_country USA` o `--submitter_country USA,Germany,Japan` (separados por comas, sin espacios)  
Python: `submitter_country="USA"` o `submitter_country=["USA", "Germany", "Japan"]`

`--source_database`  
Filtra por base de datos de origen. Uno de: 'genbank' o 'refseq'.

_Filtros de muestra y aislado_

`--isolate`  
Filtra por nombre de aislado (p. ej. 'Wuhan-hu-1'). Puede ser un solo nombre de aislado o una lista de nombres de aislados. Cualquier aislado que coincida mantendrá la secuencia.  
Línea de comandos: `--isolate Wuhan-hu-1` o `--isolate Wuhan-hu-1,LASV_3609` (separados por comas, sin espacios)  
Python: `isolate="Wuhan-hu-1"` o `isolate=["Wuhan-hu-1", "LASV_3609"]`

`--isolation_source`  
Filtra por fuente de aislamiento (tejido/espécimen/fuente) (p. ej. 'blood', 'serum'). Puede ser una sola fuente o una lista de fuentes. Cualquier fuente que coincida mantendrá la secuencia.  
Línea de comandos: `--isolation_source blood` o `--isolation_source blood,serum,plasma` (separados por comas, sin espacios)  
Python: `isolation_source="blood"` o `isolation_source=["blood", "serum", "plasma"]`

`--env_source`  
Filtra por fuente ambiental (p. ej. 'water', 'sewage'). Excluye cualquier secuencia con hospedadores nombrados. NO combinar con el filtro `--host`. Puede ser una sola fuente o una lista de fuentes. Cualquier fuente que coincida mantendrá la secuencia.  
Línea de comandos: `--env_source water` o `--env_source water,soil,air` (separados por comas, sin espacios)  
Python: `env_source="water"` o `env_source=["water", "soil", "air"]`  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

_Filtros de clasificación viral_

`--genotype`  
Filtra por genotipo (p. ej. 'H5N1', 'H3N2'). Puede ser un solo genotipo o una lista de genotipos. Cualquier genotipo que coincida mantendrá la secuencia.  
Línea de comandos: `--genotype H5N1` o `--genotype H5N1,H3N2` (separados por comas, sin espacios)  
Python: `genotype="H5N1"` o `genotype=["H5N1", "H3N2"]`  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

`--gen_mol_type`  
Filtra por tipo de molécula genómica (p. ej. 'dsDNA', 'RNA'). Puede ser un solo tipo o una lista de tipos. Cualquier tipo de molécula que coincida mantendrá la secuencia.  
Línea de comandos: `--gen_mol_type dsDNA` o `--gen_mol_type RNA,dsRNA` (separados por comas, sin espacios)  
Python: `gen_mol_type="dsDNA"` o `gen_mol_type=["RNA", "dsRNA"]`  
**Nota:** El uso de este filtro habilita automáticamente la obtención de metadatos de GenBank (`-g`).

_Filtros específicos de SARS-CoV-2_

`--lineage`  
Filtra por linaje Pango de SARS-CoV-2 (p. ej. 'B.1.1.7', 'P.1'). Puede ser un solo linaje o una lista de linajes. Cualquier linaje que coincida mantendrá la secuencia.  
Línea de comandos: `--lineage B.1.1.7` o `--lineage B.1.1.7,P.1` (separados por comas, sin espacios)  
Python: `lineage="B.1.1.7"` o `lineage=["B.1.1.7", "P.1"]`

_Configuración del pipeline_

`--genbank_batch_size`  
Tamaño de lote para solicitudes a la API de metadatos de GenBank. Por defecto: 200. Lotes más grandes son más rápidos pero pueden ser más propensos a timeouts.  

`-o` `--out`  
Ruta a la carpeta donde se guardarán los resultados. Por defecto: `./gget_virus_output/{virus}_{timestamp}/` en el directorio de trabajo actual.  
Python: `outfolder="path/to/folder"`

`--baseline`  
Ruta a un archivo de metadatos de referencia (CSV, JSONL, JSON o texto) que contiene accesiones a omitir. Solo se descargarán las accesiones nuevas que no se encuentren en la referencia. Útil para actualizaciones incrementales o para reanudar después de fallos de la API.  
Los archivos CSV deben tener una columna 'accession'. Los archivos de texto deben tener una accesión por línea.  
Python: `baseline_metadata="path/to/previous_metadata.csv"`

`--merge-results`  
Al usar `--baseline`, fusiona los resultados nuevos con la referencia en un único archivo de salida combinado. Este es el comportamiento predeterminado.  
Python: `merge_results=True` (predeterminado)

`--no-merge`  
Al usar `--baseline`, genera los resultados nuevos por separado de la referencia en lugar de fusionarlos. Crea `{virus}_new.csv` (solo secuencias nuevas) y conserva la referencia como referencia.  
Python: `merge_results=False`

**Banderas**  
`-a` `--is_accession`  
Bandera para indicar que el argumento posicional `virus` es un número de acceso, una lista de accesiones separadas por espacios, o una ruta a un archivo de texto que contiene números de acceso (uno por línea).

`--download_all_accessions`  
Use esta bandera al aplicar filtros sin buscar un virus específico (deje el argumento `virus` vacío).  
⚠️ **ADVERTENCIA**: Si no especifica filtros adicionales, esta bandera descargará TODAS las secuencias virales disponibles de NCBI (toda la taxonomía de Virus, taxon ID 10239). Este es un conjunto de datos extremadamente grande que puede tardar muchas horas en descargarse y requerir un espacio considerable en disco. Úsela con precaución y asegúrese de contar con suficiente almacenamiento y ancho de banda. Cuando esta bandera está activada, el argumento `virus` se ignora.

`--is_sars_cov2`  
Usa los paquetes de datos optimizados en caché de NCBI para una consulta de SARS-CoV-2. Esto proporciona descargas más rápidas y confiables. El sistema puede detectar automáticamente consultas por nombre de taxón de SARS-CoV-2, pero para consultas basadas en accesiones debes establecer esta bandera explícitamente.

`--is_alphainfluenza`  
Usa los paquetes de datos optimizados en caché de NCBI para una consulta de Alphainfluenza (virus de la Influenza A). Esto proporciona descargas más rápidas y confiables para grandes conjuntos de datos de Influenza A. El sistema puede detectar automáticamente consultas por nombre de taxón de Alphainfluenza, pero para consultas basadas en accesiones debes establecer esta bandera explícitamente.

`-g` `--genbank_metadata`  
Obtiene y guarda metadatos adicionales detallados desde GenBank, incluyendo fechas de recolección, detalles del hospedador y referencias de publicaciones, en un archivo separado `{virus}_genbank_metadata.csv` (además de volcados completos XML/CSV dumps).  
**Nota:** Esta bandera se habilita automáticamente al usar cualquiera de los siguientes filtros dependientes de GenBank: `--has_proteins`, `--gen_mol_type`, `--env_source`, `--genotype`, `--provirus`, `--min_gene_count`, `--max_gene_count`, `--min_mature_peptide_count`, `--max_mature_peptide_count`.

`--proteins_complete`  
Bandera para incluir solo secuencias donde todas las proteínas anotadas estén completas.  

`-kt` `--keep_temp`  
Bandera para conservar todos los archivos intermedios/temporales generados durante el procesamiento. Por defecto, solo se conservan los archivos de salida finales.

`-q` `--quiet`  
Uso limitado para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False`.  

### Ejemplo

```bash
gget virus "Zika virus" --nuc_completeness complete --host human --out zika_data
````

```python
# Python
import gget

gget.virus(
  "Zika virus",
  nuc_completeness="complete",
  host="human",
  outfolder="zika_data"
)
```

→ Descarga genomas completos de Zika virus de hospedadores humanos. Los resultados se guardan en la carpeta `zika_data` como `Zika_virus_sequences.fasta`, `Zika_virus_metadata.csv`, `Zika_virus_metadata.jsonl` y `command_summary.txt`.


<br><br>
**Descargar un genoma de referencia específico de SARS-CoV-2 usando su número de acceso:**

```bash
gget virus NC_045512.2 --is_accession --is_sars_cov2
```

```python
# Python
import gget

gget.virus("NC_045512.2", is_accession=True, is_sars_cov2=True)
```

→ Uses the optimized download method for SARS-CoV-2 to fetch the reference genome and its metadata.

<br><br>
**Descargar secuencias de SARS-CoV-2 con optimización en caché Y metadatos de GenBank:**

```bash
gget virus "SARS-CoV-2" --host human --nuc_completeness complete --min_seq_length 29000 --genbank_metadata
```

```python
# Python
import gget

gget.virus(
  "SARS-CoV-2",
  host="human",
  nuc_completeness="complete",
  min_seq_length=29000,
  genbank_metadata=True,
  is_sars_cov2=True,
  outfolder="covid_data"
)
```

→ Uses cached download for speed (via NCBI's SARS-CoV-2 data packages when available), applies the sequence length filter post-download, and fetches detailed GenBank metadata for all filtered sequences.

<br><br>
**Descargar secuencias del virus de la Influenza A con caché optimizada y filtrado posterior a la descarga:**

```bash
gget virus "Influenza A virus" --host human --nuc_completeness complete --max_seq_length 15000 --genbank_metadata --is_alphainfluenza
```

```python
# Python
import gget

gget.virus(
  "Influenza A virus",
  host="human",
  nuc_completeness="complete",
  max_seq_length=15000,
  genbank_metadata=True,
  is_alphainfluenza=True,
  outfolder="influenza_a_data"
)
```

→ Usa los paquetes de datos en caché de NCBI para Alphainfluenza para descargar genomas completos de Influenza A de hospedadores humanos mucho más rápido que el método estándar de API, luego aplica el filtro de longitud de secuencia y obtiene metadatos de GenBank.

<br><br>
**Reanudar una descarga fallida usando deduplicación de referencia:**

```bash
gget virus "SARS-CoV-2" --host human --nuc_completeness complete --baseline previous_run/SARS_CoV_2_metadata.csv --merge-results -o covid_update
```

```python
# Python
import gget

gget.virus(
  "SARS-CoV-2",
  host="human",
  nuc_completeness="complete",
  baseline_metadata="previous_run/SARS_CoV_2_metadata.csv",
  merge_results=True,
  outfolder="covid_update"
)
```

→ Carga las accesiones del archivo de metadatos de una ejecución anterior, omite las ya descargadas y fusiona los resultados nuevos con la referencia en una salida combinada única.

---

### Archivos de salida

`gget virus` guarda los resultados en la carpeta de salida especificada (por defecto: `./gget_virus_output/{virus}_{timestamp}/`). Los archivos de salida estándar son:

| Archivo | Descripción |
|---------|-------------|
| `{virus}_sequences.fasta` | Secuencias nucleotídicas en formato FASTA |
| `{virus}_metadata.csv` | Metadatos de todas las secuencias en formato CSV |
| `{virus}_metadata.jsonl` | Metadatos en formato JSONL (un objeto JSON por línea) |
| `{virus}_genbank_metadata.csv` | Metadatos detallados de GenBank (solo cuando se usa `-g` o se habilita automáticamente) |
| `{virus}_genbank_metadata_full.xml` | Volcado XML completo de GenBank (solo cuando se usa `-g`) |
| `{virus}_genbank_metadata_full.csv` | Volcado CSV completo de GenBank - formato XML legible (solo cuando se usa `-g`) |
| `command_summary.txt` | Resumen de ejecución con estadísticas, archivos de salida y errores |

### Archivo de resumen de comando

Cada ejecución de `gget virus` genera un archivo `command_summary.txt` en la carpeta de salida, proporcionando un registro completo de la ejecución, incluyendo el comando exacto utilizado, estadísticas del conjunto de datos, archivos de salida con tamaños y detalles de cualquier error u operación fallida. Esto es útil para reproducibilidad, depuración y recuperación manual después de fallos parciales.

**Ejemplo de `command_summary.txt` para una ejecución exitosa:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-03-15 14:30:22
Output Folder: /home/user/zika_data

--------------------------------------------------------------------------------
SOFTWARE VERSIONS
--------------------------------------------------------------------------------
gget version: 0.28.10
NCBI datasets version: 16.40.2

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus "Zika virus" --nuc_completeness complete --host human --out zika_data

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
✅ Command completed successfully

--------------------------------------------------------------------------------
RUNTIME
--------------------------------------------------------------------------------
Total wall-clock time: 4m 12s (252.3 seconds)

--------------------------------------------------------------------------------
MEMORY USAGE
--------------------------------------------------------------------------------
Process RSS (resident memory): 512.4 MB
Process VMS (virtual memory): 1024.8 MB
Process memory percent: 3.2%
System total memory: 16384 MB
System available memory: 12288 MB
System memory used: 25.0%

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 1523
After metadata filtering: 1523
Final sequences (after all filters): 1523

--------------------------------------------------------------------------------
FILTER BREAKDOWN BY STAGE
--------------------------------------------------------------------------------

No records were filtered out at any stage.

--------------------------------------------------------------------------------
DETAILED STATISTICS
--------------------------------------------------------------------------------
Unique hosts: 1
  - Homo sapiens

Unique geographic locations: 42
  - Brazil
  - Colombia
  - ...

Sequence length range: 10217 - 10839 bp
Average sequence length: 10708 bp

Completeness breakdown:
  - complete: 1523

Source database breakdown:
  - GenBank: 1510
  - RefSeq: 13

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
FASTA Sequences: Zika_virus_sequences.fasta (16.02 MB)
CSV Metadata: Zika_virus_metadata.csv (1.85 MB)
JSONL Metadata: Zika_virus_metadata.jsonl (3.41 MB)

END OF SUMMARY
```

<br>

**Ejemplo de `command_summary.txt` después de un error del servidor de la API:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-03-19 21:03:22
Output Folder: /home/user/11632_20260319_210251

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus 11632 --nuc_completeness complete --geographic_location Gabon --host human

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
✗ Command failed
Error: HTTP error while fetching virus metadata: 500 Server Error: Internal Server
Error for url: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/11632/dataset_report
?filter.complete_only=true&filter.host=human&filter.geo_location=Gabon&page_size=1000

🔧 SERVER ERROR DETECTED: NCBI's API is experiencing temporary server-side issues.
This is not a problem with your query.
Try again in a few minutes, or consider using more specific filters to reduce the dataset size.

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 0
After metadata filtering: 0
Final sequences (after all filters): 0

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
No output files generated

END OF SUMMARY
```

<br>

**Ejemplo de `command_summary.txt` con lotes de metadatos fallidos e instrucciones de recuperación:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-04-01 10:15:33
Output Folder: /home/user/hiv_data

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus "HIV-1" --host human --nuc_completeness complete

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
✗ Command failed
Error: HTTP error while fetching virus metadata after 15 retries

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 8500
After metadata filtering: 0
Final sequences (after all filters): 0

--------------------------------------------------------------------------------
💾 PARTIAL METADATA RECOVERY
--------------------------------------------------------------------------------
Partial metadata saved: /home/user/hiv_data/HIV_1_partial_metadata_api_failure.jsonl

Recovery command:
  gget virus HIV-1 --baseline /home/user/hiv_data/HIV_1_partial_metadata_api_failure.jsonl --merge-results -o /home/user/hiv_data

--------------------------------------------------------------------------------
⚠️ FAILED OPERATIONS - MANUAL RETRY REQUIRED
--------------------------------------------------------------------------------

📍 FAILED METADATA BATCHES (2 batches):

   Batch 3: 1000 accessions
   Error: 500 Server Error: Internal Server Error
   API URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/11676/dataset_report?...

   Batch 7: 1000 accessions
   Error: ConnectionError: Connection reset by peer
   API URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/taxon/11676/dataset_report?...

📍 PAGINATION TIMEOUTS (1 pages):
   Page 5: 4000 records retrieved
   Error: ReadTimeout: HTTPSConnectionPool read timed out

💡 RECOVERY INSTRUCTIONS:
   1. Copy the URL from above and paste it into your browser
   2. Save the downloaded file manually
   3. Retry the command with updated filters (e.g., stricter date ranges)
   4. If the issue persists, NCBI servers may be temporarily unavailable

   5. RESUME with baseline deduplication:
      gget virus HIV-1 --baseline /home/user/hiv_data/HIV_1_partial_metadata_api_failure.jsonl --merge-results -o /home/user/hiv_data

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
No output files generated

END OF SUMMARY
```

<br>

**Ejemplo de `command_summary.txt` completado con advertencias de GenBank y lotes de secuencias fallidos:**

```
GGET VIRUS COMMAND SUMMARY

Execution Date: 2026-03-20 08:45:11
Output Folder: /home/user/ebola_data

--------------------------------------------------------------------------------
COMMAND LINE
--------------------------------------------------------------------------------
gget virus "Ebola virus" --host human --genbank_metadata --out ebola_data

--------------------------------------------------------------------------------
EXECUTION STATUS
--------------------------------------------------------------------------------
Command completed with warnings
⚠️ GenBank metadata retrieval failed: Connection timed out after 5 retries

--------------------------------------------------------------------------------
RUNTIME
--------------------------------------------------------------------------------
Total wall-clock time: 12m 45s (765.2 seconds)

--------------------------------------------------------------------------------
MEMORY USAGE
--------------------------------------------------------------------------------
Process RSS (resident memory): 1024.5 MB
Process VMS (virtual memory): 2048.3 MB
Process memory percent: 6.3%
System total memory: 16384 MB
System available memory: 10240 MB
System memory used: 37.5%

--------------------------------------------------------------------------------
SEQUENCE STATISTICS
--------------------------------------------------------------------------------
Total records from API: 2150
After metadata filtering: 2150
After GenBank metadata filtering: 2130
Final sequences (after all filters): 2130

--------------------------------------------------------------------------------
FILTER BREAKDOWN BY STAGE
--------------------------------------------------------------------------------

GenBank metadata filtering (records excluded):
  genbank_fetch_failed: 20

--------------------------------------------------------------------------------
⚠️ FAILED OPERATIONS - MANUAL RETRY AVAILABLE
--------------------------------------------------------------------------------

📍 FAILED SEQUENCE DOWNLOAD BATCHES (1 batches):

   Batch 4
   Error: 503 Service Unavailable
   Retry URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/genome/download?accessions=...

📍 SEQUENCE FETCH FAILURES (1 operations):

   Operation: batch_sequence_download
   Accessions: 20
   Error: ReadTimeout: HTTPSConnectionPool read timed out
   Retry URL: https://api.ncbi.nlm.nih.gov/datasets/v2/virus/genome/download?accessions=...

💡 RECOVERY INSTRUCTIONS:
   1. Copy the URL from above and paste it into your browser
   2. Save the downloaded file manually
   3. Retry the command with updated filters (e.g., stricter date ranges)
   4. If the issue persists, NCBI servers may be temporarily unavailable

--------------------------------------------------------------------------------
OUTPUT FILES
--------------------------------------------------------------------------------
FASTA Sequences: Ebola_virus_sequences.fasta (24.31 MB)
CSV Metadata: Ebola_virus_metadata.csv (2.10 MB)
JSONL Metadata: Ebola_virus_metadata.jsonl (4.56 MB)

END OF SUMMARY
```

El archivo de resumen rastrea los siguientes tipos de fallos, cada uno con detalles accionables (mensajes de error, URLs para reintento manual, comandos de recuperación):

- **Tiempo de espera de API agotado** — La API de NCBI agotó el tiempo de espera durante la obtención inicial de metadatos.
- **Respuesta vacía de la API** — La API no devolvió resultados para la consulta dada.
- **Lotes de metadatos fallidos** — Una o más solicitudes de API paginadas para metadatos fallaron después de reintentos.
- **Tiempos de espera/errores de paginación** — Páginas específicas de resultados agotaron el tiempo de espera o devolvieron errores durante la paginación.
- **Lotes de descarga de secuencias fallidos** — Uno o más lotes de descargas de secuencias (FASTA) fallaron.
- **Fallos de obtención de secuencias** — Operaciones individuales de descarga de secuencias fallaron.
- **Errores de metadatos de GenBank** — La obtención de metadatos de GenBank falló (el comando aún se completa con una advertencia).
- **Recuperación parcial de metadatos** — Cuando la API falla a mitad de descarga, los metadatos parciales se guardan en un archivo JSONL con un comando de recuperación para reanudar usando `--baseline`.


#### [Más ejemplos](https://github.com/pachterlab/gget_examples/tree/main/gget_virus)

# Citar

Si utilizas `gget virus` en una publicación, por favor cita los siguientes artículos:

  - Nasri, F. et al (2026). En preparación.

  - Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

  - O'Leary, N.A., Cox, E., Holmes, J.B. et al (2024). Exploring and retrieving sequence and metadata for species across the tree of life with NCBI Datasets. Sci Data 11, 732. [https://doi.org/10.1038/s41597-024-03571-y](https://doi.org/10.1038/s41597-024-03571-y)
