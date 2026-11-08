"""Publish the QR2 successor queue; never overwrite QR1 evidence or game files."""
from pathlib import Path
import sys,datetime,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
OLD=W/'prealpha/quest_restoration_qr1'
assert not (O/'queue.json').exists(), 'Preserve completed queue checkpoint'
queue=read(OLD/'queue.json');oldrows=read(OLD/'contract_status_matrix.json')
ids=['mq045_victor_debt','mq038_neweridentity','mq035_ozob']
findings={i:read(O/'quests'/i/'contracts.json') for i in ids}
keys=list(queue['quests'][0]['contracts'])
adapters={'completion':'completion_rewards_cleanup'}
assert len(keys)==10
review_paths={'mq045_victor_debt':O/'reviews/paid_in_full.json','mq038_neweridentity':O/'reviews/big_in_japan.json','mq035_ozob':O/'reviews/send_in_clowns.json'}
rows=[];diffs=[];counts=collections.Counter()
for q in queue['quests']:
 if q['id'] not in findings:continue
 f=findings[q['id']];source=O/'quests'/q['id']/'contracts.json'
 normalized={adapters.get(k,k):v for k,v in f['contracts'].items()}
 assert set(normalized)==set(keys),(q['id'],set(normalized),set(keys))
 assert review_paths[q['id']].is_file(),str(review_paths[q['id']])
 for k,v in normalized.items():
  assert v['status'] in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY']
  assert v.get('proven') and v.get('evidence'),(q['id'],k)
  counts[v['status']]+=1
  v['findings_source']=str(source);v['findings_source_sha256']=sha(source)
  v['review']=str(review_paths[q['id']]);v['review_sha256']=sha(review_paths[q['id']])
  for text in v.get('approved_differences',[]):
   diffs.append({'quest_id':q['id'],'contract':k,'difference':text,'source':str(source),'source_sha256':sha(source),'new_in_qr2':False,'authority':'Root AGENTS.md invariants2-5; PROJECT restoration policy; existing source-pinned donor contracts cited by quest findings','evidence':v['evidence']})
 q['contracts']=normalized;q['status']='DEEP_REVIEWED_WITH_STATIC_LIMITS'
 q['deep_review']=str(source);q['deep_review_sha256']=sha(source)
 q['review']=str(review_paths[q['id']]);q['defects']=f.get('defects',[]);q['repairs']=f.get('repairs',f.get('runtime_repairs',[]))
 q['tests'] += [{'path':str(source),'scope':'QR2 ten-contract source/native route investigation; exact focused test paths in findings'},{'path':str(O/'ancestor_review.json'),'scope':'Fresh native parent containment/termination and provider input checks'}]
 q['remaining']=[{'contract':k,'status':v['status'],'item':x} for k,v in normalized.items() for x in v.get('remaining',[])]
 q['fully_static_verified']=all(v['status'] in ['PASS','APPROVED_DEVIATION'] for v in normalized.values())
for row in oldrows:
 q=next(q for q in queue['quests'] if q['id']==row['quest_id'])
 if q['id'] in findings:
  v=q['contracts'][row['stage']]
  row['prior_status']=row['status'];row['status']=v['status'];row['proven']=v['proven'];row['approved_differences']=v.get('approved_differences',[]);row['remaining']=v.get('remaining',[]);row['evidence']=v['evidence'];row['findings_source']=v['findings_source'];row['review']=v['review']
 rows.append(row)
# CSV records share an explicit union schema; unchanged QR1 rows remain intact.
fields=list(dict.fromkeys(k for r in rows for k in r))
flat=[{k:r.get(k) for k in fields} for r in rows]
queue['checkpoint_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
queue['predecessor_queue']=str(OLD/'queue.json');queue['predecessor_queue_sha256']=sha(OLD/'queue.json')
queue['deep_reviewed_ids']=ids
queue['deep_reviewed_count']=len(ids)
queue['static_verified_count']=sum(bool(q.get('fully_static_verified')) for q in queue['quests'])
queue['completed_count']=queue['static_verified_count'];queue['gameplay_repairs']=sum(len(q['repairs']) for q in queue['quests'])
remaining_q01=[{'id':q['id'],'title':q['title']} for q in queue['quests'] if q['batch']=='Q01' and q['id'] not in ids]
assert len(queue['quests'])==queue['selected_count'] and len(rows)==len(queue['quests'])*10
write(O/'queue.json',queue);write(O/'contract_status_matrix.json',rows);csvwrite(O/'contract_status_matrix.csv',flat)
write(O/'quest_status_matrix.json',queue['quests'])
quest_fields=list(dict.fromkeys(k for r in queue['quests'] for k in r))
csvwrite(O/'quest_status_matrix.csv',[{k:r.get(k) for k in quest_fields} for r in queue['quests']])
write(O/'intentional_differences.json',{'scope':'Existing adaptations reviewed in this batch; no new runtime differences','differences':diffs})
write(O/'checkpoint.json',{'state':'Q01_FIRST_THREE_DEEP_REVIEWED_WITH_STATIC_LIMITS','baseline':read(O/'inputs.json')['baseline'],'queue':str(O/'queue.json'),'queue_sha256':sha(O/'queue.json'),'previous':str(OLD/'checkpoint.json'),'investigated':ids,'contract_status_counts':dict(counts),'static_verified_count':queue['static_verified_count'],'runtime_repairs':queue['gameplay_repairs'],'remaining_Q01':remaining_q01,'next':remaining_q01[0],'full_scope_quests':queue['selected_count'],'not_deep_reviewed':queue['selected_count']-len(ids),'package_created':False,'restrictions':'No deployment, game launch, saves/facts, releases or publication','required_reuse':'QR1 131-source compile, 1574-payload reproduction and38 controls remain pinned; no unchanged baseline build was repeated'})
print({'investigated':len(ids),'contracts':dict(counts),'static_verified':queue['static_verified_count'],'remaining_Q01':len(remaining_q01)})
