"""Independent normalized payload/edge review of the serialized Brendan fix."""
from pathlib import Path
import json,hashlib,ast,copy
W=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent;O=D/'reviews';O.mkdir(exist_ok=True)
dest=O/'brendan_serialized.json';assert not dest.exists()
# Reuse only the already-inspected pure raw parser definitions from this agent's
# independent review, without executing that module's top-level I/O/checkpoint.
src=(D/'review_mq030.py').read_text();tree=ast.parse(src);keep=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ['Raw','val','walk']]
ns={};exec(compile(ast.Module(body=keep,type_ignores=[]),'<independent raw parser>','exec'),ns);Raw=ns['Raw']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
p=W/'prealpha/quest_restoration_qr3/candidate_01/repair';b=p/'before.json';a=p/'after.json'
before=Raw(json.loads(b.read_text(encoding='utf-8-sig')));after=Raw(json.loads(a.read_text(encoding='utf-8-sig')))
bn,be=before.graph();an,ae=after.graph();checks=[]
def check(name,ok,evidence):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
check('same13savednodeIDs',set(bn)==set(an) and len(bn)==13,sorted(bn))
for i in bn:
 check('node payload retained '+i,before.clean(bn[i])==after.clean(an[i]),i)
 bs=[(str(ns['val'](before.d(s)['name'])),before.d(s)['type']) for s in bn[i]['sockets']];as_=[(str(ns['val'](after.d(s)['name'])),after.d(s)['type']) for s in an[i]['sockets']]
 check('socket identities retained '+i,bs==as_,i)
check('one edge removed',be-ae=={('1004','True','1005','In')},list(be-ae))
check('one edge added',ae-be=={('1004','True','1008','In')},list(ae-be))
def reach(edges,seed):
 seen={seed};todo=[seed]
 while todo:
  x=todo.pop()
  for v,s,w,t in edges:
   if v==x and w not in seen and s!='CutSource' and t!='CutDestination':seen.add(w);todo.append(w)
 return seen
old=reach(be,'1000');new=reach(ae,'1000')
check('defective baseline enters full native body','34'in old and '1005'in old,sorted(old))
check('patched freshinput refuses before Issued','1008'in new and not {'1005','1006','34'}&new,sorted(new))
check('refusedwriter owns only existing diagnostic',after.clean(an['1008'])['type']=={'$type':'questSetVar_NodeType','factName':'PTFRS23_MQ037_Refused','setExactValue':1,'value':1},'No native journal/reset/ack writer added')
for seed in ['1005','1006','34']:
 check('saved descendant reachability retained '+seed,reach(be,seed)==reach(ae,seed),{'seed':seed,'nodes':sorted(reach(ae,seed))})
check('resource metadata retained',{k:before.clean(v) for k,v in before.root.items() if k!='graph'}=={k:after.clean(v) for k,v in after.root.items() if k!='graph'},'All resource-root fields besides graph')
patch=json.loads((p/'patch.json').read_text(encoding='utf-8-sig'));raw=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source/towercontinued/sidejobs_s23/base_b/mq037.questphase'
check('readback binds actual staged raw resource',sha(raw)==patch['after'] and patch['before']=='E42A7DE2591C367ACD1FCFAFD0D9BA728204034D57CEA0577848445C7C8DD94E',patch)
tampered=(ae-{('1004','True','1008','In')})|{('1004','True','1005','In')}
check('regression detects restored faulty edge','34'in reach(tampered,'1000'),'Actual repairedgraph mutation restores policy fault')
out={'status':'PASS_SERIALIZED_MINIMAL_QUARANTINE_REVIEW','reviewer':'Agent D; independent raw-handle/socket parser; no root/C/B verifier imported','checks':checks,'check_count':len(checks),'inputs':{'before_json':{'path':str(b),'sha256':sha(b)},'after_json':{'path':str(a),'sha256':sha(a)},'staged_raw':{'path':str(raw),'sha256':sha(raw)},'raw_parser_source_sha256':sha(D/'review_mq030.py')},'scope':'Serialized single-edge preclaim refusal only; native body/payloads/saved descendants preserved. Not a complete earned-history continuation adapter.','limitations':['Already-queued old work past guard1004, serialized engine scheduling and saved runtime adoption remain LIVE_ONLY.','Excluded Dumpster leak is contained for new input; selected later Brendan quests remain unsupported until a justified earned-history seam.'],'runtime_edits':False}
dest.write_text(json.dumps(out,indent=2,ensure_ascii=True)+'\n',encoding='utf-8');print(json.dumps({'status':out['status'],'checks':len(checks)}))
