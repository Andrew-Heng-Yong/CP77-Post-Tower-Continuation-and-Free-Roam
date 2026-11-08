from model import *
import copy,itertools
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_03'
b=read(C/'build_01.json');inv=read(W/'diagnostics/phone_restoration_preparation_20261029_01/current_01/inventory.json')
rows={r['depot']:r for r in inv['resources']};checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
def current(dep):return model(C/(dep.replace('\\','_')+'.json'))
def native(dep):return model(rows[dep]['json'])
def stripid(n):return {k:v for k,v in n.items() if k!='id'}
cleanup='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
old=model(C/('before_'+cleanup.replace('\\','_')+'.json'));new=current(cleanup)
for gp,g in old.items():
 check('cleanup old nodes '+gp,all(new[gp]['nodes'][i]==n for i,n in g['nodes'].items()))
 expected=[(a,s,1400,'In') if t==6 and d=='In2' and gp=='root' else (a,s,t,d) for a,s,t,d in g['edges']]
 check('cleanup preserved edges '+gp,all(e in new[gp]['edges'] for e in expected))
for ix,c in enumerate(b['contracts']):
 dep=c['depot'];g=current(dep)['root'];s=c['source'];init=native(s['native_initializer_bindings'][0]['depot'])['root']['nodes'][c['init_node']]
 check('native initializer '+c['contact'],stripid(g['nodes'][10])==stripid(init))
 check('scoped wrapper '+c['contact'],len(g['nodes'])==6 and len(g['edges'])==6)
 writes=[x for i,n in g['nodes'].items() if i!=10 for x in walk(n) if x.get('$type')=='questSetVar_NodeType']
 check('only owned receipt writes '+c['contact'],all(x['factName'] in [c['tag']+'_Ready',c['tag']+'_Issued'] and x['value']==1 for x in writes))
 conditions=list(walk(g['nodes'][2]['condition']))
 facts={x['factName']:x['value'] for x in conditions if x.get('$type')=='questVarComparison_ConditionType'}
 check('no interruption deadlock '+c['contact'],not any(k.startswith('holo_interrupt') or k=='holo_active_call_interrupted' for k in facts))
 check('persistent claim '+c['contact'],facts[c['tag']+'_Issued']==0 and (4,'Out',10,next(e[3] for e in g['edges'] if e[0]==4)) in g['edges'])
 check('Tower journal proof '+c['contact'],any(x.get('$type')=='questJournalEntryState_ConditionType' and x['state']=='Succeeded' and x['path']['realPath']=='ep1/quests/main_quest/q307_before_tomorrow' for x in conditions))
 src=native(s['cleanup_integration']['source']);base=1400+ix*3
 check('native cleanup counter '+c['contact'],stripid(new['root']['nodes'][base+1])==stripid(src['root']['nodes'][c['cleanup_condition']]))
 check('native cleanup payload '+c['contact'],stripid(new['root']['nodes'][base+2])==stripid(src['root']['nodes'][c['cleanup_phase']]))
 if c['contact'] in ('mark_bana','janet'):
  check('nested cleanup edges '+c['contact'],new['root/'+str(base+2)]['edges']==src['root/'+str(c['cleanup_phase'])]['edges'])
 else:check('service/gig external cleanup '+c['contact'],'phaseResource'in new['root']['nodes'][base+2])
for job in ['sts_ep1_08','sts_std_arr_06','sts_std_arr_12']:
 dep='towercontinued\\native_gigs_u9\\'+job+'_entry.questphase';o=model(C/('before_'+dep.replace('\\','_')+'.json'));n=current(dep)
 for gp,g in o.items():
  check('entry nodes preserved '+job+gp,all(n[gp]['nodes'][i]==v for i,v in g['nodes'].items()))
  if gp!='root':check('entry nested edges preserved '+job+gp,n[gp]['edges']==g['edges'])
  else:
   changed=[e for e in g['edges'] if e[0]==65001];assert len(changed)==1
   expected=[(a,s,64999,'In') if a==65001 else (a,s,t,d) for a,s,t,d in g['edges']]+[(64999,'Out',changed[0][2],changed[0][3])]
   check('entry readiness only '+job,set(expected)==set(n[gp]['edges']))
# Original controllers are infrastructure under both native retirement routes.
base=model(C/'base_quest_cyberpunk2077.questphase.json');q=model(C/'ep1_quest_main_quests_q307_q307.quest.json');ep=model(C/'ep1_quest_ep1.questphase.json')
check('base root terminates after Tower success',base['root']['nodes'][107]['type']=='Terminating' and (106,'Out',109,'In') in base['root']['edges'] and (109,'Out',107,'In') in base['root']['edges'])
check('alternate initialization cut',all(e in q['root']['edges'] for e in [(16,'Out',18,'In'),(18,'Out',17,'In'),(17,'CutSource',6,'CutDestination')]))
check('alternate cut contains both initializers',all(any(n.get('phaseResource',{}).get('DepotPath',{}).get('$value')==d for n in q['root/6']['nodes'].values()) for d in ['base\\quest\\holocalls\\holocall_initializers.questphase','ep1\\quest\\holocalls\\holocall_initializers_ep1.questphase']))
check('EP1 cut precedes killed receipt',all(e in ep['root/10']['edges'] for e in [(8,'Out',9,'In'),(9,'Out',10,'In'),(9,'CutSource',3,'CutDestination'),(9,'CutSource',4,'CutDestination'),(9,'CutSource',5,'CutDestination')]))
out={'status':'PASS_NATIVE_BINDINGS_AND_SERIALIZED_OWNER','checks':len(checks),'details':checks,'runtime_gameplay':'UNVERIFIED','saved_owner_liveness':'No public runtime query; admission uses completed Tower journal plus audited original retirement ancestry and restored context; receipts prevent repeat issue.'}
(C/'semantic_verification_01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='details'}))


