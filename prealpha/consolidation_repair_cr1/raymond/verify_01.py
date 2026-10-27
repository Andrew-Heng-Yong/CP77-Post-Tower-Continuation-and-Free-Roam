"""Read-only Raymond handoff evidence; emits workspace proof, never a runtime patch."""
import hashlib,json,re,sys
from pathlib import Path
W=Path(__file__).resolve().parents[3]; O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
BASE='research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json'
Q307='research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json'
MINOR='research/coyote_sidejobs_audit/native_01/json/base/quest/minor_quests/minorquests.questphase.json'
MQ040='research/coyote_sidejobs_audit/native_01/json/base/quest/minor_quests/mq040/mq040_biosculpt.questphase.json'
PUBLIC=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/red4ext/plugins/Codeware/Scripts/Codeware.Global.reds')
S29=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')
sources={}
def record(p):
 p=Path(p);p=p if p.is_absolute() else W/p
 key=p.relative_to(W).as_posix() if p.is_relative_to(W) else p.as_posix()
 raw=p.read_bytes();sources[key]={'sha256':hashlib.sha256(raw).hexdigest().upper(),'bytes':len(raw)}
 return raw
def graphs(p):
 r=SafeResource(json.loads(record(p)));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def node(g,i):return next(n for n in g['nodes'] if n['id']==i)
def edge(g,a,b,out='Out',ins='In'):return [a,out,b,ins] in g['edges']
def depot(n):return n['phaseResource']['DepotPath']['$value']
checks=[]
def check(name,ok,evidence):
 assert ok,name
 checks.append({'name':name,'passed':True,'evidence':evidence})
b=graphs(BASE);q=graphs(Q307);m=graphs(MINOR);r=graphs(MQ040)
check('Normal Tower termination follows fact writer',node(b['root'],109)['type']['factName']=='q307_main_game_killed' and node(b['root'],107)['type']=='Terminating' and edge(b['root'],106,109) and edge(b['root'],109,107),{'graph':'base root','edges':[[106,'Out',109,'In'],[109,'Out',107,'In']]})
check('MQ040 belongs beneath terminating base root',depot(node(b['root/82'],6))=='base\\quest\\minor_quests\\minorquests.questphase' and depot(node(m['root'],49))=='base\\quest\\minor_quests\\mq040\\mq040_biosculpt.questphase',{'owner_chain':'base root /82 /6 -> minorquests /49 -> mq040_biosculpt'})
check('Alternate q307 writer precedes a different cut',node(q['root'],18)['type']['factName']=='q307_main_game_killed' and edge(q['root'],16,18) and edge(q['root'],18,17) and edge(q['root'],17,6,'CutSource','CutDestination'),{'graph':'q307.quest root','writer':18,'cut':17,'cut_target':6})
children=[depot(n) for n in q['root/6']['nodes'] if n['$type']=='questPhaseNodeDefinition']
check('Alternate cut target is infrastructure, not the MQ040 owner',len(children)==6 and all('minorquests' not in d and 'mq040' not in d and 'cyberpunk2077.questphase' not in d for d in children),children)
check('MQ040 reserves before its encounter phase',node(r['root/3'],14)['type']=={'$type':'questSetVar_NodeType','factName':'mq040_active','setExactValue':1,'value':1} and node(r['root/3'],11)['type']['factName']=='elcoyote_barman_default_on' and node(r['root/3'],11)['type']['value']==0 and edge(r['root'],3,4,'Out1','In1'),{'graph':'mq040 root/3','active_writer':14,'service_disable_writer':11,'next_phase':'root/4 mq040_bar_corpo'})
check('Normal setup has world obligations',node(r['root/3'],10)['actions'][0]['type']['action']=='Reactivate' and node(r['root/3'],10)['actions'][0]['type']['phaseName']['$value']=='mq040_01_bartop',{'community_nodes':[2,4],'pepe_reactivate':10,'community_cycle':[17,18,19]})
check('Cleanup restores the service and has a failure-branch active clear',node(r['root/12'],20)['type']['factName']=='elcoyote_barman_default_on' and node(r['root/12'],20)['type']['value']==1 and node(r['root/12'],41)['type']['factName']=='mq040_active' and node(r['root/12'],41)['type']['value']==0 and edge(r['root/12'],29,38) and edge(r['root/12'],38,30) and edge(r['root/12'],30,41),{'graph':'mq040 root/12','service_restore':20,'active_clear':41,'active_clear_route':'Failed input29 -> outside-trigger38 -> content-token30 -> active-clear41'})
public=record(PUBLIC).decode('utf-8-sig')
extensions=re.findall(r'@addMethod\(QuestsSystem\)\s*([^\r\n]+)',public)
check('Public Codeware quest extension is ExecuteNode only',len(extensions)==1 and 'ExecuteNode' in extensions[0],extensions)
runtime=record(S29).decode('utf-8-sig')
def array(name):
 match=re.search(r'func '+name+r'\(\).*?return \[(.*?)\];',runtime)
 assert match,name
 return json.loads('['+match.group(1)+']')
