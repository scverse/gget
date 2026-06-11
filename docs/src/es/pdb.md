[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/pdb.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget pdb 🔮
Obtenga la estructura o los metadatos de una proteína usando data de [RCSB Protein Data Bank (PDB)](https://www.rcsb.org/).  
Regresa: El archivo 'pdb' se regresa en formato PDB. Todos los demás datos se regresan en formato JSON.

**Parámetro posicional**  
`pdb_id`  
ID del tipo PDB, p. ej. '7S7U'.  

**Parámetros optionales**  
 `-r` `--resource`  
Define el tipo de información a regresar. Uno de los siguientes:  
 'pdb': Regresa la estructura de la proteína en formato PDB (regresa por defecto).  
 'entry': Regresa información sobre las estructuras PDB en el nivel superior de la organización de datos PDB jerárquicos.  
 'pubmed': Regresa anotaciones de PubMed (datos integrados de PubMed) para la cita principal de un ID PDB.  
 'assembly': Regresa información sobre estructuras PDB en el nivel de estructura cuaternaria.  
 'branched_entity': Regresa la descripción de la entidad ramificada (defina el ID de la entidad como `identifier`).  
 'nonpolymer_entity': Regresa datos de entidades no poliméricas (defina el ID de la entidad como `identifier`).  
 'polymer_entity': Regresa datos de entidades poliméricas (defina el ID de la entidad como `identifier`).  
 'uniprot': Regresa anotaciones UniProt para una entidad macromolecular (defina el ID de la entidad como `identifier`).  
 'branched_entity_instance': Regresa la descripción de instancia de entidad ramificada (defina el ID de cadena como `identifier`).  
 'polymer_entity_instance': Regresa datos de instancia de entidad polimérica (también conocida como cadena) (defina el ID de cadena como `identifier`).  
 'nonpolymer_entity_instance': Regresa datos de instancia de entidad no polimérica (defina el ID de cadena como `identifier`).

`-i` `--identifier`  
Este parámetro se puede utilizar para definir el ID de ensamblaje, entidad o cadena (po defecto: None). Los IDs de ensamblaje/entidad son números (p. ej., 1) y los IDs de cadena son letras (p. ej., 'A').

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/7S7U.pdb (o 7S7U_entry.json). Por defecto: salida estándar (STDOUT).  
Para Python, usa `save=True` para guardar los resultados en el directorio de trabajo actual.  

### Por ejemplo
```bash
gget pdb 7S7U -o 7S7U.pdb
```
```python
# Python
gget.pdb("7S7U", save=True)
```
&rarr; Guarda la estructura de 7S7U en formato PDB como '7S7U.pdb' en el directorio de trabajo actual.

**Encuentre estructuras cristalinas de PDB para un análisis comparativo de la estructura de proteínas:**  
```bash
# Encuentre IDs de PDB asociados con un ID de Ensembl
gget info ENSG00000130234

# Alternativamente: como que muchas entradas en el PDB no tienen ID de Ensembl vinculados,
# es probable que encuentre más entradas de PDB BLASTing la secuencia contra el PDB:

# Obtenga la secuencia de aminoácidos
gget seq --translate ENSG00000130234 -o gget_seq_results.fa

# BLAST la secuencia de aminoácidos para encontrar estructuras similares en el PDB
gget blast --database pdbaa gget_seq_results.fa

# Obtenga archivos PDB de los IDs de PDB regresados por gget blast para un análisis comparativo
gget pdb 7DQA -o 7DQA.pdb
gget pdb 7CT5 -o 7CT5.pdb
```
```python
# Encuentre IDs de PDB asociados con un ID de Ensembl
gget.info("ENSG00000130234")

# Alternativamente: como que muchas entradas en el PDB no tienen ID de Ensembl vinculados,
# es probable que encuentre más entradas de PDB BLASTing la secuencia contra el PDB:

# Obtenga la secuencia de aminoácidos
gget.seq("ENSG00000130234", translate=True, save=True)

# BLAST la secuencia de aminoácidos para encontrar estructuras similares en el PDB
gget.blast("gget_seq_results.fa", database="pdbaa")

# Obtenga archivos PDB de los IDs de PDB regresados por gget blast para un análisis comparativo
gget.pdb("7DQA", save=True)
gget.pdb("7CT5", save=True)
```
&rarr; Este caso de uso ejemplifica cómo encontrar archivos PDB para un análisis comparativo de la estructura de las proteínas asociado con IDs de Ensembl o secuencias de aminoácidos. Los archivos PDB obtenidos también se pueden comparar con las estructuras predichas generadas por [`gget alphafold`](alphafold.md). Los archivos PDB se pueden ver de forma interactiva en 3D [aquí](https://rcsb.org/3d-view), o usando programas como [PyMOL](https://pymol.org/) o [Blender](https://www.blender.org/). Múltiple archivos PDB se pueden visualizar para comparación [aquí](https://rcsb.org/alignment).

#### [Más ejemplos](https://github.com/pachterlab/gget_examples)

# Citar  
Si utiliza `gget pdb` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Berman HM, Westbrook J, Feng Z, Gilliland G, Bhat TN, Weissig H, Shindyalov IN, Bourne PE. The Protein Data Bank. Nucleic Acids Res. 2000 Jan 1;28(1):235-42. doi: [10.1093/nar/28.1.235](https://doi.org/10.1093/nar/28.1.235). PMID: 10592235; PMCID: PMC102472.
