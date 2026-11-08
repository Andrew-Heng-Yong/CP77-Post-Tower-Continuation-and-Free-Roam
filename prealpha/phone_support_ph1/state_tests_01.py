from model import *
H=Path(__file__).resolve().parent;C=H/'candidate_03';b=read(C/'build_01.json');checks=[]
def evaluate(c,f,journal=True):
 t=c['$type']
 if t=='questLogicalCondition':
  v=[evaluate(x,f,journal) for x in c['conditions']];return all(v) if c['operation']=='AND' else any(v)
 if t in ('questFactsDBCondition','questJournalCondition'):return evaluate(c['type'],f,journal)
 if t=='questJournalEntryState_ConditionType':return journal
 if t=='questVarComparison_ConditionType':
  a=f.get(c['factName'],0);v=c['value'];return {'Equal':a==v,'Greater':a>v,'Less':a<v,'GreaterOrEqual':a>=v,'LessOrEqual':a<=v,'NotEqual':a!=v}[c['comparisonType']]
 raise AssertionError(t)
def test(name,ok):
 assert ok,name
 checks.append(name)
for con in b['contracts']:
 c=model(C/(con['depot'].replace('\\','_')+'.json'))['root']['nodes'][2]['condition'];s=con['source'];f=dict(con['guard']);tag=con['tag'];f[tag+'_Issued']=0
 if s['job']:
  p='PTFRU9_'+s['job']+'_';f.update({p+'Permit':1,p+'Fault':0,p+'Started':0})
  test(tag+' fresh',evaluate(c,f))
  f.update({p+'Permit':0,p+'ParentEntered':1,p+'Started':1,p+'MainFinished':0,p+'OwnerFinished':0})
  test(tag+' active pending call',evaluate(c,f))
  for suffix in ['MainFinished','OwnerFinished','Fault']:
   q=dict(f);q[p+suffix]=1;test(tag+' refuse '+suffix,not evaluate(c,q))
 else:
  site='NIX' if con['contact']=='nix' else 'VIKTOR';p='PTFRB0S4'+site+'_';f.update({p+'Ready':1,p+'Enabled':1,p+'OwnerActive':1,p+'Excluded':0})
  test(tag+' restored service',evaluate(c,f))
  q=dict(f);q[p+'OwnerActive']=0;test(tag+' no service owner',not evaluate(c,q))
  q=dict(f);q[p+'Excluded']=1;test(tag+' excluded service',not evaluate(c,q))
 for key,val in list(con['guard'].items())+[(tag+'_Issued',0)]:
  q=dict(f);q[key]=0 if val else 1;test(tag+' guard '+key,not evaluate(c,q))
 test(tag+' nonTower journal',not evaluate(c,f,False))
 for flag in ['holo_interrupt_call','holo_interrupt_call_manual','holo_active_call_interrupted','holo_interrupt_braindance']:
  q=dict(f);q[flag]=1;test(tag+' unfinished-call interruption '+flag,evaluate(c,q))
 for stage in ['start_activate','end_activate','start_done','end_done']:
  q=dict(f);q['holo_'+con['contact']+'_calls_v_'+stage]=1;test(tag+' preserve pending '+stage,evaluate(c,q))
out={'status':'PASS_SCOPED_ADMISSION_AND_PENDING_CALL_CASES','checks':len(checks),'details':checks,'limitation':'Structural condition evaluation; does not simulate engine scheduling or saved phase restoration.'}
(C/'state_tests_01.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(checks))
