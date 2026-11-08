"""Read-only PE inspection; never loads the game binary or a save.

Output must be fresh. Static function boundaries come from PE .pdata.
"""
from pathlib import Path
import argparse, bisect, hashlib, json, struct, sys

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
sys.path.insert(0, str(WORKSPACE / 'research/finalboards_dismissal/tooling/python'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

EXE = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe')
EXPECTED = 'D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'

class Image:
    def __init__(self):
        self.data = EXE.read_bytes()
        self.sha = hashlib.sha256(self.data).hexdigest().upper()
        assert self.sha == EXPECTED, 'Native binary differs from the previously verified version'
        pe = struct.unpack_from('<I', self.data, 60)[0]
        op = pe + 24
        self.base = struct.unpack_from('<Q', self.data, op + 24)[0]
        sh = op + struct.unpack_from('<H', self.data, pe + 20)[0]
        self.sections = []
        for i in range(struct.unpack_from('<H', self.data, pe + 6)[0]):
            at = sh + i * 40
            name = self.data[at:at+8].rstrip(b'\0').decode()
            vs, rva, size, raw = struct.unpack_from('<IIII', self.data, at + 8)
            self.sections.append((name, rva, size, raw))
        _, pd, ps, po = next(x for x in self.sections if x[0] == '.pdata')
        self.functions = []
        for i in range(po, po + ps - 11, 12):
            a, c, u = struct.unpack_from('<III', self.data, i)
            if a and c > a:
                self.functions.append((a, c, u))
        self.functions.sort()
        self.starts = [x[0] for x in self.functions]
        self.md = Cs(CS_ARCH_X86, CS_MODE_64)

    def off(self, rva):
        return next(raw + rva - a for _, a, size, raw in self.sections if a <= rva < a + size)

    def rva(self, off):
        return next(a + off - raw for _, a, size, raw in self.sections if raw <= off < raw + size)

    def function(self, rva):
        at = bisect.bisect_right(self.starts, rva) - 1
        if at >= 0 and self.functions[at][0] <= rva < self.functions[at][1]:
            return self.functions[at]

    def disasm(self, rva):
        f = self.function(rva)
        if not f:
            rows = []
            for i in self.md.disasm(self.data[self.off(rva):self.off(rva)+256], self.base+rva):
                rows.append(dict(rva=hex(i.address-self.base), bytes=i.bytes.hex(), mnemonic=i.mnemonic,
                                 operands=i.op_str))
                if i.mnemonic == 'ret':
                    break
            return {'requested_rva': hex(rva), 'begin_rva': hex(rva), 'end_rva': None,
                    'boundary_limit': 'No .pdata boundary; maximum256 bytes decoded from supplied RVA through first RET',
                    'instructions': rows}
        a, c, u = f
        rows = [dict(rva=hex(i.address-self.base), bytes=i.bytes.hex(), mnemonic=i.mnemonic,
                     operands=i.op_str) for i in self.md.disasm(self.data[self.off(a):self.off(a)+c-a], self.base+a)]
        return {'requested_rva': hex(rva), 'begin_rva': hex(a), 'end_rva': hex(c),
                'unwind_rva': hex(u), 'instructions': rows}

    def pointers_to(self, rva):
        needle = struct.pack('<Q', self.base + rva)
        rows = []
        off = 0
        while True:
            off = self.data.find(needle, off)
            if off < 0:
                break
            try:
                where = self.rva(off)
            except StopIteration:
                off += 1
                continue
            rows.append(hex(where))
            off += 1
        return rows

    def calls_to(self, target):
        rows = []
        _, a, size, raw = next(s for s in self.sections if s[0] == '.text')
        text_bytes = self.data[raw:raw+size]
        off = 0
        while True:
            off = text_bytes.find(b'\xe8', off)
            if off < 0 or off + 5 > size:
                break
            where = a + off
            if where + 5 + struct.unpack_from('<i', text_bytes, off+1)[0] == target:
                f = self.function(where)
                # A matching raw displacement is a candidate until included in a decoded function.
                rows.append({'candidate_call_rva': hex(where), 'container_rva': hex(f[0]) if f else None})
            off += 1
        return rows

    def refs_to(self, target):
        rows = []
        _, a, size, raw = next(s for s in self.sections if s[0] == '.text')
        data = self.data
        # Match common RIP-relative LEA/MOV encodings; complete containing decode validates each candidate.
        for prefix in (b'\x48\x8d', b'\x4c\x8d', b'\x48\x8b', b'\x4c\x8b', b'\x48\x89', b'\x4c\x89'):
            off = raw
            while True:
                off = data.find(prefix, off, raw+size-6)
                if off < 0:
                    break
                if data[off+2] & 0xc7 == 0x05:
                    where = a+off-raw
                    if where+7+struct.unpack_from('<i', data, off+3)[0] == target:
                        f = self.function(where)
                        rows.append({'candidate_reference_rva': hex(where), 'container_rva': hex(f[0]) if f else None})
                off += 1
        return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rva', action='append', default=[], type=lambda v: int(v, 0))
    ap.add_argument('--pointer', action='append', default=[], type=lambda v: int(v, 0))
    ap.add_argument('--callers', action='append', default=[], type=lambda v: int(v, 0))
    ap.add_argument('--refs', action='append', default=[], type=lambda v: int(v, 0))
    ap.add_argument('--strings', action='append', default=[])
    ap.add_argument('--qwords', action='append', default=[], type=lambda v: int(v, 0))
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()
    assert args.out.resolve().parent == HERE, 'Evidence output is confined to this fresh investigation directory'
    assert not args.out.exists(), 'Refuse overwriting evidence'
    im = Image()
    result = {'exe_path': str(EXE), 'exe_sha256': im.sha, 'image_base': hex(im.base),
              'method': 'Read file bytes only; PE sections/unwind .pdata boundaries; Capstone static decoding',
              'source_writes': 0, 'game_api_calls': 0, 'functions': [im.disasm(v) for v in args.rva],
              'pointer_references': {hex(v): im.pointers_to(v) for v in args.pointer},
              'direct_call_candidates': {hex(v): im.calls_to(v) for v in args.callers},
              'rip_reference_candidates': {hex(v): im.refs_to(v) for v in args.refs}}
    result['strings'] = {}
    for text in args.strings:
        needle = text.encode()
        rows = []
        off = 0
        while True:
            off = im.data.find(needle, off)
            if off < 0:
                break
            try:
                where = im.rva(off)
                rows.append({'rva': hex(where), 'rip_refs': im.refs_to(where), 'pointer_refs': im.pointers_to(where)})
            except StopIteration:
                pass
            off += 1
        result['strings'][text] = rows
    result['qwords'] = {}
    for rva in args.qwords:
        result['qwords'][hex(rva)] = [(hex(rva+i*8), hex(struct.unpack_from('<Q', im.data, im.off(rva)+i*8)[0])) for i in range(48)]
    args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print({k:v for k,v in result.items() if k not in ('functions', 'qwords')})
    for f in result['functions']:
        print(f"Function {f.get('begin_rva')}..{f.get('end_rva')} ({len(f.get('instructions', []))} instructions)")
        if not args.quiet:
            for i in f.get('instructions', []):
                print(f"{i['rva']}: {i['mnemonic']} {i['operands']}")
    for k,v in result['qwords'].items():
        print('Qwords', k, v)

if __name__ == '__main__':
    main()
