"""Independent native ancestor/termination checks against fresh provider exports.

This proves graph containment and authored termination, not engine scheduling or
the contents of any player's executing save tree. No gameplay writes occur.
"""
from pathlib import Path
import sys,copy,json,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
C=read(O/'provider_readback_01/capture.json');idx=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
checks=[];inputs=[]
def check(name,ok,evidence):
 checks.append({'name':name,'pass':bool(ok),'evidence':evidence})
 assert ok,name
def load(d):
 rows=[r for r in C['providers'] if r['depot']==d]
 assert rows and all(r['stock'] for r in rows),d
 assert len({r['sha256'] for r in rows})==1,d
 p=Path(rows[0]['json'] or idx[d]['json'])
 if not rows[0]['json']:assert rows[0]['sha256']==idx[d]['sha256']
 inputs.append({'depot':d,'resource_sha256':rows[0]['sha256'],'source_json':str(p),'json_sha256':sha(p),'archives':[r['archive'] for r in rows]})
 return Resource(read(p)).normalize()
game=load('base\\quest\\cyberpunk2077.questphase')
bug=load('base\\quest\\bugfixing.questphase')
qb=load('base\\quest\\bugfixing\\quest_bugfixing.questphase')
minor=load('base\\quest\\minor_quests\\minorquests.questphase')
debt=load('base\\quest\\bugfixing\\minor_quests\\mq033\\mq033_quest_bugfixes.questphase')
g=game['graphs']['root']
def termination_ok(graph):
 return all(e in graph['edges'] for e in [['106','Out','109','In'],['109','Out','107','In']]) and graph['nodes']['107']['payload']['type']=='Terminating' and any(r.get('state')=='Succeeded' and r.get('path',{}).get('realPath')=='ep1/quests/main_quest/q307_before_tomorrow' for r in graph['nodes']['106']['reads']) and graph['nodes']['109']['writes']==[{'$type':'questSetVar_NodeType','factName':'q307_main_game_killed','setExactValue':1,'value':1}]
check('native_genuine_Tower_journal_to_receipt_to_terminating_output',termination_ok(g),'root106.Out→109.In;109.Out→107.In; terminating107 contains all root descendants')
check('minorquests_is_contained_by_terminated_main_root','base\\quest\\minor_quests\\minorquests.questphase' in game['graphs']['root/82']['nodes']['6']['refs'],'cyberpunk root/82 node6')
check('bugfixing_is_contained_by_terminated_main_root','base\\quest\\bugfixing.questphase' in game['graphs']['root/82']['nodes']['4']['refs'],'cyberpunk root/82 node4')
check('native_bugfix_parent_owns_quest_bugfixing','base\\quest\\bugfixing\\quest_bugfixing.questphase' in bug['graphs']['root']['nodes']['9']['refs'],'bugfixing root9;16.Out→9.In1')
check('native_quest_bugfix_parent_owns_mq033','base\\quest\\bugfixing\\minor_quests\\mq033\\mq033_quest_bugfixes.questphase' in qb['graphs']['root/3']['nodes']['51']['refs'],'quest_bugfixing root/3 node51')
check('native_mq033_activates_inline_debt_chain',['20','Out','21','In1'] in debt['graphs']['root']['edges'],'mq033 root20.Out→21.In1;debt graph root/21')
owners={}
for key in ['mq035','mq038']:
 owners[key]=[{'graph':gp,'node':i,'refs':n['refs'],'prefabs':n['payload'].get('phaseInstancePrefabs',[])} for gp,gr in minor['graphs'].items() for i,n in gr['nodes'].items() if any(('\\'+key+'\\') in d for d in n['refs'])]
 check('native_minor_parent_contains_'+key,bool(owners[key]),owners[key])
for kind in ['terminator','edge','journal']:
 mutated=copy.deepcopy(g)
 if kind=='terminator':mutated['nodes']['107']['payload']['type']='NonTerminating'
 if kind=='edge':mutated['edges'].remove(['109','Out','107','In'])
 if kind=='journal':mutated['nodes']['106']['reads'][0]['state']='Active'
 check('mutation_rejected_'+kind,not termination_ok(mutated),'In-memory mutation against actual fresh original graph; no fixture files replace sources')
by=collections.defaultdict(list)
for r in C['providers']:by[r['depot']].append(r)
disagree=[d for d,rs in by.items() if len({r['sha256'] for r in rs if r['sha256']})>1]
bad=[r for r in C['providers'] if r['matches_expected'] is False]
check('reviewed_graph_provider_hashes_equal_pins',not bad,{'hashed_provider_payloads':sum(bool(r['sha256']) for r in C['providers']),'differing_hash_depots':disagree})
write(O/'ancestor_review.json',{'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','inputs':inputs,'checks':checks,'native_minor_owners':owners,'scope':'Native authored containment/termination and current bounded provider equivalence; no saved-owner adoption or runtime scheduling proof','provider_missing':C['missing'],'runtime_changes':[]})
print(json.dumps({'status':'PASS','checks':len(checks),'inputs':len(inputs),'missing_literal_localization_assets':len(C['missing'])}))
