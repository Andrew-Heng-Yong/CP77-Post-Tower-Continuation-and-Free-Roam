"""Generate an explicit fresh-only service contract, never infer freshness from save bytes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cap=load(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')
job=next(j for j in cap['second']['jobs'] if j['id']=='sq_q001_wakako')
source='research/sidejobs_s24/services/native_01/raw/base/quest/main_quests/prologue/q001/phases/q101_wakako_reward.questphase'
contact='research/sidejobs_s24/services/native_01/raw/base/quest/main_quests/prologue/q001/q001.questphase'
native=load(ROOT/(source.replace('/raw/','/json/')+'.json'))
journals=[{'path':j['path'],'class':j['class'],'states':[1]} for j in job['journals']]
for p in ('contacts/wakako_okada/sq_q001_reward/sq_q001_msg_reward_01','contacts/wakako_okada/sq_q001_reward/sq_q001_msg_reward_02'):
 journals.append({'path':p,'class':'gameJournalPhoneMessage','states':[1]})
owner={
 'id':'sq_q001_wakako','ids':['sq_q001_wakako'],'title':'The Gig','key':'THEGIG','tag':'PTFRS24_THEGIG',
 'depot':'towercontinued\\sidejobs_s24\\services\\the_gig_fresh.questphase',
 'facts_equal':{'q001_wakako_reward_given':0,'sq_q001_active':0,'sq_q001_done':0,'sq_q001_add_reward':0,
  'PTFRS22_SQ_Q001_Issued':0,'PTFRS22_SQ_Q001_Finished':0,'PTFRS22_SQ_Q001_Fault':0,
  'PTFRFO1_wakako_Issued':1,'PTFRB0STCASSIUS_Ready':1,'PTFRB0STCASSIUS_Enabled':1,
  'PTFRB0STCASSIUS_Excluded':0,'PTFRB0ST_Suspended':0,'PTFRBASE_Suspended':0},
 'fact_ranges':{'q001_done':{'min':1,'max':2147483647},'q101_enable_side_content':{'min':1,'max':2147483647},
  'wakako_default_on':{'min':1,'max':2147483647},'wat_nid_ripperdoc_01_default_on':{'min':1,'max':2147483647}},
 'journals':journals,'reactivate_paths':[],
 'native_source':source,'native_depot':'base\\quest\\main_quests\\prologue\\q001\\phases\\q101_wakako_reward.questphase',
 'contact_source':contact,'contact_source_node':168,'contact_target':'contacts/wakako_okada',
 'sourcepins':{source:sha(ROOT/source),contact:sha(ROOT/contact)},
 'seam':'Only wholly Inactive journal/objectives and undelivered reward SMS; all local cash/reward state untouched. Original q101_wakako_reward entry, not the main q001 root.',
 'notes':['Existing FO1 full Wakako default scene supplies the original cash dialogue; existing B0 Cassius full service supplies trade.',
  'Native contact-list operation copied from q001 node168, changing only contact path from Dex to Wakako. No phone controller or actor restart.',
  'Original reward graph has no failure path or Failed journal write. After native activation its Active root blocks old S22 admission until completion; cash0 also blocks old S22 before activation.',
  'Tyger tattoo acquisition remains native. This component does not grant/equip items or change the existing cyberware restriction policy.',
  'Current captured The Gig is Active with cash already earned and is protected, not a fresh fixture.']}
out={'schema':1,'status':'FRESH_SOURCE_IMPLEMENTATION_NOT_LIVE_PROOF','policy':'Unstarted R4 only; preserve all prior restored branches and partial progress. No pre-Tower history certificate fabricated.','owners':[owner],
 'deferred':{'sq_q001_wilson':'Requires reintroducing quest choices in B0 Wilson reduced native shop scene plus cooperative lease with MQ011. No changes made.',
 'mq045_victor_debt':'B0 Viktor deliberately excludes debt-choice routes. Needs a separate scene/ownership integration, not journal activation.',
 'sq018_jackie':'Needs Mama Welles contact/controller and coordinated native Misty/Viktor/Padre/Pepe/Coyote ownership. Main native owner copy alone is insufficient.'}}
p=HERE/'contract.json'
if p.exists():raise RuntimeError('Contract already exists')
p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'contract':str(p),'owners':1,'protected_current_state':job['rootState']}))
