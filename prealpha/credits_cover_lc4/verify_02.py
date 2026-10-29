import hashlib,json,sys
from pathlib import Path
W=Path(__file__).resolve().parents[2]
C=W/'prealpha/credits_cover_lc4/candidate_02'
sys.path.insert(0,str(W/'diagnostics/skippy_triggers_20261027_01/runtime_review'))
from inspect_graph_01 import Resource
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):h.update(x)
 return h.hexdigest().upper()
r=Resource(C/'final_boards_patched_01.json')
n=r.nodes(r.graph);e=r.edges(r.graph);tests=[]
def check(name,v):tests.append(dict(name=name,passed=bool(v)));assert v,name
def typ(i):return r.plain(n[i]).get('type',{})
def edges(i):return sorted(x for x in e if x[0]==i)
original=Resource(W/'diagnostics/credits_transition_cover_20261028_01/source/base/quest/main_quests/epilogue/final_boards.questphase.json')
old=original.edges(original.graph)
check('Two old edges removed only',old-e=={(100,'Out',27,'In'),(27,'Out',28,'In')})
check('Expected branch fanout',e-old=={(100,'Out',182,'In'),(182,'True',183,'In'),(182,'False',27,'In'),(183,'Out',27,'In'),(27,'Out',184,'In'),(184,'True',185,'In'),(184,'False',28,'In')})
check('Two guards exact copied identity',r.plain(n[182])['condition']==original.plain(original.nodes(original.graph)[101])['condition'] and r.plain(n[184])['condition']==original.plain(original.nodes(original.graph)[101])['condition'])
check('Acquisition before notify',[(x[0],x[2]) for x in edges(182)]==[(182,27),(182,183)] and (183,'Out',27,'In') in e)
check('Instant black from Q307 precedent',typ(183)['$type']=='questSetFadeInOut_NodeType' and typ(183)['fadeIn']==0 and typ(183)['duration']==0)
check('Vanilla reveal remains on false branch',(184,'False',28,'In') in e and typ(28)['fadeIn']==1 and typ(28)['duration']==0)
check('No double start or teleport',[(i,typ(i).get('factName')) for i in n if typ(i).get('factName')=='PTFRPA2_Started']==[(140,'PTFRPA2_Started')])
check('Native credit notice preserved',typ(27)['$type']=='questFinalBoardsVideosFinished_NodeType')
check('Cover handoff retained',(180,'Out',181,'In') in e and (181,'Out',176,'In') in e and typ(176)['fadeIn']==1)
check('No-op receipt terminates owned branch',typ(185)['factName']=='PTFRLC4_CreditsBlackHeld' and not edges(185))
check('All original top-level node IDs and types preserved',all(i in n and r.plain(n[i])['$type']==original.plain(v)['$type'] for i,v in original.nodes(original.graph).items()))
b=read(C/'build_01.json');check('Exactly one changed packed resource',len(b['changed_members'])==1 and b['old_member_bytes_unchanged']==1562)
check('Packed phase source hash',sha(C/'archive_source/base/quest/main_quests/epilogue/final_boards.questphase')==b['changed_members'][0]['after'])
report=dict(status='PASS_SCOPED_GRAPH_SEMANTICS',checks=tests,game_writes=0,save_writes=0,limits=['Static graph and archive checks do not prove first rendered frame or watched/skipped runtime ordering.'])
(C/'verification_02.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],checks=len(tests))))
