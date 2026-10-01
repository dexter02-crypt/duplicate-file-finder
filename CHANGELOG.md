# Changelog

## 0.1.0 — 2026-10-01

Initial public release of the read-only duplicate-file finder.

- Groups regular files by size and SHA-256 without deleting or rewriting source files.
- Skips symbolic links and nonregular files.
- Counts hard-link aliases once.
- Detects files that change during hashing and reports a partial result.
- Enforces file-count and hashing-work limits.
- Escapes terminal paths and supports non-overwriting JSON export.
- Includes automated tests, synthetic examples, documentation, and GitHub Actions coverage.
