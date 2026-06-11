#!/usr/bin/env python3
"""
Translate English documentation changes to Spanish using the Claude API.

For modified files, only the specific edits are translated and applied.
For new files, the entire file is translated.
Deleted English files cause the Spanish counterpart to be deleted.

Reference Spanish files and a glossary are provided to Claude to ensure
consistent terminology across all translated documents.
"""

import os
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic

EN_DIR = "docs/src/en"
ES_DIR = "docs/src/es"

# Files to use as style/terminology reference (picked for breadth of patterns)
REFERENCE_FILES = ["archs4.md", "blast.md", "info.md"]

# Glossary of canonical translations for repeated terms.
# This is fed to the model so that flags like --quiet always get
# the same Spanish description regardless of which file is being translated.
GLOSSARY = """\
## Translation glossary - use these EXACT translations for consistency

### Page boilerplate
- GitHub link text: "Ver el codigo fuente de la pagina en GitHub"
  (URL must point to es/ version of the file)
- Python-args note (modules): "Parámetros de Python són iguales a los parámetros largos (`--parámetro`) de Terminal, si no es especificado de otra manera. Las banderas son designadas como cierto o falso (True/False) en Python. El manuál para cualquier modulo de gget se puede obtener desde Terminal con la bandera `-h` `--help`."

### Section headers
- "Positional argument" → "Parámetro posicional"
- "Optional arguments" → "Parámetros optionales"
- "Flags" → "Banderas"
- "Examples" / "Example" → "Ejemplo"
- "More examples" → "Más ejemplos"
- "References" / "If you use `gget X` in a publication, please cite the following articles:" → "Citar" / "Si utiliza `gget X` en una publicación, favor de citar los siguientes artículos:"

### Common flag/argument descriptions
- `-q` `--quiet`:
  "Solo para Terminal. Impide la información de progreso de ser exhibida durante la ejecución del programa.
  Para Python, usa `verbose=False` para impedir la información de progreso de ser exhibida durante la ejecución del programa."

- `-o` `--out`:
  "Ruta al archivo en el que se guardarán los resultados, p. ej. ruta/al/directorio/resultados.csv (o .json). Por defecto: salida estándar (STDOUT).
  Para Python, use `save=True` para guardar los resultados en el directorio de trabajo actual."

- `-csv` `--csv`:
  "Solo para Terminal. Produce los resultados en formato CSV.
  Para Python, usa `json=True` para obtener los resultados en formato JSON."

- `-e` `--ensembl`:
  "Usa esta bandera si `gene` se ingresa como ID tipo Ensembl."

### Common phrases
- "Return format:" → "Produce: Resultados en formato"
- "Default:" / "(default)" → "Por defecto:" / "(se usa por defecto)"
- "e.g." → "p. ej."
- "Command-line only." → "Solo para Terminal."
- "Python: Use ..." → "Para Python, usa ..."

### Rules
- Do NOT translate: code snippets, command examples, function names, parameter
  names/values, URLs (the `(...)` part of links), file paths, gene names,
  database names, tool names (gget, ARCHS4, Ensembl, UniProt, BLAST, etc.),
  reference citations.
- DO translate: all human-readable text, INCLUDING link text (the `[...]` part
  of markdown links). For example, `[No-code, shareable Google Colab notebook
  for querying viral sequences.](https://...)` → the text inside `[...]` should
  be translated to Spanish while the URL stays unchanged.
- Keep ALL markdown formatting exactly as-is: tables, links, code blocks,
  HTML tags, emojis, blank lines, trailing spaces for line breaks.
- The GitHub source link URL must use es/ instead of en/.
"""


def get_changed_files(before_sha, after_sha):
    """Return dict of added/modified/deleted English doc files."""
    # Check if before_sha is a valid commit
    is_valid = subprocess.run(
        ["git", "cat-file", "-t", before_sha],
        capture_output=True,
        text=True,
    ).returncode == 0

    if not is_valid:
        # Initial push or invalid ref — treat all current files as new
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", after_sha, "--", EN_DIR],
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "added": [f for f in result.stdout.strip().split("\n") if f],
            "modified": [],
            "deleted": [],
        }

    result = subprocess.run(
        ["git", "diff", "--name-status", before_sha, after_sha, "--", EN_DIR],
        capture_output=True,
        text=True,
        check=True,
    )

    files = {"added": [], "modified": [], "deleted": []}
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0][0]  # A, M, D, or R (first char handles R100 etc.)
        if status == "A":
            files["added"].append(parts[1])
        elif status == "M":
            files["modified"].append(parts[1])
        elif status == "D":
            files["deleted"].append(parts[1])
        elif status == "R":
            files["deleted"].append(parts[1])
            files["added"].append(parts[2])
    return files


