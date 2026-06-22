[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/es/setup.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget setup 🔧

Función para instalar/descargar dependencias de terceros para un módulo de gget.  

> **Nota:** Algunas dependencias (por ejemplo, `cellxgene-census`) pueden no ser compatibles con las versiones más recientes de Python. Si encuentras errores durante la instalación, intenta usar un entorno con una versión anterior de Python.

**Parámetro posicional**  
`module`  
Módulo gget para el que se deben instalar las dependencias.  
Elige entre: "alphafold", "gpt", "cellxgene", "elm", o "cbio"

**Parámetros optionales**  
`-o` `--out`  
Solo aplica cuando `module='elm'`. Ruta a una carpeta donde se descargarán los archivos sin procesar de la base de datos ELM (`elm_instances.fasta`, `elms_classes.tsv`, `elm_instances.tsv`, `elm_interaction_domains.tsv`) — útil si deseas una copia local de los datos de ELM para tus propios scripts o inspección, de forma independiente a ejecutar [`gget elm`](elm.md).  
NOTA: Para configurar los archivos de modo que [`gget elm`](elm.md) pueda usarlos, **omite este argumento** — [`gget elm`](elm.md) solo lee desde la ubicación predeterminada dentro de la carpeta de instalación del paquete `gget`. Los archivos descargados en una ruta `--out` personalizada no serán detectados por [`gget elm`](elm.md).  
Por defecto: None (los archivos descargados se guardan dentro de la carpeta de instalación del paquete `gget` donde [`gget elm`](elm.md) puede encontrarlos).  

**Banderas**  
`-q` `--quiet`  
Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.  
Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa.


### Por ejemplo
```bash
gget setup alphafold
```
```python
# Python
gget.setup("alphafold")
```
&rarr; Instala todas las dependencias de terceros (modificadas) y descarga los parámetros del algoritmo (~4 GB) necesarios para ejecutar [`gget alphafold`](alphafold.md).
