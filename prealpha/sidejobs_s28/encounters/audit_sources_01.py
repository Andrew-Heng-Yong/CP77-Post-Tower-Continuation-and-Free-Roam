"""Read-only exact patch delta and normal-campaign prerequisite ordering proof."""
import sys,json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
HERE=ROOT/'research/sidejobs_s28/encounters'
PINS={};CHECKS=[]
def pin(p):
 p=str(p).replace('\\','/');PINS[p]=sha(ROOT/p);return p
def load(p):
 pin(p);pin(p.replace('/json/','/raw/').removesuffix('.json'));r=SafeResource(read(ROOT/p));return r,{g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def chk(ok,why):
 assert ok,why;CHECKS.append(why)
def edge(gs,g,*e):chk(list(e) in gs[g]['edges'],[g,'edge',e])
def node(gs,g,n):return next(x for x in gs[g]['nodes'] if x['id']==n)
def fact(gs,g,n,f,v):
 t=node(gs,g,n)['type'];chk(t['factName']==f and t['value']==v,[g,n,f,v])
def main():
 out=HERE/'source_assessment_01.json';assert not out.exists()
 pin(str(Path(__file__).relative_to(ROOT)));pin('tools/catalog_gig_rollout_r2.py');pin('tools/test_rite_g2.py');pin('tools/audit_activity_batches_b1.py');pin('research/sidejobs_s28/encounters/official_check_01/report.json')
 current='research/sidejobs_s28/encounters/official_check_01/basegame_4_gamedata/json/'
 a,ag=load('research/omitted_jobs_audit/native_01/json/base/quest/minor_quests/mq003/mq003_orbitals.questphase.json');b,bg=load(current+'base/quest/minor_quests/mq003/mq003_orbitals.questphase.json')
 chk(a.obj['Data']==b.obj['Data'],'mq003 entire decoded Data equality; raw difference not used as current source identity')
 a,ag=load('research/coyote_sidejobs_audit/native_01/json/base/quest/default_dialogs.questphase.json');b,bg=load(current+'base/quest/default_dialogs.questphase.json')
 chk(ag.keys()==bg.keys(),'default graphs unchanged')
 for gp in ag:
  if gp!='root/4/21':chk(ag[gp]==bg[gp],['default unchanged graph',gp])
 old=ag['root/4/21'];new=bg['root/4/21'];ns={n['id']:n for n in new['nodes']};chk(all(n==ns[n['id']] for n in old['nodes']),'all existing Tarot payloads preserved')
 chk(set(ns)-{n['id'] for n in old['nodes']}=={57,58,59},'only Tarot new nodes57/58/59')
 removed=[[39,'Out',45,'In'],[39,'Out',3,'live_in']];added=[[57,'False',45,'In'],[57,'False',3,'live_in'],[57,'True',58,'In'],[58,'Out',45,'In'],[39,'Out',57,'In'],[58,'Out',3,'live_in']]
 chk(sorted(e for e in old['edges'] if e not in removed)+[]==sorted(e for e in new['edges'] if e not in added),'only exact Tarot edge replacement')
 chk(ns[57]['condition']['type']['factName']=='mq033_minor_grafitti_reward_choose' and ns[58]['condition']['type']['factName']=='mq033_minor_reward_spawn' and ns[59]['condition']['type']['factName']=='mq033_grafitti_counter','Tarot-specific additions')
 chk({k:v for k,v in a.obj['Data']['RootChunk'].items() if k!='graph'}=={k:v for k,v in b.obj['Data']['RootChunk'].items() if k!='graph'},'default root prefab metadata equality')
 a,ag=load('research/sidejobs_s28/encounters/native_02/json/base/quest/main_quests/part1/q101/phases/q101_p2_meet_takemura.questphase.json');b,bg=load(current+'base/quest/main_quests/part1/q101/phases/q101_p2_meet_takemura.questphase.json')
 chk(ag.keys()==bg.keys(),'q101 graphs unchanged')
 for gp in ag:
  if gp!='root':chk(ag[gp]==bg[gp],['q101 nested equality',gp])
 old=ag['root'];new=bg['root'];ns={n['id']:n for n in new['nodes']};chk(all(n==ns[n['id']] for n in old['nodes']),'q101 existing node payload equality');chk(set(ns)-{n['id'] for n in old['nodes']}=={171,172},'onlyq101 render nodes171172')
 chk(sorted(old['edges']+[[4,'v_flat_out',172,'In'],[23,'Out',171,'In']])==new['edges'],'onlyq101 two parallel render edges')
 chk(all(ns[n]['type'].get('$className')=='questIncreaseLocalShadowmapUpdates_NodeType' for n in [171,172]),'q101 new render-only type')
 causal={}
 paths={
 'prologue':'research/sidejobs_s28/encounters/native_01/json/base/quest/main_quests/prologue/prologue.questphase.json',
 'base':'research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json',
 'act1':'research/sidejobs_s28/encounters/native_01/json/base/quest/main_quests/part1/act_1.questphase.json',
 'q101':'research/sidejobs_s27/heroes/native_04/json/base/quest/main_quests/part1/q101/q101.questphase.json',
 'cleanup':'research/sidejobs_s28/encounters/native_02/json/base/quest/main_quests/part1/q101/phases/q101_cleanup.questphase.json',
 'q110b':'research/sidejobs_s28/encounters/native_05/json/base/quest/main_quests/part1/q110/q110b.questphase.json',
 'ep1':'research/q307_extracted/json/ep1/quest/ep1.questphase.json',
 'ep1main':'research/sidejobs_s28/encounters/native_01/json/ep1/quest/main_quests/ep1_main_quests.questphase.json',
 'bugfix':'research/q307_extracted/json/base/quest/bugfixing.questphase.json'}
 for k,p in paths.items():causal[k]=load(p)[1]
 edges={
 'prologue':[[16,'Out1',20,'In1'],[20,'Out1',48,'In1'],[48,'Out1',42,'In'],[42,'Otherwise',18,'In1'],[42,'Otherwise',21,'In1'],[18,'Out1',50,'In2'],[21,'Out1',50,'In1'],[50,'Out1',19,'In1'],[19,'Out1',43,'In']],
 'base':[[32,'Out1',33,'Q101']],
 'act1':[[28,'Out',2,'In1'],[2,'Out1',167,'In1'],[167,'Out1',158,'In1'],[158,'Out1',9,'In1'],[9,'Start_q110',10,'In1'],[10,'StartQ108',11,'In1'],[11,'Out',148,'StartQ110Alt']],
 'q101':[[105,'Out1',119,'In1'],[119,'Out1',39,'In']],
 'cleanup':[[0,'Out',2,'Succeeded'],[2,'Out',4,'In'],[4,'Out',3,'In'],[3,'Out',6,'In'],[6,'Out',7,'In']],
 'q110b':[[277,'Out',266,'In'],[266,'Out',289,'In']],
 'ep1':[[0,'Out',14,'In'],[14,'Out',16,'In'],[16,'False',21,'In'],[16,'True',22,'In1'],[21,'True',22,'In2'],[22,'Out1',9,'Base']],
 'ep1main':[[0,'Out',1,'In1'],[1,'Out1',2,'In1'],[2,'Out1',3,'In1'],[3,'Out1',4,'In1'],[4,'Out1',18,'In'],[18,'True',6,'In1'],[18,'False',7,'00_start'],[29,'True',33,'In1'],[35,'True',33,'In1'],[33,'Out1',12,'main_in']]}
 for k,es in edges.items():
  for e in es:edge(causal[k],'root',*e)
 fact(causal['cleanup'],'root',6,'q101_done',1);chk(node(causal['cleanup'],'root',2)['type']['path']['realPath']=='quests/main_quest/act_01/q101_resurrection','q101 completion journal precedes native completion output')
 fact(causal['q110b'],'root',266,'q110_done',1);fact(causal['q110b'],'root',289,'ep1_active',1)
 chk(node(causal['ep1'],'root',14)['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'ep1_active','value':1},'normal EP1 launch requires native q110 completion')
 edge(causal['bugfix'],'root/30',2,'True',3,'In');fact(causal['bugfix'],'root/30',3,'ep1_active',1);chk(node(causal['bugfix'],'root/30',2)['condition']['type']['factName']=='q110_done','legacy EP1 activation also requires completed q110')
 result={'status':'PASS_CURRENT_PATCH_DELTAS_NORMAL_CAMPAIGN_PREREQUISITE_ORDER','checks':len(CHECKS),'assertions':CHECKS,'source_pins':PINS,'patch_deltas':{'mq003':'Entire decoded Data identical; current raw selected.','default_dialogs':'Only unrelated Tarot root/4/21 adds nodes57/58/59 and exact edge reroute. Diner subtree and loading_conditions root prefab identical.','q101_meet_takemura':'Only two parallel local shadowmap update render nodes; no native existing payload/edge removed.'},'prerequisite_order':{'source_paths':paths,'edges':edges,'reasoning':'Normal campaign q001 and q005 complete before prologue Out1 dispatches q101. Native q101 completion journal and done fact precede q101 Out1, which starts q105 and then q110/q108/q110b. q110b sets q110_done before ep1_active. Normal EP1 launch waits ep1_active, and subsequent native campaign reaches q307. The existing-game EP1 repair also requires q110_done. Therefore normal-campaign genuine Tower completion causally postdates the required early quest completion; this is not an invented timestamp or writable certificate.','scope':'Normal campaign only, with ep1_standalone=0, cp77_ep1_testing=0, genuine Tower admission and q001/q005/q101 complete facts plus actual q101 Succeeded required. Developer input ports, standalone skip history, imported fabricated facts, and general all-save provenance are not certified. No excluded parent is started or modified.'},'limitations':['This report does not certify compatibility of the changed script cache or all installed mods.','Current archive full identity and fresh raw-to-JSON decoding remain aggregate audit requirements.']}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(CHECKS),'pins':len(PINS),'sha256':sha(out)}))
if __name__=='__main__':main()
