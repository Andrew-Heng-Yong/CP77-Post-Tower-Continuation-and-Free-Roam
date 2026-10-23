"""Independent graph, preservation, admission and native dependency checks."""
import copy, json, sys, binascii
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'prealpha/airdrop_d1'),str(ROOT/'tools')]
from research import resources, SafeResource, flatten, walk, value
from catalog_gig_rollout_r2 import read,sha

def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def evaluate(c,s):
 if c['$type']=='questLogicalCondition':
  vals=[evaluate(x,s) for x in c['conditions']];return all(vals) if c['operation']=='AND' else any(vals)
 assert c['$type']=='questFactsDBCondition'
 t=c['type'];a=s.get(t.get('factName',t.get('factName1')),0);b=s.get(t['factName2'],0) if 'factName2' in t else t['value']
 return {'Equal':a==b,'Greater':a>b}[t['comparisonType']]

def verify(build):
 m=read(build/'build.json');assert m['status']=='BUILT_D1_LIVE_PENDING'
 assert len(m['resources'])==2 and len(m['files'])==2 and len(m['boots'])==1
 assert m['packed_readback'] and not m['official_overrides'] and m['runtime_scripts_added']==0
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h,p
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 native=graphs(ROOT/(m['native_source'].replace('/raw/','/json/')+'.json'));new=graphs(build/'readback/loop.json')
 assert set(new)==set(native)
 count=0
 for name,g in native.items():
  assert nodes(new[name])==nodes(g),name
  want=edges(g)
  if name=='root':want=want-{(23,'False',3,'Intro')}|{(23,'False',17,'In')}
  assert edges(new[name])==want,name
  count+=len(g['nodes'])
 assert count==172
 # Every encounter remains an official reference; all nested selection/pause/
 # cooldown, finite token waits, reward and used/unique-variant logic is identical.
 rootnodes=nodes(new['root']);assert rootnodes[46]['type']['value']==5
 assert nodes(new['root/3/239'])[5]['condition']['type']['minutes']==1
 assert nodes(new['root/50'])[5]['type']['factName']=='sa_ep1_reward_counter'
 boot=graphs(build/'readback/boot.json');assert set(boot)=={'root'}
 n=nodes(boot['root']);assert set(n)==set(range(6))
 assert edges(boot['root'])=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',5,'In1')}
 assert n[5]['phaseResource']['DepotPath']['$value']==r'towercontinued\airdrop_d1\loop.questphase'
 assert n[2]['condition']==n[3]['condition'];c=n[2]['condition']
 expected={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,'PTFRD1_Issued':0,'ep1_sa_test_airdrop_loop':0,'mq304_airdrops_active':0}
 pos=['ep1_installed','ep1_active','ep1_side_content'];assert m['guard_equal']==expected and m['guard_positive']==pos
 terms=[x['type'] for x in c['conditions']]
 assert sorted((t['factName'],t['comparisonType'],t['value']) for t in terms if 'factName' in t)==sorted([(k,'Equal',v) for k,v in expected.items()]+[(k,'Greater',0) for k in pos])
 assert [t for t in terms if 'factName1' in t]==[{'$type':'questVarVsVarComparison_ConditionType','comparisonType':'Equal','factName1':'sa_ep1_counter','factName2':'sa_ep1_reward_counter'}]
 good=expected|dict.fromkeys(pos,1)|{'sa_ep1_counter':8,'sa_ep1_reward_counter':8};assert evaluate(c,good)
 negatives=0
 for k,v in expected.items():
  for wrong in [-1,0,1,2]:
   if wrong==v:continue
   assert not evaluate(c,good|{k:wrong}),(k,wrong);negatives+=1
 for k in pos:
  for wrong in [-1,0]:assert not evaluate(c,good|{k:wrong});negatives+=1
 for a,b in [(8,7),(7,8),(100,0)]:assert not evaluate(c,good|{'sa_ep1_counter':a,'sa_ep1_reward_counter':b});negatives+=1
 # Repeatable history (including stale killed-owner active flags) must not be
 # treated as one-shot gig completion or silently reset at admission.
 assert evaluate(c,good|{'sa_ep1_38_active':1,'sa_ep1_38_used':1,'sa_ep1_37_finished':42})
 assert not evaluate(c,good|{'PTFRD1_Issued':1})
 assert [(n[i]['type']['factName'],n[i]['type']['value']) for i in [1,4]]==[('PTFRD1_Ready',1),('PTFRD1_Issued',1)]
 rs=resources();refs=set();casts=set()
 for d,p in rs.items():
  if d.endswith('ep1_sandbox_activities.questphase'):continue
  obj=read(p)
  assert not obj['Data']['RootChunk'].get('actors')
  for x in walk(obj):
   if x.get('$type')=='ResourcePath' and x.get('$storage')=='string' and x.get('$value','').endswith(('.questphase','.scene')):refs.add(x['$value'])
   if x.get('$type')=='questSceneNodeDefinition':casts.add(d)
 assert not casts and not (refs-set(rs))
 assert len(refs)==17
 # CRC plus current XL inventory: collision check is independent of builder.
 key=(m['boots'][0]+':1').encode();crc=binascii.crc_hqx(key,0xffff)
 assert crc not in [x['id'] for x in m['installed_injections']]
 xl=(build/'TowerContinued_Airdrops_D1.archive.xl').read_text();assert xl.count('towercontinued\\airdrop_d1\\boot.questphase')==1
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'native_nodes_unchanged':count,'native_edge_changes':1,'negative_admissions':negatives,'native_references':len(refs),'original_cast_scenes':0,'injection_id':crc,'lifecycle_model_not_live':True}

if __name__=='__main__':
 build=Path(sys.argv[1]);target=build/'tests.json';assert not target.exists(),'Evidence pinned'
 result=verify(build);target.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
