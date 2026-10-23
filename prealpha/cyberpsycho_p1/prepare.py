"""Build a bounded test-data inventory from native resources; no game writes."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'prealpha/ncpd_scanner_n1'))
from native_inspect import SafeResource,flatten
from catalog_gig_rollout_r2 import walk,value

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cat=read(ROOT/'research/cyberpsycho_p1/catalog_v1.json')
s=next(r for r in cat['rows'] if r['key']=='ma_wat_kab_08')
r=SafeResource(read(ROOT/s['source']))
paths={}
for g in flatten(r,r.obj['Data']['RootChunk']):
 for n in g['nodes']:
  for x in walk(n):
   if x.get('$type')=='gameJournalPath' and 'ma_wat_kab_08' in x['realPath']:
    paths[x['realPath']]=value(x['className'])
out=ROOT/'research/cyberpsycho_p1/test_data_v1.json'
assert not out.exists()
out.write_text(json.dumps({'key':s['key'],'paths':[{'path':p,'class':c} for p,c in sorted(paths.items())],
 'facts':['ma_kab_08_start','ma_kab_08_finished','ma_wat_kab_08_psycho_combat_started'],
 'limits':'Only a disposable branch with all 17 done and mq043 reward already claimed. Respawn/ResetKillCount is a test-only native operation, not fresh-history proof. Shard/device history may remain; replay requires live validation.'},indent=2)+'\n')
print(out)
