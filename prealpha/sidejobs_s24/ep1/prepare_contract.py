"""Native-source fresh admissions; no post-Tower progress inferred from absence."""
import hashlib,json,sys
from pathlib import Path
from inspect import graphs,value,walk,read
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
NATIVE=ROOT/'research/sidejobs_s24/ep1/native_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def journal_catalog(path):
 d=read(path);handles={x['HandleId']:x['Data'] for x in walk(d) if 'HandleId' in x and 'Data' in x};out={}
 def visit(w,p):
  n=w.get('Data',handles.get(w.get('HandleRefId'),w));k=n.get('id','');p=p+([k] if k else [])
  if n.get('$type','').startswith('gameJournal'):out['/'.join(p)]=n['$type']
  for child in n.get('entries',[]):visit(child,p)
 visit(d['Data']['RootChunk']['entry'],[]);return out
def dep_refs(path):
 return {value(x['DepotPath']) for x in walk(read(path)) if 'DepotPath' in x and isinstance(value(x['DepotPath']),str) and value(x['DepotPath']).endswith(('.questphase','.scene'))}
def closure(main):
 todo={main};seen={}
 while todo:
  depot=todo.pop()
  if depot in seen:continue
  matches=list(NATIVE.parent.glob('native_*/json/'+depot.replace('\\','/')+'.json'))
  p=matches[0] if matches else NATIVE/'json'/(depot.replace('\\','/')+'.json')
  if not p.exists():raise ValueError('Missing native dependency '+depot)
  seen[depot]=p
  if depot.endswith('.questphase'):todo |= dep_refs(p)-set(seen)
 return seen
common=read(ROOT/'prealpha/sidejobs_s23/ep1/contract.json')['common_equal']
catalog={};pins={}
for family in ('base','ep1'):
 rel=f'research/sidejobs_s24/ep1/native_02/json/{family}/journal/cooked_journal.journal.json'
 catalog.update(journal_catalog(ROOT/rel));pins[rel]=sha(ROOT/rel)
 rawrel=rel.replace('/json/','/raw/')[:-5];pins[rawrel]=sha(ROOT/rawrel)
