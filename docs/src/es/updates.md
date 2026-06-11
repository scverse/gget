[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/updates.md)

## ✨ ¡Lo más reciente!  
**Versión ≥ 0.30.6** (10 de junio de 2026):
- [`gget blat`](blat.md): Mejora la resistencia contra fallas del endpoint UCSC BLAT (corrige pruebas que fallan de manera intermitente).
  - Se agregó reintento con backoff exponencial para fallas transitorias (HTTP 429/5xx, errores de red, y respuestas no-JSON 200 causadas por limitación de tasa de UCSC o páginas de error HTML). Hasta 4 intentos con backoff de 1.5s → 3s → 6s.
  - Se reemplazó el mensaje engañoso "sequence too short or assembly invalid" con la respuesta real del servidor (código de estado, vista previa de respuesta) para que las fallas sean diagnosticables.
  - `HTTPError` y `URLError` ahora se capturan explícitamente en lugar de aparecer como excepciones no manejadas.
- Correcciones de errores:
  - [`gget cosmic`](cosmic.md): Corregido mensaje de error engañoso cuando falla el paso de descarga — reportaba el código de retorno/stderr del comando anterior en lugar del comando que falló.
  - [`gget cosmic`](cosmic.md): Se limitó el manejador de excepción de parseo JSON a `json.JSONDecodeError` para que `ValueError`s no relacionados ya no sean enmascarados por el mensaje "Failed to download file".
  - `gget --version`, `gget --help`, `gget` invocado sin argumentos, y `gget <module>` sin más argumentos ahora todos salen con estado 0 en lugar de 1, para que scripts de CI y pipelines de shell ya no traten estas salidas informativas como fallas.
  - Se agregaron tiempos límite de solicitud a llamadas `requests` anteriormente no protegidas en [`gget ref`](ref.md), [`gget info`](info.md), [`gget 8cube`](8cube.md), [`gget enrichr`](enrichr.md), y [`gget opentargets`](opentargets.md). Por defecto es 10s conexión / 60s lectura; configurable a través de la nueva constante `DEFAULT_REQUESTS_TIMEOUT`.
  - Se limitó un `except:` desnudo en `utils.get_uniprot_seqs` a `(KeyError, IndexError, TypeError)` para que errores no relacionados (incluyendo `KeyboardInterrupt`) ya no sean suprimidos.
  - Se agregaron los helpers `utils.http_json()` y `utils.dig()` que emiten una solicitud y parsean JSON / caminan por una ruta de respuesta anidada con reporte de errores consistente. Se migraron [`gget bgee`](bgee.md), [`gget opentargets`](opentargets.md), y un sitio de llamada `.json()` en [`gget virus`](virus.md) para usarlos; los módulos restantes migrarán oportunmente. Páginas de error HTML upstream, JSON malformado, y claves de respuesta faltantes ahora aparecen como `RuntimeError`s claros nombrando el servicio que falla en lugar de trazas crípticas de `JSONDecodeError` / `KeyError`.
  - `utils.http_json()` ahora reintenta fallas transitorias (errores de conexión, tiempos límite de lectura, HTTP 5xx) hasta 3 veces con backoff exponencial. Suaviza interrupciones upstream cortas (por ejemplo, tiempos límite de lectura de bgee.org) sin afectar errores 4xx, que siguen levantándose inmediatamente.
  - [`gget virus`](virus.md): Se reemplazaron 11 bloques desnudos `except: pass` alrededor de llamadas de limpieza `file.close()` / `os.remove()` con manejadores `except OSError` limitados que registran la falla en `DEBUG`. Anteriormente, problemas reales de I/O durante la limpieza (disco lleno, permisos) se eliminaban silenciosamente y la ruta de limpieza también suprimía `KeyboardInterrupt`.
  - [`gget cbio`](cbio.md): Se corrigió una ruta de código en `cbio_plot` que llamaba al `DataFrame.append()` removido-en-pandas-2.0 dentro de un bucle al llenar genes CNA faltantes — toda la rama se colgaba en pandas moderno. Ahora construye un solo DataFrame de filas faltantes y concatena una vez.
