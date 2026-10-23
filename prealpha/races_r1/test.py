"""Race graph preservation, admission, resume and installed-resource tests.

Offline validation is not a live interaction, reward, or save/reload pass.
"""
import binascii, copy, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'prealpha/races_r1'),str(ROOT/'tools')]
from research import resources,SafeResource,flatten,walk,value
from catalog_gig_rollout_r2 import read,sha

def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def evaluate(c,s,j):
 if c['$type']=='questLogicalCondition':
  v=[evaluate(x,s,j) for x in c['conditions']];return all(v) if c['operation']=='AND' else any(v)
 t=c['type']
 if c['$type']=='questJournalCondition':
  state=j.get(t['path']['realPath'],'Inactive');result=state==t['state'];return not result if t['inverted'] else result
 assert c['$type']=='questFactsDBCondition'
 a=s.get(t['factName'],0);b=t['value'];return {'Equal':a==b,'Greater':a>b}[t['comparisonType']]

def verify(build):
 m=read(build/'build.json');assert m['status']=='BUILT_R1_LIVE_PENDING'
 assert len(m['resources'])==3 and len(m['files'])==2 and len(m['boots'])==1
 assert m['packed_readback'] and not m['official_overrides'] and m['runtime_scripts_added']==0 and m['native_scenes_unchanged']
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h,p
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 count=0
 for label,key in [('owner','owner_source'),('main','main_source')]:
  src=ROOT/(m[key].replace('/raw/','/json/')+'.json');a=graphs(src);b=graphs(build/'readback'/f'{label}.json')
  assert set(a)==set(b),(label,'graph set')
  for name,g in a.items():
   wanted=copy.deepcopy(nodes(g));out=nodes(b[name]);ee=edges(g)
   if label=='owner' and name=='root':wanted[9]['phaseResource']['DepotPath']['$value']=r'towercontinued\races_r1\main.questphase'
   if label=='main' and name=='root':
    assert set(out)==set(wanted)|{1000,1001}
    ee=ee-{(0,'Out',34,'In')}|{(0,'Out',1000,'In'),(1000,'False',34,'In'),(1000,'True',1001,'In'),(1001,'Out',23,'In1')}
    assert out[1001]['type']=={'$type':'questSetVar_NodeType','factName':'PTFRR1_Resumed','setExactValue':1,'value':1}
    out={i:n for i,n in out.items() if i<1000}
   assert out==wanted,(label,name,'payload')
   assert edges(b[name])==ee,(label,name,'edges')
   count+=len(wanted)
  # Preserve root-level prefab data as well as all embedded graph payloads.
  srcroot=read(src)['Data']['RootChunk'];dstroot=read(build/'readback'/f'{label}.json')['Data']['RootChunk']
  assert {k:v for k,v in srcroot.items() if k!='graph'}=={k:v for k,v in dstroot.items() if k!='graph'}
 boot=graphs(build/'readback/boot.json');assert set(boot)=={'root'};n=nodes(boot['root'])
 assert set(n)==set(range(6))
 assert edges(boot['root'])=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',5,'Intro_in')}
 assert n[5]['phaseResource']['DepotPath']['$value']==r'towercontinued\races_r1\owner.questphase'
 assert n[2]['condition']==n[3]['condition'];c=n[2]['condition']
 expected={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,'PTFRR1_Issued':0,'mq056_test_drive':0,'mq056_cour_active':0,'mq056_active':0,'mq056_prevention_fail':0}
 phases=['01_city_center','02_badlands','03_santo_domingo','04_big_race'];assert m['guard_equal']==expected and m['guard_journal_inactive']==phases and m['guard_positive']==['sq024_done']
 terms=[x['type'] for x in c['conditions'] if x['$type']=='questFactsDBCondition']
 assert sorted((t['factName'],t['comparisonType'],t['value']) for t in terms)==sorted([(k,'Equal',v) for k,v in expected.items()]+[('sq024_done','Greater',0)])
 jterms=[x['type'] for x in c['conditions'] if x['$type']=='questJournalCondition']
 assert sorted((t['path']['realPath'],value(t['path']['className']),t['state'],t['inverted']) for t in jterms)==sorted(('quests/minor_quest/mq056_race_replay/'+p,'gameJournalQuestPhase','Active',1) for p in phases)
 good=expected|{'sq024_done':1};assert evaluate(c,good,{})
 negatives=0
 for k,v in expected.items():
  for wrong in [-1,0,1,2]:
   if wrong==v:continue
   assert not evaluate(c,good|{k:wrong},{}),(k,wrong);negatives+=1
 for wrong in [-1,0]:assert not evaluate(c,good|{'sq024_done':wrong},{});negatives+=1
 for p in phases:assert not evaluate(c,good,{'quests/minor_quest/mq056_race_replay/'+p:'Active'});negatives+=1
 for state in ['Inactive','Succeeded','Failed']:
  assert evaluate(c,good,{('quests/minor_quest/mq056_race_replay/'+p):state for p in phases})
 # Existing wins/Claire refusal/cyberpsycho completion are not reset or gated.
 assert evaluate(c,good|{'mq056_citycenter_won':7,'sq024_claire_pissed':1,'ow_psychos_done':17},{})
 resume=nodes(graphs(build/'readback/main.json')['root'])[1000]['condition']
 assert resume['operation']=='OR' and len(resume['conditions'])==2
 path='contacts/announcer_mq056/mq056_hook/01_hook2'
 assert [(t['type']['path']['realPath'],value(t['type']['path']['className']),t['type']['state']) for t in resume['conditions']]==[(path,'gameJournalPhoneMessage',s) for s in ['Active','Succeeded']]
 for state in ['Inactive','Active','Succeeded','Failed']:assert evaluate(resume,{}, {path:state})==(state in ['Active','Succeeded'])
 main=graphs(build/'readback/main.json');mn=nodes(main['root'])
 assert mn[35]['condition']['type']['days']==3
 # Four native starts, interaction inputs, completion and prevention-retry
 # ports remain intact. Their race payloads are not packed or overridden.
 for graph,scene_id,scene_name in [(26,4,'01_city_race'),(28,11,'02_badlands'),(29,4,'03_santo_domingo'),(30,10,'04_big_race')]:
  part=main['root/'+str(graph)];scene=nodes(part)[scene_id]
  assert scene['sceneFile']['DepotPath']['$value']==('base\\quest\\minor_quests\\mq056\\scenes\\mq056_'+scene_name+'.scene')
  assert any(e[2]==scene_id and 'waiting' in e[3] for e in edges(part))
 owner=graphs(build/'readback/owner.json')['root']
 for race,port in [(12,'In_again_cc'),(14,'In_again_badlands'),(15,'In_santo_doming'),(16,'In_westbrook')]:assert (race,'Out1',9,port) in edges(owner)
 for port in ['Badlands_fail_out','CityCenter_fail_out','SantoDomingo_fail_out','Westbrook_fail_out']:assert any(e[0]==38 and e[1]==port and e[2]==9 for e in edges(owner))
 parent=graphs(ROOT/'research/races_r1/parents_01/json/base/quest/bugfixing/quest_bugfixing.questphase.json')['root/3']
 assert nodes(parent)[75]['condition']['type']['factName']=='sq024_done' and (75,'Out',74,'Intro_in') in edges(parent)
 refs={x['$value'] for p in resources().values() for x in walk(read(p)) if x.get('$type')=='ResourcePath' and x.get('$storage')=='string' and x.get('$value','').endswith(('.questphase','.scene'))}
 assert not (refs-set(resources()))
 scenes={d:read(p)['Data']['RootChunk'] for d,p in resources().items() if d.endswith('.scene')}
 # The existing JV1 policy must remain installed verbatim; P1/race patches do
 # not mute audio or replace scenes. Visible props still need a live check.
 jv=ROOT/'prealpha/build/20261013T021845834Z/package/r6/scripts/PTFR_PreAlpha/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds'
 live=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')/'r6/scripts/PTFR_PreAlpha/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds'
 assert sha(jv)==sha(live)
 crc=binascii.crc_hqx((m['boots'][0]+':1').encode(),0xffff);assert crc not in [x['id'] for x in m['installed_injections']]
 assert (build/'TowerContinued_Races_R1.archive.xl').read_text().count(m['boots'][0])==1
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'copied_native_nodes_checked':count,'main_entry_edge_removed':1,'main_entry_edges_added':4,'owner_resource_redirects':1,'negative_admissions':negatives,'resume_states_checked':4,'dependency_resources':len(resources()),'native_scenes_unchanged':len(scenes),'johnny_policy_sha256':sha(jv),'injection_id':crc,'not_proven':['rendered start interaction','race opponents/checkpoints','payout','repeat','new-save reload','Johnny voice/body delivery']}

if __name__=='__main__':
 build=Path(sys.argv[1]);target=build/'tests.json';assert not target.exists(),'Evidence pinned'
 result=verify(build);target.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
