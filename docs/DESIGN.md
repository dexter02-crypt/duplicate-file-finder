# Design notes

Collect regular-file metadata, deduplicate inode identities, group by size,
hash only candidate groups, then group by the pair (size, SHA-256). Hashing
uses a fixed-size buffer rather than loading a whole file into memory.

A file's device, inode, size, modification time, and change time must match
at collection, opening, and completion. The read consumes the recorded size
plus at most one extra byte, so a growing file cannot keep the reader busy
indefinitely. The final path is checked as well. `O_NOFOLLOW` is used where
available, but ancestor-directory replacement is not sandboxed; use ordinary
stable directories you control.

Repeated hard links to the same inode are not extra copies. SHA-256 matching
is a practical content fingerprint, not a mathematical collision-free proof.
Logical duplicate bytes count all but one file in each group; this is not an
actual disk-reclamation forecast and is never used to trigger deletion.

Three questions to explain: why compare sizes first; why filenames alone
cannot identify duplicates; why hard links should not inflate savings.
A small next improvement would be a user-supplied filename exclusion pattern,
with tests that make the scope visible in JSON.
