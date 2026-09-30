"""Read-only duplicate candidates by size and SHA-256. Never deletes source files."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat

IGNORED_DIRECTORIES = {'.git', '.venv', 'node_modules', '__pycache__'}

@dataclass(frozen=True)
class FileEntry:
    path: Path
    relative: str
    signature: tuple[int, int, int, int, int]
    @property
    def size(self) -> int:
        return self.signature[2]


def signature(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def digest_file(entry: FileEntry, *, chunk_size: int = 1024 * 1024) -> str:
    """Check the collected snapshot before/after a bounded, streamed read."""
    if chunk_size < 1:
        raise ValueError('chunk_size must be positive.')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    descriptor = os.open(entry.path, flags)
    with os.fdopen(descriptor, 'rb') as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode) or signature(before) != entry.signature:
            raise OSError('File changed before hashing.')
        digest = hashlib.sha256()
        remaining = entry.size
        while remaining:
            block = handle.read(min(chunk_size, remaining))
            if not block:
                raise OSError('File shrank while hashing.')
            digest.update(block)
            remaining -= len(block)
        # Read at most one extra byte; do not follow an indefinitely growing file.
        if handle.read(1):
            raise OSError('File grew while hashing.')
        if signature(os.fstat(handle.fileno())) != entry.signature:
            raise OSError('File changed while hashing.')
    after = entry.path.lstat()
    if not stat.S_ISREG(after.st_mode) or signature(after) != entry.signature:
        raise OSError('Path changed after hashing.')
    return digest.hexdigest()


def scan_folder(root: Path, *, include_hidden: bool = False, max_files: int = 10_000,
                max_hash_bytes: int = 256 * 1024 * 1024) -> dict:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Root must be an existing directory, not a symbolic link.')
    if max_files < 1 or max_hash_bytes < 0:
        raise ValueError('max_files must be positive and max_hash_bytes nonnegative.')
    root = root.resolve()
    by_size: dict[int, list[FileEntry]] = defaultdict(list)
    seen_inodes = set()
    warnings = []
    file_count = visited = skipped = hardlinks = 0

    def walk_error(exc):
        # Do not export absolute paths in reports.
        try:
            name = str(Path(exc.filename).relative_to(root))
        except (TypeError, ValueError):
            name = '(directory)'
        warnings.append({'path': name, 'reason': 'Could not read directory.'})

    for current, directories, names in os.walk(root, followlinks=False, onerror=walk_error):
        parent = Path(current)
        keep = []
        for name in sorted(directories):
            path = parent / name
            if name in IGNORED_DIRECTORIES or (name.startswith('.') and not include_hidden) or path.is_symlink():
                skipped += 1
            else:
                keep.append(name)
        directories[:] = keep
        for name in sorted(names):
            visited += 1
            if visited > max_files:
                raise ValueError(f'Encountered more than {max_files} file entries. Choose a smaller folder or raise --max-files.')
            path = parent / name
            relative = path.relative_to(root).as_posix()
            if name.startswith('.') and not include_hidden:
                skipped += 1
                continue
            try:
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode):
                    skipped += 1
                    continue
                inode = (info.st_dev, info.st_ino)
                if inode in seen_inodes:
                    hardlinks += 1
                    continue
                seen_inodes.add(inode)
                file_count += 1
                by_size[info.st_size].append(FileEntry(path, relative, signature(info)))
            except OSError:
                warnings.append({'path': relative, 'reason': 'Could not inspect file.'})
    candidates = [entry for size in sorted(by_size) if len(by_size[size]) > 1 for entry in by_size[size]]
    expected_bytes = sum(entry.size for entry in candidates)
    if expected_bytes > max_hash_bytes:
        raise ValueError(f'Candidate content totals {expected_bytes} bytes; the hashing limit is {max_hash_bytes}. Choose a smaller folder or raise --max-hash-mb.')
    by_hash: dict[tuple[int, str], list[str]] = defaultdict(list)
    hashed_files = hashed_bytes = 0
    for entry in candidates:
        try:
            digest = digest_file(entry)
            by_hash[(entry.size, digest)].append(entry.relative)
            hashed_files += 1
            hashed_bytes += entry.size
        except OSError:
            warnings.append({'path': entry.relative, 'reason': 'Unreadable or changed during hashing; excluded.'})
    groups = []
    for (size, digest), paths in sorted(by_hash.items()):
        if len(paths) > 1:
            groups.append({'size_bytes': size, 'sha256': digest, 'files': sorted(paths),
                           'logical_duplicate_bytes': size * (len(paths)-1)})
    return {'root_name': root.name, 'complete': not warnings, 'files_considered': file_count,
            'files_hashed': hashed_files, 'bytes_hashed_successfully': hashed_bytes,
            'skipped_entries': skipped, 'hardlink_aliases_skipped': hardlinks,
            'group_count': len(groups), 'groups': groups,
            'logical_duplicate_bytes': sum(group['logical_duplicate_bytes'] for group in groups),
            'warnings': warnings,
            'scope': {'include_hidden': include_hidden, 'ignored_directories': sorted(IGNORED_DIRECTORIES),
                      'max_files': max_files, 'max_hash_bytes': max_hash_bytes},
            'notes': ['Read-only scan: no source file is deleted, renamed, or rewritten.',
                      'Groups match size and SHA-256; there is no separate byte-by-byte comparison.',
                      'Logical duplicate bytes are not guaranteed recoverable disk space.',
                      'Hard-link aliases are counted once. Symlinks and nonregular files are skipped.',
                      'Complete means no observed read errors within the stated scope, not a whole-disk inventory.',
                      'This is not an adversarial filesystem sandbox; use a stable local directory.']}


def terminal_report(report: dict) -> str:
    # JSON-quote paths so filenames cannot inject terminal escape sequences.
    safe = lambda value: json.dumps(value, ensure_ascii=True)
    lines = ['DUPLICATE FILE FINDER — READ-ONLY',
             f"Status: {'COMPLETE within selected scope' if report['complete'] else 'PARTIAL — see warnings'}",
             f"Files considered: {report['files_considered']} | Files hashed: {report['files_hashed']}",
             f"Duplicate groups: {report['group_count']}",
             f"Logical duplicate bytes: {report['logical_duplicate_bytes']} (not a disk-space guarantee)"]
    for index, group in enumerate(report['groups'], 1):
        lines.append(f"\nGroup {index} | {group['size_bytes']} bytes each | SHA-256 {group['sha256'][:16]}...")
        lines.extend('  '+safe(path) for path in group['files'])
    for warning in report['warnings']:
        lines.append('WARNING '+safe(warning['path'])+': '+warning['reason'])
    lines.append('\nNo source files were modified or deleted.')
    return '\n'.join(lines)


def save_json(report: dict, output: Path) -> None:
    output = Path(output)
    payload = json.dumps(report, indent=2, ensure_ascii=True) + '\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        handle.write(payload)