names=array('FactNames5');minimum=array('FactMin5');maximum=array('FactMax5')
at=names.index('mq040_active')
check('Current S29 does not admit the captured partial owner',minimum[at]==0 and maximum[at]==0,{'fact':'mq040_active','minimum':minimum[at],'maximum':maximum[at],'captured':1})
for p in [
 'docs/sidejob_entry_review_20261026.md',
 'diagnostics/sidejob_entry_phone_audit_20261026_01/raymond_log_excerpt_01.json',
 'diagnostics/sidejob_entry_phone_audit_20261026_01/entry_state/partial_state_01.json',
 'research/framework_pr63_01/codeware/src/App/Quest/QuestPhaseRegistry.hpp',
 'research/framework_pr63_01/codeware/src/App/Quest/QuestPhaseRegistry.cpp',
 'research/framework_pr63_01/codeware/scripts/Base/Imports/questNodeLoadingCondition.reds',
 'research/framework_pr63_01/codeware/scripts/Base/Imports/questSceneNode_ConditionType.reds',
 'redscript/PTFR_B0_StoryServices/StoryServiceDriver.reds',
]:record(p)
out={'schema':1,'status':'RAYMOND_HANDOFF_NOT_IMPLEMENTED_OWNER_RETIREMENT_UNPROVEN',
 'scope':'MQ040 pre-journal partial-owner handoff only; excludes marker identification and speculative MQ018/MQ028 changes.',
 'checks':checks,'sources':sources,
 'decision':{'production_changes':0,'runtime_admission_changes':0,'reason':'Normal base-root termination contains MQ040, but the existing killed fact is written before that output and by another native graph whose cut does not target MQ040. The captured save has no owner-retirement acknowledgement. Inspected public Codeware script additions expose only mutating ExecuteNode; internal C++ phase registry lookup is not a public script query and a phase object lookup alone does not certify executing state.',
 'needed':'A read-only saved/runtime phase-state proof for the exact original MQ040 owner, or a new explicit acknowledged retirement seam with verified world cleanup and single-owner transfer; then a bounded resume adapter preserving journal, choices, rewards, and calls.',
 'forbidden_shortcuts':['clear mq040_active','force elcoyote_barman_default_on','relax fresh fact guard on rootInactive alone','treat q307_main_game_killed alone as unique retirement acknowledgement','reset original graph facts','replace public Codeware with a custom build']},
 'protected_actions':{'game_launches':0,'game_file_writes':0,'save_writes':0,'fact_writes':0,'installations':0},
 'limitations':['Structural source assertions, not live owner observation or gameplay proof.','No exhaustive claim that all possible engine APIs have been ruled out.','Existing captured evidence is reused; no new live state was obtained.']}
(O/'assessment_01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'all_passed':True,'sources':len(sources),'production_changes':0}))
