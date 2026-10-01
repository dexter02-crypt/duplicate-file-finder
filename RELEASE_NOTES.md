# duplicate-file-finder 0.1.0

Duplicate File Finder is a small read-only Python command-line tool that groups local files by size and SHA-256. It does not contain a delete command and uses the Python standard library only.

## Highlights

- Groups different filenames with matching size and SHA-256.
- Hashes only same-size candidates using streamed reads.
- Skips symbolic links and nonregular files.
- Counts hard-link aliases once instead of inflating duplicate totals.
- Rejects or excludes files that change while being hashed.
- Enforces file-count and candidate-hashing limits.
- Prints escaped terminal paths and can export a JSON report without overwriting an existing file.
- Reports logical duplicate bytes without claiming physical disk space savings.

## Existing public validation

Public `main` commit `c54508aa4390d66320da4262580312ada7a3040d` passed GitHub Actions run `36765362499`.

That run completed successfully across six jobs:

- Ubuntu / Python 3.11
- Ubuntu / Python 3.13
- Ubuntu / Python 3.14
- macOS / Python 3.11
- macOS / Python 3.13
- macOS / Python 3.14

## Release-candidate validation

The release-candidate local suite contains 20 test methods, including a package-version identity check.

The release-candidate workflow adds Python 3.12 on both Ubuntu and macOS, expanding the configured matrix from six to eight jobs. Release publication requires the full eight-job Ubuntu/macOS matrix to pass on the final main commit; branch and pull-request runs are intermediate evidence.

## Scope

This is a bounded local duplicate-candidate reporting tool. SHA-256 matching is a practical content fingerprint, not a mathematical collision-free proof. It is not a hostile-filesystem sandbox, forensic acquisition tool, or automatic cleanup utility.

Logical duplicate bytes are not guaranteed recoverable disk space because compression, filesystem clones, allocation units, and other storage behavior can differ.
