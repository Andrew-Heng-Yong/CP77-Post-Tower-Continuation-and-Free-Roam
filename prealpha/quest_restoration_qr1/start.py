"""Pin PH3, stage a full successor and create the complete persistent repair queue."""
import sys,shutil,datetime
from pathlib import Path
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import *
AUDIT=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';BASE=W/'prealpha/phone_studios_ph3/candidate_01';C=H/'candidate_01'
assert not (H/'queue.json').exists() and not C.exists(),'Preserve existing repair state'
manifest=read(BASE/'install_manifest_01.json');game=Path(manifest['game_root']);pointer=read(W/'research/gig_restoration/lore_whitelist_current.json');selection=W/pointer['selection_file'];assert sha(selection)==pointer['sha256'];catalogue=read(selection)['decision_registry']
protected=[Path(p) for p in read(AUDIT.parent/'protection_before.json')['files']];protected.extend([game/'r6/cache/final.redscripts',game/'r6/cache/final.redscripts.ts',game/'engine/tools/scc.exe'])
old=read(AUDIT.parent/'protection_before.json');write(H/'protection_before.json',{'files':snapshot(protected),'game_metadata':tree_metadata(game),'save_root':old['save_root'],'save_metadata':tree_metadata(old['save_root'])})
for r in manifest['package_files']:
 assert sha(game/r['path'])==sha(BASE/'package'/r['path'])==r['after'],r['path']
source_files=[p for p in (BASE/'archive_source').rglob('*') if p.is_file()];source={str(p.relative_to(BASE/'archive_source')).replace('/','\\'):sha(p) for p in source_files}
prior={r['depot']:r['sha256'] for r in read(AUDIT/'../queries.json')['private']};assert source==prior,'PH3 source drift'
C.mkdir();shutil.copytree(BASE/'archive_source',C/'archive_source');shutil.copytree(BASE/'package',C/'package')
write(H/'baseline.json',{'candidate':str(BASE),'manifest':str(BASE/'install_manifest_01.json'),'manifest_sha256':sha(BASE/'install_manifest_01.json'),'game':str(game),'audit':str(AUDIT),'catalogue_pointer':pointer,'catalogue_sha256':sha(selection),'private_resources':source,'package_files':manifest['package_files'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'installed_unchanged_required':True,'deploy_authorized':False})
audit={r['id']:r for r in read(AUDIT/'quest_results.json')};stages=read(AUDIT/'stage_results.json');queue=[]
for q in catalogue:
 if q['decision']!='INCLUDE':continue
 a=audit[q['id']];queue.append({'id':q['id'],'title':q.get('title'),'category':q.get('category'),'selection':'INCLUDE','status':'PENDING_REVIEW','vanilla_candidates':a['native_root_candidates'],'restored_candidates':a['private_root_candidates'],'dependencies':a['dependency_closure'],'contracts':{k:{'status':'PENDING','evidence':[]} for k in ['entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies']},'prior_audit_stages':[s for s in stages if s['quest_id']==q['id']],'differences_registry':str(AUDIT/'intentional_differences.json'),'defects':[],'repairs':[],'tests':[],'remaining':['Prior UNKNOWN/OPAQUE is not a defect; exact contract evidence required'],'batch':None})
write(H/'queue.json',{'schema':1,'source_catalogue':str(selection),'catalogue_sha256':sha(selection),'derived_selected_count':len(queue),'excluded':[r['id'] for r in catalogue if r['decision']=='EXCLUDE'],'separate_scope':[r['id'] for r in catalogue if r['decision']=='SEPARATE_SCOPE'],'held':['mq057_motorbreath'],'quests':queue})
write(H/'checkpoint.json',{'state':'IMPLEMENTATION_ACTIVE','baseline':str(BASE),'staged_candidate':str(C),'queue':str(H/'queue.json'),'next':'Trace shared phone cleanup and establish exact lifecycle/identity mappings before modifying resources','restrictions':'No deployment, game launch, save/fact write or published-release changes','completed':[]})
print(json.dumps({'status':'BASELINE_PINNED_AND_STAGED','quests':len(queue),'resources':len(source),'managed_paths':len(manifest['package_files'])}))
