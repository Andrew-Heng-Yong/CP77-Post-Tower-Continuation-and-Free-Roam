"""One bounded displacement search; candidates are not class identities."""
from pathlib import Path
import json, re, struct, sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from inspect_prefabs import Image
out = HERE / 'queue_candidates_03.json'
assert not out.exists()
im = Image()
_, start, size, raw = next(s for s in im.sections if s[0] == '.text')
data = im.data[raw:raw+size]
needle = struct.pack('<I', 0x2D8)
pos = 0; candidates = set(); raw_count = 0
while True:
    pos = data.find(needle, pos)
    if pos < 0: break
    raw_count += 1
    assert raw_count <= 10000
    fn = im.function(start+pos)
    if fn: candidates.add(fn[0])
    pos += 1
rows = []
for a in sorted(candidates):
    f = im.disasm(a)
    inst = f['instructions']
    fields = {v: set() for v in ('2d8', '2e8')}
    for i in inst:
        for reg, value in re.findall(r'\[(r\w+) \+ 0x(2d8|2e8)\]', i['operands']):
            if reg not in ('rsp', 'rbp'): fields[value].add(reg)
    same_lock_import = any(i['mnemonic'] == 'call' and i['bytes'].startswith('ff15') and
        int(i['rva'], 16) + 6 + struct.unpack('<i', bytes.fromhex(i['bytes'])[2:6])[0] == 0x2FF3710 for i in inst)
    if fields['2d8'] and fields['2e8'] and same_lock_import:
        rows.append(f)
assert len(rows) <= 100
result = {'exe_sha256': im.sha, 'method': 'Raw .text UInt32 displacement 0x2D8 candidates, decoded enclosing .pdata functions, retained only exact +2D8 and +2E8 operands; class/caller identity requires separate evidence.',
          'raw_occurrences': raw_count, 'candidate_functions': len(candidates), 'filter': 'Exact offsets must use registers other than RSP/RBP and call same FF15 import slot2FF3710 as queue producer; still only candidates.', 'functions': rows,
          'game_api_calls': 0, 'runtime_changes': 0}
out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print({k: v for k, v in result.items() if k != 'functions'})
for f in rows:
    print(f['begin_rva'], len(f['instructions']))
    for i in f['instructions']:
        if '0x2d8]' in i['operands'] or '0x2e8]' in i['operands']: print(i)
