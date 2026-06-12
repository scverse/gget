[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/installation.md)

[![pypi version](https://img.shields.io/pypi/v/gget)](https://pypi.org/project/gget)

# Instalación

## Puedes usar `uv` o `pip` para instalar gget:
```bash
uv pip install gget
```
or
```bash
pip install --upgrade gget
```

## Recomendado: Instalar en un entorno limpio

Recomendamos usar un entorno virtual para una instalación limpia y sin conflictos. Puedes usar `uv`, `venv`, or `conda`:

**Con [uv](https://github.com/astral-sh/uv):**
```bash
pip install uv  # if you don't have uv yet
uv venv .venv
source .venv/bin/activate

uv pip install gget
```

**Con pip y venv:**
```bash
python -m venv .venv
source .venv/bin/activate

pip install --upgrade gget
```

**Con conda:**
```bash
conda create -n gget-env python=3.11
conda activate gget-env

pip install --upgrade gget
```

---

Para uso en Jupyter Lab / Google Colab:
```python
import gget
```

---

# Instalar desde el código fuente
```bash
git clone https://github.com/pachterlab/gget.git
cd gget
uv pip install .
```
or

```bash
git clone https://github.com/pachterlab/gget.git
cd gget
pip install .
```
---

# Solución de problemas
- Si ves errores sobre dependencias faltantes, asegúrate de estar usando un entorno limpio y tener la última versión de `pip` o `uv`.
- Si instalaste gget previamente de forma global, desinstálalo con:
  ```bash
  pip uninstall gget
  ```
  o elimina el ejecutable de tu `PATH` del sistema.
- Si sigues teniendo problemas, por favor [contáctanos](https://github.com/pachterlab/gget/issues).
