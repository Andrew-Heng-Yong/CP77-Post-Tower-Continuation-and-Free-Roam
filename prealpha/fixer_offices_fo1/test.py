"""Independent serialized-graph and negative admission checks; no live proof."""
import copy, json, sys, binascii
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from test_rite_g2 import SafeResource
from test_gig_pilot_r1 import reachable
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read, sha, walk

SPECS={
 'wakako':({0,17,19,20,52,53,54,55,59},52,['#wakako_okada_default']),
 'dakota':({53,64},53,[]), 'dyno':({40,50,48},40,[]),
 'el_capitan':({52,59},52,['#muamar_reyes_default']),
 'padre':({55,56},55,['#padre_default_prefab']),
 'reggie':({88,128,98},88,['#pr_reggie_default']),
 'mr_hands':(set(),0,[])}
GUARD={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,
 'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,
 'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,
 'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,
 'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0}

def graph_map(r): return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g): return {n['id']:n for n in g['nodes']}
def edges(g): return {tuple(e) for e in g['edges']}
def predicates(condition):
 assert condition['$type']=='questLogicalCondition' and condition['operation']=='AND'
 out=[]
 for c in condition['conditions']:
  assert c['$type']=='questFactsDBCondition'
  t=c['type'];assert t['$type']=='questVarComparison_ConditionType'
  out.append((t['factName'],t['comparisonType'],t['value']))
 return out
def accepts(preds,state):
 return all(state.get(k,0)==v if op=='Equal' else state.get(k,0)>v for k,op,v in preds)

