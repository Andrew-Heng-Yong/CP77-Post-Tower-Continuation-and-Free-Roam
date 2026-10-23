"""Current native diner/Johnny community identity evidence, no world mutation."""
import json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
HERE=ROOT/'research/sidejobs_s28/encounters'
def canonical(o):
 if isinstance(o,list):return [canonical(x) for x in o]
 if not isinstance(o,dict):return o
 if o.get('$type')=='TweakDBID':
  s=o.get('$value');h=o.get('hash')
  if h is None:h=(zlib.crc32(s.encode())|(len(s.encode())<<32)) if o['$storage']=='string' else int(s)
  return {'$type':'TweakDBID','hash':h}
 return {k:canonical(v) for k,v in o.items() if k!='HandleId'}
def main():
 out=HERE/'world_support_01.json';assert not out.exists()
 current='research/sidejobs_s28/vehicles/world_03/json/ep1_1_nightcity_always_loaded_1.streamingsector.json';raw=current.replace('/json/','/raw/').removesuffix('.json');inv='research/sidejobs_s28/vehicles/world_03/inventory.json';audit='research/sidejobs_s28/encounters/current_donors_01/report.json';oldnodes='research/sidejobs_s28/review/world_diner_nodes_01.json';oldregistry='research/sidejobs_s28/review/world_diner_registry_01.json'
 pins={p:sha(ROOT/p) for p in [current,raw,inv,audit,oldnodes,oldregistry,str(Path(__file__).relative_to(ROOT)).replace('\\','/')]};checks=[]
 def check(ok,why):assert ok,why;checks.append(why)
 r=next(r for r in read(ROOT/inv)['rows'] if r['raw']==raw);a=next(r for r in read(ROOT/audit)['rows'] if r['depot']==r_depot and r['archive'].lower()==r_archive.lower()) if False else next(x for x in read(ROOT/audit)['rows'] if x['depot']==r['depot'] and x['archive'].lower()==r['archive'].lower())
 check(r['raw_sha256']==pins[raw] and r['json_sha256']==pins[current] and a['exact'] and a['current_sha256']==pins[raw],'current official archive binds exact world raw/json source')
 d=read(ROOT/current);registry={};nodes={};ids={'3592017345110379073','1788738451982074994','10707106092698157394'}
 for x in walk(d):
  if x.get('$type')=='worldCommunityRegistryItem':
   ident=x['communityId']['entityId']['hash']
   if ident in ids:check(ident not in registry,['unique registry',ident]);registry[ident]=x
  elif x.get('$type')=='worldCompiledCommunityAreaNode' and x.get('sourceObjectId',{}).get('hash') in ids:
   ident=x['sourceObjectId']['hash'];check(ident not in nodes,['unique compiled community',ident]);nodes[ident]=x
 check(set(registry)==ids,'diner barman/patrons and global Johnny registry all found')
 for old in read(ROOT/oldregistry):
  ident=old['communityId']['entityId']['hash'];check(canonical(old)==canonical(registry[ident]),['historical diner registry payload equals current',ident])
 for old in read(ROOT/oldnodes)['nodes']:
  old=old['Data'];ident=old['sourceObjectId']['hash'];check(canonical(old)==canonical(nodes[ident]),['historical diner compiled area payload equals current',ident])
 def entries(ident):return {value(x['entryName']):value(x['characterRecordId']) for x in walk(registry[ident]) if x.get('$type')=='communitySpawnEntry'}
 barman=entries('3592017345110379073');patrons=entries('1788738451982074994');johnny=entries('10707106092698157394')
 check(set(barman)=={'barman'},'separate default service owns quest barman');check('barman' not in patrons and len(patrons)==6,'quest community contains only six patrons');check(johnny=={'johnny':'Character.Silverhand'},'current global Johnny is exact JV1 Silverhand record')
 result={'status':'PASS_CURRENT_ENCOUNTER_COMMUNITY_IDENTITY_AND_DINER_EQUIVALENCE','checks':len(checks),'assertions':checks,'source_pins':pins,'depot':r['depot'],'archive':r['archive'],'raw_sha256':pins[raw],'barman':barman,'patrons':patrons,'johnny':johnny,'current_registry':registry,'current_compiled_areas':nodes,'limits':['Current native source identity and scope proven; no save-specific actor liveness or gameplay claimed.','Exact prior diner payloads remain valid after2.5; this does not dispatch or duplicate them.']}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(checks),'sha256':sha(out)}))
if __name__=='__main__':main()
