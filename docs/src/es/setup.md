[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/setup.md)

> Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no especificado de otra manera. Banderas son parámetros de verdadero o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede llamar desde la Terminal con la bandera `-h` `--help`.  
# gget setup 🔧

Función para instalar/descargar dependencias de terceros para un módulo de gget.  

> **Nota:** Algunas dependencias (por ejemplo, `cellxgene-census`) pueden no ser compatibles con las versiones más recientes de Python. Si encuentras errores durante la instalación, intenta usar un entorno con una versión anterior de Python.

**Parámetro posicional**  
`module`  
Módulo gget para el que se deben instalar las dependencias.  

### Por ejemplo
```bash
gget setup alphafold
```
```python
# Python
gget.setup("alphafold")
```
&rarr; Instala todas las dependencias de terceros (modificadas) y descarga los parámetros del algoritmo (~4 GB) necesarios para ejecutar [`gget alphafold`](alphafold.md).
