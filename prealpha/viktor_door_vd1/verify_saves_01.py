"""Read-only preservation check before and after the two-file installation."""
import argparse,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;C=H/'candidate_02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
a=argparse.ArgumentParser();a.add_argument('stage',choices=['before','after']);args=a.parse_args()
baseline=read(C/'save_baseline_01.json');root=Path(baseline['root'])
actual=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.rglob('*')) if p.is_file()]
assert actual==baseline['files'],'Save names or bytes changed'
manifest=read(C/'install_manifest_01.json');game=Path(manifest['game_root'])
rows=manifest['package_files']+manifest['compatibility_files']
key='before' if args.stage=='before' else 'after'
assert all(sha(game/x['path'])==x[key] for x in rows),'Managed installation drift'
result={'status':'PASS_SAVE_NAMES_AND_BYTES_UNCHANGED','stage':args.stage,'files':len(actual),'managed_files_verified':len(rows),'game_writes':0,'save_writes':0}
output=C/f'save_comparison_{args.stage}_01.json'
assert not output.exists(),'Preserve prior verification'
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
