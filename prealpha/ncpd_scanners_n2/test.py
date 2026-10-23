"""Independent N2 binary-readback/source parity and no-replay checks."""
import binascii,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'prealpha/ncpd_scanner_n1'))
from native_inspect import SafeResource,flatten
from catalog_gig_rollout_r2 import read,sha,walk,value
COMMON={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'PTFRN1_Support_Issued':1}
PILOTS={'ma_wat_lch_01','ma_wat_lch_02','ma_wat_lch_03'}
SPECIAL={'ma_cct_cpz_16','ma_wbr_nok_05'}
def load(p):
 r=SafeResource(read(p));return r,{g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def predicate(c):
 assert c['$type']=='questLogicalCondition' and c['operation']=='AND'
 result={}
 for h in c['conditions']:
  assert h['$type']=='questFactsDBCondition';t=h['type'];assert t['$type']=='questVarComparison_ConditionType' and t['comparisonType']=='Equal'
  assert t['factName'] not in result;result[t['factName']]=t['value']
 return result
def setter(n,f):assert n['type']=={'$type':'questSetVar_NodeType','factName':f,'setExactValue':1,'value':1}
def verify(build):
 m=read(build/'build.json');cat=read(ROOT/'research/ncpd_scanners_n2/catalog_v2.json');catalog={r['key']:r for r in cat['rows']}
 assert m['status']=='BUILT_N2_LIVE_PENDING' and len(catalog)==157 and len(m['activities'])==154
 assert m['packed_readback'] and m['native_scenes_unchanged'] and not m['official_overrides'] and not m['mod_override']
 assert m['runtime_scripts_added']==1 and m['game_writes']==m['save_writes']==0
 assert {r['key'] for r in m['activities']}==catalog.keys()-PILOTS
 assert set(m['pilots_preserved'])==PILOTS
 assert {r['id'] for r in m['unwired_journal_entries']}=={'ma_wat_kab_04','ma_wat_kab_11','ma_wat_kab_14','ma_wbr_hil_05_01'}
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 for p,h in m['resources'].items():assert sha(build/'source'/Path(p.replace('\\','/')))==h
 assert set(m['resources'])==set(m['boots']) and len(m['boots'])==154
 exact=negative=0;result=[];parents={}
 for row in m['activities']:
  key=row['key'];c=catalog[key];tag='PTFRN2_'+key
  if c['parent'] not in parents:parents[c['parent']]=load(ROOT/c['parent'])
  _,pg=parents[c['parent']];pn=nodes(pg['root']);pe=edges(pg['root']);ids=set(row['selected_nodes'])
  r,gs=load(build/f'readback/{key}.json');outer=nodes(gs['root']);g=gs['root/100'];n=nodes(g);e=edges(g)
  assert r.obj['Data']['RootChunk']['phasePrefabs']==[] and r.obj['Data']['RootChunk']['inplacePhases']==[] and not r.obj['Data']['EmbeddedFiles']
  assert set(outer)==({0,1,2,100,9} if c['extra_parent_gate'] else {0,1,2,100})
  assert set(n)==ids|({1000,1001,1002,1003,1004,1005} if key in SPECIAL else {1000,1001,1002})
  for i in ids:assert n[i]==pn[i],(key,i,'native payload');exact+=1
  nested={k for k in pg if k!='root' and int(k.split('/')[1]) in ids}
  assert set(gs)=={'root','root/100'}|{'root/100'+k[4:] for k in nested}
  for k in nested:
   copied=gs['root/100'+k[4:]]
   assert nodes(copied)==nodes(pg[k]) and edges(copied)==edges(pg[k]),(key,k)
   exact+=len(pg[k]['nodes'])
  # Every retained original edge is kept except the one initial admission
  # edge. This includes all outputs, inline cleanup and Kabuki's reset loop.
  ad=tuple(row['admission_edge']);assert ad in pe
  expected={x for x in pe if x[0] in ids and x[2] in ids}-{ad}
  expected|={(1000,'True',1001,'In'),(1000,'False',1002,'In'),(1001,'Out',ad[2],ad[3])}
  if key in SPECIAL:
   expected|={(ad[0],ad[1],1003,'In'),(1003,'Out',1004,'In'),(1004,'Out',1005,'In'),(1005,'True',1000,'In'),(1005,'False',1002,'In')}
   setter(n[1003],tag+'_Request');assert n[1004]['condition']['operation']=='OR'
   assert {h['type']['factName'] for h in n[1004]['condition']['conditions']}=={tag+'_Permit',tag+'_Denied'}
   assert n[1005]['condition']['type']['factName']==tag+'_Permit' and n[1005]['condition']['type']['value']==1
  else:expected.add((ad[0],ad[1],1000,'In'))
  assert e==expected,(key,'edge delta')
  assert {x for x in pe if x[0]==c['child']}=={x for x in e if x[0]==c['child']},(key,'native outputs')
  assert not any(x[3]=='CutDestination' and x[2] in ids and x[0] not in ids for x in pe),(key,'lost external cut')
  guard=COMMON|{tag+'_Issued':0}|{f:0 for f in c['start_facts']+c['finish_facts']}
  if key in ('ma_wat_lch_14','ma_wat_lch_15'):
   guard.pop('ma_wat_lch_14_finished')
   own=[w for w in c['writes'] if w['factName']==key+'_start']
   assert len(own)==1 and own[0]['setExactValue']==0 and own[0]['value']==1
  guard|={w['factName']:0 for w in c['writes'] if w['factName'].endswith('_av_start_only') and w['value']>0}
  assert row['guard_equal']==guard and predicate(outer[2]['condition'])==predicate(n[1000]['condition'])==guard
  setter(outer[1],tag+'_Ready');setter(n[1001],tag+'_Issued');setter(n[1002],tag+'_Refused')
  want={(0,'Out',1,'In'),(1,'Out',2,'In')}
  if c['extra_parent_gate']:
   _,bg=load(ROOT/'research/ncpd_scanner_n1/parents_02/json/base/open_world/minor_activities/badlands/badlands_minor_activities.questphase.json')
   assert outer[9]==nodes(bg['root'])[9];exact+=1;want|={(2,'Out',9,'In'),(9,'Out',100,row['input'])}
  else:want.add((2,'Out',100,row['input']))
  assert edges(gs['root'])==want and value(n[c['input']]['socketName'])==row['input']
  if c['native_depot'] not in (None,0,'0'):
   assert value(n[c['child']]['phaseResource']['DepotPath'])==c['native_depot']
  assert not any(d.startswith('base\\') or d.startswith('ep1\\') for d in m['resources'])
  admits=lambda facts:all(facts.get(k,0)==v for k,v in guard.items())
  assert admits(guard)
  for k,v in guard.items():assert not admits(guard|{k:1-v});negative+=1
  assert not admits(guard|{tag+'_Issued':1}) and not any(x[0]==1002 for x in e)
  result.append({'key':key,'native_nodes':len(ids),'saved_poi_guard':key in SPECIAL,'outputs':c['outputs']})
 # Independent CRC implementation and all installed/root identities.
 ids=[binascii.crc_hqx((d+':1').encode(),0xffff) for d in m['boots']]
 ep=read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')
 occupied={x['id'] for x in m['installed_injections']}|{n['Data']['id'] for n in ep['Data']['RootChunk']['graph']['Data']['nodes']}
 assert len(set(ids))==154 and not set(ids)&occupied
 assert dict(zip(m['boots'],ids))=={r['depot']:r['injection_id'] for r in m['activities']}
 xl=(build/'TowerContinued_NCPD_N2.archive.xl').read_text();assert xl.count('    - path: ')==xl.count('      parent: ep1\\quest\\ep1.quest')==154
 # Audit all referenced dispatcher scenes; no Johnny, romance or civilian
 # scene cast is silently accepted merely because the filename says scanner.
 casts={}
 for p in (ROOT/'research/ncpd_scanners_n2/scenes_01/json').rglob('*.json'):
  actors=read(p)['Data']['RootChunk']['actors'];names=[a['actorName'] for a in actors]
  assert len(actors)==1 and actors[0]['acquisitionPlan']=='spawnSet'
  assert value(actors[0]['spawnSetParams']['entryName'])=='ncpd_dispatcher_holo'
  assert value(actors[0]['spawnSetParams']['reference'])=='#ncpd_dispatcher_holo'
  casts[str(p.relative_to(ROOT))]=names
 assert len(casts)==17
 script=(build/'ScannerAdmissionN2.reds').read_text()
 assert script==(ROOT/'prealpha/ncpd_scanners_n2/ScannerAdmissionN2.reds').read_text()
 assert 'ModLog' not in script and 'LogChannel' not in script and 'RegisterMappin' not in script
 assert script.count('.SetFactStr(')==1 and 'tag+(fresh ? "_Permit" : "_Denied")' in script
 assert 'return found && (Equals(phase,gamedataMappinPhase.DefaultPhase) || Equals(phase,gamedataMappinPhase.UndiscoveredPhase));' in script
 assert 'if phase<0 { return; }' in script and 'epoch!=this.epoch' in script
 assert 'this.Fact(tag+"_Permit")!=0 || this.Fact(tag+"_Denied")!=0' in script
 # Model the actual request -> saved-state response -> graph gates -> issue
 # handshake. Duplicate callbacks and restoring an issued owner cannot restart.
 def step(state,phase,found=True,tower=True,epoch=True):
  s=dict(state)
  if not tower or not epoch or s.get('request')!=1 or s.get('issued',0)!=0 or s.get('permit',0)!=0 or s.get('denied',0)!=0:return s
  if not found or phase<0:return s
  s['permit' if phase in (1,3) else 'denied']=1
  return s
 for phase in range(0,7):
  for found in (False,True):
   r=step({'request':1},phase,found)
   assert bool(r.get('permit'))==(found and phase in (1,3))
   assert bool(r.get('denied'))==(found and phase not in (1,3));negative+=1
 for state in ({'request':0},{'request':1,'issued':1},{'request':1,'permit':1},{'request':1,'denied':1}):
  assert step(state,3)==state;negative+=1
 for kwargs in ({'tower':False},{'epoch':False},{'found':False}):assert step({'request':1},3,**kwargs)=={'request':1};negative+=1
 assert step({'request':1},-1)=={'request':1};negative+=1
 permit=step({'request':1},3);assert step(permit,0)==permit;negative+=1
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'native_nodes_exact':exact,'negative_admission_cases':negative,'activities':result,'scene_casts':casts,'total_stock_connected':157,'added':154,'pilot_owners_untouched':3,'limits':'Source/binary/compile tests are not playtest proof. Saved-POI API availability for two factless owners still needs live validation; unknown means defer, never replay.'}
if __name__=='__main__':
 build=ROOT/'prealpha/ncpd_scanners_n2/build'/sys.argv[1];dest=build/'tests.json';assert not dest.exists()
 report=verify(build);dest.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('activities','scene_casts')},indent=2))
