"""Fresh, bounded static PE evidence for quest prefab lifecycle; no execution."""
from pathlib import Path
import argparse, json, struct, sys
HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[3]
sys.path.insert(0, str(WORKSPACE / 'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def main():
    ap = argparse.ArgumentParser()
    for name in ('rva', 'pointer', 'callers', 'refs', 'qwords'):
        ap.add_argument('--' + name, action='append', default=[], type=lambda s: int(s, 0))
    ap.add_argument('--span', action='append', default=[])
    ap.add_argument('--strings', action='append', default=[])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()
    assert args.out.resolve().parent == HERE and not args.out.exists()
    im = Image()
    result = {'exe_sha256': im.sha, 'method': 'Read-only pinned PE .pdata and Capstone. No binary loading, game API, process attachment, or save access.',
              'functions': [im.disasm(v) for v in args.rva],
              'pointer_refs': {hex(v): im.pointers_to(v) for v in args.pointer},
              'direct_call_candidates': {hex(v): im.calls_to(v) for v in args.callers},
              'rip_ref_candidates': {hex(v): im.refs_to(v) for v in args.refs},
              'qwords': {hex(v): [(hex(v+i*8), hex(struct.unpack_from('<Q', im.data, im.off(v)+i*8)[0])) for i in range(80)] for v in args.qwords},
              'explicit_spans': [], 'strings': {}, 'game_api_calls': 0, 'runtime_changes': 0}
    for spec in args.span:
        a, c = (int(v, 0) for v in spec.split(':'))
        assert 0 < c-a <= 8192
        result['explicit_spans'].append({'begin_rva': hex(a), 'end_rva': hex(c), 'boundary_limit': 'Explicit bounded span; no function-boundary claim',
            'instructions': [{'rva': hex(i.address-im.base), 'bytes': i.bytes.hex(), 'mnemonic': i.mnemonic, 'operands': i.op_str}
                             for i in im.md.disasm(im.data[im.off(a):im.off(a)+c-a], im.base+a)]})
    for value in args.strings:
        rows = []; off = 0
        while True:
            off = im.data.find(value.encode(), off)
            if off < 0: break
            try:
                rva = im.rva(off)
                rows.append({'rva': hex(rva), 'refs': im.refs_to(rva)})
            except StopIteration: pass
            off += 1
        result['strings'][value] = rows
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    for key in ('pointer_refs', 'direct_call_candidates', 'rip_ref_candidates', 'qwords', 'strings'):
        if result[key]: print(key, result[key])
    for f in result['functions'] + result['explicit_spans']:
        print('Function/span', f['begin_rva'], f['end_rva'], len(f['instructions']))
        if not args.quiet:
            for row in f['instructions']: print(row['rva'], row['mnemonic'], row['operands'])

if __name__ == '__main__': main()
