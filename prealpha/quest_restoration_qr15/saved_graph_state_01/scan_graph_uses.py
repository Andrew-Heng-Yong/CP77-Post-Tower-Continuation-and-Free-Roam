"""Static candidate search for QuestContext's FactManager access at+0x138.

This searches file bytes, decodes only containing .pdata functions, and emits
matches. Matches are candidates until register data flow is manually reviewed.
"""
from pathlib import Path
import json
from inspect_native import Image, HERE

def main():
    out = HERE / 'native_graph_uses_01.json'
    assert not out.exists()
    im = Image()
    _, start, size, raw = next(s for s in im.sections if s[0] == '.text')
    off, candidates = raw, set()
    while True:
        off = im.data.find(b'\x38\x01\x00\x00', off, raw + size)
        if off < 0:
            break
        func = im.function(start+off-raw)
        if func:
            candidates.add(func[0])
        off += 1
    matched = []
    for rva in sorted(candidates):
        f = im.disasm(rva)
        rows = f['instructions']
        if any(r['mnemonic'] == 'mov' and 'qword ptr' in r['operands'] and '+ 0x138]' in r['operands'] for r in rows):
            if any(r['mnemonic'] in ('call', 'jmp') and ('+ 0x10]' in r['operands'] or '+ 0x18]' in r['operands']) for r in rows):
                matched.append(f)
    result = {'exe_sha256': im.sha, 'method': 'Read-only .text byte search for displacement0x138, containing .pdata decode, filter pointer loads and virtualslot10/18; candidate dataflow only',
              'candidate_functions': len(candidates), 'matching_functions': len(matched), 'functions': matched,
              'game_api_calls': 0, 'source_writes': 0}
    out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print({k:v for k,v in result.items() if k != 'functions'})
    for f in matched:
        print('\nFunction', f['begin_rva'], f['end_rva'])
        rows=f['instructions']; chosen=set()
        for i,r in enumerate(rows):
            if r['mnemonic'] in ('call','jmp') and ('+ 0x10]' in r['operands'] or '+ 0x18]' in r['operands']):
                chosen.update(range(max(0,i-14), min(len(rows),i+5)))
        for i in sorted(chosen):
            r=rows[i];print(r['rva'],r['mnemonic'],r['operands'])

if __name__ == '__main__':
    main()
