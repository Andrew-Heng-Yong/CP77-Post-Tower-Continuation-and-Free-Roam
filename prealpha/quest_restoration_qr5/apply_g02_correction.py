"""Apply independently approved G02 supersession without changing originals."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
cp=O/'groups/G13/corrections/G02_SPR01/verification_02/correction.json';c=read(cp);rp=O/'groups/G10/reviews/G02_correction_01.json';r=read(rp)
assert r['status'].startswith(('PASS','APPROVE')),r['status']
assert sha(c['original'])==c['original_sha256']and sha(c['corrected'])==c['corrected_sha256']
q=read(O/'queue.json');rows=read(O/'contract_status_matrix.json');item=next(x for x in q['quests']if x['id']=='sts_hey_spr_01');original=read(c['original']);corrected=read(c['corrected'])
for stage,v in corrected['contracts'].items():
 v['original_proven']=copy.deepcopy(original['contracts'][stage]['proven']);v['original_status']=original['contracts'][stage]['status'];v['source_correction']={'path':str(cp),'sha256':sha(cp),'independent_review':str(rp),'independent_review_sha256':sha(rp)};v['findings_source']=c['corrected'];v['findings_source_sha256']=c['corrected_sha256'];v['original_evidence_base']=str(Path(c['original']).parent);v['evidence'] += [str(cp),str(rp)]
item['contracts']=corrected['contracts'];item['source_correction']=corrected['contracts']['communications']['source_correction'];item['remaining']=[{'contract':k,'status':v['status'],'item':s}for k,v in item['contracts'].items()for s in v.get('remaining',[])]
for row in rows:
 if row['quest_id']==item['id']:row.update(copy.deepcopy(item['contracts'][row['stage']]))
issues=read(O/'review_issues.json');issue=next(x for x in issues['issues']if x['id']=='QR5-G02-SPR01-OUTGOING-CALL');issue['status']='CLOSED_EXPLICIT_SUPERSESSION_NO_RUNTIME_CHANGE';issue['correction']=item['source_correction'];issue['current_communications_status']='CONDITIONAL';write(O/'review_issues.json',issues)
write(O/'queue.json',q);write(O/'contract_status_matrix.json',rows)
progress=read(O/'progress.json');progress['groups']['G02']['review_addendum_applied']=item['source_correction'];write(O/'progress.json',progress)
print({'status':'APPLIED_APPROVED_G02_OUTGOING_CALL_SUPERSESSION','communications':'CONDITIONAL','runtime_changes':0})