- Rendimiento:
  - `utils.get_uniprot_seqs`: Recolecta DataFrames por-ID en una lista y `pd.concat(..., ignore_index=True)` una vez al final, evitando el costo O(n²) de hacer crecer un DataFrame dentro del bucle de solicitud.
  - Se cachearon `utils.find_latest_ens_rel`, `utils.search_species_options`, `utils.ref_species_options`, y `utils.find_nv_kingdom` con `functools.lru_cache`. Estos acceden a listados FTP de Ensembl que son estables para una versión; llamadas repetidas dentro de un proceso de Python ahora son gratuitas.
  - Se agregó `utils.parallel_map`, un envoltorio delgado de `ThreadPoolExecutor` para trabajo vinculado a I/O. Se usa para distribuir `utils.get_uniprot_seqs` a través de la lista de ID de entrada — buscar N IDs ahora está limitado por ~`N / pool_size` viajes redondos a UniProt en lugar de `N`. El tamaño del pool por defecto es 8 y se puede sobrescribir a través de la variable de entorno `GGET_MAX_WORKERS`.

**Versión ≥ 0.30.5** (23 de mayo de 2026):
- [`gget opentargets`](opentargets.md): Se reescribió este módulo para reflejar la nueva estructura de la API de Open Targets
  - algunos nombres de columnas/claves de salida pueden diferir para reflejar la nueva estructura de la API
  - Se eliminó el argumento `--filter_mode`
- [`gget blast`](blast.md): Se corrigió la compatibilidad con versiones más nuevas de pandas (≥ 2.0) donde `pd.read_html()` ya no acepta cadenas HTML directamente, causando un error `FileNotFoundError` / `OSError: Filename too long` al analizar los resultados de BLAST
- [`gget cosmic`](cosmic.md): Se agregaron argumentos overwrite y gzip a los componentes internos.

**Versión ≥ 0.30.3** (26 de febrero de 2026):  
- [`gget virus`](virus.md): Nuevas opciones de filtrado, modo silencioso y mejora en la fiabilidad de descargas
  - Se añadió el filtro `--segment` para virus segmentados (por ejemplo, segmentos de Influenza A como 'HA', 'NA', 'PB1')
  - Se añadió el filtro `--vaccine_strain` para incluir o excluir secuencias de cepas vacunales
  - Se añadió el filtro `--source_database` para seleccionar secuencias de 'genbank' o 'refseq' (reemplaza `refseqOnly`)
  - Se añadió la bandera `-q` / `--quiet` para suprimir la información de progreso
  - Se extendieron las estrategias de respaldo para mejorar la fiabilidad de descarga en conjuntos de datos grandes
  - El archivo de resumen de comandos ahora incluye la versión del software

**Versión ≥ 0.30.2** (08 de febrero de 2026):  
- [`gget virus`](virus.md): Optimización del streaming de metadatos, mejora del filtrado de proteínas y manejo de errores y lógica de reintentos mejorados  
  - Los metadatos ahora se escriben en disco durante la descarga para evitar el agotamiento de memoria en conjuntos de datos grandes (100.000+ registros)
  - Corrección del mapeo del CSV de metadatos (camelCase → snake_case) para nombre del organismo, hospedador y fecha de recolección
  - Mejora del filtrado de proteínas para virus segmentados con un parseo más robusto de los encabezados FASTA
  - Se añadió la opción `annotated=False` para filtrar secuencias no anotadas
  - Se añadieron barras de progreso para descargas de secuencias por lotes
  - Corrección de un error en el nombre del campo de fecha de recolección
  - Mejora de los mensajes de error para fechas de filtrado inválidas
  - Se añadieron reintentos mejorados para la resolución de nombres de virus
  - Se añadió mayor verbosidad en los pasos de verificación de influenza A y COVID-19

