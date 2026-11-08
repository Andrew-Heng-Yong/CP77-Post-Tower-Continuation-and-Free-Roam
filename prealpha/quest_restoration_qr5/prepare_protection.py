"""Protect predecessor evidence plus game/save inputs without creating a build."""
from pathlib import Path
import sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr4'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,snapshot,tree_metadata
assert not (O/'protection_before.json').exists()
old=read(P/'protection_before.json');evidence=read(P/'EVIDENCE.json')
assert all(sha(P/name)==r['sha256'] for name,r in evidence['artifacts'].items()),'Predecessor evidence drift'
files=[Path(p) for p in old['files']]+[p for p in P.rglob('*') if p.is_file()];pins=snapshot(files)
assert all(pins[p]['sha256']==r['sha256'] for p,r in old['files'].items()),'Protected predecessor/game input changed'
prep=read(P/'prepared.json');game=prep['game']
write(O/'prepared.json',{'game':game,'predecessor':str(P),'working_source':str(P/'candidate_01'),'installed':'PH3 unchanged','scope':'Q05-Q07primary,Q08stretch; justifiedrepairs only, no deploy'})
write(O/'protection_before.json',{'files':pins,'game_metadata':tree_metadata(game),'save_root':old['save_root'],'save_metadata':tree_metadata(old['save_root'])})
write(O/'protection_start.json',{'status':'PASS_PREDECESSOR_AND_PROTECTION_PINNING','protected_hashes':len(pins),'QR4_artifact_hashes_verified':len(evidence['artifacts']),'game_and_save_writes':0})
print({'status':'PASS_PROTECTION_SNAPSHOT','protected':len(pins),'predecessor_artifacts':len(evidence['artifacts'])})
