"""S24 fresh-only contracts. Old capture supplies a catalogue, NEVER fresh state."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23'))
from audit import graphs,walk,value
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
CAP='research/sidejobs_s23/live_20261016_01/capture.json'
PARENT='research/sidejobs_s2/sacrum_audit/native_01/raw/base/quest/minor_quests/minorquests.questphase'
jobs={j['id']:j for j in load(ROOT/CAP)['first']['jobs']}
CATALOG='research/sidejobs_s24/ep1/native_02/json/base/journal/cooked_journal.journal.json'
def journal_catalog():
 d=load(ROOT/CATALOG);h={x['HandleId']:x['Data'] for x in walk(d) if 'HandleId' in x and 'Data' in x};result={};todo=[(d['Data']['RootChunk']['entry'],[])]
 while todo:
  w,p=todo.pop();n=w.get('Data',h.get(w.get('HandleRefId'),w));k=n.get('id','');p=p+([k] if k else [])
  result['/'.join(p)]=n.get('$type');todo.extend((v,p) for v in n.get('entries',[]))
 return result
catalog=journal_catalog();excluded_refs=[]
specs=[
 ('MQ010','mq010_barry','Happy Together',1,'mq010/mq010.questphase','research/sidejobs_s24/base/native_01',[],[54,80,55,1],
  [[54,'Out',80,'In'],[80,'Out',55,'In'],[55,'Out',1004,'In']],54,1),
 ('MQ019','mq019_paparazzi','Violence',38,'mq019/mq019_paparazzi.questphase','research/sidejobs_s24/base/native_01',['LIZZY'],[54,80,55,171,133,94,38],
  [[54,'Out',80,'In'],[80,'Out',55,'In'],[55,'Out',171,'In'],[171,'False',133,'In1'],[133,'Out1',94,'In'],[94,'Out',1004,'In']],54,38),
 ('MQ015','mq015_wizardbook','Spellbound',36,'mq015/mq015_wizardbook.questphase','research/sidejobs_s23/native_01',['R3NO'],[54,80,55,78,153,152,174,134,36],
  [[54,'Out',80,'In'],[80,'Out',55,'In'],[55,'Out',78,'In'],[78,'Out',153,'In'],[153,'Out',152,'In'],[152,'Out',174,'In'],[174,'False',1004,'In'],[134,'Out',36,'In1']],54,134),
]
owners=[];pins={CAP:sha(ROOT/CAP),PARENT:sha(ROOT/PARENT),CATALOG:sha(ROOT/CATALOG)}
for key,id,title,parent,phase,base,phone,nodes,edges,start,issue_target in specs:
 job=jobs[id]
 # Current branch completed all three; it is a negative protection control.
 assert job['rootState']=='Succeeded'
 fs={k:0 for k in job['facts'] if k.startswith(key.lower()+'_')}
 ranges={}
 if key=='MQ015':
  # Original minorquests node134 sets exact1 before the hook; passive owner
  # initialization alone is not acceptance. Every objective remains Inactive.
  fs.pop('mq015_active');ranges['mq015_active']={'min':0,'max':1}
  fs['web_smugglers_cache_treasures']=0;fs['sq015_sellar_keepalive']=0
 elif key=='MQ019':
  fs.update({k:0 for k in job['facts'] if k.startswith('holo_v_calls_lizzy_')})
 journals=[{'path':j['path'],'class':j['class'],'states':[1]} for j in job['journals']]
 source=base+'/raw/base/quest/minor_quests/'+phase
 localpins={source:sha(ROOT/source)}
 # Record all actual current phase/scene dependencies for the final byte audit.
 folder=ROOT/base/'raw/base/quest/minor_quests'/key.lower()
 closure=[]
 phone_journals={}
 for path in sorted(folder.rglob('*')):
  if path.is_file() and path.suffix in ('.questphase','.scene') and not any(x in path.parts for x in ('versions','test')):
   rel=path.relative_to(ROOT).as_posix();localpins[rel]=sha(path);closure.append(rel)
   jp=ROOT/(rel.replace('/raw/','/json/')+'.json')
   localpins[jp.relative_to(ROOT).as_posix()]=sha(jp)
   for obj in walk(load(jp)):
    name=str(value(obj.get('factName','')))
    if name.startswith(key.lower()+'_') and name not in ranges:fs[name]=0
    pathref=obj.get('realPath','')
    if (key=='MQ019' and pathref.startswith('contacts/lizzy_wizzy/') and pathref!='contacts/lizzy_wizzy/reveal') or (key=='MQ015' and pathref.startswith(('contacts/nix/mq015','contacts/seller/mq015'))):
     cls=value(obj['className'])
     if catalog.get(pathref)==cls:phone_journals[pathref]={'path':pathref,'class':cls,'states':[1]}
     else:
      assert pathref=='contacts/nix/mq015_01_contact_details/mq015_02_ch_got_it' and pathref not in catalog,(pathref,cls,catalog.get(pathref))
      excluded_refs.append({'path':pathref,'class':cls,'reason':'Stale native graph reference absent from actual current cooked journal. Not a valid live admission guard; native gameplay unchanged.'})
 journals+=list(sorted(phone_journals.values(),key=lambda x:x['path']))
 contact_copy=None
 if key=='MQ019':
  contact_copy={'source':base+'/raw/base/quest/minor_quests/mq019/phases/mq019_05_holocall.questphase','graph':'root/8','id':9,'path':'contacts/lizzy_wizzy'}
 elif key=='MQ015':
  contact_copy={'source':'research/q307_extracted/raw/ep1/quest/ep1.questphase','graph':'root/12/37','id':10,'path':'contacts/nix'}
 if contact_copy:
  for rel in (contact_copy['source'],contact_copy['source'].replace('/raw/','/json/')+'.json'):localpins[rel]=sha(ROOT/rel)
 pins.update(localpins)
 owners.append({'id':id,'ids':[id],'title':title,'key':key,'tag':'PTFRS24_'+key,
  'depot':'towercontinued\\sidejobs_s24\\base\\'+key.lower()+'.questphase','facts_equal':dict(sorted(fs.items())),
  'fact_ranges':ranges,'journals':journals,'reactivate_paths':[],
  'native_source':source,'native_depot':'base\\quest\\minor_quests\\'+phase.replace('/','\\'),
  'parent_node':parent,'parent_nodes':nodes,'parent_edges':edges,'parent_start':start,'issue_target':issue_target,
  'input':'In1','phone_dependencies':phone,'sourcepins':localpins,'native_closure':closure,'contact_copy':contact_copy,
  'seam':'Original unstarted quest entry only; root and every catalogued child Inactive, local progress zero. No reset or saved-progress inference.',
  'capture_control_state':'Succeeded','passive_initialization':{'mq015_active':'0 or 1; exact1 is written by original parent node134 before hook.'} if key=='MQ015' else {}})
result={'schema':1,'status':'SOURCE_IMPLEMENTATION_NOT_LIVE_PROOF','capture_catalogue':CAP,'capture_sha256':sha(ROOT/CAP),
 'policy':'Whitelisted unstarted side jobs only. Existing S23/S22 routes preserved. Current completed roots are negative controls, not fresh fixtures.',
 'owners':owners,'source_pins':pins,'excluded_invalid_native_journal_refs':excluded_refs,'deferred':[
 {'id':'mq026_conspiracy','reason':'Existing S23 exact captured-progress owner can become eligible as a new fresh owner progresses; defer overlapping fresh owner without modifying preserved S23 ownership.'}]}
out=HERE/'contract03.json'
if out.exists():raise RuntimeError('Contract exists')
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'owners':len(owners),'source_pins':len(pins),'contract':str(out)}))
