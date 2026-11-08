"""Versioned pre-delivery A02 peer expansion; preserve exact earlier publication."""
from pathlib import Path
import sys,copy,shutil,re
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
S=O/'publication_supersession_01';assert not S.exists();S.mkdir()
names=['queue.json','progress.json','group_evidence_index.json','quest_status_matrix.json','quest_status_matrix.csv','contract_status_matrix.json','contract_status_matrix.csv','coverage.json','checkpoint.json','publication_01.json','REPORT.md','HANDOFF.md']
before={}
for name in names:
 f=O/name;shutil.copyfile(f,S/name);before[name]=sha(f);assert sha(S/name)==before[name]
q=read(O/'queue.json');orig=copy.deepcopy(q);p=read(O/'progress.json');ix=read(O/'group_evidence_index.json');rp=O/'groups/B01/reviews/A02/verification_03/review.json';rv=read(rp);old=p['groups']['A02']['review'];assert rv['group']=='A02'and rv['checks']==351 and not rv['issues']and rv['failures']==0
new={'path':str(rp),'sha256':sha(rp),'reviewer':'qr6_b'};assert sha(old['path'])==old['sha256'];p['groups']['A02']['review']=new;p['groups']['A02']['prior_bounded_review']=old
for x in q['quests']:
 if x['id']not in p['groups']['A02']['ids']:continue
 x.update(review=str(rp),review_sha256=sha(rp))
 for v in x['contracts'].values():v.update(independent_review=str(rp),independent_review_sha256=sha(rp))
for x in ix['groups']:
 if x['group']=='A02':x.update(review=new,prior_bounded_review=old)
ix['input_pins'][str(rp)]=sha(rp)
for x,y in zip(orig['quests'],q['quests']):
 assert x['id']==y['id']
 for k,v in x['contracts'].items():
  a={kk:vv for kk,vv in v.items()if kk not in ['independent_review','independent_review_sha256']};b={kk:vv for kk,vv in y['contracts'][k].items()if kk not in ['independent_review','independent_review_sha256']};assert a==b
write(O/'queue.json',q);write(O/'progress.json',p);write(O/'group_evidence_index.json',ix);write(O/'quest_status_matrix.json',q['quests'])
rows=[{'quest_id':x['id'],'title':x['title'],'stage':k,**copy.deepcopy(v),'review_state':x['status']}for x in q['quests']for k,v in x['contracts'].items()];write(O/'contract_status_matrix.json',rows)
for name,data in [('quest_status_matrix.csv',q['quests']),('contract_status_matrix.csv',rows)]:
 keys=list(dict.fromkeys(k for x in data for k in x));csvwrite(O/name,[{k:x.get(k)for k in keys}for x in data])
cov=read(O/'coverage.json');cov['queue_sha256']=sha(O/'queue.json');write(O/'coverage.json',cov)
# Cosmetic prose corrections occur before the independent final review. Only
# natural prose outside inline/fenced code is spaced; identifiers/hashes stay exact.
def prose_space(text):
 chunks=text.split('`')
 for i in range(0,len(chunks),2):
  s=chunks[i]
  s=re.sub(r'(?<=\d)(?=[a-z])',' ',s)
  s=re.sub(r'\b(All|all|new|previous|All|New|Only|only|all|prior|four|exact)(?=\d)',r'\1 ',s)
  s=re.sub(r'(?<=\d)(?=(?:PASS|FAIL|OPAQUE|CONDITIONAL|UNKNOWN|REDS|JSON|Inactive|Active|Terminating)\b)',' ',s)
  s=s.replace('STATIC_VERIFIED.**524','STATIC_VERIFIED.** 524').replace('contracts.524','contracts. 524').replace('No remaining Q09','No remaining Q09')
  chunks[i]=s
 return '`'.join(chunks)
report=(O/'REPORT.md').read_text('utf-8').replace('5229events/25controls','5264events/25controls').replace('**5229events/25controls**','**5264events/25controls**').replace('| A02 | 3 | 131 / 3 | 316 / 3 |','| A02 | 3 | 131 / 3 | 351 / 3 |')
assert report!=(S/'REPORT.md').read_text('utf-8');(O/'REPORT.md').write_text(prose_space(report),encoding='utf-8');(O/'HANDOFF.md').write_text(prose_space((O/'HANDOFF.md').read_text('utf-8')),encoding='utf-8')
cp=read(O/'checkpoint.json');cp.update(queue_sha256=sha(O/'queue.json'),report_sha256=sha(O/'REPORT.md'),handoff_sha256=sha(O/'HANDOFF.md'));write(O/'checkpoint.json',cp)
pub=read(O/'publication_01.json');pub.update(peer_assertion_events=5264,report_sha256=sha(O/'REPORT.md'),handoff_sha256=sha(O/'HANDOFF.md'),queue_sha256=sha(O/'queue.json'),coverage_sha256=sha(O/'coverage.json'),checkpoint_sha256=sha(O/'checkpoint.json'),supersession=str(S/'addendum.json'));write(O/'publication_01.json',pub)
ad={'status':'A02_EXPANDED_INDEPENDENT_NATIVE_ALIAS_REVIEW_AND_PRE_REVIEW_PUBLICATION_CORRECTION','old_review':old,'new_review':new,'review_checks_before':316,'review_checks_after':351,'scope':'Five additional Highwayman S28 custom-path body/scene alias comparisons. Original bounded review and exact earlier central publication preserved. All findings/status/core source data unchanged; only peer metadata, derived matrix/report hashes and prose spacing updated.','snapshots':{name:{'path':str(S/name),'sha256':h}for name,h in before.items()},'current_artifacts':{name:sha(O/name)for name in names},'runtime_or_package_changes':0,'source_epoch_changed':False,'all1610contract_cores_unchanged':True,'final_review_started_before_change':False}
write(S/'addendum.json',ad);print({'status':ad['status'],'new_review_sha256':sha(rp),'peer_events':5264,'contract_cores_changed':0})
