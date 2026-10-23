"""Produce capture-bound component contracts, not inferred fresh history."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
CAP=ROOT/'research/sidejobs_s23/live_20261016_01/capture.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
capture=json.loads(CAP.read_text(encoding='utf-8-sig'))
assert capture['repeatedReadMatched'] is True
jobs={j['id']:j for j in capture['first']['jobs']}
families=[
 ('MQ013',['mq013_punks'],17,'mq013/mq013.questphase',['mq013_','std_arr_foodshop_03_','sq024_mq013_'],None),
 ('MQ030',['mq030_melisa'],18,'mq030/mq030.questphase',['mq030_','cct_dtn_cloth_01_'],'ZAN'),
 ('MQ011',['mq011_wilson'],15,'mq011/mq011.questphase',['mq011_','holo_wilson_','wat_lch_gunsmith_01_','wilson_shooting_'],'WV'),
 ('MQ038',['mq038_neweridentity'],11,'mq038/mq038.questphase',['mq038_'],None),
 ('MQ037',['mq037_brendan','mq037_brendan_dumpster','mq037_brendan_hooligan001'],34,'mq037/mq037_brendan.questphase',['mq037_','hey_rey_techstore_01_'],None),
 ('MQ049',['mq049_edgerunners'],64,'mq049/mq049.questphase',['mq049_'],None),
 ('MQ026',['mq026_conspiracy'],39,'mq026/mq026.questphase',['mq026_','mq027_50_prophet','mq027_5_prophet','mq018_'],None),
]
rows=[]
for key,ids,node,phase,prefixes,lease in families:
 fs={};js=[]
 for id in ids:
  job=jobs[id]
  assert job['rootState']=='Inactive'
  fs.update({k:v for k,v in job['facts'].items() if any(k.startswith(p) for p in prefixes)})
  for j in job['journals']:
   assert j['state']=='Inactive',(id,j)
   js.append({'path':j['path'],'class':j['class'],'states':[1]})
 source=('research/sidejobs_s23/native_01' if key=='MQ026' else 'research/activity_state_r3/native_sources')+'/raw/base/quest/minor_quests/'+phase
 rows.append({'id':ids[0],'ids':ids,'key':key,'tag':'PTFRS23_'+key,'depot':'towercontinued\\sidejobs_s23\\base_b\\'+key.lower()+'.questphase',
  'facts_equal':dict(sorted(fs.items())),'fact_ranges':{},'journals':js,'reactivate_paths':[],
  'native_source':source,'native_depot':'base\\quest\\minor_quests\\'+phase.replace('/','\\'),'parent_node':node,'input':'In1',
  'service_lease':lease,'phone_dependencies':['WILSON'] if key=='MQ011' else [],
  'seam':'Captured all journal entries Inactive; native original entry preserves exact local initializer/background facts. Other progress states are not erased.',
  'sourcepins':{source:sha(ROOT/source)}})
out={'schema':1,'status':'SOURCE_IMPLEMENTATION_NOT_LIVE_PROOF','capture':str(CAP.relative_to(ROOT)).replace('\\','/'),'capture_sha256':sha(CAP),
 'policy':'Current whitelist Failed OR Inactive; these seven bounded native-entry seams admit observed Inactive states only. No generic partial restart.',
 'owners':rows,'existing_owners_unchanged':['mq005_alley','mq032_sacrum']}
p=HERE/'contract.json'
if p.exists():raise RuntimeError('Contract already exists; revise explicitly with apply_patch')
p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'owners':len(rows),'roots':sum(len(x['ids']) for x in rows),'contract':str(p),'sha256':sha(p)}))
