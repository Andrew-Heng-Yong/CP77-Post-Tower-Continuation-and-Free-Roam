from pathlib import Path
import json,sys,re,hashlib,copy
H=Path(__file__).resolve().parent;W=H.parent.parent;N=H/'native_01';C=H/'candidate_01'
sys.path.insert(0,str(W/'tools'))
from review_stock_shark_u2 import graph
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks=[]
def ck(name,value):
 assert value,name
 checks.append(name)
def g(path):return graph(str(path.relative_to(W)))['root']
def nodes(gr):return {n['id']:n for n in gr['nodes']}
inv=read(H/'research_01/inventory.json')
def src(archive,dep):
 rows=[r for r in inv if Path(r['archive']).name==archive and r['depot']==dep];assert len(rows)==1
 return W/(rows[0]['raw']+'.json')
def output(dep):return N/'readback'/(dep.replace('\\','_')+'.json')
dep=r'towercontinued\sidejobs_s23\base_b\mq038.questphase'
before=g(src('0000_TowerContinued_SideJobs_S23.archive',dep));after=g(output(dep));bn=nodes(before);an=nodes(after)
ck('MQ038 all original IDs and edges retained',bn.keys()==an.keys() and before['edges']==after['edges'])
for i in bn:
 if i!=1003:ck('MQ038 unchanged node '+str(i),bn[i]==an[i])
expected=copy.deepcopy(bn[1003]);expected['condition']['conditions'].append({'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRJD1_Dennis_Issued','value':1}})
ck('MQ038 sole edit is handler dependency at existing wait',expected==an[1003])
dep=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
before=g(src('00000000_TowerContinued_SideJobs_S29.archive',dep));after=g(output(dep));bn=nodes(before);an=nodes(after)
ck('cleanup only adds three nodes',set(an)-set(bn)=={1300,1301,1302} and not set(bn)-set(an))
for i in bn:ck('cleanup preserves old node '+str(i),bn[i]==an[i])
expected=[];reroutes=0
for e in before['edges']:
 e=e.copy()
 if e[0] in (1255,1210,1211) and e[2]==6:e[2:]=[1300,'In'];reroutes+=1
 expected.append(e)
expected += [[1300,'False',6,'In2'],[1300,'True',1301,'In'],[1301,'False',6,'In2'],[1301,'True',1302,'In13'],[1302,'Out13',6,'In2']]
ck('cleanup retains original routes with one appended owned contact',reroutes==3 and sorted(expected)==sorted(after['edges']))
native=nodes(g(src('basegame_4_gamedata.archive',r'base\quest\holocalls\holocall_cleanup.questphase')))
for old,new in [(439,1301),(303,1302)]:
 n=copy.deepcopy(native[old]);n['id']=new;ck('original Dennis cleanup payload '+str(old),n==an[new])
phone=nodes(g(output(r'towercontinued\judy_dennis_jd1\dennis_phone.questphase')))
native=nodes(g(src('basegame_4_gamedata.archive',r'base\quest\holocalls\holocall_initializers.questphase')))
ck('original Dennis controller with unchanged input',phone[106]==native[106])
ck('admission rechecked before once-only receipt',phone[1002]['condition']==phone[1003]['condition'])
component=read(N/'component.json');base=component['common'].copy()
def evaluate(c,facts,state):
 t=c['$type']
 if t=='questLogicalCondition':
  values=[evaluate(x,facts,state) for x in c['conditions']]
  return all(values) if c['operation']=='AND' else any(values)
 if t=='questFactsDBCondition':
  c=c['type'];assert c['comparisonType']=='Equal';return facts.get(c['factName'],0)==c['value']
 if t=='questJournalCondition':return state==c['type']['state']
 raise AssertionError(t)
def admission(facts,state):return evaluate(phone[1002]['condition'],facts,state)
fresh=base|{'PTFRS23_MQ038_Permit':1};active=base|{'PTFRS23_MQ038_Issued':1,'PTFRS23_MQ038_Entered':1}
ck('fresh valid owner can bootstrap before native start',admission(fresh,'Inactive'))
ck('existing active owner can receive missing handler',admission(active,'Active'))
ck('pending native call request remains admissible',admission(active|{'holo_dennis_calls_v_start_activate':1},'Active'))
ck('unowned active quest is not admitted',not admission(base,'Active'))
ck('fresh permission cannot restart an already active quest',not admission(fresh,'Active'))
for state in ['Succeeded','Failed']:
 ck('terminal journal preserved '+state,not admission(active,state) and not admission(fresh,state))