def verify(build):
 m=read(build/'build.json');assert m['status']=='BUILT_FO1_LIVE_PENDING'
 assert m['packed_readback'] and m['native_scenes_unchanged']
 assert not m['official_overrides'] and m['runtime_scripts_added']==0
 assert [f['relative'] for f in m['files']]==['archive/pc/mod/TowerContinued_FixerOffices_FO1.archive','archive/pc/mod/TowerContinued_FixerOffices_FO1.archive.xl']
 for f in m['files']: assert sha(build/Path(f['relative']).name)==f['sha256']
 for p,h in m['source_pins'].items(): assert sha(ROOT/p)==h,p
 assert set(m['resources'])=={f'towercontinued\\fixer_offices_fo1\\{k}.questphase' for k in SPECS}
 assert {o['key'] for o in m['offices']}==set(SPECS)
 checks=[];native_nodes=0;negative_cases=0
 for row in m['offices']:
  key=row['key'];ids,entry,prefabs=SPECS[key]
  assert set(row['selected_nodes'])==ids and row['entry']==entry and row['prefabs']==prefabs
  nr=SafeResource(read(ROOT/(row['source'].replace('/raw/','/json/')+'.json')))
  pr=SafeResource(read(build/f'readback/{key}.json'))
  old=graph_map(nr);new=graph_map(pr);root=pr.obj['Data']['RootChunk']
  assert root['phasePrefabs']==[] and root['inplacePhases']==[]
  assert not pr.obj['Data']['EmbeddedFiles']
  pn=nodes(new['root']);assert set(pn)=={0,1,2,3,4,100}
  assert edges(new['root'])=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',100,'In1')}
  tag='PTFRFO1_'+key
  for ident,suffix in [(1,'Ready'),(4,'Issued')]:
   assert pn[ident]['type']=={'$type':'questSetVar_NodeType','factName':tag+'_'+suffix,'setExactValue':1,'value':1}
  eq=GUARD|{tag+'_Issued':0}
  positive=[key+'_default_on']+(['mr_hands_default_ep1'] if key=='mr_hands' else [])
  expected=[(k,'Equal',v) for k,v in eq.items()]+[(k,'Greater',0) for k in positive]
  for i in (2,3): assert sorted(predicates(pn[i]['condition']))==sorted(expected)
  assert pn[2]['$type']=='questPauseConditionNodeDefinition' and pn[3]['$type']=='questConditionNodeDefinition'
  good=eq|{k:1 for k in positive};assert accepts(expected,good)
  for fact,op,val in expected:
   bad=good|{fact:(1-val if op=='Equal' else 0)}
   assert not accepts(expected,bad),(key,fact);negative_cases+=1
  # Reload must not re-admit an already issued owner; it stays serialized.
  assert not accepts(expected,good|{tag+'_Issued':1})
  assert [p['prefabNodeRef']['$value'] for p in pn[100]['phaseInstancePrefabs']]==prefabs
  assert pn[100]['saveLock']==0
  if key=='mr_hands':
   assert set(new)=={'root'}
   assert pn[100]['phaseResource']['DepotPath']['$value']==r'ep1\openworld\fixers\mr_hands\phases\mr_hands_combat_zone_default.questphase'
  else:
   on=nodes(old['root']);sn=nodes(new['root/100'])
   assert set(sn)==ids|{0}
   for i in ids: assert sn[i]==on[i],(key,i,'payload');native_nodes+=1
   want={e for e in edges(old['root']) if e[0] in ids and e[2] in ids}
   want.add((19,'Out',20,'In') if key=='wakako' else (0,'Out',entry,'In1'))
   assert edges(new['root/100'])==want,(key,'slice edges')
   assert ids<=reachable(want,0),(key,'unreachable selected node')
   selected={p for p in old if p!='root' and int(p.split('/')[1]) in ids}
   assert set(new)=={'root','root/100'}|{p.replace('root','root/100',1) for p in selected}
   for p in selected:
    ng=new[p.replace('root','root/100',1)]
    assert nodes(old[p])==nodes(ng),(key,p,'nested payload')
    assert edges(old[p])==edges(ng),(key,p,'nested edges')
    native_nodes+=len(ng['nodes'])
   # No copied graph can force availability, payout, completion, or district credit.
   setters=[v for g in new.values() for n in g['nodes'] for v in walk(n) if v.get('$type')=='questSetVar_NodeType']
   for v in setters:
    assert not any(s in v['factName'] for s in ('_achievement','_sts_counter','ow_psychos_','mq043_'))
    assert v['factName'] not in positive
   assert all(v.get('$type')!='questGiveReward_NodeType' for g in new.values() for n in g['nodes'] for v in walk(n))
  raw=build/'source'/Path(row['depot'].replace('\\','/'))
  assert sha(raw)==m['resources'][row['depot']]
  assert binascii.crc_hqx((row['depot']+':1').encode(),0xffff)==row['injection_id']
  checks.append({'office':key,'native_slice':True,'gated_prefabs':True,'no_forced_default':True})
 ids=[r['injection_id'] for r in m['offices']];assert len(set(ids))==7
 assert not set(ids)&{i['id'] for i in m['installed_injections']}
 stock=read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')
 assert not set(ids)&{n['Data']['id'] for n in stock['Data']['RootChunk']['graph']['Data']['nodes']}
 xl=(build/'TowerContinued_FixerOffices_FO1.archive.xl').read_text()
 assert xl.count('    - path: ')==7 and xl.count('      parent: ep1\\quest\\ep1.quest')==7
 assert xl.count('        node: [1]')==7 and xl.count('        socket: Out')==7
 for r in m['offices']: assert xl.count('    - path: '+r['depot']+'\n')==1
 # Preserve Regina's original repeat-payment guard, rather than clearing it.
 rr=SafeResource(read(ROOT/'research/fixer_offices_fo1/scenes/json/base/open_world/fixers/reggie/scenes/reggie_default.scene.json'))
 conditions=[rr.payload(v) for v in walk(rr.obj) if v.get('$type')=='questVarComparison_ConditionType' and v.get('factName')=='ow_psychos_reward_collected']
 assert any(c['comparisonType']=='GreaterOrEqual' and c['value']==1 for c in conditions)
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),
         'native_nodes_exact':native_nodes,'negative_admission_cases':negative_cases,'offices':checks,
         'scope':'Native conversation/default-owner branches only. Prompts, native scene execution, repeat visits and save/reload require playtest.'}

if __name__=='__main__':
 build=ROOT/'prealpha/fixer_offices_fo1/build'/sys.argv[1]
 out=build/'tests.json';assert not out.exists(),'Pinned result already exists'
 result=verify(build);out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
