"""Prepare the unopened, previously prepared KOLD entry correction; no game writes."""
from pathlib import Path
import copy
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
WS=HERE.parents[1]
BASELINE=WS/'prealpha/mid_quest_resume_retire_20261115_01/stage_08/deployment_01/installed_manifest_01.json'
BASE_SHA='902D8E432D7BEBA074080C3B66578EE80D9920063292F222CBFAB25EE484C270'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
DEPOT=r'towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase'
COMPILE=WS/'prealpha/mid_quest_resume_retire_20261115_01/stage_06/compile/assessment.json'
TAG='PTFRS29_mq016_bartmoss_'
sys.path.insert(0,str(WS/'prealpha/quest_restoration_qr13'))
from resource_edit import Edit

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def plain(p):
 for q in (Path(p),*Path(p).parents):
  if q.exists():assert not q.is_symlink() and not q.stat().st_file_attributes&0x400,q
def baseline():
 assert sha(BASELINE)==BASE_SHA
 b=read(BASELINE);game=Path(b['game_root'])
 for r in b['core_files']+b['required_files']:
  p=game/r['path'];plain(p);assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],p
 return b
def main():
 b=baseline()
 capture=read(HERE/'work/sources_01/providers.json')
 donor_capture=read(HERE/'work/sources_02/providers.json')
 for h in capture['hits']+donor_capture['hits']:
  assert sha(h['raw'])==h['sha256'] and sha(h['json'])==h['json_sha256']
 entry,=[h for h in capture['hits'] if h['depot']==DEPOT]
 donor,=[h for h in donor_capture['hits'] if h['depot']==r'base\quest\minor_quests\mq042\phases\mq042_nomad_01_hook.questphase']
 ed=Edit(copy.deepcopy(read(entry['json'])))
 native=Edit(read(donor['json']))
 lock=native.node(native.graph('root'),43)['condition']
 assert native.r.d(native.r.d(lock)['type'])=={'$type':'questContentLock_ConditionType','isContentBlocked':0}
 root=ed.graph('root');wait=ed.node(root,196);outer=ed.r.d(wait['condition'])
 assert outer['operation']=='AND' and len(outer['conditions'])==2
 original=outer['conditions'][0]
 assert ed.r.d(ed.r.d(original)['type'])=={'$type':'questContentToken_ConditionType','type':'MinorQuestAndSts'}
 # Revalidate the existing admission contract at the saved wait, changing only
 # the receipt from unissued to issued. No stage or reward is restarted.
 prepared=ed.clone(ed.node(root,65004)['condition'],ed.r)
 guard=prepared['Data'];assert guard['operation']=='AND'
 changed=0
 for h in guard['conditions']:
  d=h['Data']
  if d['$type']=='questFactsDBCondition' and d['type']['Data']['factName']==TAG+'Issued':
   assert d['type']['Data']['value']==0
   d['type']['Data']['value']=1;changed+=1
 assert changed==1
 guard['conditions'] += [ed.fact('mq016_active',1),ed.clone(lock,native.r)]
 fresh=ed.logic('AND',[ed.fact('mq016_active',0),ed.clone(original,ed.r)])
 # Prepared branch comes first. The active=0 arm retains the original token.
 outer['conditions'][0]=ed.logic('OR',[prepared,fresh])
 out=HERE/'work/graph_01';out.mkdir()
 write(out/'edited.json',ed.ordered())
 packed=read(WS/'prealpha/mid_quest_resume_retire_20261115_01/stage_03/pack/readback.json')
 assert packed['archive_sha256']==b['archive_sha256'] and len(packed['members'])==1748
 members={r['depot']:r['sha256'] for r in packed['members']}
 assert members[DEPOT]==entry['sha256']
 write(HERE/'work/inputs.json',dict(status='PREPARED',baseline=str(BASELINE),baseline_sha256=BASE_SHA,
  game=b['game_root'],archive_sha256=b['archive_sha256'],archive_source=b['archive_source'],members=members,
  root=entry|{'path':entry['raw']},donor=donor,edited=str(out/'edited.json'),edited_sha256=sha(out/'edited.json'),
  source_inventory_sha256=sha(HERE/'work/sources_01/providers.json'),donor_inventory_sha256=sha(HERE/'work/sources_02/providers.json'),
  changed_nodes=[196],preserved='All nodes, edges, prefab ownership, receipts, scripts, XL, native downstream gameplay and rewards',
  game_writes=0,save_writes=0))
 print('Prepared one private wait correction; untouched starts retain MinorQuestAndSts.')
if __name__=='__main__':main()
