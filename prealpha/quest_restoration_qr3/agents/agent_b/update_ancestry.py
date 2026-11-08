"""Supersede only the resolved owner-input documentation gap; preserve snapshots."""
from pathlib import Path
import sys,shutil
W=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
src=W/'prealpha/quest_restoration_qr3/native_owner_gap_resolution.json';r=read(src);checks=[]
assert r['status']=='PASS_CURRENT_NATIVE_ANCESTOR_CONTAINMENT_WITH_HISTORICAL_SOURCE_CORRECTIONS'
for edge in r['chain'][1:]:
 row=r['fresh_inputs'][edge['parent']];assert sha(row['raw'])==row['sha256']
 m=Resource(read(row['json'])).normalize();n=m['graphs'][edge['graph']]['nodes'][edge['node']]
 assert edge['child'] in n['refs'];checks.append({'parent':edge['parent'],'sha256':row['sha256'],'graph':edge['graph'],'node':edge['node'],'child':edge['child'],'status':'PASS'})
copies=[]
for q in ['mq046_cave_vehicle','mq047_ad_vehicle']:
 p=O/'quests'/q/'contracts.json';old=p.with_name('contracts_01.json');assert not old.exists();shutil.copyfile(p,old)
 d=read(p);own=d['contracts']['ownership'];own['proven'].append('Current native ancestor containment is now verified: cyberpunk2077 root/82 node3 -> additional_game_elements root19 -> open_world_content root11 -> open_world_minor_activities root6 -> badlands_minor_activities root6 -> native district nodes141/145. Genuine Tower journal -> receipt109 -> Terminating107 encloses this original world tree. Fresh unique-provider graph evidence supersedes the earlier missing-top-caller gap; saved executing-owner behavior remains conditional.')
 own['remaining']=[x for x in own['remaining'] if 'direct top-level caller' not in x]
 own['evidence'].append(str(src));shared=d['contracts']['shared_dependencies'];shared['remaining']=[x.replace('Original world/bugfix owner retirement/survival and shared prefab lease lifetime need exact top ancestry plus saved-owner evidence','Authored original world containment is proven; saved world/bugfix owner retirement/survival and shared prefab lease lifetime still need saved-owner evidence') for x in shared['remaining']];shared['evidence'].append(str(src))
 d['review_update']='REVIEW-B-ANCESTRY resolved by current raw graph chain; original contracts_01.json preserved. Two stale global parent exports are explicitly superseded; all six original AgentB binary pins match actual current providers.'
 write(p,d);report=p.with_name('REPORT.md');orig=report.with_name('REPORT_01.md');assert not orig.exists();shutil.copyfile(report,orig)
 text=report.read_text(encoding='utf-8');text=text.replace('full original world-owner retirement path','saved executing-owner/lease transition evidence (current native top-level containment is now proven)')
 text+='\nREVIEW-B-ANCESTRY update: the current native top-level containment gap is resolved by `../../../../native_owner_gap_resolution.json`. Earlier report/contract snapshots remain preserved. The stale global open_world_content/open_world_minor_activities exports are not treated as current; the district/body inputs used here match fresh current providers. Saved owner and engine termination remain CONDITIONAL.\n'
 report.write_text(text,encoding='utf-8');copies.append({'quest_id':q,'before':str(old),'before_sha256':sha(old),'current':str(p),'current_sha256':sha(p)})
p=O/'REPORT.md';text=p.read_text();text=text.replace('original world-owner ancestry remain explicit','saved world-owner/lease transitions remain explicit. Current native top-level containment is now proven; see ancestry_update_02.json');p.write_text(text,encoding='utf-8')
write(O/'ancestry_update_02.json',{'status':'PASS_REVIEW_B_ANCESTRY_GAP_RESOLVED_WITH_SAVED_OWNER_LIMIT','source':str(src),'source_sha256':sha(src),'independent_current_raw_checks':checks,'snapshots':copies,'runtime_changes':[]})
print({'status':'PASS_REVIEW_B_ANCESTRY_GAP_RESOLVED_WITH_SAVED_OWNER_LIMIT','raw_chain_checks':len(checks)})
