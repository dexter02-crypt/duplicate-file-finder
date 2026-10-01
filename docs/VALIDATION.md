# Validation record

## Public implementation baseline

Repository: `dexter02-crypt/duplicate-file-finder`

Baseline `main` commit:

`c54508aa4390d66320da4262580312ada7a3040d`

GitHub Actions run `36765362499` completed successfully on that exact commit.

The six successful jobs were:

- macOS / Python 3.11
- macOS / Python 3.13
- macOS / Python 3.14
- Ubuntu / Python 3.11
- Ubuntu / Python 3.13
- Ubuntu / Python 3.14

Each job checked out the repository, configured Python, processed the dependency file, and ran:

`python -m unittest discover -s tests -v`

## Release-candidate local coverage

The release-candidate suite contains **20 test methods**.

Coverage includes:

- expected duplicate groups and logical duplicate bytes from the synthetic fixture
- same-size/different-content rejection
- duplicate content under different filenames and nested paths
- empty files
- avoiding hashes for unique sizes
- hidden and ignored directory behavior
- symbolic-link skipping and symbolic-link root rejection
- hard-link alias deduplication
- known SHA-256 hashing
- changed-file rejection before and during hashing
- partial-result behavior
- file-count and hashing-work limits
- source-file preservation
- refusal to overwrite an existing JSON report
- empty-folder behavior
- terminal path escaping
- real CLI execution and JSON output
- invalid-root rejection
- package version identity for 0.1.0

The release-candidate workflow adds Python 3.12 on both Ubuntu and macOS, expanding the configured matrix from six to eight jobs. Release publication requires the full eight-job Ubuntu/macOS matrix to pass on the final main commit; branch and pull-request runs are intermediate evidence.

## Demonstration

The included six-file synthetic fixture produces two duplicate groups. The repository includes `docs/demo.txt` and `docs/demo.json` as captured application outputs.

The reported logical duplicate bytes are not a promise of physical disk space that can be reclaimed.

## Boundaries

The application uses Python standard-library modules only.

It is intentionally read-only with respect to scanned source files. The optional JSON report is the only CLI output file. Existing report files are not overwritten.

Groups match size and SHA-256; there is no separate byte-for-byte equality pass. Repeated hard links to the same inode are counted once. Symbolic links and nonregular files are skipped.

A file is checked by device, inode, size, modification time, and change time around hashing, but the tool is not an adversarial filesystem sandbox. Directory races and later changes remain outside its guarantees.

GitHub Actions evidence demonstrates only the listed hosted runner/Python combinations. It does not establish universal filesystem behavior, collision impossibility, forensic suitability, or recoverable disk-space guarantees.
