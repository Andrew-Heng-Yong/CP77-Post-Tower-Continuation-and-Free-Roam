"""Read-only successor proof: native post-conversation slice and opt-in safety."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23/base_a'))
from audit import graphs,sha,load,walk,capture
sys.path.insert(0,str(HERE))
from prepare import contract
STATES={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}

def ev(c,f,j,inventory=1):
 if c['$type']=='questLogicalCondition':
  a=[ev(v,f,j,inventory) for v in c['conditions']]
  return {'AND':all(a),'OR':any(a),'NOR':not any(a)}[c['operation']]
 t=c['type']
 if c['$type']=='questJournalCondition':return j.get(t['path']['realPath'])==t['state']
 if c['$type']=='questObjectCondition':
  assert t['$type']=='questInventory_ConditionType' and t['isPlayer']==1 and t['itemID']['hash']==81386061912
  assert t['quantity']==1 and t['comparisonType']=='GreaterOrEqual';return inventory>=1
 assert c['$type']=='questFactsDBCondition'
 a=f.get(t['factName']);b=t['value']
 if a is None:return False
 return {'Equal':lambda:a==b,'GreaterOrEqual':lambda:a>=b,'LessOrEqual':lambda:a<=b}[t['comparisonType']]()

def verify(out):
 checks=cases=0;spec=load(HERE/'contract.json');assert spec==contract();m=load(out/'manifest.json')
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p;checks+=1
 old=load(ROOT/spec['reused_manifest']);oldtests=load(ROOT/'research/sidejobs_s23/base_a/audit_03/tests.json')
 assert oldtests['component_sha256']==sha(ROOT/spec['reused_manifest']) and oldtests['status'].startswith('PASS');checks+=2
 assert spec['owners'][:8]==load(ROOT/'prealpha/sidejobs_s23/base_a/contract.json')['owners'];checks+=8
 assert len(m['resources'])==10 and len(m['boots'])==9 and len(m['rows'])==10;checks+=3
 for a,b in zip(old['rows'],m['rows'][:8]):
  assert Path(a['raw']).read_bytes()==Path(b['raw']).read_bytes();assert Path(a['json']).read_bytes()==Path(b['json']).read_bytes();checks+=2
 for r in m['rows']:
  assert sha(Path(r['raw']))==r['sha256'] and sha(Path(r['json']))==r['readback_sha256'];checks+=2
 s=spec['owners'][-1]
 native={g['path']:g for g in graphs(ROOT/(s['resume_source'].replace('/raw/','/json/')+'.json'))}
 result={g['path']:g for g in graphs(out/'mq007_resume_owner.json')}
 nn={n['id']:n for n in native['root']['nodes']};rn={n['id']:n for n in result['root']['nodes']}
 assert set(rn)==set(s['resume_nodes']) and {2,4,8,10}.isdisjoint(rn);checks+=2
 for i in s['resume_nodes']:assert rn[i]==nn[i],i;checks+=1
 assert result['root']['edges']==s['resume_edges'];checks+=1
 assert (4,'Out1',5,'In1') in set(map(tuple,native['root']['edges']));checks+=1
 selected={'root'}|{p for p in native if p!='root' and int(p.split('/')[1]) in s['resume_nodes']}
 assert set(result)==selected;checks+=1
 for p in selected-{'root'}:assert result[p]==native[p],p;checks+=len(native[p]['nodes'])+len(native[p]['edges'])
 # Native 2-day delay, reveal acknowledgement and one reward path remain intact.
 ret={n['id']:n for n in result['root/5']['nodes']};re=set(map(tuple,result['root/5']['edges']))
 assert any(v.get('$type')=='questGameTimeDelay_ConditionType' and v['days']==2 for v in walk(ret[83]));checks+=1
 assert ret[63]['type']['factName']=='mq007_skippy_owner_known' and ret[63]['type']['value']==1;checks+=1
 assert {(13,'Out',10,'In'),(10,'Out',66,'In'),(66,'Out',62,'In')}<=re;checks+=1
 assert ret[10]['$type']=='questRewardManagerNodeDefinition' and ret[66]['type']['factName']=='mq007_done';checks+=1
 # No pickup / mode conversation resource exists in this bounded closure.
 assert not any('mq007_01_gun_found.scene' in str(g) or 'mq007_03_skippy_about_killing.scene' in str(g) for g in result.values());checks+=1
 boot={g['path']:g for g in graphs(out/'mq007_resume_boot.json')};n={v['id']:v for v in boot['root']['nodes']}
 parent={g['path']:g for g in graphs(ROOT/(s['native_source'].replace('/raw/','/json/')+'.json'))};pn={v['id']:v for v in parent['root']['nodes']}
 for i in s['selected_nodes']:
  expected=copy.deepcopy(pn[i])
  if i==21:expected['phaseResource']['DepotPath']['$value']=s['resume_depot']
  assert n[i]==expected,i;checks+=1
 for p,g in parent.items():
  if p!='root' and int(p.split('/')[1]) in s['selected_nodes']:assert boot[p]==g,p;checks+=len(g['nodes'])
 assert set(n)==set(s['selected_nodes'])|set(range(1000,1012))|{1100,1101};checks+=1
 expected={tuple(e) for e in s['native_edges'] if e[0]!=0 and e[2]!=21}
 expected|={(0,'Out',1000,'In'),(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'True',1003,'In'),(1002,'False',1009,'In'),(1003,'Out',1004,'In'),(1004,'True',1005,'Active'),(1005,'Out',1006,'In'),(1006,'Out',1007,'In'),(1004,'False',1007,'In'),(1007,'Out',1008,'In'),(1008,'False',1009,'In'),(1010,'Out',1011,'In'),(1100,'True',1101,'In'),(1100,'False',1009,'In'),(1101,'Out',1010,'In')}
 expected|={(1008,'True',e[2],e[3]) for e in s['native_edges'] if e[0]==0}
 expected|={(e[0],e[1],1100,'In') for e in s['native_edges'] if e[2]==21}
 expected|={(1101,'Out',21,e[3]) for e in s['native_edges'] if e[2]==21}
 assert set(map(tuple,boot['root']['edges']))==expected;checks+=1
 assert n[1001]['condition']==n[1002]['condition'] and n[1007]['condition']==n[1008]['condition']==n[1100]['condition'];checks+=2
 jt=n[1005]['type'];assert jt['path']['realPath']==s['root'] and jt['sendNotification']==0 and jt['trackQuest']==0
 assert set(jt)=={'$type','optional','path','sendNotification','trackQuest','version'};checks+=2
 for i,v in n.items():
  if i not in s['selected_nodes'] and v['$type']=='questFactsDBManagerNodeDefinition':
   assert v['type']['factName'].startswith(s['tag']+'_') and v['type']['value']==1 and v['type']['setExactValue']==1;checks+=1
 f=dict(m['common'])|s['facts_equal']|{s['tag']+'_Permit':1,s['tag']+'_Issued':0,s['tag']+'_Finished':0,s['tag']+'_Fault':0,s['tag']+'_RootReactivated':0}
 js={v['path']:STATES[v['states'][0]] for v in s['journals']};g=n[1001]['condition'];ack=n[1007]['condition']
 assert ev(g,f,js);cases+=1
 for k,v in f.items():
  if k.endswith('_RootReactivated'):continue
  for wrong in [None,-1,0,1,2,11,51,95,999]:
   assert ev(g,f|{k:wrong},js)==(wrong==v),(k,wrong);cases+=1
 for row in s['journals']:
  for state in [None,'Inactive','Active','Succeeded','Failed','Unknown']:
   assert ev(g,f,js|{row['path']:state})==(state in [STATES[v] for v in row['states']]);cases+=1
 for inv in [0,1,2]:assert ev(g,f,js,inv)==(inv>=1);cases+=1
 af=f|{s['tag']+'_Issued':1,s['tag']+'_Permit':0}
 assert ev(ack,af,js);assert not ev(ack,af,js|{s['root']:'Active'});assert ev(ack,af|{s['tag']+'_RootReactivated':1},js|{s['root']:'Active'});cases+=3
 for k,v in s['facts_equal'].items():assert not ev(ack,af|{k:v+1},js);cases+=1
 cf=f|capture()[s['id']]['facts'];cj={j['path']:j['state'] for j in capture()[s['id']]['journals']}
 assert ev(g,cf,cj);assert not ev(g,cf|{s['history_confirmation_fact']:0},cj);assert not ev(g,cf|{'PTFRS23_MQ007_Issued':1},cj);cases+=3
 # Fresh and progressed routes are mutually exclusive before any ownership write.
 fresh=next(x for x in spec['owners'] if x['tag']=='PTFRS23_MQ007')
 assert fresh['facts_equal']['mq007_skippy_50_enemies_defeated']==0 and s['facts_equal']['mq007_skippy_50_enemies_defeated']==1;cases+=1
 assert fresh['facts_equal']['mq007_skippy_enemies_total']==0 and s['facts_equal']['mq007_skippy_enemies_total']==95;cases+=1
 return {'status':'PASS_CONFIRMED_SKIPPY_SEAM_LIVE_PENDING','component_sha256':sha(out/'manifest.json'),'tester_sha256':sha(Path(__file__)),'native_payload_checks':checks,'policy_cases':cases,'reused_proof':oldtests,'resources':10,'boots':9,'history_default_protected':True,'native_progress_resets':False,'live_pending':['Skippy original return reveal after native delay','Regina delivery interaction and chosen outcome/reward once','gun mode/counter preservation','save/reload']}

if __name__=='__main__':print(json.dumps(verify(Path(sys.argv[1])),indent=2))
