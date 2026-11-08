"""Bounded stock-record targets from source-pinned quest graph payloads."""
from pathlib import Path
import sys,gzip,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';I=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');q=read(O/'queue.json');ep=read(O/'source_epoch_00.json')
out=O/'shared/tdb_targets_01';assert not out.exists()
uses=[];pins={};limits=[]
for quest in [x for x in q['quests'] if x['batch'] in ['Q05','Q06','Q07','Q08']]:
 for d in sorted(set(quest['vanilla_candidates']+quest['restored_candidates'])):
  if d not in MI or d not in I:limits.append({'quest':quest['id'],'depot':d,'reason':'No existing decoded model; not assumed empty'});continue
  r=I[d];mp=Path(MI[d]['normalized_model']);j=Path(r['json']);raw=j.with_suffix('')
  if d in ep['source_resources']:raw=Path(ep['candidate'])/'archive_source'/d;expected=ep['source_resources'][d]
  else:
   expected=r['sha256']
   if not raw.is_file() and 'json' in j.parts:
    parts=list(j.parts);parts[parts.index('json')]='raw';raw=Path(*parts).with_suffix('')
  if not raw.is_file() or sha(raw)!=expected:limits.append({'quest':quest['id'],'depot':d,'reason':'Binary absent or hash differs from model inventory; not used'});continue
  model=read(mp) if not str(mp).endswith('.gz') else __import__('json').loads(gzip.decompress(mp.read_bytes()))
  pins[d]={'binary':str(raw),'sha256':expected,'json':str(j),'json_sha256':sha(j),'model':str(mp),'model_sha256':sha(mp),'provider':r['archive']}
  for gp,g in model.get('graphs',{}).items():
   for ni,n in g['nodes'].items():
    # Only concrete TweakDBID fields in native/effective node payloads. No
    # presumed execution or reward applicability is inferred from occurrence.
    for v in walk(n['payload']):
     if v.get('$type')=='TweakDBID':
      record=str(value(v))
      if record not in ['0','None','']:
       uses.append({'quest':quest['id'],'depot':d,'graph':gp,'node':ni,'node_type':n['type'],'record':record,'reward_node':n.get('reward',False),'source_sha256':expected})
targets=sorted({x['record'] for x in uses});write(out/'targets.json',{'status':'SOURCE_PINNED_TARGET_OCCURRENCES_NOT_EXECUTION_PROOF','targets':targets,'uses':uses,'source_pins':pins,'limits':limits,'inventory_pins':{str(A/'resource_inventory.json'):sha(A/'resource_inventory.json'),str(A/'model_inventory.json'):sha(A/'model_inventory.json')},'scope':'Existing per-quest candidate closures; not whole-game dependency exhaustion or live-effective TweakDB proof'})
print({'quests':len({x['quest'] for x in uses}),'targets':len(targets),'uses':len(uses),'binary_pins':len(pins),'input_limits':len(limits)})
