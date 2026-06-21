[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/elm.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget elm 🎭
Prediga localmente motivos lineales eucarióticos (ELMs) a partir de una secuencia de aminoácidos o UniProt Acc utilizando datos de la [base de datos ELM](http://elm.eu.org/).  
Produce: Resultados en formato JSON (Terminal) o Dataframe/CSV (Python). Este módulo devuelve dos tipos de resultados (ver ejemplos).  

**Los datos de ELM se pueden descargar y distribuir para uso no comercial de acuerdo con el [acuerdo de licencia de software de ELM](http://elm.eu.org/media/Elm_academic_license.pdf).**  

Antes de usar `gget elm` por primera vez, ejecute `gget setup elm` / `gget.setup("elm")` una vez (consulte también [`gget setup`](setup.md)).  

**Parámetro posicional**  
`sequence`  
Secuencia de aminoácidos o Uniprot Acc (str).  
Al proporcionar una Uniprot Acc, use la bandera `--uniprot` (Python: `uniprot=True`).  

**Parámetros optionales**  
`-s` `sensitivity`  
Sensibilidad de la alineación DIAMOND (str). Por defecto: "very-sensitive" (muy sensible).  
Uno de los siguientes: fast, mid-sensitive, sensitive, more-sensitive, very-sensitive, or ultra-sensitive.  

`-t` `threads`  
Número de hilos de procesamiento utilizados en la alineación de secuencias con DIAMOND (int). Por defecto: 1.  

`-bin` `diamond_binary`  
Ruta al binario DIAMOND (str). Por defecto: None -> Utiliza el binario DIAMOND instalado automáticamente con `gget`.  

`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados (str), p. ej. "ruta/al/directorio". Por defecto: salida estándar (STDOUT); los archivos temporales se eliminan.  

**Banderas**  
`-u` `--uniprot`  
Use esta bandera cuando `sequence` es una Uniprot Acc en lugar de una secuencia de aminoácidos.  

`-e` `--expand`  
Amplíe la información devuelta en el marco de datos de expresiones regulares para incluir los nombres de proteínas, los organismos y las referencias en las que se validó originalmente el motivo.  

`-csv` `--csv`  
Solo para Terminal. Produce los resultados en formato CSV.  
Para Python, usa `json=True` para producir los resultados en formato JSON.  

`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa.  

### Ejemplo
Encuentre ELM en una secuencia de aminoácidos:  
```bash
gget setup elm          # Descarga/actualiza la base de datos ELM local
gget elm -o gget_elm_results LIAQSIGQASFV
```
```python
# Python
gget.setup(“elm”)      # Descarga/actualiza la base de datos ELM local
ortholog_df, regex_df = gget.elm("LIAQSIGQASFV")
```

Encuentre ELM que proporcionen a una UniProt Acc:
```bash
gget setup elm          # Descarga/actualiza la base de datos ELM local
gget elm -o gget_elm_results --uniprot Q02410 -e
```
```python
# Python
gget.setup(“elm”)      # Descarga/actualiza la base de datos ELM local
ortholog_df, regex_df = gget.elm("Q02410", uniprot=True, expand=True)
```
&rarr; Produce dos resultados con información extensa sobre ELMs asociados con proteínas ortólogas y motivos encontrados en la secuencia de entrada directamente en función de sus expresiones regex:  

ortholog_df:  

|Ortholog_UniProt_Acc|ProteinName|class_accession|ELMIdentifier  |FunctionalSiteName                   |Description                                                                                                                              |Organism    |…  |
|:-----------------:|:---------:|:-------------:|:-------------:|:-----------------------------------:|:---------------------------------------------------------------------------------------------------------------------------------------:|:----------:|:-:|
|Q02410             |APBA1_HUMAN|ELME000357     |LIG_CaMK_CASK_1|CASK CaMK domain binding ligand motif|Motif that mediates binding to the calmodulin-dependent protein kinase (CaMK) domain of the peripheral plasma membrane protein CASK/Lin2.|Homo sapiens|…  |
|Q02410             |APBA1_HUMAN|ELME000091     |LIG_PDZ_Class_2|PDZ domain ligands                   |The C-terminal class 2 PDZ-binding motif is classically represented by a pattern such as                                                 |Homo sapiens|…  |

regex_df:  

|Instance_accession|ELMIdentifier     |FunctionalSiteName             |ELMType|Description                                                                                                                                            |Instances (Matched Sequence)|Organism                      |…  |
|:----------------:|:----------------:|:-----------------------------:|:-----:|:-----------------------------------------------------------------------------------------------------------------------------------------------------:|:--------------------------:|:----------------------------:|:-:|
|ELME000321        |CLV_C14_Caspase3-7|Caspase cleavage motif         |CLV    |Caspase-3 and Caspase-7 cleavage site.                                                                                                                 |ERSDG                       |Mus musculus                  |…  |
|ELME000102        |CLV_NRD_NRD_1     |NRD cleavage site              |CLV    |N-Arg dibasic convertase (NRD/Nardilysin) cleavage site.                                                                                               |RRA                         |Rattus norvegicus             |…  |
|ELME000100        |CLV_PCSK_PC1ET2_1 |PCSK cleavage site             |CLV    |NEC1/NEC2 cleavage site.                                                                                                                               |KRD                         |Mus musculus                  |…  |
|ELME000146        |CLV_PCSK_SKI1_1   |PCSK cleavage site             |CLV    |Subtilisin/kexin isozyme-1 (SKI1) cleavage site.                                                                                                       |RLLTA                       |Homo sapiens                  |…  |
|ELME000231        |DEG_APCC_DBOX_1   |APCC-binding Destruction motifs|DEG    |An RxxL-based motif that binds to the Cdh1 and Cdc20 components of APC/C thereby targeting the protein for destruction in a cell cycle dependent manner|SRVKLNIVR                   |Saccharomyces cerevisiae S288c|…  |
|…                 |…                 |…                              |…      |…                                                                                                                                                      |…                           |…                             |…  |

(Los motivos que aparecen en muchas especies diferentes pueden parecer repetidos, pero todas las filas deben ser únicas.)

#### [Màs ejemplos](https://github.com/pachterlab/gget_examples)  

# Citar  
Si utiliza `gget elm` en una publicación, favor de citar los siguientes artículos:  
- Laura Luebbert, Chi Hoang, Manjeet Kumar, Lior Pachter, Fast and scalable querying of eukaryotic linear motifs with gget elm, _Bioinformatics_, 2024, btae095, [https://doi.org/10.1093/bioinformatics/btae095](https://doi.org/10.1093/bioinformatics/btae095)

- Manjeet Kumar, Sushama Michael, Jesús Alvarado-Valverde, Bálint Mészáros, Hugo Sámano‐Sánchez, András Zeke, Laszlo Dobson, Tamas Lazar, Mihkel Örd, Anurag Nagpal, Nazanin Farahi, Melanie Käser, Ramya Kraleti, Norman E Davey, Rita Pancsa, Lucía B Chemes, Toby J Gibson, The Eukaryotic Linear Motif resource: 2022 release, Nucleic Acids Research, Volume 50, Issue D1, 7 January 2022, Pages D497–D508, [https://doi.org/10.1093/nar/gkab975](https://doi.org/10.1093/nar/gkab975)
