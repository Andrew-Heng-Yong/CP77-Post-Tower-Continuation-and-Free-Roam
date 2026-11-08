"""Pinned executable and graph inspection only. Never opens a process or save."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'saved_graph_state_01'))
from inspect_native import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--string', action='append', default=[])
    ap.add_argument('--rva', action='append', default=[], type=lambda x: int(x, 0))
    ap.add_argument('--calls', action='append', default=[], type=lambda x: int(x, 0))
    ap.add_argument('--refs', action='append', default=[], type=lambda x: int(x, 0))
    ap.add_argument('--table', action='append', default=[], type=lambda x: int(x, 0))
    args = ap.parse_args()
    out = HERE / args.out
    assert out.parent == HERE and not out.exists(), 'Fresh local output required'
    im = Image()
    result = {
        'exe_sha256': im.sha,
        'method': 'Pinned executable file bytes, PE unwind boundaries, static Capstone decoding. No process, game API or original save access.',
        'functions': {hex(r): im.disasm(r) for r in args.rva},
        'calls': {hex(r): im.calls_to(r) for r in args.calls},
        'refs': {hex(r): im.refs_to(r) for r in args.refs},
        'tables': {hex(r): [hex(struct.unpack_from('<Q', im.data, im.off(r)+i*8)[0]) for i in range(48)] for r in args.table},
        'strings': {},
    }
    for text in args.string:
        needle = text.encode() + b'\0'
        rows = []
        offset = 0
        while (offset := im.data.find(needle, offset)) >= 0:
            rva = im.rva(offset)
            rows.append({'rva': hex(rva), 'refs': im.refs_to(rva)})
            offset += len(needle)
        result['strings'][text] = rows
    out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('functions', 'tables')}))
    for r, f in result['functions'].items():
        print('FUNCTION', r, f.get('begin_rva'), f.get('end_rva'))
        if not args.quiet:
            for i in f['instructions']:
                print(i['rva'], i['mnemonic'], i['operands'])


if __name__ == '__main__':
    main()