**Versión ≥ 0.30.0** (19 de enero de 2026):  
- NUEVOS MÓDULOS:
  - [`gget 8cube`](8cube.md)
  - [`gget virus`](virus.md)
- MEJORAS DE SEGURIDAD:
  - Se reemplazó `os.system()` con f-strings que contienen URLs de APIs externas en `gget/main.py`
  - Se reemplazó `exec()` por `importlib.import_module()` en [`gget setup`](setup.md) para importaciones dinámicas más seguras
  - Se reemplazaron llamadas a subprocess con `shell=True` por argumentos basados en listas en [`gget muscle`](muscle.md), [`gget diamond`](diamond.md) y [`gget setup`](setup.md) para prevenir la inyección de comandos


**Versión ≥ 0.29.3** (11 de septiembre de 2025):  
- [`gget blat`](blat.md): Actualiza la solicitud a la API para los nuevos permisos.
- [`gget pdb`](pdb.md): Agregado el sitio web de `wwpdb`, retrocede a `rcsb` si las solicitudes fallan.  
- [`gget cellxgene`](cellxgene.md): Mejora el manejo de argumentos; el frontend no cambia.
- [`gget setup`](setup.md)/[`gget alphafold`](alphafold.md): Corrige el error pip_cmd en `gget.setup("alphafold")`.
  
**Versión ≥ 0.29.2** (03 de julio de 2025):  
- Ahora se puede instalar `gget` usando `uv pip install gget`
  - Toda la metadata del paquete (versión, autor, descripción, etc.) ahora se gestiona en `setup.cfg` para una compatibilidad total con herramientas modernas como `uv`, `pip` y PyPI  
  - `gget` ahora utiliza un `setup.py` mínimo y es completamente compatible con PEP 517/518
- [`gget setup`](setup.md) intentará usar primero `uv pip install` por su velocidad y resolución moderna de dependencias, y recurrirá a `pip install` si `uv` falla o no está disponible  
  - Se informa a los usuarios en cada paso qué instalador se está utilizando y si se realiza un reintento  
  - **Nota**: Algunas dependencias científicas (por ejemplo, `cellxgene-census`) pueden no ser compatibles todavía con Python 3.12. Si encuentras errores de instalación, prueba usar Python 3.9 o 3.10. (La instalación con `pip` también podría funcionar en estos casos.)
- Todas las dependencias requeridas ahora están listadas en `setup.cfg` bajo `install_requires` → Instalar gget con `pip install .` o `uv pip install .` instalará automáticamente todas las dependencias

**Versión ≥ 0.29.1** (21 de abril de 2025):  
- [`gget mutate`](mutate.md):  
  - gget mutate se ha simplificado para enfocarse en recibir como entrada una lista de mutaciones y el genoma de referencia correspondiente con información de anotación asociada, y producir como salida las secuencias con la mutación incorporada y una región corta de contexto circundante. Para la funcionalidad completa de la versión anterior y cómo se integra en el contexto de un pipeline de análisis de variantes novedosas, visita el repositorio varseek que está siendo desarrollado por miembros del equipo de gget en https://github.com/pachterlab/varseek.git.
  - Se añadió información adicional a los data frames retornados, como se describe aquí: https://github.com/pachterlab/gget/pull/169
- [`gget cosmic`](cosmic.md):  
  - Reestructuración importante del módulo `gget cosmic` para cumplir con los nuevos requisitos de inicio de sesión establecidos por COSMIC
  - Se añadieron nuevos argumentos `email` y `password` para permitir que el usuario introduzca manualmente sus credenciales sin necesidad de input adicional para la descarga de datos
  - Cambio por defecto: `gget_mutate=False`
  - Argumento en desuso: `entity`
  - Argumento `mutation_class` ahora es `cosmic_project`
- [`gget bgee`](bgee.md):  
  - `type="orthologs"` ahora es el valor por defecto, eliminando la necesidad de especificar el argumento `type` al consultar ortólogos
  - Se permite la consulta de múltiples genes a la vez.
