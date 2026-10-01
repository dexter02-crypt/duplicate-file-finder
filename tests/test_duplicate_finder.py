import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import duplicate_finder
from duplicate_finder.core import FileEntry,digest_file,scan_folder,save_json,signature,terminal_report
ROOT=Path(__file__).resolve().parents[1]
class DuplicateTests(unittest.TestCase):
    def test_package_version_matches_release(self):
        self.assertEqual(duplicate_finder.__version__, "0.1.0")

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def put(self,name,content=b'hello'):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content);return path

    def test_sample_groups_and_bytes(self):
        report=scan_folder(ROOT/'examples/files')
        self.assertEqual(report['files_considered'],6)
        self.assertEqual(report['group_count'],2)
        expected=2*(ROOT/'examples/files/notes.txt').stat().st_size+(ROOT/'examples/files/inventory.csv').stat().st_size
        self.assertEqual(report['logical_duplicate_bytes'],expected)
        self.assertTrue(report['complete'])

    def test_same_size_different_content_not_grouped(self):
        self.put('a',b'ab');self.put('b',b'cd')
        self.assertEqual(scan_folder(self.root)['group_count'],0)

    def test_different_names_same_content(self):
        self.put('a');self.put('nested/b');self.put('c',b'different')
        report=scan_folder(self.root)
        self.assertEqual(report['groups'][0]['files'],['a','nested/b'])
        self.assertEqual(report['logical_duplicate_bytes'],5)

    def test_empty_files(self):
        self.put('a',b'');self.put('b',b'')
        report=scan_folder(self.root)
        self.assertEqual(report['group_count'],1)
        self.assertEqual(report['logical_duplicate_bytes'],0)

    def test_unique_sizes_avoid_hashing(self):
        self.put('a',b'a');self.put('b',b'ab')
        report=scan_folder(self.root)
        self.assertEqual(report['files_hashed'],0)

    def test_hidden_and_ignored_directories(self):
        self.put('a');self.put('.hidden');self.put('.git/object');self.put('node_modules/module')
        self.assertEqual(scan_folder(self.root)['group_count'],0)
        report=scan_folder(self.root,include_hidden=True)
        self.assertEqual(report['groups'][0]['files'],['.hidden','a'])

    def test_symlink_file_and_directory_skipped(self):
        self.put('a');self.put('nested/b')
        (self.root/'link').symlink_to(self.root/'a')
        (self.root/'dirlink').symlink_to(self.root/'nested',target_is_directory=True)
        report=scan_folder(self.root)
        self.assertEqual(report['files_considered'],2)
        self.assertEqual(report['skipped_entries'],2)

    def test_symlink_root_rejected(self):
        (self.root/'real').mkdir();link=self.root/'link';link.symlink_to(self.root/'real',target_is_directory=True)
        with self.assertRaises(ValueError):scan_folder(link)

    def test_hardlinks_count_once(self):
        source=self.put('a');os.link(source,self.root/'b')
        report=scan_folder(self.root)
        self.assertEqual(report['hardlink_aliases_skipped'],1)
        self.assertEqual(report['group_count'],0)

    def test_hash_matches_known_sha(self):
        path=self.put('a',b'hello')
        self.assertEqual(digest_file(FileEntry(path,'a',signature(path.stat())),chunk_size=2),hashlib.sha256(b'hello').hexdigest())

    def test_changed_file_rejected(self):
        path=self.put('a',b'hello');entry=FileEntry(path,'a',signature(path.stat()))
        path.write_bytes(b'changed')
        with self.assertRaises(OSError):digest_file(entry)

    def test_changed_during_hash_is_partial(self):
        self.put('a');self.put('b')
        with patch('duplicate_finder.core.digest_file',side_effect=OSError('changed')):
            report=scan_folder(self.root)
        self.assertFalse(report['complete'])
        self.assertEqual(len(report['warnings']),2)
        self.assertEqual(report['group_count'],0)

    def test_limit_refusal(self):
        self.put('a');self.put('b')
        with self.assertRaises(ValueError):scan_folder(self.root,max_files=1)
        with self.assertRaises(ValueError):scan_folder(self.root,max_hash_bytes=1)

    def test_files_remain_unchanged(self):
        self.put('a');self.put('b')
        before={p.name:(p.read_bytes(),signature(p.stat())) for p in self.root.iterdir()}
        scan_folder(self.root)
        after={p.name:(p.read_bytes(),signature(p.stat())) for p in self.root.iterdir()}
        self.assertEqual(before,after)

    def test_output_does_not_overwrite(self):
        report=scan_folder(self.root);target=self.root/'out.json'
        save_json(report,target)
        self.assertEqual(json.loads(target.read_text()),report)
        with self.assertRaises(FileExistsError):save_json(report,target)

    def test_empty_folder(self):
        report=scan_folder(self.root)
        self.assertEqual(report['group_count'],0)
        self.assertTrue(report['complete'])

    def test_terminal_paths_are_escaped(self):
        self.put('a\x1b[31m');self.put('b')
        text=terminal_report(scan_folder(self.root))
        self.assertNotIn('\x1b',text)
        self.assertIn('\\u001b',text)

    def test_cli_demo(self):
        output=self.root/'report.json'
        result=subprocess.run([sys.executable,'-m','duplicate_finder','examples/files','--output',str(output)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Duplicate groups: 2',result.stdout)
        self.assertEqual(json.loads(output.read_text())['group_count'],2)

    def test_invalid_root(self):
        with self.assertRaises(ValueError):scan_folder(self.root/'missing')
