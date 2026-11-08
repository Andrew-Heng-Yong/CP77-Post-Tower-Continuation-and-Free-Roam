"""Pin this session's existing external state; distinguish drift since QR5."""
from pathlib import Path
import sys,datetime,concurrent.futures
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,tree_metadata
assert not (O/'protection_before.json').exists()
old=read(P/'protection_before.json'); game=Path(read(P/'prepared.json')['game']); save=Path(old['save_root'])
files=sorted(set([Path(p) for p in old['files']]+[p for p in P.rglob('*') if p.is_file()]))
def pin(p):
 if not p.is_file() or p.is_symlink():return str(p),None
 s=p.stat();return str(p),{'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)}
pins={}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i,(p,v) in enumerate(pool.map(pin,files),1):
  if v:pins[p]=v
  if i%1000==0:print('Pinned',i,'of',len(files),flush=True)
drift=[{'path':p,'QR5':v,'QR6_start':pins.get(p)} for p,v in old['files'].items() if p not in pins or pins[p]['sha256']!=v['sha256']]
external=[x for x in drift if Path(x['path']).is_relative_to(game) or Path(x['path']).is_relative_to(save)]
assert len(external)==len(drift),'Immutable workspace predecessor drift: '+str([x['path'] for x in drift if x not in external])
write(O/'external_drift_since_QR5.json',{'status':'EXISTING_EXTERNAL_STATE_CHANGED_SINCE_PREVIOUS_SESSION_PIN_CURRENT_STATE','detected_before_any_QR6_runtime_or_save_write':True,'changes':drift,'interpretation':'Historical QR5 snapshot is not the current user save/cache state; preserve current bytes. No evidence of QR6 runtime or save writes. Initial capture stopped on strict historical equality; this fresh capture explicitly distinguishes external state from pinned candidate/evidence.','source_unchanged_sentinel':str(O/'sentinel.json')})
write(O/'prepared.json',{'game':str(game),'save_root':str(save),'candidate':read(O/'source_epoch_00.json')['candidate'],'scope':'33 remaining deep quests and source-confirmed safe repairs only; no deploy'})
write(O/'protection_before.json',{'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'game_metadata':tree_metadata(game),'save_root':str(save),'save_metadata':tree_metadata(save)})
write(O/'protection_start.json',{'status':'PASS_CURRENT_SESSION_PROTECTION_PINNING','protected_hashes':len(pins),'preexisting_external_drift':len(drift),'game_and_save_writes':0})
print({'status':'PASS_CURRENT_PROTECTION','protected_hashes':len(pins),'external_changes_since_QR5':len(drift)},flush=True)
