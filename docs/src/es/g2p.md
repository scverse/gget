[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/g2p.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no es especificado de otra manera. Las banderas son designadas como cierto o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede obtener desde Terminal con la bandera `-h` `--help`.  
# gget g2p 🧬➜🧪
Consulta el [portal Genomics 2 Proteins (G2P)](https://g2p.broadinstitute.org/) para vincular genes/proteínas con anotaciones estructurales y funcionales a nivel de residuo (p. ej. pLDDT de AlphaFold, sitios de UniProt, bolsillos predichos, PTMs), el mapa gen–transcrito–proteína–isoforma–estructura, y alineamientos entre isoformas.  

Produce: Un Dataframe con la información G2P solicitada.  

Este módulo fue escrito por [Elarwei](https://github.com/Elarwei001).

**Parámetro posicional**  
`gene`  
Símbolo del gen, p. ej. BRCA1.  

**Otros parámetros requeridos**  
`-u` `--uniprot_id`  
Identificador UniProt, p. ej. P38398. Para `--resource alignment` esta es la isoforma canónica (p. ej. P01130-1).  
Consejo: encuentra el ID de UniProt de un gen con [`gget info`](info.md).  

**Parámetros optionales**  
`-r` `--resource`  
Define el tipo de información a producir (se usa por defecto: 'features'):  
`features`: Tabla de características de la proteína por residuo (pLDDT de AlphaFold, sitios de UniProt, estructura secundaria, bolsillos predichos, PTMs, etc.).  
`map`: Mapa de gen → transcrito → isoforma de proteína → estructura (identificadores UniProt/Ensembl/RefSeq/PDB).  
`alignment`: Alineamiento de secuencia a nivel de residuo entre dos isoformas (requiere `--isoform`; `--uniprot_id` es la isoforma canónica).  

`-i` `--isoform`  
Identificador UniProt de una isoforma alternativa (p. ej. P01130-2). Requerido cuando `--resource alignment`. Por defecto: None.  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.json. Por defecto: salida estándar (STDOUT).  
Para Python, use `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-csv` `--csv`  
Solo para Terminal. Produce los resultados en formato CSV en lugar de JSON.  
Para Python, usa `json=False` (se usa por defecto) para producir un Dataframe.  

`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa.  

### Ejemplo
```bash
# Características de la proteína por residuo para BRCA1 (pLDDT de AlphaFold, sitios de UniProt, ...)
gget g2p BRCA1 -u P38398
```
```python
# Python
gget.g2p("BRCA1", uniprot_id="P38398", resource="features")
```
&rarr; Produce un Dataframe con una fila por residuo de la proteína BRCA1 (UniProt P38398) y sus anotaciones estructurales/funcionales.  

<br/><br/>

```bash
# Mapa gen -> transcrito -> isoforma -> estructura (CSV)
gget g2p BRCA1 -u P38398 -r map --csv
```
```python
# Python
gget.g2p("BRCA1", uniprot_id="P38398", resource="map")
```
&rarr; Produce el mapeo de BRCA1 a sus isoformas de UniProt, identificadores de Ensembl/RefSeq, y estructuras del PDB.  

<br/><br/>

```bash
# Alineamiento a nivel de residuo entre dos isoformas de LDLR
gget g2p LDLR -u P01130-1 -r alignment -i P01130-2
```
```python
# Python
gget.g2p("LDLR", uniprot_id="P01130-1", resource="alignment", isoform="P01130-2")
```
&rarr; Produce el alineamiento a nivel de residuo entre las isoformas P01130-1 y P01130-2 de LDLR.  

# Citar
Si utiliza `gget g2p` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Kwon, S., Safer, J., Nguyen, D.T., et al. Genomics 2 Proteins portal: a resource and discovery tool for linking genetic screening outputs to protein sequences and structures. Nature Methods (2024). [https://doi.org/10.1038/s41592-024-02409-0](https://doi.org/10.1038/s41592-024-02409-0)