for fact,value in [('mq038_done',1),('PTFRS23_MQ038_Fault',1),('PTFRS23_MQ038_Finished',1),('PTFRJD1_Dennis_Issued',1),('holo_setup_active',1),('holo_setup_started',1),('holo_interrupt_call',1),('holo_dennis_calls_v_end_activate',1),('q307_active',1),('q307_done',0),('q307_main_game_killed',0),('PostTowerFreeRoamActive',0)]:
 ck('admission refuses '+fact,not admission(active|{fact:value},'Active') and not admission(fresh|{fact:value},'Inactive'))
written=[n['type']['factName'] for n in phone.values() if n['$type']=='questFactsDBManagerNodeDefinition']
ck('bootstrap only writes its own receipts',set(written)=={'PTFRJD1_Dennis_Ready','PTFRJD1_Dennis_Issued'})
ck('no official resources overridden',all(d.startswith('towercontinued\\') for d in component['resources']))

# Compare compiled output against the current installed framework/PTFR baseline.
B=W/'diagnostics/equipmentex_20261025_01/candidate_01/compile_01/compiled.script';A=C/'compile_03/compiled.script'
def classes(p):
 s=p.read_text(encoding='utf-8-sig');out={}
 for m in re.finditer(r'(?m)^(?:(?:public|abstract|native|importonly|final) )*class ([\w.$]+)[^{\n]*\{',s):out[m.group(1)]=s[m.start():s.index('\n}',m.end())+2]
 return out
def canonical(s):
 s=re.sub(r'\b(wrapper|proxy)\$\d+',r'\1$GENERATED',s);s=s[:s.rfind('\n}')]
 starts=[m.start() for m in re.finditer(r'(?m)^  [^\n]*\bfunc ',s)]
 return (s[:starts[0]].strip(),sorted(s[a:b].strip() for a,b in zip(starts,starts[1:]+[len(s)]))) if starts else s
bc=classes(B);ac=classes(A);allowed={'Door','DoorControllerPS','JudysDoor','PTFR.Housing.HousingPurchaseUI'}
ck('only expected new compiled class',set(ac)-set(bc)=={'PTFR.Housing.JudyDoorJD1'} and not set(bc)-set(ac))
for name in bc:
 if name not in allowed:ck('unchanged compiled '+name,canonical(bc[name])==canonical(ac[name]))
 old=re.findall(r'(?m)^  .*persistent.*;$',bc[name]);new=re.findall(r'(?m)^  .*persistent.*;$',ac[name])
 if name=='DoorControllerPS':new=[x for x in new if 'judyJD1OwnLock' not in x]
 ck('old persistent fields preserved '+name,old==new)
before=(Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\r6\scripts\TowerContinued_Housing_H1\HousingPurchase.reds')).read_text(encoding='utf-8-sig')
after=(C/'package/r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds').read_text(encoding='utf-8-sig')
ck('purchase source only adds one door tick',after.replace('    JudyDoorJD1.Tick(game);\n','')==before)
s=(H/'JudyDoorJD1.reds').read_text()
ck('door script has no quest facts/payment/item operations',not re.search(r'\b(SetFact|GiveItem|RemoveItem|Purchase\()',s))
ck('door exact private path excludes street and bedroom',s.count('{sq026_dvc_judys_door_apartment}')==1 and 'door_main_front' not in s and 'door_bedroom' not in s)
ck('native open setter and both visual door implementations guarded',s.count('@wrapMethod(DoorControllerPS)')==3 and '@wrapMethod(JudysDoor)' in s and '@wrapMethod(Door)' in s)
result={'status':'PASS_OFFLINE_NOT_GAMEPLAY','count':len(checks),'checks':checks,'component_sha256':sha(N/'component.json'),'compiled_sha256':read(C/'compile_03/result.json')['compiled_sha256'],'baseline_compiled_source_sha256':sha(B),'limitations':['Native phone callback and existing-save wait resumption require live testing.','Judy door placement, animation, egress and reload require live testing.']}
p=N/'tests_01.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
