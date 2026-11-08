"""QR3 checkpoint only; no game APIs, builds or installed-file writes."""
from pathlib import Path
import sys,datetime,shutil
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,snapshot,tree_metadata
assert not (O/'protection_before.json').exists(),'Pinned checkpoint exists'
old=W/'prealpha/quest_restoration_qr2';prior=read(old/'protection_before.json')
files=[Path(p) for p in prior['files']]+[p for p in old.rglob('*') if p.is_file()]
assert all(p.is_file() for p in files),'Required predecessor input missing'
snap=snapshot(files)
changes=[p for p,r in prior['files'].items() if snap[p]['sha256']!=r['sha256']]
prep=read(old/'prepared.json');game=Path(prep['game'])
write(O/'prepared.json',{'game':str(game),'predecessor':str(old),'scope':'Remaining13 Q01 deep investigations, independent reviews, source-confirmed repairs only; no deployment'})
write(O/'protection_before.json',{'files':snap,'game_metadata':tree_metadata(game),'save_root':prior['save_root'],'save_metadata':tree_metadata(prior['save_root'])})
queue=read(old/'queue.json');assert queue['selected_count']==161 and queue['deep_reviewed_count']==3
assignment={
 'agent_a':['07_nc_underground'],
 'agent_b':['mq046_cave_vehicle','mq047_ad_vehicle'],
 'agent_c':['mq037_brendan','mq037_brendan_hooligan001'],
 'agent_d':['mq041_corpo','mq044_jakes_vehicle','mq049_edgerunners'],
 'agent_e':['mq030_melisa','mq032_sacrum','mq026_conspiracy'],
 'agent_f':['mq025_06_pacifica','mq025_psycho_brawl']}
target={q['id'] for q in queue['quests'] if q['batch']=='Q01'}-set(queue['deep_reviewed_ids'])
assert target=={i for ids in assignment.values() for i in ids}
write(O/'assignments.json',{'worker_concurrency':3,'coordinator':1,'waves':[['agent_a','agent_b','agent_c'],['agent_d','agent_e','agent_f']],'assignments':assignment,'required_quests':len(target),'protected_hashes':len(snap)})
cap=read(old/'provider_readback_01/capture.json');now={str(p.resolve()):p for p in (game/'archive/pc').rglob('*.archive')};arcchanges=[]
for r in cap['archives']:
 p=now.get(str(Path(r['path']).resolve()))
 ts=datetime.datetime.fromisoformat(r['mtime_utc'].replace('Z','+00:00'))
 if p is None or p.stat().st_size!=r['bytes'] or abs(p.stat().st_mtime-ts.timestamp())>0.000002:arcchanges.append(r['path'])
new=set(now)-{str(Path(r['path']).resolve()) for r in cap['archives']}
write(O/'shared_evidence_index.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'predecessor_queue':{'path':str(old/'queue.json'),'sha256':sha(old/'queue.json')},'changed_prior_protected_inputs':changes,'archive_metadata_delta':arcchanges,'new_archives':sorted(new),'scope':'Metadata/input equivalence and reuse pointers only; not a repeated provider census or independent payload-hash proof for all game archives','reuse':{n:{'path':str(old/n),'sha256':sha(old/n)} for n in ['ancestor_review.json','reuse_validation.json','provider_readback_01/capture.json','EVIDENCE.json','review_resolutions.json']},'new_provider_work':'Only newly investigated missing/ambiguous sources if needed; each agent pins actual native and PH3 bytes','baseline':'PH3; installed unchanged by QR3'})
source=Path(r'C:\Users\Ayong\.codex\attachments\158416ad-7408-4797-ba63-10e91faba55a\Pasted text.txt')
shutil.copyfile(source,O/'REQUEST.md')
print({'protected_hashes':len(snap),'new_quests':len(target),'changed_old_inputs':len(changes),'archive_metadata_changes':len(arcchanges),'new_archives':len(new)})
