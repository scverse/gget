[<kbd> View page source on GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/en/muscle.md)

> Python arguments are equivalent to long-option arguments (`--arg`), unless otherwise specified. Flags are True/False arguments in Python. The manual for any gget tool can be called from the command-line using the `-h` `--help` flag.  
# gget muscle 🦾
Align multiple nucleotide or amino acid sequences to each other using [Muscle5](https://www.drive5.com/muscle/).  
Return format: ClustalW formatted standard out or aligned FASTA (.afa).  

**Positional argument**  
`fasta`  
List of sequences or path to FASTA or .txt file containing the nucleotide or amino acid sequences to be aligned.  

**Optional arguments**  
`-o` `--out`  
Path to the aligned FASTA file the results will be saved in, e.g. path/to/directory/results.afa. Default: Standard out.  
Python: `save=True` will save the output in the current working directory.

**Flags**  
`-s5` `--super5`  
Aligns input using the [Super5 algorithm](https://drive5.com/muscle5/Muscle5_SuppMat.pdf) instead of the [Parallel Perturbed Probcons (PPP) algorithm](https://drive5.com/muscle5/Muscle5_SuppMat.pdf) to decrease time and memory.  
Use for large inputs (a few hundred sequences).

`-q` `--quiet`  
Command-line only. Prevents progress information from being displayed.  
Python: Use `verbose=False` to prevent progress information from being displayed.


### Example
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
&rarr; Returns an overview of the aligned sequences with ClustalW coloring. (To return an aligned FASTA (.afa) file, use `--out` argument (or `save=True` in Jupyter Lab/Google Colab).) In the above example, the 'fasta.fa' includes several sequences to be aligned (e.g. isoforms returned from `gget seq`).

![alt text](https://github.com/pachterlab/gget/blob/main/figures/example_muscle_return.png?raw=true)

You can also view aligned fasta files returned by `gget.muscle` using programs like [`alv`](https://github.com/arvestad/alv), as shown below:
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

# References
If you use `gget muscle` in a publication, please cite the following articles:  

- Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

- Edgar RC (2021), MUSCLE v5 enables improved estimates of phylogenetic tree confidence by ensemble bootstrapping, bioRxiv 2021.06.20.449169. [https://doi.org/10.1101/2021.06.20.449169](https://doi.org/10.1101/2021.06.20.449169)
