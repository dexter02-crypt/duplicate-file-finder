# Duplicate File Finder

A small **read-only** command-line tool that groups local files by size and
SHA-256. It prints a readable summary and can export JSON. It has **no delete
command**. Python standard library only; no API key or server.

## Run

Use Python 3.11–3.14. Run from this repository's directory:

```bash
bash setup.sh
.venv/bin/python -m duplicate_finder examples/files --output outputs/demo.json
```

The synthetic example contains six files and two duplicate groups. Actual
captured output is included in [docs/demo.txt](docs/demo.txt).

Scan a folder you own without changing its contents:

```bash
.venv/bin/python -m duplicate_finder "$HOME/Downloads/a-small-folder"
```

Do not start with your entire home directory. Keep the scan small and stable.
An optional JSON report is the only file the CLI writes. Existing reports are
never overwritten. Filenames in a report may be private, so review before
sharing. Reports use relative paths, not the absolute root path.

## What makes it useful

Different filenames can contain the same content. Files are first grouped by
size, then only same-size candidates are hashed in chunks. Symbolic links
and nonregular files are skipped. Hard-link aliases count once, avoiding
fake duplicate-storage totals. The reader checks file identity and timestamps
before and after hashing; unreadable or changing files are excluded with
warnings and a **PARTIAL** result.

## Options

```bash
.venv/bin/python -m duplicate_finder examples/files --include-hidden --max-files 20000 --max-hash-mb 512
```

Defaults: 10,000 encountered file entries and 256 MiB of candidate content to
hash. `.git`, `.venv`, `node_modules`, and `__pycache__` are always ignored.
Hidden entries are ignored unless explicitly included. A limit breach stops
the scan rather than silently truncating the result. Exit code 0 means no
observed errors within scope; code 2 means a partial scan or an error.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover real hashing, same-size/different-content negatives, nested files,
empty files, hard links, symbolic links, changed-file rejection, limits,
terminal escaping, JSON output, actual CLI execution, and source preservation.
See [docs/VALIDATION.md](docs/VALIDATION.md).

## Limits

Groups match file size and SHA-256; there is no extra byte-by-byte equality
comparison. This is not a hostile-filesystem sandbox or a forensic acquisition
tool. Directory races and changes after the scan are outside its guarantee.
Normal reads may update filesystem access times. "Logical duplicate bytes"
is not guaranteed recoverable space: compression, filesystem clones, and
other storage behavior matter. No automatic cleanup is performed.

## License and provenance

MIT. All example files are synthetic. Maintainer: Shikhar Singh; see [docs/PROVENANCE.md](docs/PROVENANCE.md).
Official references: [hashlib](https://docs.python.org/3/library/hashlib.html)
and [os.walk](https://docs.python.org/3/library/os.html#os.walk).
