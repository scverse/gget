[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/8cube.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.
# gget 8cube 🔬

<a href="https://www.biorxiv.org/content/10.1101/2025.04.21.649844">
  <img
    align="right"
    width="500"
    alt="Screenshot 2026-01-19 at 5 34 43 PM"
    src="https://github.com/user-attachments/assets/1fa9b68f-27e3-4f94-a46d-4f2d4df36b11"
  />
</a>

Consulta [**8cubeDB**](https://eightcubedb.onrender.com/) (datos de secuenciación de snRNA de 8 cepas, tejidos e individuos diferentes de ratón (cuatro de cada sexo)) para métricas de especificidad a nivel génico y valores de expresión normalizados.  

Formato de salida: **JSON** (línea de comandos) o **data frame/CSV** (Python).

Este módulo fue escrito por [Nikhila Swarna](https://github.com/nikkiswarna).

<br clear="right" />

---

# gget 8cube specificity 🎯

Recupera estadísticas de especificidad **ψ** y **ζ** para uno o más genes.

```

gget 8cube specificity <GENES...>

````

**Argumento posicional**  
`genes`  
Símbolos génicos o IDs de genes Ensembl. Se permiten múltiples genes.

**Argumentos opcionales**  
`-csv` `--csv`  
Devuelve CSV en lugar de JSON (solo línea de comandos).  
Python: usar `json=False` (DataFrame por defecto) o `json=True` para JSON.

`-o` `--out`  
Ruta del archivo de salida (CSV o .json según `--csv`).  
Python: `save=True` guarda automáticamente en el directorio actual.

**Banderas**  
`-q` `--quiet`  
Suprime la información de progreso.  
Python: usar `verbose=False`.

### Ejemplo

```bash
gget 8cube specificity Acsm2 ENSMUSG00000046623.9
````

```python
# Python
from gget.gget_8cube import specificity
specificity(["Acsm2", "ENSMUSG00000046623.9"])
```

→ Devuelve los valores de especificidad ψ y ζ para **Acsm2**.

---

# gget 8cube psi_block 🧩

Recupera valores de **ψ-block** (especificidad a nivel de bloque) para uno o más genes.

```
gget 8cube psi_block <GENES...> --analysis_level <LEVEL> --analysis_type <TYPE>
```

**Argumento posicional**
`genes`
Símbolos génicos o IDs Ensembl.

**Argumentos requeridos**
`-al` `--analysis_level`
Nivel de análisis biológico (p. ej., `Kidney`, `Across_tissues`).

`-at` `--analysis_type`
Tipo de partición (p. ej., `Sex:Celltype`, `Sex:Strain`).

**Argumentos opcionales**
`-csv` `--csv`
Devuelve CSV en lugar de JSON.
Python: usar `json=True` para JSON.

`-o` `--out`
Ubicación del archivo de salida.

**Banderas**
`-q` `--quiet`
Suprime la impresión del progreso.

### Ejemplo

```bash
gget 8cube psi_block Acsm2 \
    --analysis_level Kidney \
    --analysis_type "Sex:Celltype"
```

```python
# Python
from gget.gget_8cube import psi_block
psi_block(["Acsm2"], analysis_level="Kidney", analysis_type="Sex:Celltype")
```

→ Devuelve puntuaciones de especificidad ψ-block a nivel de partición para **Acsm2**.

---

# gget 8cube expression 📊

Recupera la **media y varianza de los valores de expresión normalizados** para uno o más genes.

```
gget 8cube expression <GENES...> --analysis_level <LEVEL> --analysis_type <TYPE>
```

**Argumento posicional**
`genes`
Símbolos génicos o IDs Ensembl. Se aceptan múltiples.

**Argumentos requeridos**
`-al` `--analysis_level`
Agrupación biológica (p. ej., `Kidney`, `Across_tissues`).

`-at` `--analysis_type`
Diseño de partición (p. ej., `Sex:Celltype`).

**Argumentos opcionales**
`-csv` `--csv`
Devuelve CSV en lugar de JSON.
Python: usar `json=True`.

`-o` `--out`
Ruta del archivo de salida.

**Banderas**
`-q` `--quiet`
Suprime los mensajes de progreso.

### Ejemplo

```bash
gget 8cube expression ENSMUSG00000046623.9 \
    --analysis_level Across_tissues \
    --analysis_type Strain
```

```python
# Python
from gget.gget_8cube import gene_expression
gene_expression(["ENSMUSG00000046623.9"], analysis_level="Across_tissues", analysis_type="Strain")
```

→ Devuelve valores de expresión normalizados agrupados por tipo celular y sexo.

---

# Ejemplo de flujo de trabajo

```bash
# Especificidad
gget 8cube specificity Gjb4

# Especificidad ψ-block
gget 8cube psi_block Gjb4 --analysis_level Across_tissues --analysis_type Strain

# Valores de expresión
gget 8cube expression Gjb4 --analysis_level Across_tissues --analysis_type Strain
```

---

# API de Python

```python
from gget.gget_8cube import specificity, psi_block, gene_expression
```

o

```python
from gget import specificity, psi_block, gene_expression
```

---

# Notas

* Funciona con símbolos génicos **y** IDs Ensembl (con o sin números de versión).
* Las tres funciones aceptan **múltiples genes** a la vez.
* La salida por defecto en Python es un **DataFrame de pandas**; use `json=True` para JSON.
* La CLI usa **JSON** por defecto, a menos que se utilice `--csv`.

---

# Citar

Si utiliza `gget 8cube` en una publicación, por favor cite:

* **Swarna NP, et al.**
  *Determining gene specificity from multivariate single-cell RNA sequencing data* (2025).
  [https://doi.org/10.1101/2025.11.21.689845](https://doi.org/10.1101/2025.11.21.689845)

* **Luebbert, L., & Pachter, L. (2023).**
  *Efficient querying of genomic reference databases with gget.* Bioinformatics.
  [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

* **Rebboah E, et al.**
  *Systematic cell-type resolved transcriptomes of 8 tissues in 8 lab and wild-derived mouse strains captures global and local expression variation* (2025).
  [https://doi.org/10.1101/2025.04.21.649844](https://doi.org/10.1101/2025.04.21.649844)

```
```
