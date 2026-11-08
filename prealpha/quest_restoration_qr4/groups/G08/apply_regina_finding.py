"""Revise only G08 audit adjudications after narrowed source evidence; no resource edits."""
from pathlib import Path
import sys,shutil,collections,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha
ev=H/'regina_followup_01/evidence.json';x=read(ev);assert all(t['pass']for t in x['checks'])
save=H/'before_regina_followup_01';assert not save.exists()
p=H/'quests/mq007_smartgun/contracts.json'
for old in [p,p.parent/'REPORT.md',H/'REPORT.md',H/'results.json']:
 target=save/old.relative_to(H);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old,target)
q=read(p);defect='MQ007_POST_RETURN_REACQUISITION_MISSING_CONSUMER'
q['defects']=[defect];q['status']='DEEP_REVIEWED_CONFIRMED_STATIC_DISCREPANCY_REPAIR_BLOCKED'
proven='Global discovery across5,136 source-pinned normalized models finds exactly five matching resources. Current native/copied return5/66 writes mq007_done1. Only original bugfix MQ00714 waits that fact, five game days, then outside Regina reacquisition trigger AND MinorQuestAndSts before enabling #mq007_pr_gun_return.var_container, activating three Regina messages and writing re_acquiring_done1. Genuine Tower root106→109→Terminating107 encloses root82/4→bugfixing9→quest_bugfixing root3/27→this original handler; no current private/embedded or REDscript rehost consumes the new post-Tower completion into that continuation.'
for key in ['communications','completion_rewards_cleanup','shared_dependencies']:
 c=q['contracts'][key];c['status']='FAIL';c['proven'].append(proven);c['remaining']=[s for s in c['remaining']if 'bugfix14'not in s and 'corrective-owner'not in s and 'Regina/default leases'not in s]
 c['remaining'] += ['SOURCE_CONFIRMED_STATIC_GAP: Newly completed supported fresh/resume story can emit done1 after the sole native post-return handler has been structurally terminated. This is separate from the known unsupported progressed-admission seam.','REPAIR_BLOCKED_PENDING_SCOPE_REVIEW: Isolate native14 only after original gun-return prefab placement/lease, MinorQuestAndSts content-token context and conservative existing saved timer/variant/receipt transition review. Do not restart the entire bugfix resource or relax/reset counters. Root independent repair review is required.']
 c['evidence'].append('../../regina_followup_01/evidence.json')
for key in ['ownership','persistence']:
 q['contracts'][key]['proven'].append('Original post-return14 is structurally inside the genuine Tower terminated tree; this narrow missing-consumer finding is no longer classified solely as generic old-owner uncertainty. Main return/ambient saved transition limits remain separate.')
 q['contracts'][key]['evidence'].append('../../regina_followup_01/evidence.json')
write(p,q)
report=['# Machine Gun — mq007_smartgun','','Confirmed static discrepancy: '+defect+'. No runtime repair was written.','']
for key,c in q['contracts'].items():
 report+=['## '+key+' — '+c['status'],'']+['- '+s for s in c['proven']]+['']
 if c['approved_differences']:report+=['Approved differences:']+['- '+s for s in c['approved_differences']]+['']
 if c['remaining']:report+=['Remaining:']+['- '+s for s in c['remaining']]+['']
(p.parent/'REPORT.md').write_text('\n'.join(report),encoding='utf8')
write(H/'discrepancies.json',{'findings':[{'id':defect,'quest_id':'mq007_smartgun','severity':'MEDIUM','status':'SOURCE_CONFIRMED_STATIC_MISSING_CONSUMER_REPAIR_SCOPE_REVIEW_REQUIRED','faulty_route':'Current private fresh/resume →native return5→66 done1; original consumer bugfix14 is under main-root terminating107; no replacement.','native_expected':'After done1 wait5game days, native context/office wait→container var_container on→three Regina SMS→re_acquiring_done1.','evidence':str(ev),'evidence_sha256':sha(ev),'affected_contracts':['communications','completion_rewards_cleanup','shared_dependencies'],'minimal_candidate_scope':'An isolated native14 continuation tied only to newly entered supported private fresh/resume story and saved one-time owner, after independent root/placement/context/save review; no whole bugfix restart.','blockers':x['safe_slice_blockers'],'repair_implemented':False}],'runtime_changes':[]})
r=read(H/'results.json');row=next(y for y in r['quests']if y['quest_id']=='mq007_smartgun');row['contracts_sha256']=sha(p);row['status_counts']=dict(collections.Counter(v['status']for v in q['contracts'].values()));r['confirmed_unique_defects']=1;r['discrepancies']=str(H/'discrepancies.json');r['followup_tests']={'path':str(ev),'sha256':sha(ev),'checks':len(x['checks']),'global_discovery_models':x['global_model_discovery_count']};write(H/'results.json',r)
text=(H/'REPORT.md').read_text(encoding='utf8');text=text.replace('No new source-confirmed defect or gameplay repair is justified.','One source-confirmed missing post-return consumer was found by a subsequent narrow trace; repair is blocked pending original prefab/context/save scope review. No gameplay repair was implemented.').replace('Native later Regina reacquisition is explicitly assigned to separate bugfix14, whose post-Tower execution is conditional.','Native later Regina reacquisition is assigned to original bugfix14 under the genuine Tower terminating root. Newly completed supported fresh/resume story still emits its done1 producer, while no private/embedded/script consumer restores the five-day/variant/three-message continuation. See discrepancies.json and regina_followup_01/evidence.json.').replace('Machine Gun:1APPROVED_DEVIATION,2PASS,6CONDITIONAL,1OPAQUE.','Machine Gun:1APPROVED_DEVIATION,2PASS,3CONDITIONAL,1OPAQUE,3FAIL.').replace('No runtime resources changed.','Nine follow-up checks pin the complete original retirement ancestry and scan all5,136 models for matching producer/consumer/variant/embedded paths. Before-follow-up reports are preserved under before_regina_followup_01/. No runtime resources changed.');(H/'REPORT.md').write_text(text,encoding='utf8')
print(json.dumps({'defect':defect,'contracts':row['status_counts'],'source_epoch_unchanged':True,'repairs':0}))
