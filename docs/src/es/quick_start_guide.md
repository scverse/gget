[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/quick_start_guide.md)
# 🪄 Guía de inicio rápido
Terminal:
```bash
# Obtenga todos los FTP de anotaciones y referencias de Homo sapiens de la última versión de Ensembl
$ gget ref homo_sapiens

# Obtenga IDs de Ensembl de genes humanos con "ace2" o "angiotensin converting enzyme 2" en su nombre/descripción
$ gget search -s homo_sapiens 'ace2' 'angiotensin converting enzyme 2'

# Busque el gen ENSG00000130234 (ACE2) y su transcripción ENST00000252519
$ gget info ENSG00000130234 ENST00000252519

# Obtenga la secuencia de aminoácidos de la transcripción canónica del gen ENSG00000130234
$ gget seq --translate ENSG00000130234

# Rápidamente encuentra la ubicación genómica de la secuencia de aminoácidos
$ gget blat MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS

# BLAST la secuencia de aminoácidos
$ gget blast MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS

# Alinee múltiples secuencias de nucleótidos o aminoácidos entre sí (también acepta la ruta al archivo FASTA)  
$ gget muscle MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS

# Alinee una o más secuencias de aminoácidos con una referencia (que contiene una o más secuencias) (BLAST local) (también acepta rutas a archivos FASTA)  
$ gget diamond MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS -ref MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS

# Alinea secuencias de nucleótidos o aminoácidos en un archivo FASTA
$ gget muscle path/to/file.fa

# Use Enrichr para un análisis de ontología de una lista de genes
$ gget enrichr -db ontology ACE2 AGT AGTR1 ACE AGTRAP AGTR2 ACE3P

# Obtene la expresión en tejido humano del gen ACE2
$ gget archs4 -w tissue ACE2

# Obtenga la estructura de la proteína (en formato PDB) de ACE2 (ID de PDB devuelta por gget info)
$ gget pdb 1R42 -o 1R42.pdb

# Descargar conjuntos de datos del genoma de virus de NCBI Virus (por ejemplo, secuencias del virus del Zika).
$ gget virus "Zika virus" --host "Homo sapiens" --nuc_completeness complete

# Encuentre motivos lineales eucarióticos (ELM) en una secuencia de aminoácidos
$ gget setup elm        # solo debe ejecutarse una vez
$ gget elm -o results MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS

# Obtene una matriz de recuento de scRNAseq (formato AnnData) basada en genes, tejidos y tipos de células especificados (especie predeterminada: humano)
$ gget setup cellxgene  # solo debe ejecutarse una vez
$ gget cellxgene --gene ACE2 SLC5A1 --tissue lung --cell_type 'mucus secreting cell' -o example_adata.h5ad
```
Python (Jupyter Lab / Google Colab):
```python  
import gget
gget.ref("homo_sapiens")
gget.search(["ace2", "angiotensin converting enzyme 2"], "homo_sapiens")
gget.info(["ENSG00000130234", "ENST00000252519"])
gget.seq("ENSG00000130234", translate=True)
gget.blat("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS")
gget.blast("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS")
gget.muscle(["MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS", "MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS"])
gget.diamond("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS", reference="MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS")
gget.enrichr(["ACE2", "AGT", "AGTR1", "ACE", "AGTRAP", "AGTR2", "ACE3P"], database="ontology", plot=True)
gget.archs4("ACE2", which="tissue")
gget.pdb("1R42", save=True)
gget.virus("Zika virus", host="Homo sapiens", nuc_completeness="complete")

gget.setup("elm")         # solo debe ejecutarse una vez
ortho_df, regex_df = gget.elm("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS")

gget.setup("cellxgene")   # solo debe ejecutarse una vez
gget.cellxgene(gene = ["ACE2", "SLC5A1"], tissue = "lung", cell_type = "mucus secreting cell")
```
Use a `gget` con R usando [reticulate](https://rstudio.github.io/reticulate/):
```r
system("pip install gget")
install.packages("reticulate")
library(reticulate)
gget <- import("gget")

gget$ref("homo_sapiens")
gget$search(list("ace2", "angiotensin converting enzyme 2"), "homo_sapiens")
gget$info(list("ENSG00000130234", "ENST00000252519"))
gget$seq("ENSG00000130234", translate=TRUE)
gget$blat("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS")
gget$blast("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS")
gget$muscle(list("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS", "MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS"), out="out.afa")
gget$diamond("MSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLAS", reference="MSSSSWLLLSLVEVTAAQSTIEQQAKTFLDKFHEAEDLFYQSLLAS")
gget$enrichr(list("ACE2", "AGT", "AGTR1", "ACE", "AGTRAP", "AGTR2", "ACE3P"), database="ontology")
gget$archs4("ACE2", which="tissue")
gget$pdb("1R42", save=TRUE)
gget$virus("Zika virus", host="Homo sapiens", nuc_completeness="complete")
```
#### [Más ejemplos](https://github.com/pachterlab/gget_examples)
