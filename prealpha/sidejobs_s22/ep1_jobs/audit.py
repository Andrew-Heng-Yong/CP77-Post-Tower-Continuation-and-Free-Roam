"""Build source-bound S22 EP1 adapter requirements and missing MQ306 detail."""
import json,re,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import walk,value
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def save(p,d):
 if p.exists():
  assert read(p)==d,str(p)+' is immutable'
  return
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def main():
 log=ROOT/'research/sidejobs_s22/live_20261015_01/scripting.log'
 text=log.read_text(encoding='utf-8-sig').split('FAILED q304_car_retrieval |')[-1].split('FAILED mq306_dumpster |')[0]
 journals=[{'path':p,'class':c,'state':int(s)} for p,c,s in re.findall(r'^J (.*?) \[(.*?)\]=(\d+)$',text,re.M)]
 facts={k:int(v) for k,v in re.findall(r'^F ([^=]+)=(-?\d+)$',text,re.M) if k not in ('air_traffic_off','q304_06_netrunners_car_parked_front')}
 assert len(journals)==20 and len([j for j in journals if j['state']==4])==3,(len(journals),journals)
 for j in journals:
  if j['state']==4:j['allowed_states']=[1,4]
 common=read(ROOT/'prealpha/sidejobs_s2/admission.json')['common_guards']
 spec={'id':'q304_car_retrieval','title':'Moving Heat','tag':'Q304','route':1,'status':'RESUME_ACCEPTED_SMS_FIRST_DOOR_ONLY',
  'depot':'towercontinued\\sidejobs_s22\\moving_heat_resume.questphase','entry':'In1','output':'Out1',
  'common_guard_equal':common,'guard_equal':facts,'journal_guards':journals,
  'reactivate':[j for j in journals if j['state']==4],
  'outside_triggers':['#q304_tr_car_retrieval_main_trigger','#q304_tr_car_retrieval_entire_garage'],
  'native_parent_gate_any':[{'q305_done':1,'comparison':'GreaterOrEqual'},{'q306_done':1,'comparison':'GreaterOrEqual'}],
  'runtime_preconditions':['ProfilePolicy complete and nonfaulted','BodyPolicy.Safe','settled journal and stable exact guards','owned Permit1/Issued0/Finished0/Fault0'],
  'journal_activation':'Only three exact Failed-or-Inactive entries become Active; no bulk operation or child reset. Recheck all 20 expected journal states and unchanged progress facts before child dispatch.',
  'preserved':['accepted SMS objective Succeeded','all phone messages and choices','started/active/accepted=1 unchanged','unstarted later objectives Inactive','original gameplay and future rewards'],
  'omitted_native_startup_nodes':[2,252,253],'source_log':str(log.relative_to(ROOT)),'source_log_sha256':sha(log),
  'not_supported':['later Moving Heat stages','actual prior reward/completion','generic other-state restart']}
 save(HERE/'admission.json',spec)
 # MQ306 was absent from R3's catalogue; native graph plus actual cooked tree
 # provides read-only details. Root Failed alone never picks a resume route.
 native=ROOT/'research/sidejobs_s22/ep1_jobs/native_02/json/ep1/quest/minor_quests/mq306'
 rawjournal=ROOT/'research/phase2b_p2/extracted/json/ep1/journal/cooked_journal.journal.json'
 obj=read(rawjournal); resource=SafeResource(obj)
 entries=[]
 def tree(wrapper,path):
  n=resource.d(wrapper)
  if not isinstance(n,dict):return
  ident=n.get('id','');here=path+('/'+ident if ident else '')
  if '/mq306_dumpster' in here: entries.append({'path':here.lstrip('/'),'class':n['$type']})
  for child in n.get('entries',[]):tree(child,here)
 tree(obj['Data']['RootChunk']['entry'],'')
 # Actual root folders are journal logical identifiers, not filenames.
 entries=[e for e in entries if e['class'] in ['gameJournalQuest','gameJournalQuestPhase','gameJournalQuestObjective','gameJournalQuestDescription']]
 assert entries and any(e['path']=='ep1/quests/minor_quest/mq306_dumpster' for e in entries),entries[:3]
 factset=set();refs=set();sources={};graphs={}
 for p in native.rglob('*.json'):
  d=read(p);sources[str(p.relative_to(ROOT))]=sha(p)
  factset.update(str(x['factName']) for x in walk(d) if 'factName' in x)
  refs.update(x['$value'] for x in walk(d) if x.get('$type')=='ResourcePath' and x.get('$storage')=='string' and x['$value'].endswith(('.scene','.questphase')))
  if p.name=='mq306.questphase.json':
   r=SafeResource(d);graphs={g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
 save(ROOT/'research/sidejobs_s22/ep1_jobs/mq306_details_01.json',{'id':'mq306_dumpster','status':'READ_ONLY_DETAIL_CATALOGUE_NO_RESUME_ADMISSION','journals':entries,'fact_names':sorted(factset),'source_pins':sources|{str(rawjournal.relative_to(ROOT)):sha(rawjournal)},'native_inputs':['In1','Intro','Expo','Ripper','Ending','Scavs'],'warning':'Alternate entry sockets include debug state mutations; do not select on root Failed or socket name alone. Current stage unknown.'})
 print(json.dumps({'moving_heat_journals':len(journals),'moving_heat_facts':len(facts),'mq306_journals':len(entries),'mq306_facts':len(factset)}))
if __name__=='__main__':main()
