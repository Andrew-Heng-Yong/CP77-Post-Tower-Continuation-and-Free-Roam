"""Compare fresh protection baseline before/after deployment, no game writes."""
import sys
from common import *
phase=sys.argv[1];assert phase in ['preinstall','postinstall']
base=read(CANDIDATE/'baseline_01.json');before={r['path']:r['sha256'] for r in base['files']}
after={str(p):sha(p) for p in protected_paths()}
manifest=read(CANDIDATE/'manifest.json')
expected={str(GAME/r['path']):r['sha256'] for r in manifest['files']} if phase=='postinstall' else {}
allowed={p:v for p,v in expected.items() if before.get(p)!=v}
changes=[{'path':p,'before':before.get(p),'after':after.get(p)} for p in sorted(before.keys()|after.keys()) if before.get(p)!=after.get(p)]
unexpected=[r for r in changes if r['path'] not in allowed or r['after']!=allowed[r['path']]]
assert not unexpected,unexpected
assert {r['path'] for r in changes}==set(allowed)
save_paths={str(p) for p in SAVES.rglob('*') if p.is_file()}
assert save_paths=={r['path'] for r in base['files'] if r['save']}
for r in base['files']:
    if r['save']:assert after[r['path']]==r['sha256'],r['path']
proof={'status':'PASS','phase':phase,'protected_baseline':len(before),'expected_package_changes':changes,'unaffected_files_unchanged':len(before)-len(changes),'save_files_unchanged':len(save_paths),'unexpected_changes':unexpected,'game_launched':False,'save_writes':0}
write_new(CANDIDATE/(phase+'_preservation_01.json'),proof)
print(json.dumps(proof))
