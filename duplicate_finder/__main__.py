import argparse
from pathlib import Path
import sys
from .core import scan_folder, save_json, terminal_report

def main(argv=None):
    parser=argparse.ArgumentParser(description='Find size/SHA-256 duplicate groups without deleting source files.')
    parser.add_argument('folder',type=Path)
    parser.add_argument('--output',type=Path,help='Optional new JSON report; existing files are never overwritten.')
    parser.add_argument('--include-hidden',action='store_true')
    parser.add_argument('--max-files',type=int,default=10000)
    parser.add_argument('--max-hash-mb',type=int,default=256,help='Maximum candidate content to hash, in MiB.')
    args=parser.parse_args(argv)
    try:
        if args.output and (args.output.exists() or args.output.is_symlink()):
            raise FileExistsError('Output already exists. Choose a new JSON filename.')
        report=scan_folder(args.folder,include_hidden=args.include_hidden,max_files=args.max_files,max_hash_bytes=args.max_hash_mb*1024*1024)
        if args.output:
            save_json(report,args.output)
        print(terminal_report(report))
        if args.output:
            print(f'Report: {args.output}')
        return 0 if report['complete'] else 2
    except (OSError,ValueError) as exc:
        print(f'Error: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
