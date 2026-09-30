# Validation record

## Executed here

- Environment: Linux, CPython 3.13.5.
- Command: `python -B -m unittest discover -s tests -v`.
- Result: **19 tests passed**, zero failed, zero skipped.
- Full captured test output: [test-output.txt](test-output.txt).

The application and its tests use Python standard-library modules only.

The included `setup.sh` was also executed in a fresh, isolated project copy: it created a new virtual environment and passed all tests without third-party dependencies.

## Actual demonstration

The included six-file fixture yields two duplicate groups, five files hashed and 173 logical duplicate bytes. `docs/demo.txt` and `docs/demo.json` are actual application outputs. These bytes are not a promise of physical disk space recovered. No input file is removed, moved or overwritten.

## Boundaries

macOS installation, your local GUI/file-opening behavior, successful live webcam
capture, real GitHub publication and GitHub Actions execution have **not** been
verified by this record. The workflow requests multiple Python/OS combinations;
that configuration is not evidence that those jobs ran. No measured detection
accuracy, production-readiness or universal input-correctness claim is made.
These are author-run tests, not independent certification.

## Your local verification

Run setup and the sample on your own machine. Once the repository is published,
record your actual OS/Python versions, the command, its real result, and one
small change you understand. Do not rewrite unexecuted checks as passing checks.
