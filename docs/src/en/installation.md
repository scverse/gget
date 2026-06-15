[<kbd> View page source on GitHub </kbd>](https://github.com/scverse/gget/blob/main/docs/src/en/installation.md)

[![pypi version](https://img.shields.io/pypi/v/gget)](https://pypi.org/project/gget)

# Installation

## You can use `uv` or `pip` to install gget:
```bash
uv pip install gget
```
or
```bash
pip install --upgrade gget
```

## Recommended: Install in a clean environment

We recommend using a virtual environment for a clean, conflict-free install. You can use `uv`, `venv`, or `conda`:

**With [uv](https://github.com/astral-sh/uv):**
```bash
pip install uv  # if you don't have uv yet
uv venv .venv
source .venv/bin/activate

uv pip install gget
```

**With pip and venv:**
```bash
python -m venv .venv
source .venv/bin/activate

pip install --upgrade gget
```

**With conda:**
```bash
conda create -n gget-env python=3.11
conda activate gget-env

pip install --upgrade gget
```

---

For use in Jupyter Lab / Google Colab:
```python
import gget
```

---

# Install from source
```bash
git clone https://github.com/scverse/gget.git
cd gget
uv pip install .
```
or

```bash
git clone https://github.com/scverse/gget.git
cd gget
pip install .
```
---

# Troubleshooting
- If you see errors about missing dependencies, make sure you are using a clean environment and have the latest version of pip or uv.
- If you previously installed gget system-wide, uninstall it with:
  ```bash
  pip uninstall gget
  ```
  or remove the executable from your system path.
- If you continue to having trouble, please [reach out](https://github.com/scverse/gget/issues).
