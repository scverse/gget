[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/muscle.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget muscle 🦾
Alinea múltiples secuencias de nucleótidos o aminoácidos usando el algoritmo [Muscle5](https://www.drive5.com/muscle/).  
Regresa: Salida estándar (STDOUT) en formato ClustalW o archivo de tipo 'aligned FASTA' (.afa).  

**Parámetro posicional**  
`fasta`  
Lista de secuencias o ruta al archivo FASTA o .txt que contiene las secuencias de nucleótidos o aminoácidos que se van a alinear.  

**Parámetros optionales**  
`-o` `--out`  
Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.afa. Por defecto: salida estándar (STDOUT).  
Para Python, usa `save=True` para guardar los resultados en el directorio de trabajo actual.  

**Banderas**  
`-s5` `--super5`  
Alinea las secuencies usando el algoritmo [Super5](https://drive5.com/muscle5/Muscle5_SuppMat.pdf) en lugar del algoritmo [Parallel Perturbed Probcons (PPP)](https://drive5.com/muscle5/Muscle5_SuppMat.pdf) para disminuir el tiempo y la memoria usada durante la corrida.  
Use para ingresos grandes (unos cientos secuencias).

`-q` `--quiet`  
Solo para la Terminal. Impide la informacion de progreso de ser exhibida durante la corrida.  
Para Python, usa `verbose=False` para imipidir la informacion de progreso de ser exhibida durante la corrida.  


### Por ejemplo  
```bash
gget muscle MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS
```
```python
# Python
gget.muscle(["MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS", "MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS"])
```

```bash
gget muscle fasta.fa
```
```python
# Python
gget.muscle("fasta.fa")
```
&rarr; Regresa las secuencias alineadas con coloración ClustalW. (Para devolver un archivo FASTA alineado (.afa), use el argumento `--out` (o `save=True` en Python).) En este ejemplo, el archivo 'fasta.fa' incluye varias secuencias para alineación (por ejemplo, isoformas devueltas desde `gget seq`).

![alt text](https://github.com/pachterlab/gget/blob/main/figures/example_muscle_return.png?raw=true)

También puede ver archivos FASTA alineados devueltos por `gget.muscle` usando programas como [`alv`](https://github.com/arvestad/alv):
```python
# Python
!pip install biopython
!pip install alv
from Bio import AlignIO
import alv

gget.muscle("fasta.fa", out="fasta_aligned.afa")
msa = AlignIO.read("fasta_aligned.afa", "fasta")
alv.view(msa)
```

#### [More examples](https://github.com/pachterlab/gget_examples)

# Citar  
Si utiliza `gget muscle` en una publicación, favor de citar los siguientes artículos:

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Edgar RC (2021), MUSCLE v5 enables improved estimates of phylogenetic tree confidence by ensemble bootstrapping, bioRxiv 2021.06.20.449169. [https://doi.org/10.1101/2021.06.20.449169](https://doi.org/10.1101/2021.06.20.449169)