def get_file_diff(filepath, before_sha, after_sha):
    """Return the unified diff for a single file."""
    result = subprocess.run(
        ["git", "diff", before_sha, after_sha, "--", filepath],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def load_reference_files():
    """Load a few Spanish files to give the model style context."""
    refs = {}
    for fname in REFERENCE_FILES:
        path = Path(ES_DIR) / fname
        if path.exists():
            refs[fname] = path.read_text()
    return refs


def build_reference_block(references):
    """Format reference files into a single text block."""
    return "\n\n---\n\n".join(
        f"=== {name} ===\n{content}" for name, content in references.items()
    )


def clean_model_output(text):
    """Strip markdown code-fences the model may wrap around the output."""
    text = text.strip()
    for prefix in ("```markdown", "```md", "```"):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
            break
    if text.endswith("```"):
        text = text[:-3].strip()
    return text + "\n"


def translate_new_file(client, en_content, filename, ref_block):
    """Translate a complete English file to Spanish."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16384,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Translate the following English gget documentation file to Spanish.\n\n"
                    f"You MUST match the style, terminology, and formatting of the existing "
                    f"Spanish documentation files provided below as reference. Use the "
                    f"glossary for common translations.\n\n"
                    f"Output ONLY the translated markdown content. Do not include any "
                    f"commentary, explanations, or markdown code fences around the output.\n\n"
                    f"{GLOSSARY}\n\n"
                    f"### Existing Spanish files for style reference:\n{ref_block}\n\n"
                    f"### English file to translate ({filename}):\n{en_content}"
                ),
            }
        ],
    )
    return clean_model_output(response.content[0].text)


def translate_diff(client, diff_text, en_content, es_content, filename, ref_block):
    """Apply only the changed parts of an English file to its Spanish counterpart."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16384,
        messages=[
            {
                "role": "user",
                "content": (
                    f"The English documentation file '{filename}' has been updated. "
                    f"Apply ONLY the corresponding changes to the Spanish version.\n\n"
                    f"CRITICAL RULES:\n"
                    f"1. Do NOT rewrite or re-translate the entire Spanish file. ONLY modify "
                    f"the parts that correspond to changes shown in the English diff.\n"
                    f"2. For added lines/sections: translate them and insert at the "
                    f"corresponding position in the Spanish file.\n"
                    f"3. For removed lines/sections: remove the corresponding content from "
                    f"the Spanish file.\n"
                    f"4. For modified lines: update ONLY those lines in the Spanish file.\n"
                    f"5. Everything else in the Spanish file MUST remain EXACTLY as-is, "
                    f"preserving existing translations word-for-word, including any existing "
                    f"quirks or typos that were not affected by the diff.\n"
                    f"6. Use the glossary below for consistent translations of any NEW text.\n"
                    f"7. Output ONLY the complete updated Spanish file content. No commentary, "
                    f"no code fences.\n\n"
                    f"{GLOSSARY}\n\n"
                    f"### Existing Spanish files for style reference:\n{ref_block}\n\n"
                    f"### Diff of changes to the English file:\n```\n{diff_text}\n```\n\n"
                    f"### Current full English file (for context):\n{en_content}\n\n"
                    f"### Current Spanish file (apply changes to this):\n{es_content}"
                ),
            }
        ],
    )
    return clean_model_output(response.content[0].text)


def main():
    before_sha = os.environ.get("BEFORE_SHA", "").strip()
    after_sha = os.environ.get("AFTER_SHA", "HEAD").strip()

    # Fall back to HEAD~1 when no valid before SHA is available
    if not before_sha or before_sha == "0" * 40:
        before_sha = "HEAD~1"

    print(f"Comparing {before_sha}..{after_sha}")

    changed = get_changed_files(before_sha, after_sha)
    if not any(changed.values()):
        print("No English doc files changed.")
        return

    total = sum(len(v) for v in changed.values())
    print(
        f"Changes detected — added: {len(changed['added'])}, "
        f"modified: {len(changed['modified'])}, "
        f"deleted: {len(changed['deleted'])} "
        f"({total} file(s) total)"
    )

    client = Anthropic()
    references = load_reference_files()
    ref_block = build_reference_block(references)

    # --- Deletions ---
    for filepath in changed["deleted"]:
        es_path = filepath.replace(EN_DIR, ES_DIR, 1)
        if Path(es_path).exists():
            Path(es_path).unlink()
            print(f"Deleted: {es_path}")

    # --- New files ---
    for filepath in changed["added"]:
        en_content = Path(filepath).read_text()
        filename = Path(filepath).name
        print(f"Translating new file: {filename} ...")
        translated = translate_new_file(client, en_content, filename, ref_block)
        es_path = filepath.replace(EN_DIR, ES_DIR, 1)
        Path(es_path).parent.mkdir(parents=True, exist_ok=True)
        Path(es_path).write_text(translated)
        print(f"  -> Created: {es_path}")

    # --- Modified files ---
    for filepath in changed["modified"]:
        filename = Path(filepath).name
        es_path = filepath.replace(EN_DIR, ES_DIR, 1)
        en_content = Path(filepath).read_text()

        if not Path(es_path).exists():
            # No Spanish counterpart yet — translate the full file
            print(f"Spanish file missing for {filename}, translating full file ...")
            translated = translate_new_file(client, en_content, filename, ref_block)
        else:
            diff_text = get_file_diff(filepath, before_sha, after_sha)
            if not diff_text.strip():
                print(f"No diff for {filename}, skipping.")
                continue
            es_content = Path(es_path).read_text()
            print(f"Applying edits to {filename} ...")
            translated = translate_diff(
                client, diff_text, en_content, es_content, filename, ref_block
            )

        Path(es_path).parent.mkdir(parents=True, exist_ok=True)
        Path(es_path).write_text(translated)
        print(f"  -> Updated: {es_path}")

    print("Translation complete.")


if __name__ == "__main__":
    main()
