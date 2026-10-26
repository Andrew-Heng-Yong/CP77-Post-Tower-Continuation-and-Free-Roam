from collections import Counter
from pathlib import Path
import hashlib
import json
import re

here = Path(__file__).resolve().parent
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
probe = here / 'reds_module_probe_01'
result = json.loads((probe / 'result.json').read_text(encoding='utf-8'))
assert result['status'] == 'FULL_SCC_MODULE_MERGE_PASS'
assert result['original_sources'] == 76 and result['merged_sources'] == 46

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

for row in result['rows']:
    merged = (probe / 'scripts' / row['path']).read_text(encoding='utf-8-sig')
    assert sha(probe / 'scripts' / row['path']) == row['sha256']
    for source in row['sources']:
        original = (game / source).read_text(encoding='utf-8-sig')
        if len(row['sources']) == 1:
            assert merged == original
            continue
        body = '\n'.join(line for line in original.splitlines() if not re.match(r'^(module|import)\s+', line)).strip()
        assert body in merged, source

def line_counter(path):
    counter = Counter()
    with path.open(encoding='utf-8-sig') as stream:
        for line in stream:
            normalized = re.sub(r'\$\d+', '$#', line.strip())
            if normalized:
                counter[normalized] += 1
    return counter

baseline = here.parent / 'sidejob_repair_sr1/candidate_02/compile_01/compiled.script'
merged = probe / 'compiled.script'
a, b = line_counter(baseline), line_counter(merged)
assert a == b
proof = {'status': 'PTFR_76_REDS_TO_46_MODULE_SAFE_SOURCE_AND_DECOMPILE_MULTISET_PASS', 'original_sources': 76, 'merged_sources': 46, 'decompiled_nonblank_lines': sum(a.values()), 'compiled_sha256': result['compiled_sha256'], 'game_writes': 0, 'save_writes': 0}
dest = here / 'candidate_01/test_reds_modules_01.json'
assert not dest.exists()
dest.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
