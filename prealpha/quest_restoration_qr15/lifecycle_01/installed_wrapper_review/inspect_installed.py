"""Read-only installed Codeware PE metadata and targeted static disassembly."""
from pathlib import Path
import argparse, bisect, hashlib, json, struct, sys, uuid
HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[3]
sys.path.insert(0, str(WORKSPACE / 'research/finalboards_dismissal/tooling/python'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
DLL = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\red4ext\plugins\Codeware\Codeware.dll')
EXPECTED = '808D8BCE11641073091DDA33830D06AB98BD9AC710A9A47ECD7EC56E6193440C'

class Image:
    def __init__(self):
        self.data = DLL.read_bytes(); self.sha = hashlib.sha256(self.data).hexdigest().upper()
        assert self.sha == EXPECTED
        pe = struct.unpack_from('<I', self.data, 60)[0]; self.op = op = pe+24
        assert struct.unpack_from('<H', self.data, op)[0] == 0x20B
        self.base = struct.unpack_from('<Q', self.data, op+24)[0]
        sh = op+struct.unpack_from('<H', self.data, pe+20)[0]
        self.sections = []
        for n in range(struct.unpack_from('<H', self.data, pe+6)[0]):
            at = sh+n*40
            vs, a, size, raw = struct.unpack_from('<IIII', self.data, at+8)
            self.sections.append((self.data[at:at+8].rstrip(b'\0').decode(), a, size, raw))
        _, a, size, raw = next(s for s in self.sections if s[0] == '.pdata')
        self.functions = sorted((x, y, z) for x, y, z in struct.iter_unpack('<III', self.data[raw:raw+size-size%12]) if x and y>x)
        self.starts = [f[0] for f in self.functions]; self.md = Cs(CS_ARCH_X86, CS_MODE_64)
    def off(self, a): return next(raw+a-x for _, x, size, raw in self.sections if x<=a<x+size)
    def rva(self, a): return next(x+a-raw for _, x, size, raw in self.sections if raw<=a<raw+size)
    def function(self, a):
        n = bisect.bisect_right(self.starts, a)-1
        return self.functions[n] if n>=0 and self.functions[n][0]<=a<self.functions[n][1] else None
    def disasm(self, a, end=None):
        f = self.function(a)
        if end is not None: start, limit, mode = a, end, 'Explicit bounded span; no function boundary claim'
        elif f: start, limit, mode = f[0], f[1], 'PE .pdata extent'
        else: start, limit, mode = a, a+256, 'No .pdata: at most256 bytes through first RET; branch continuations require separate spans'
        rows = []
        for i in self.md.disasm(self.data[self.off(start):self.off(start)+limit-start], self.base+start):
            rows.append({'rva': hex(i.address-self.base), 'bytes': i.bytes.hex(), 'mnemonic': i.mnemonic, 'operands': i.op_str})
            if not f and end is None and i.mnemonic == 'ret': break
        return {'requested_rva': hex(a), 'begin_rva': hex(start), 'end_rva': hex(limit) if f or end else None, 'extent': mode, 'instructions': rows}
    def refs(self, target):
        rows = []
        _, a, size, raw = next(s for s in self.sections if s[0] == '.text')
        data = self.data[raw:raw+size]
        for n in range(len(data)-7):
            if data[n] in (0x48, 0x4C) and data[n+1] in (0x8D, 0x8B, 0x89) and data[n+2]&0xC7==5:
                address = a+n
                if address+7+struct.unpack_from('<i', data, n+3)[0] == target:
                    f = self.function(address)
                    rows.append({'candidate_rva': hex(address), 'container_rva': hex(f[0]) if f else None})
        return rows
    def strings(self, value):
        rows = []; pos = 0
        while True:
            pos = self.data.find(value.encode(), pos)
            if pos<0: break
            try:
                a = self.rva(pos); rows.append({'rva': hex(a), 'refs': self.refs(a)})
            except StopIteration: pass
            pos += 1
        return rows
    def codeview(self):
        a, size = struct.unpack_from('<II', self.data, self.op+112+6*8)
        rows = []
        for n in range(size//28):
            v = struct.unpack_from('<IIHHIIII', self.data, self.off(a)+n*28)
            if v[4] == 2:
                data = self.data[v[7]:v[7]+v[5]]
                assert data[:4] == b'RSDS'
                path = data[24:].split(b'\0')[0].decode(errors='replace')
                rows.append({'debug_entry_rva': hex(a+n*28), 'signature': 'RSDS',
                    'guid': str(uuid.UUID(bytes_le=data[4:20])).upper(), 'age': struct.unpack_from('<I', data, 20)[0],
                    'pdb_path': path, 'pdb_path_exists': Path(path).is_file()})
        return rows

def main():
    ap = argparse.ArgumentParser()
    for name in ('rva', 'refs', 'qwords', 'pointer', 'callers'):
        ap.add_argument('--'+name, action='append', default=[], type=lambda v:int(v,0))
    ap.add_argument('--strings', action='append', default=[])
    ap.add_argument('--span', action='append', default=[])
    ap.add_argument('--out', type=Path, required=True); ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args(); assert args.out.resolve().parent == HERE and not args.out.exists()
    im = Image()
    result = {'dll_path': str(DLL), 'dll_sha256': im.sha, 'bytes': len(im.data), 'image_base': hex(im.base),
        'method': 'Static file bytes only; never loads DLL, calls game/framework code or accesses any process',
        'codeview': im.codeview(), 'strings': {v:im.strings(v) for v in args.strings},
        'rip_ref_candidates': {hex(v):im.refs(v) for v in args.refs},
        'qwords': {hex(v):[(hex(v+8*n),hex(struct.unpack_from('<Q', im.data, im.off(v)+n*8)[0])) for n in range(32)] for v in args.qwords},
        'functions': [im.disasm(v) for v in args.rva], 'pointer_refs': {}, 'direct_call_candidates': {}, 'explicit_spans': [], 'game_api_calls': 0, 'runtime_changes': 0}
    for target in args.callers:
        _, start, size, raw=next(v for v in im.sections if v[0]=='.text'); data=im.data[raw:raw+size]
        addresses=[]; pos=0
        while True:
            pos=data.find(b'\xe8',pos)
            if pos<0 or pos+5>len(data): break
            a=start+pos
            if a+5+struct.unpack_from('<i',data,pos+1)[0]==target:
                f=im.function(a)
                addresses.append({'candidate_rva':hex(a),'container_rva':hex(f[0]) if f else None})
            pos+=1
        result['direct_call_candidates'][hex(target)]=addresses
    for target in args.pointer:
        addresses=[]; pos=0; needle=struct.pack('<Q', im.base+target)
        while True:
            pos=im.data.find(needle,pos)
            if pos<0: break
            try: addresses.append(hex(im.rva(pos)))
            except StopIteration: pass
            pos+=1
        result['pointer_refs'][hex(target)] = addresses
    for value in args.span:
        a, end = (int(v,0) for v in value.split(':')); assert 0<end-a<=8192
        result['explicit_spans'].append(im.disasm(a,end))
    args.out.write_text(json.dumps(result, indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('functions', 'explicit_spans')},indent=2))
    for f in result['functions']+result['explicit_spans']:
        print(f['begin_rva'],f['end_rva'],len(f['instructions']))
        if not args.quiet:
            for i in f['instructions']: print(i['rva'],i['mnemonic'],i['operands'])

if __name__=='__main__': main()
