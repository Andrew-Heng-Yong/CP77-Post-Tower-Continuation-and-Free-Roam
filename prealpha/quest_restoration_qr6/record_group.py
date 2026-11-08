"""Coordinator-only pinning and integration of completed, independently reviewed groups."""
from pathlib import Path
import sys,argparse,copy,datetime
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
STAGES={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
STATUSES={'PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','LIVE_ONLY','FAIL'}
ap=argparse.ArgumentParser();ap.add_argument('--group',required=True);ap.add_argument('--review');ap.add_argument('--reviewer');ap.add_argument('--adjudication',action='append',default=[]);a=ap.parse_args()
p=read(O/'progress.json');g=p['groups'][a.group];rp=O/'groups'/a.group/'results.json';r=read(rp);assert set(r['quest_ids'])==set(g['ids'])
if g.get('result_sha256'):assert g['result_sha256']==sha(rp),'Frozen result drift; explicit successor evidence required'
findings=[];pins={str(rp):sha(rp)}
for x in r['quest_results']:
 fp=Path(x['contracts']);h=sha(fp);assert h==x['contracts_sha256'];d=read(fp);assert d['quest_id']==x['quest_id']and set(d['contracts'])==STAGES
 for stage,v in d['contracts'].items():
  assert v['status']in STATUSES and v.get('proven')and v.get('evidence'),(d['quest_id'],stage)
  for ev in v['evidence']:
   if isinstance(ev,str)and ev not in pins and Path(ev).is_file():pins[ev]=sha(ev)
 pins[str(fp)]=h;findings.append({'id':x['quest_id'],'contracts':str(fp),'sha256':h})
assert set(x['id']for x in findings)==set(g['ids'])and len(findings)==len(g['ids'])
for fp in r.get('tests_paths',[])+r.get('source_pin_paths',r.get('source_pins_paths',[])):
 assert Path(fp).is_file()
 if fp not in pins:pins[fp]=sha(fp)
g.update(status='INVESTIGATED_AWAITING_REVIEW',result=str(rp),result_sha256=sha(rp),findings=findings,investigation_input_pins=pins,reported_check_events=r.get('total_checks',r.get('checks')),reported_mutation_events=r.get('mutations'))
if a.review:
 assert a.reviewer and a.reviewer!=g['worker'],'Independent worker required'
 review=Path(a.review).resolve();rv=read(review);assert review.is_file();resolution=[]
 for z in a.adjudication:
  z=Path(z).resolve();assert z.is_file();resolution.append({'path':str(z),'sha256':sha(z)})
 # Acceptance is explicitly selected by coordinator only after reviewing actual
 # peer findings and any corrections; this utility does not infer source parity.
 g.update(status='REVIEWED_WITH_LIMITS',review={'path':str(review),'sha256':sha(review),'reviewer':a.reviewer},adjudications=resolution)
 q=read(O/'queue.json');e=read(q['source_epoch_manifest'])
 for f in findings:
  item=next(x for x in q['quests']if x['id']==f['id']);orig=read(f['contracts']);item['contracts']=copy.deepcopy(orig['contracts'])
  for stage,v in item['contracts'].items():v.update(findings_source=f['contracts'],findings_source_sha256=f['sha256'],original_findings_source=f['contracts'],original_findings_source_sha256=f['sha256'],source_epoch_investigated='QR6:00 (byte-identical QR5:08)',effective_source_epoch='QR6:'+str(e['epoch']).zfill(2),independent_review=str(review),independent_review_sha256=sha(review))
  item.update(status='DEEP_REVIEWED_WITH_STATIC_LIMITS',finding_source_epoch='QR6:00',effective_source_epoch='QR6:'+str(e['epoch']).zfill(2),review=str(review),review_sha256=sha(review),fully_static_verified=all(v['status']in ['PASS','APPROVED_DEVIATION']for v in item['contracts'].values()),QR6_group=a.group)
 old=set(q['retained_QR5_deep_reviewed_ids']);new={i for gg in p['groups'].values()if gg['status']=='REVIEWED_WITH_LIMITS'for i in gg['ids']}
 q.update(deep_reviewed_ids=[x['id']for x in q['quests']if x['id']in old|new],deep_reviewed_count=len(old|new),new_investigated_count=len(new),pending_review_ids=[i for gg in p['groups'].values()if gg['status']=='INVESTIGATED_AWAITING_REVIEW'for i in gg['ids']],static_verified_count=sum(bool(x.get('fully_static_verified'))for x in q['quests']),checkpoint_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 write(O/'queue.json',q)
p['events'].append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'group':a.group,'state':g['status'],'review':g.get('review')});write(O/'progress.json',p)
print({'group':a.group,'state':g['status'],'quests':len(g['ids']),'evidence_files_pinned':len(pins)})
