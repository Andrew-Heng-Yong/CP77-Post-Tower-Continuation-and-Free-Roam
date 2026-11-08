"""Coordinator-only progress updates; workers cannot claim or overwrite work."""
from pathlib import Path
import sys,argparse,datetime
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
pa=argparse.ArgumentParser();pa.add_argument('action',choices=['complete','claim','review']);pa.add_argument('group');pa.add_argument('--worker');pa.add_argument('--review');args=pa.parse_args()
p=read(O/'progress.json');g=p['groups'][args.group]
if args.action=='complete':
 assert g['status']=='CLAIMED',g['status']
 evidence=[]
 for i in g['ids']:
  f=O/'groups'/args.group/'quests'/i/'contracts.json';d=read(f);assert len(d['contracts'])==10
  for k,v in d['contracts'].items():assert v.get('proven') and v.get('evidence') and v.get('status'),(i,k)
  evidence.append({'id':i,'contracts':str(f),'sha256':sha(f)})
 g['status']='INVESTIGATED_AWAITING_REVIEW';g['findings']=evidence
 p['completed_quests']=sorted(set(p['completed_quests'])|set(g['ids']))
elif args.action=='claim':
 assert g['status']=='UNCLAIMED' and args.worker,g
 g['status']='CLAIMED';g['worker']=args.worker
elif args.action=='review':
 assert g['status']=='INVESTIGATED_AWAITING_REVIEW' and args.review
 r=Path(args.review);assert r.is_file()
 g['review']={'path':str(r.resolve()),'sha256':sha(r)};g['status']='REVIEWED_WITH_LIMITS'
if args.action in ['complete','review']:
 q=read(O/'queue.json');matrix=read(O/'contract_status_matrix.json')
 for i in g['ids']:
  f=O/'groups'/args.group/'quests'/i/'contracts.json';d=read(f)
  item=next(x for x in q['quests'] if x['id']==i)
  item['contracts']=d['contracts'];item['group']=args.group;item['source_epoch']=g['epoch'];item['finding_path']=str(f);item['finding_sha256']=sha(f)
  item['status']='DEEP_REVIEWED_WITH_STATIC_LIMITS' if args.action=='review' else 'DEEP_INVESTIGATED_PENDING_INDEPENDENT_REVIEW'
  for row in matrix:
   if row['quest_id']==i:
    v=d['contracts'][row['stage']];row.update({'status':v['status'],'proven':v['proven'],'remaining':v.get('remaining',[]),'approved_differences':v.get('approved_differences',[]),'evidence':v['evidence'],'findings_source':str(f),'review_state':g['status']})
 reviewed={i for group in p['groups'].values() if group['status']=='REVIEWED_WITH_LIMITS' for i in group['ids']}
 q['deep_reviewed_ids']=list(dict.fromkeys(q['deep_reviewed_ids']+sorted(reviewed)));q['deep_reviewed_count']=len(q['deep_reviewed_ids']);q['pending_review_ids']=sorted(set(p['completed_quests'])-reviewed);q['new_investigated_count']=len(p['completed_quests'])
 write(O/'queue.json',q);write(O/'contract_status_matrix.json',matrix)
p['events'].append({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':args.action.upper(),'group':args.group,'worker':g['worker']})
write(O/'progress.json',p)
print({'group':args.group,'status':g['status'],'new_quest_investigations':len(p['completed_quests']),'primary_done':sum(i in p['completed_quests'] for k,v in p['groups'].items() if int(k[1:])<=8 for i in v['ids']),'stretch_done':sum(i in p['completed_quests'] for k,v in p['groups'].items() if int(k[1:])>8 for i in v['ids'])})
