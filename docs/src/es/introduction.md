[![pypi version](https://img.shields.io/pypi/v/gget)](https://pypi.org/project/gget)
[![Downloads](https://static.pepy.tech/personalized-badge/gget?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/gget)
[![license](https://img.shields.io/pypi/l/gget)](https://github.com/pachterlab/gget/blob/main/LICENSE)
[![status](https://github.com/pachterlab/gget/actions/workflows/ci.yml/badge.svg)](https://github.com/pachterlab/gget/blob/main/tests/pytest_results_py3.12.txt)
[![Powered by NumFOCUS](https://img.shields.io/badge/powered%20by-NumFOCUS-orange.svg?style=flat&colorA=E1523D&colorB=007D8A)](https://numfocus.org/)
[![GitHub stars](https://img.shields.io/github/stars/scverse/gget?style=social)](https://github.com/scverse/gget)

# ¡Bienvenidos!

[<img align="right" width="65%" height="65%" src="https://github.com/pachterlab/gget/blob/main/docs/assets/website_v2_gget_overview.png?raw=true" />](https://raw.githubusercontent.com/pachterlab/gget/main/figures/gget_overview.png)
  
`gget` es un programa gratuito de código fuente abierta de Terminal y Python que permite la consulta eficiente de bases de datos genómicas.  
<br>
`gget` consiste en un conjunto de módulos separados pero interoperables, cada uno diseñado para facilitar un tipo de consulta de base de datos en una sola línea de código.  
<br>
`gget` es parte del proyecto [scverse®](https://scverse.org) y está patrocinado fiscalmente por [NumFOCUS](https://numfocus.org/). Si te gusta `gget` y quieres apoyar nuestra misión, por favor considera hacer una [donación](https://opencollective.com/scverse/projects/scverse-gget/donate?interval=oneTime&amount=20&contributeAs=me) deducible de impuestos.

> Nota: Las bases de datos consultadas por `gget` se actualizan continuamente y pueden cambiar su estructura. Los módulos de `gget` se [prueban automáticamente](https://github.com/pachterlab/gget/blob/main/tests/pytest_results_py3.12.txt) dos veces por semana y se actualizan cuando es necesario. Si encuentras un problema, primero actualiza a la versión más reciente con `pip install --upgrade gget`. Si el problema persiste, por favor [repórtalo](https://github.com/pachterlab/gget/issues/new/choose).

¿Falta alguna base de datos o funcionalidad que te gustaría ver?
[<kbd> <br> Solicitar una nueva función <br> </kbd>](https://github.com/pachterlab/gget/issues/new/choose)

# Módulos gget

Estos son los módulos principales de `gget`. Haga clic en cualquier módulo para acceder a la documentación detallada.

<table style="width:100%; table-layout:fixed;">
  <tr>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/8cube.md"><strong>gget 8cube</strong></a><br>¿Cuál es la expresión del gen X en 8 cepas y tejidos diferentes de ratón?.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/alphafold.md"><strong>gget alphafold</strong></a><br>Predecir la estructura 3D de una proteína a partir de una secuencia de aminoácidos.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/archs4.md"><strong>gget archs4</strong></a><br>¿Cuál es la expresión de mi gen en el tejido X?</td>
  </tr>
  <tr>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/bgee.md"><strong>gget bgee</strong></a><br>Encontrar todos los ortólogos de un gen.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/blast.md"><strong>gget blast</strong></a><br>Realizar un BLAST de una secuencia de nucleótidos o aminoácidos.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/blat.md"><strong>gget blat</strong></a><br>Encontrar la ubicación genómica de una secuencia de nucleótidos o aminoácidos.</td>
  </tr>
  <tr>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/cbio.md"><strong>gget cbio</strong></a><br>Explorar la expresión de un gen en los cánceres especificados.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/cellxgene.md"><strong>gget cellxgene</strong></a><br>Obtener matrices de conteo de ARN de células individuales listas para usar para ciertos tejidos/enfermedades/etc.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/cosmic.md"><strong>gget cosmic</strong></a><br>Buscar genes, mutaciones y otros factores asociados con ciertos cánceres.</td>
  </tr>
  <tr>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/diamond.md"><strong>gget diamond</strong></a><br>Alinear secuencias de aminoácidos a una referencia.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/elm.md"><strong>gget elm</strong></a><br>Encontrar dominios y funciones de interacción de proteínas en una secuencia de aminoácidos.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/enrichr.md"><strong>gget enrichr</strong></a><br>Verificar si una lista de genes está asociada con un tipo celular específico/ vía/ enfermedad/ etc.</td>
  </tr>
  <tr>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/info.md"><strong>gget info</strong></a><br>Recuperar toda la información asociada con un ID de Ensembl.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/muscle.md"><strong>gget muscle</strong></a><br>Alinear múltiples secuencias de nucleótidos o aminoácidos entre sí.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/mutate.md"><strong>gget mutate</strong></a><br>Mutar secuencias de nucleótidos según mutaciones específicas.</td>
  </tr>
  <tr>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/opentargets.md"><strong>gget opentargets</strong></a><br>Explorar qué enfermedades y medicamentos están asociados con un gen.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/pdb.md"><strong>gget pdb</strong></a><br>Recuperar datos de la Base de Datos de Proteínas (PDB) según un ID de PDB.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/ref.md"><strong>gget ref</strong></a><br>Obtener genomas de referencia de Ensembl.</td>
  </tr>
  <tr>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/search.md"><strong>gget search</strong></a><br>Encontrar IDs de Ensembl asociados con la palabra de búsqueda especificada.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/seq.md"><strong>gget seq</strong></a><br>Recuperar la secuencia de nucleótidos o aminoácidos de un gen.</td>
    <td style="width:33.33%; padding:20px; text-align:center; vertical-align:top;"><a href="/gget/es/virus.md"><strong>gget virus</strong></a><br>Filtrar y obtener secuencias virales globales y metadatos extensos.</td>
  </tr>
</table>


<br>  

Si usa `gget` en una publicación, por favor [cite*](cite.md):    
```
Luebbert, L., & Pachter, L. (2023). Efficient querying of genomic reference databases with gget. Bioinformatics. https://doi.org/10.1093/bioinformatics/btac836
```
Lea el artículo aquí: [https://doi.org/10.1093/bioinformatics/btac836](https://doi.org/10.1093/bioinformatics/btac836)

Gracias a [Victor Garcia-Ruiz](https://github.com/victorg775) y [Anna Karen Orta](https://www.linkedin.com/in/akorta/) por su ayuda con la traduccion del sitio web.  

<br>  
<br>  

[![gget PyPI downloads over the last year](https://github.com/lauraluebbert/gget_downloads/raw/main/plots/downloads_gget_daily.png)](https://github.com/lauraluebbert/gget_downloads/tree/main)  

<br>  
<br>  

<div style="display: flex; justify-content: center;">
  <iframe
    width="560"
    height="315"
    src="https://www.youtube.com/embed/cVR0k6Mt97o?si=BJwRyaymmxF9w65f"
    title="YouTube video player"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen>
  </iframe>
</div>

<br>  

<p align="center">
  <img height="100" alt="scverse_symbol" src="https://github.com/user-attachments/assets/d672bd36-4749-427e-9f08-d807d3bde8fa" />
  &nbsp;&nbsp;&nbsp;
  <img height="100" alt="numfocus" src="https://github.com/user-attachments/assets/a12369cf-e6ae-4b4b-9a30-669aa3d80b5c" />
  &nbsp;&nbsp;&nbsp;
  <img height="100" alt="logo-okfn" src="https://github.com/user-attachments/assets/452ae8d8-69f0-4d0d-848c-ddfb40357eb2" />
</p>