contacts={'MQ306_FRESH':'contacts/trainer_fred','Q304_FRESH':'ep1/contacts/dan_taylor'}
for path in contacts.values():assert catalog[path]=='gameJournalContact',(path,catalog.get(path))
owners=[];audits=[]
rows=[
 ('mq305_combat_zone_report','MQ305_FRESH','ep1\\quest\\minor_quests\\mq305\\mq305.questphase','mq305_',[],['contacts/mr_hands/mq305'],{}),
 ('mq306_dumpster','MQ306_FRESH','ep1\\quest\\minor_quests\\mq306\\mq306.questphase','mq306_',['mq306_active'],['contacts/trainer_fred/mq306_hook','contacts/trainer_fred/mq306','ep1/contacts/aaron/mq306','ep1/contacts/aaron/mq306_hook'],{'PTFRS23_MQ306_Issued':0}),
 ('q304_car_retrieval','Q304_FRESH','ep1\\quest\\main_quests\\q304\\phases\\q304_car_retrieval.questphase','q304_car_retr',[],['ep1/contacts/dan_taylor/q304_car_retrieval'],{'PTFRS22_Q304_Issued':0}),
]
for id,key,main,prefix,passive,sms,old in rows:
 deps=closure(main);facts=set()
 for depot,p in deps.items():
  for n in walk(read(p)):
   for k,v in n.items():
    val=value(v)
    if k in ('factName','factName1','factName2') and isinstance(val,str) and val.startswith(prefix):facts.add(val)
 # Additional native aliases are explicit, not unrelated main-quest prerequisites.
 if key=='MQ306_FRESH':facts|={'aaron_scanned','ma306_03_cut_damir_nervous','mq306_testdef'}
 if key=='Q304_FRESH':facts|={'q304_first_track_at_the_end_of_spline','q304_retrofix_56524_on'}
 eq={k:0 for k in sorted(facts-set(passive))};eq.update(old)
 # Current busy flags only; never historical start/end equality.
 for flag in ['holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance']:
  eq[flag]=0
 if key=='MQ305_FRESH':
  for direction in ('mr_hands_calls_v','v_calls_mr_hands'):
   for suffix in ('start_activate','end_activate','active','started'):eq['holo_'+direction+'_'+suffix]=0
 root='ep1/quests/minor_quest/'+id
 core={'gameJournalQuest','gameJournalQuestPhase','gameJournalQuestObjective','gameJournalQuestDescription'}
 rootrows=[{'path':p,'class':c,'states':[1]} for p,c in catalog.items() if c in core and (p==root or p.startswith(root+'/'))]
 assert rootrows and any(x['class']=='gameJournalQuest' for x in rootrows)
 smsrows=[{'path':p,'class':c,'states':[1]} for p,c in catalog.items() if any(p==s or p.startswith(s+'/') for s in sms)]
 assert smsrows
 owner={'id':id,'key':key,'tag':'PTFRS24_'+key,'depot':'towercontinued\\sidejobs_s24\\ep1\\'+key.lower()+'_boot.questphase','entry':'In1','facts_equal':eq,'fact_ranges':{k:{'min':0,'max':1} for k in passive},'journals':rootrows+smsrows,'reactivate_paths':[],'native_only_guards':[],'native_main':main,'native_dependencies':list(deps),'phone_dependencies':['existing U9 Mr Hands controller and global phone cleanup'] if key=='MQ305_FRESH' else ['native SMS journals; no new holo controller'],'old_owner_guards':old,'contact':contacts.get(key),'route':'Original native parent gate and entry; all stock gameplay, calls, timing, choices, rewards and cleanup retained. No direct journal or native progress reset.'}
 if key=='MQ306_FRESH':owner['passive_init_audit']={'mq306_active':'Original main node30 exact-set1 before intro setup invitation delay; root33/cleanup exact-set0. Original scene does not enter until journal started. Allow0..1 only; all other progress0 and complete quest/SMS subtree Inactive.'}
 if key=='Q304_FRESH':
  owner['vehicle_not_available']='Vehicle.v_sport1_quadra_sport_r7_netrunner'
  owner['native_only_guards']=['NOT VehicleAvailable(SpecificVehicle Vehicle.v_sport1_quadra_sport_r7_netrunner); stock reward at main node291.']
 if key=='MQ305_FRESH':owner['parent_slice']={'source':'ep1\\quest\\minor_quests\\ep1_minor_quests.questphase','graph':'root','ids':[8,12,14,27,6],'entry':8,'socket':'In'}
 elif key=='MQ306_FRESH':owner['parent_slice']={'source':'ep1\\quest\\minor_quests\\ep1_minor_quests.questphase','graph':'root','ids':[8,7],'entry':8,'socket':'In'}
 else:owner['parent_slice']={'source':'ep1\\quest\\ep1_persistent_content.questphase','graph':'root/30','ids':[6],'entry':6,'socket':'In1'}
 owners.append(owner)
 audits.append({'id':id,'fresh_facts':len(eq),'fresh_journals':len(rootrows+smsrows),'native_dependencies':len(deps),'contact':contacts.get(key),'unsupported':'Any Active/Failed/Succeeded root, non-Inactive descendant, nonzero progress, used prior owner or unknown journal defers. Existing partial owners remain untouched.'})
out={'schema':'S24_EP1_FRESH_CONTRACT_1','common_equal':common,'owners':owners,'source_pins':pins,'policy':'New routes only restore R4-whitelisted unstarted jobs. All previous owners/progress unchanged. Current post-Tower evidence is not certified pre-Tower history. Runtime checks must resolve every journal; unknown defers.','audit':audits}
revision=sys.argv[sys.argv.index('--revision')+1] if '--revision' in sys.argv else '01'
assert revision.isdigit() and len(revision)==2
dest=HERE/('contract.json' if revision=='01' else 'contract'+revision+'.json')
assert not dest.exists()
dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audits,indent=2))