- [`gget diamond`](diamond.md):  
  - Ahora soporta alineamiento traducido de secuencias nucleotídicas contra secuencias de referencia de aminoácidos usando la opción `--translated`.
- [`gget elm`](elm.md):   
  - Mejorado el manejo de errores del servidor.

**Versión ≥ 0.29.0** (25 de septiembre de 2024):  
- **Nuevos módulos:**
    - [`gget cbio`](cbio.md)
    - [`gget opentargets`](opentargets.md)
    - [`gget bgee`](bgee.md)
- **[`gget enrichr`](./enrichr.md) ahora también soporta especies además de humano y ratón (mosca, levadura, gusano y pez) a través de [modEnrichR](https://maayanlab.cloud/modEnrichr/)**
- [`gget mutate`](./mutate.md):  
  `gget mutate` ahora fusionará secuencias idénticas en el archivo final por defecto. La creación de mutaciones fue vectorizada para disminuir el tiempo de ejecución. Se mejoró la verificación de la secuencia flanqueante para mutaciones no sustitutivas para asegurarse de que no se retenga ningún kmer silvestre en la secuencia que contiene la mutación. Se agregó varios nuevos argumentos para personalizar la generación de secuencias y la salida.
- [`gget cosmic`](./cosmic.md):  
  Se agregó soporte para pantallas de genes así como dirigidas. El archivo CSV creado para gget mutate ahora también contiene información sobre mutaciones de proteínas.
- [`gget ref`](./ref.md):  
  Se agregó opción de archivo de salida.
- [`gget info`](./info.md) y [`gget seq`](./seq.md):  
  Se cambió a la API POST de Ensembl para aumentar la velocidad (nada cambia en el front end).
- Otros cambios "detrás de escena":
    - Pruebas unitarias reorganizadas para aumentar la velocidad y disminuir el código
    - Requisitos actualizados para [permitir versiones más nuevas de mysql-connector](https://github.com/pachterlab/gget/pull/159)
    - [Soporte para Numpy>= 2.0](https://github.com/pachterlab/gget/issues/157)
  
**Versión ≥ 0.28.6 (2 de junio de 2024):**
- **Nuevo módulo: [`gget mutate`](./mutate.md)**
- [`gget cosmic`](./cosmic.md): Ahora puedes descargar bases de datos completas de COSMIC utilizando el argumento `download_cosmic`
- [`gget ref`](./ref.md): Ahora puede obtener la ensambladura del genoma GRCh27 usando `species='human_grch37'`
- [`gget search`](./search.md): Ajusta el acceso a los datos humanos a la estructura de la versión 112 de Ensembl (corrige [issue 129](https://github.com/pachterlab/gget/issues/129))

~~**Version ≥ 0.28.5** (May 29, 2024):~~ 
- Retirado debido a un error con 'logging' en `gget.setup("alphafold")` + mutaciones de inversión en `gget mutate` solo invierten la cadena en lugar de también calcular la hebra complementaria

**Versión ≥ 0.28.4** (31 de enero de 2024):  
- [`gget setup`](./setup.md): soluciona el error con la ruta del archivo al ejecutar `gget.setup("elm")` en el sistema operativo Windows.  

**Versión ≥ 0.28.3** (22 de enero de 2024):
- **[`gget search`](./search.md) y [`gget ref`](./ref.md) ahora también admiten hongos 🍄, protistas 🌝 y metazoos de invertebrados 🐝 🐜 🐌 🐙 (además de vertebrados y plantas)**
- **Nuevo módulo: [`gget cosmic`](./cosmic.md)**
- [`gget enrichr`](./enrichr.md): corrige puntos de dispersión duplicados en el gráfico cuando los nombres de las rutas están duplicados
- [`gget elm`](./elm.md):
  - Se cambió el nombre de la columna de resultados orto 'Ortholog_UniProt_ID' a 'Ortholog_UniProt_Acc' para reflejar correctamente el contenido de la columna, que son accesos de UniProt. 'UniProt ID' se cambió a 'UniProt Acc' en la documentación para todos los módulos `gget`.
  - Se cambió el nombre de la columna de resultados ortogonales 'motif_in_query' a 'motif_inside_subject_query_overlap'.
  - Se agregó información del dominio de interacción a los resultados (nuevas columnas: "InteractionDomainId", "InteractionDomainDescription", "InteractionDomainName").
  - La cadena de expresiones regulares para coincidencias de expresiones regulares se encapsuló de la siguiente manera: "(?=(regex))" (en lugar de pasar directamente la cadena de expresiones regulares "regex") para permitir capturar todas las apariciones de un motivo cuando la longitud del motivo es variable y hay son repeticiones en la secuencia ([https://regex101.com/r/HUWLlZ/1](https://regex101.com/r/HUWLlZ/1)).
- [`gget setup`](./setup.md): utilice el argumento `out` para especificar un directorio en el que se descargará la base de datos ELM. Completa [esta solicitud de función](https://github.com/pachterlab/gget/issues/119).
- [`gget Diamond`](./diamond.md): El comando DIAMOND ahora se ejecuta con el indicador `--ignore-warnings`, lo que permite secuencias de nicho, como secuencias de aminoácidos que solo contienen caracteres de nucleótidos y secuencias repetidas. Esto también es válido para las alineaciones DIAMOND realizadas dentro de [`gget elm`](./elm.md).
- **Cambio de back-end de [`gget ref`](./ref.md) y [`gget search`](./search.md): la versión actual de Ensembl se obtiene del nuevo [archivo de versión](https://ftp.ensembl.org/pub/VERSION) en el sitio FTP de Ensembl para evitar errores durante la carga de nuevos lanzamientos.**
- [`gget search`](./search.md):
  - Los resultados del enlace FTP (`--ftp`) se guardan en formato de archivo txt en lugar de json.
  - Se corrigieron enlaces URL al resumen de genes de Ensembl para especies con un nombre de subespecie e invertebrados.
- [`gget ref`](./ref.md):
  - Cambios de back-end para aumentar la velocidad.
  - Nuevo argumento: `list_iv_species` para enumerar todas las especies de invertebrados disponibles (se puede combinar con el argumento `release` para obtener todas las especies disponibles de una liberación específica de Ensembl)
    
**Versión ≥ 0.28.2** (15 de noviembre de 2023):
- [`gget info`](./info.md): devuelve un mensaje de error cuando el servidor NCBI falla por un motivo distinto a un error de recuperación (esto es un error en el lado del servidor en lugar de un error con `gget`)
- Reemplace el argumento obsoleto 'texto' para los métodos de tipo find() siempre que se usen con la dependencia `BeautifulSoup`
- [`gget elm`](elm.md): Elimina instancias de falsos positivos y verdaderos negativos de los resultados devueltos.
- [`gget elm`](elm.md): agrega el argumento `expand`
  
**Versión ≥ 0.28.0** (5 de noviembre de 2023):
- Documentación actualizada de [`gget muscle`](./muscle.md) para agregar un tutorial sobre cómo visualizar secuencias con diferentes longitudes de nombres de secuencia + ligero cambio en la visualización devuelta para que sea un poco más sólida ante diferentes nombres de secuencia  
- [`gget muscle`](./muscle.md) ahora también permite una lista de secuencias como entrada (como alternativa a proporcionar la ruta a un archivo FASTA)
- Permitir filtro de genes faltante para [`gget cellxgene`](cellxgene.md) (corrige [error](https://github.com/pachterlab/gget/issues/110))
- [`gget seq`](./seq.md): permite nombres de genes faltantes (correccione [https://github.com/pachterlab/gget/issues/107](https://github.com/pachterlab/gget /números/107))  
- Nuevos argumentos para [`gget enrichr`](enrichr.md): use el argumento `kegg_out` y `kegg_rank` para crear una imagen de la vía KEGG con los genes del análisis de enriquecimiento resaltados (gracias a [este PR](https ://github.com/pachterlab/gget/pull/106) por [Noriaki Sato](https://github.com/noriakis))  
- Nuevos módulos: [`gget elm`](elm.md) y [`gget Diamond`](diamond.md)
  
**Versión ≥ 0.27.9** (7 de agosto de 2023):
- Nuevos argumentos para [`gget enrichr`](enrichr.md): use el argumento `background_list` para proporcionar una lista de genes 'background'
- [`gget search`](search.md) ahora también busca sinónimos [Ensembl](https://ensembl.org/) (además de nombres y descripciones de genes) para obtener resultados de búsqueda más completos (gracias a [Samuel Klein](https://github.com/KleinSamuel) por la [sugerencia](https://github.com/pachterlab/gget/issu90))
  
**Versión ≥ 0.27.8** (12 de julio de 2023):
- Nuevo argumento para [`gget search`](search.md): especifique la versión de Ensembl desde la cual se obtiene la información con `-r` `--release`
- Se corrigió un [error](https://github.com/pachterlab/gget/issu91) en [`gget pdb`](pdb.md) (este error se introdujo en la versión 0.27.5)

**Versión ≥ 0.27.7** (15 de mayo de 2023):
- Se movieron las dependencias para los módulos [`gget gpt`](gpt.md) y [`gget cellxgene`](cellxgene.md) de los requisitos instalados automáticamente a [`gget setup`](setup.md)
- Dependencias [`gget alphafold`](alphafold.md) actualizadas para compatibilidad con Python >= 3.10
- Se agregó el argumento `census_version` a [`gget cellxgene`](cellxgene.md)

**Versión ≥ 0.27.6** (1 de mayo de 2023) (TIRO debido a problemas con las dependencias -> reemplazada por la versión 0.27.7):  
- Gracias a el PR de [Tomás Di Domenico](https://github.com/tdido): [`gget search`](search.md) ahora también puede consultar los ID de plantas 🌱 Ensembl  
- Nuevo módulo: [`gget cellxgene`](cellxgene.md)

**Versión ≥ 0.27.5** (6 de abril de 2023):
- Se actualizó [`gget search`](search.md) para que funcione correctamente con la nueva versión de [Pandas](https://pypi.org/project/pandas/2.0.0/) 2.0.0 (lanzado el 3 de abril de 2023), además de versiones anteriores de Pandas
- Se actualizó [`gget info`](info.md) con nuevos banderas `uniprot` y `ncbi` que permiten desactivar los resultados de estas bases de datos de forma independiente para ahorrar tiempo de ejecución (nota: el indicador `ensembl_only` quedó obsoleto)
- Todos los módulos gget ahora tienen una bandera `-q / --quiet` (para Python: `verbose=False`) para desactivar la información de progreso

**Versión ≥ 0.27.4** (19 de marzo de 2023):
- Nuevo módulo: [`gget gpt`](gpt.md) 

**Versión ≥ 0.27.3** (11 de marzo de 2023):
- [`gget info`](info.md) excluye los ID de PDB de forma predeterminada para aumentar la velocidad (los resultados de PDB se pueden incluir usando la marca `--pdb` / `pdb=True`).

**Versión ≥ 0.27.2** (1 de enero de 2023):
- Se actualizó [`gget alphafold`](alphafold.md) a [DeepMind's AlphaFold v2.3.0](https://github.com/deepmind/alphafold/releases/tag/v2.3.0) (incluidos los nuevos argumentos `multimer_for_monomer ` y `multimer_recycles`)

**Versión ≥ 0.27.0** (10 de diciembre de 2022):
- Se actualizó [`gget alphafold`](alphafold.md) para que coincida con los cambios recientes de DeepMind
- Número de versión actualizado para que coincida con la edad de [el creador de gget](https://github.com/lauraluebbert) siguiendo una larga tradición de laboratorio de Pachter

**Versión ≥ 0.3.13** (11 de noviembre de 2022):
- Tiempo de ejecución reducido para [`gget enrichr`](enrichr.md) y [`gget archs4`](archs4.md) cuando se usa con ID de Ensembl

**Versión ≥ 0.3.12** (10 de noviembre de 2022):
- [`gget info`](info.md) ahora también devuelve datos de localización subcelular de UniProt
- El nuevo indicador [`gget info`](info.md) `ensembl_only` devuelve solo los resultados de Ensembl
- Tiempo de ejecución reducido para [`gget info`](info.md) y [`gget seq`](seq.md)

**Versión ≥ 0.3.11** (7 de septiembre de 2022):
- Nuevo módulo: [`gget pdb`](pdb.md)

**Versión ≥ 0.3.10** (2 de septiembre de 2022):
- [`gget alphafold`](alphafold.md) ahora también devuelve valores pLDDT para generar gráficos sin volver a ejecutar el programa (consulte también las [preguntas frecuentes de gget alphafold](https://github.com/pachterlab/gget/discusion39))

**Versión ≥ 0.3.9** (25 de agosto de 2022):
- Instrucciones de instalación de openmm actualizadas para [`gget alphafold`](alphafold.md)

**Versión ≥ 0.3.8** (12 de agosto de 2022):
- Se corrigieron los requisitos de versión de mysql-connector-python

**Versión ≥ 0.3.7** (9 de agosto de 2022):
- **NOTA:** El [sitio FTP de Ensembl](http://ftp.ensembl.org/pub/) cambió su estructura el 8 de agosto de 2022. Actualice a la versión `gget` ≥ 0.3.7 si usa [`obtener ref`](ref.md)

**Versión ≥ 0.3.5** (6 de agosto de 2022):
- Nuevo módulo: [`gget alphafold`](alphafold.md)

**Versión ≥ 0.2.6** (7 de julio de 2022):
- ¡[`gget ref`](ref.md) ahora admite genomas de plantas! 🌱

**Versión ≥ 0.2.5** (30 de junio de 2022):
- **NOTA:** [UniProt](https://www.uniprot.org/) cambió la estructura de su API el 28 de junio de 2022. Actualice a la versión `gget` ≥ 0.2.5 si usa alguno de los módulos que consultan datos de UniProt ([`gget info`](info.md) y [`gget seq`](seq.md)).

**Versión ≥ 0.2.3:** (26 de junio de 2022):
- JSON ahora es el formato de regreso predeterminado para la Terminal para los módulos que anteriormente devolvían el formato de data frame (CSV) (el formato se puede convertir a data frame/CSV usando la bandera `[-csv][--csv]`). El formato data frame/CSV sigue siendo el formato de regreso predeterminada para Python (Jupyter Lab/Google Colab) (y se puede convertir a JSON con `json=True`).
- Para todos los módulos, el primer parámetro requerido se convirtió en un parámetro posicional y ya no debe nombrarse en la línea de comandos, p. ej. `gget ref -s human` &rarr; `gget ref human`.
- `gget info`: `[--expand]` está en desuso. El módulo ahora siempre devolverá toda la información disponible.
- Ligeros cambios en la salida devuelta por `gget info`, incluida la devolución de los ID de Ensembl versionados.
- `gget info` y `gget seq` ahora son compatibles con las IDs de WormBase y FlyBase.
- Ahora también se pueden ingresar IDs de tipo Ensembl a `gget archs4` y `gget enrichr` con la bandera `[-e][--ensembl]` (`ensembl=True` para Python (Jupyter Lab / Google Colab)).
- El parámetro `seqtype` de `gget seq` fue reemplazado por la bandera `[-t][--translate]` (`translate=True/False` para Python (Jupyter Lab / Google Colab)) que devolverá secuencias de nucleótidos (`False`) o aminoácidos (`True`).
- El parámetro `seqtype` de `gget search` se renombró a `id_type` (aún tomando los mismos parámetros 'gene' o 'transcript').
