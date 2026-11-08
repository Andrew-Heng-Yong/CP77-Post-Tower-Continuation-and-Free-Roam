"""Pin QR3 successor and initialize coordinator-owned dynamic work ledger."""
from pathlib import Path
import sys,datetime,shutil
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,snapshot,tree_metadata
assert not (O/'progress.json').exists(),'Fresh QR4 checkpoint required'
P=W/'prealpha/quest_restoration_qr3';q=read(P/'queue.json');m=read(P/'candidate_01/package_manifest.json');reb=read(P/'candidate_01/rebuild_01.json')
assert q['deep_reviewed_count']==16 and len(q['quests'])==q['selected_count']==161
hashes={r['depot']:r['sha256'] for r in reb['resources']};assert len(hashes)==1574
old=read(P/'protection_before.json');files=[Path(p) for p in old['files']]+[p for p in P.rglob('*') if p.is_file()]
pins=snapshot(files);changed=[p for p,r in old['files'].items() if pins.get(p,{}).get('sha256')!=r['sha256']]
assert not changed,changed
game=read(P/'prepared.json')['game']
write(O/'prepared.json',{'game':game,'predecessor':str(P),'working_source':str(P/'candidate_01'),'installed':'PH3 unchanged','scope':'Q02/Q03 primary; Q04 stretch; sourceconfirmed repairs only; no deployment'})
write(O/'protection_before.json',{'files':pins,'game_metadata':tree_metadata(game),'save_root':old['save_root'],'save_metadata':tree_metadata(old['save_root'])})
write(O/'source_epoch_00.json',{'epoch':0,'candidate':str(P/'candidate_01'),'predecessor_manifest_sha256':sha(P/'candidate_01/package_manifest.json'),'source_resources':hashes,'package_files':m['files'],'archive_sha256':m['archive_sha256'],'qr3_repairs':read(P/'approved_changes_02.json'),'scope':'Frozen investigation baseline. Root will version subsequent repairs; workers never mutate this input.'})
items={r['id']:r for r in q['quests']};by=lambda b:[r['id'] for r in q['quests'] if r['batch']==b]
g={
 'G01':['mq025_02_kabuki','mq025_03_arroyo','mq025_05_glen','mq025_07_fight_club'],
 'G02':['sq025_delamain','sq025_compensation','sq025_0_pickup','sq025c05_scared','sq025c07_suicidal'],
 'G03':['mq024_sandra','mq010_barry','mq015_wizardbook','mq019_paparazzi'],
 'G04':[i for i in by('Q03') if i.startswith('sq024_')],
 'G05':['sq_q001_wakako','sq_q001_wilson','mq011_wilson','mq012_stud'],
 'G06':['mq005_alley','mq013_punks','mq002_veterans'],
 'G07':[i for i in by('Q03') if i.startswith('sq025c') and i not in ['sq025c05_scared','sq025c07_suicidal']],
 'G08':['mq007_smartgun','mq008_party','mq021_guide']}
assert sum(map(len,g.values()))==len(set(i for ids in g.values() for i in ids))==32
assert {i for ids in g.values() for i in ids}==set(by('Q02')+by('Q03'))
stretch=by('Q04')
for n in range(4):g[f'G{9+n:02}']=stretch[n*4:(n+1)*4]
groups={k:{'ids':ids,'titles':[items[i]['title'] for i in ids],'batches':sorted({items[i]['batch'] for i in ids}),'status':'CLAIMED' if k in ['G01','G02','G03'] else 'UNCLAIMED','worker':{'G01':'qr4_worker_a','G02':'qr4_worker_b','G03':'qr4_worker_c'}.get(k),'epoch':0,'output':str(O/'groups'/k),'review':None,'dependencies':['G02 sharedcore'] if k=='G07' else []} for k,ids in g.items()}
write(O/'progress.json',{'status':'IN_PROGRESS','primary_target':32,'stretch_target':48,'predecessor_deep':16,'worker_capacity':3,'capacity_basis':'Developer exposes4concurrency slots including coordinator;threeworkerpool saturated. Reuse threads to avoid QR3distinctthreadcap.','groups':groups,'completed_quests':[],'new_defects':[],'repair_epochs':[str(O/'source_epoch_00.json')],'events':[{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':'STARTED_THREE_WORKERS_G01_G02_G03'}]})
shutil.copyfile(Path(r'C:\Users\Ayong\.codex\attachments\1c23b6af-1f16-487e-82f7-250c19ebc854\Pasted text.txt'),O/'REQUEST.md')
print({'protected_hashes':len(pins),'groups':len(groups),'primary':32,'stretch':len(stretch),'epoch':0,'source':'QR3 successor;not installedPH3'})
