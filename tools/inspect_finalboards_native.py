"""Read-only PE string/xref/function inspection; outputs evidence only in workspace."""
import argparse
import bisect
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/finalboards_dismissal/tooling/python'))
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP

parser = argparse.ArgumentParser()
parser.add_argument('exe', type=Path)
parser.add_argument('--pattern', default=r'(?i)FinalBoards|Credits|PonR|PointOfNoReturn|Engagement|PressToContinue')
parser.add_argument('--functions', nargs='*', default=[])
parser.add_argument('--ranges', nargs='*', default=[], help='start:end RVA intervals of pdata functions')
parser.add_argument('--targets', nargs='*', default=[])
parser.add_argument('--data', nargs='*', default=[], help='RVA:byte-count qword ranges')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
data = args.exe.read_bytes()
pe = pefile.PE(data=data)
base = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
funcs = [(e.struct.BeginAddress, e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION]
starts = [s for s, e in funcs]
def function(rva):
    i = bisect.bisect_right(starts, rva)-1
    return funcs[i] if i >= 0 and rva < funcs[i][1] else None
strings = {}
all_strings = {}
targets = set(int(x,0) for x in args.targets)
for m in re.finditer(rb'[\x20-\x7e]{5,}\x00', data):
    s = m.group()[:-1].decode('ascii')
    try:
        rva = pe.get_rva_from_offset(m.start())
        all_strings[rva] = s
        if re.search(args.pattern, s): strings[rva] = s
    except pefile.PEFormatError: pass
xrefs = []
def fnv1a(value):
    result = 0xcbf29ce484222325
    for b in value.encode('ascii'):
        result = ((result ^ b) * 0x100000001b3) & 0xffffffffffffffff
    return result
names = {fnv1a(v):v for v in all_strings.values()}
for sec in pe.sections:
    if not sec.Characteristics & 0x20000000: continue
    raw = sec.get_data()
    # Direct RIP-relative address loads. Validate decoded instruction before accepting.
    for m in re.finditer(rb'[\x40-\x4f]?[\x8d\x8b\x89\xc7][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]', raw):
        pos = m.start()
        rva = sec.VirtualAddress+pos
        prefix = 1 if 0x40 <= raw[pos] <= 0x4f else 0
        size = prefix+6+(4 if raw[pos+prefix]==0xc7 else 0)
        if pos+size > len(raw): continue
        target = rva+size+struct.unpack_from('<i', raw, pos+prefix+2)[0]
        if target not in strings and target not in targets: continue
        ins = next(md.disasm(raw[pos:pos+size], base+rva, count=1), None)
        if ins and ins.size == size:
            f = function(rva)
            xrefs.append({'rva':hex(rva), 'function':hex(f[0]) if f else None,
                          'target':hex(target), 'string':strings.get(target,'<target>'), 'instruction':ins.mnemonic+' '+ins.op_str})
args.out.mkdir(parents=True, exist_ok=True)
call_xrefs = []
for sec in pe.sections:
    if not sec.Characteristics & 0x20000000: continue
    raw = sec.get_data()
    for m in re.finditer(rb'[\xe8\xe9]', raw):
        pos = m.start()
        if pos+5>len(raw): continue
        rva = sec.VirtualAddress+pos
        target = rva+5+struct.unpack_from('<i',raw,pos+1)[0]
        if target in targets:
            f = function(rva)
            call_xrefs.append({'rva':hex(rva),'function':hex(f[0]) if f else None,'target':hex(target)})
pointer_xrefs = []
for target in targets:
    needle = struct.pack('<Q',base+target)
    for m in re.finditer(re.escape(needle), data):
        try: pointer_xrefs.append({'rva':hex(pe.get_rva_from_offset(m.start())),'target':hex(target)})
        except pefile.PEFormatError: pass
manifest = {'exe':str(args.exe), 'sha256':hashlib.sha256(data).hexdigest(), 'image_base':hex(base),
            'strings':{hex(k):v for k,v in strings.items()}, 'direct_rip_xrefs':xrefs,'call_xrefs':call_xrefs,'pointer_xrefs':pointer_xrefs}
(args.out/'strings_xrefs.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
requested = list(args.functions)
for value in args.ranges:
    lo,hi = (int(x,0) for x in value.split(':'))
    requested.extend(hex(start) for start,end in funcs if lo<=start<hi)
for value in dict.fromkeys(requested):
    rva = int(value,0)
    f = function(rva)
    if not f:
        f = (rva, rva+160)
        print('No pdata; bounded disassembly for', value)
    start,end = f
    raw = pe.get_data(start,end-start)
    lines = [f'; RVA {start:#x}..{end:#x}; executable SHA256 {manifest["sha256"]}']
    for ins in md.disasm(raw, base+start):
        notes = []
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                trva = ins.address+ins.size+op.mem.disp-base
                notes.append(f'RVA {trva:#x}')
                if trva in all_strings: notes.append(repr(all_strings[trva]))
                else:
                    s = pe.get_data(trva,120).split(b'\x00')[0]
                    if len(s)>=4 and all(32<=b<127 for b in s): notes.append(repr(s.decode('ascii')))
            elif op.type == X86_OP_IMM and op.imm & 0xffffffffffffffff in names:
                notes.append('CName? '+repr(names[op.imm & 0xffffffffffffffff]))
        lines.append(f'{ins.address-base:08x}: {ins.mnemonic:8} {ins.op_str}' + (' ; '+', '.join(notes) if notes else ''))
    (args.out/f'function_{start:08x}.asm').write_text('\n'.join(lines),encoding='utf-8')
for value in args.data:
    addr, size = (int(x,0) for x in value.split(':'))
    lines = []
    for rva in range(addr,addr+size,8):
        blob = pe.get_data(rva,8)
        if len(blob)!=8:
            lines.append(f'{rva:08x}: not file-backed (possibly BSS)')
            continue
        q = struct.unpack('<Q',blob)[0]
        target = q-base
        note = all_strings.get(target, names.get(q,''))
        if 0 <= target < pe.OPTIONAL_HEADER.SizeOfImage:
            note = f'RVA {target:#x} '+note
        lines.append(f'{rva:08x}: {q:016x} {note}')
    (args.out/f'data_{addr:08x}.txt').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'strings':len(strings),'xrefs':len(xrefs),'output':str(args.out)}))
for x in xrefs:
    if x['string']=='<target>': print(x)
for x in call_xrefs: print(x)
for x in pointer_xrefs: print(x)
