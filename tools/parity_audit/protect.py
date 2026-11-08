"""Verify protected inputs; never repair them or write outside the audit output."""
from common import *
import datetime

def verify(w,o):
 before=read(o/'protection_before.json');bad=[];verified=0
 for name,b in before['files'].items():
  p=Path(name)
  if not p.is_file():bad.append({'path':name,'kind':'MISSING'});continue
  h=sha(p)
  if h!=b['sha256']:bad.append({'path':name,'kind':'HASH_CHANGED','before':b['sha256'],'after':h})
  else:verified+=1
 prep=read(o/'prepared.json');now_game=tree_metadata(prep['game']);now_save=tree_metadata(before['save_root'])
 def delta(a,b):return [{'path':p,'before':a.get(p),'after':b.get(p)} for p in sorted(set(a)|set(b)) if a.get(p)!=b.get(p)]
 game_changes=delta(before['game_metadata'],now_game);save_changes=delta(before['save_metadata'],now_save)
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if not bad and not game_changes and not save_changes else 'CHANGES_OBSERVED','hashes_verified':verified,'hash_discrepancies':bad,'game_metadata_changes':game_changes,'save_metadata_changes':save_changes,'scope':'Full protected-file SHA256; entire game/save file names, sizes and modification times. Does not attribute external changes to the auditor; no game/save writes exist in auditor.'}
 write(o/'protection_after.json',result);print(json.dumps(result,indent=2))
