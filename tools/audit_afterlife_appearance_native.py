"""Read-only, version-bound search for native Character appearance-field readers."""
import bisect
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/finalboards_dismissal/tooling/python"))
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM

exe = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe")
data = exe.read_bytes()
pe = pefile.PE(data=data)
base = pe.OPTIONAL_HEADER.ImageBase
functions = [(e.struct.BeginAddress, e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION]
starts = [a for a, b in functions]
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
rows = []
for section in pe.sections:
    if not section.Characteristics & 0x20000000:
        continue
    raw = section.get_data()
    for match in re.finditer(rb"[\x48-\x4f]\x8d.[\x04\x60][\x04\x02]\x00\x00", raw):
        pos = match.start()
        rva = section.VirtualAddress + pos
        decoded = list(md.disasm(raw[pos:pos + 35], base + rva))
        first = decoded[0]
        if first.mnemonic != "lea" or not any(o.type == X86_OP_MEM and o.mem.disp in (0x404, 0x260) for o in first.operands):
            continue
        i = bisect.bisect_right(starts, rva) - 1
        fn = functions[i][0] if i >= 0 and rva < functions[i][1] else None
        rows.append({"rva": hex(rva), "function": hex(fn) if fn is not None else None,
                     "instructions": [f"{ins.address-base:08x}: {ins.mnemonic} {ins.op_str}" for ins in decoded]})
out = ROOT / "research/afterlife_world/appearance_rules/native_field_readers.json"
out.write_text(json.dumps({"exe_sha256": hashlib.sha256(data).hexdigest(), "candidates_not_all_proven_character_reads": rows}, indent=2) + "\n")
filtered = [r for r in rows if any("0x14033fcf8" in x for x in r["instructions"])]
print(json.dumps({"candidate_count": len(rows), "distribution_bool_getter_candidates": filtered}, indent=2))
