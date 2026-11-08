"""Seal approved QR13 evidence and handoff. No game/build/deployment operations."""
from pathlib import Path
import datetime,hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def main():
 dest=H/'completion.json';assert not dest.exists();peerpath=H/'worker_c/final_package_01/verification/review.json';peer=read(peerpath)
 assert peer['status']=='PASS_INDEPENDENT_FINAL_QR13_COMPLETE_ARCHIVE_ZIP_SOURCE_SCRIPT_AND_PRESERVATION'
 ep=H/'source_epoch_02.json';e=read(ep);assert sha(ep)==peer['source_epoch_sha256']
 pm=H/'candidate_01/package_manifest.json';package=read(pm)
 assert sha(package['zip'])==package['zip_sha256']==peer['zip_sha256']
 assert package['archive_sha256']==peer['archive_sha256']
 for name in ['REPORT.md','HANDOFF.md','TEST_CARDS.md','REGRESSION_REPORT.md','REPRODUCE.md','development_queue.json']:assert(H/name).is_file()
 read(H/'development_queue.json');links=[]
 for name in ['REPORT.md','HANDOFF.md','TEST_CARDS.md','REGRESSION_REPORT.md','REPRODUCE.md']:
  p=H/name
  for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
   if '://'not in ref:
    assert(p.parent/ref.split('#')[0]).resolve().exists(),(name,ref);links.append({'document':name,'target':ref})
 artifacts={}
 selected=[H/'baseline.json',ep,pm,peerpath,H/'worker_c/FINAL_PACKAGE_REVIEW.md',H/'verification/compile_01/result.json',H/'candidate_01/rebuild_01.json',H/'candidate_01/promotion.json',
  H/'worker_c/ronald_serialized_01/review.json',H/'worker_a/actual_brendan06_02/review.json',H/'worker_c/brendan_support_scope_01/review.json',H/'brendan_provider_match.json',
  *[H/x for x in ['REPORT.md','HANDOFF.md','TEST_CARDS.md','REGRESSION_REPORT.md','REPRODUCE.md','development_queue.json','seal.py']]]
 for p in selected:artifacts[str(p.relative_to(H))]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
 for r in read(peer['input_manifest'])['frozen_pins']:assert sha(r['path'])==r['sha256'],'Frozen final verification input changed'
 result={'status':'QR13_COMPLETE_IMPLEMENTED_STAGED_CONDITIONAL_RESTORATION_WITH_EXPLICIT_BLOCKERS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_epoch':str(ep),'canonical_epoch_sha256':sha(ep),
  'candidate':str(H/'candidate_01'),'zip':package['zip'],'zip_sha256':package['zip_sha256'],'archive_sha256':package['archive_sha256'],
  'implemented':['Ronald prospective real-consent first enrollment/contact and reviewed native shared bar support','Strict pre-ending-certified earned peaceful Coin Operated Boy final-Theo continuation with bounded passive support lifetime'],
  'changed_resources':peer['changed_resources'],'changed_scripts':peer['changed_scripts'],'package_paths':peer['package_paths'],'archive_payloads':peer['archive_payloads'],'unchanged_old_payloads':1574,'unchanged_package_paths':48,
  'fresh_compile_sources':peer['compiler_sources_checked'],'fresh_compile_input_pins':peer['input_pins_checked'],'independent_final_checks':peer['checks'],'installed_pins_preserved':peer['installed_pins_checked'],'save_files_preserved':peer['save_files_checked'],
  'installed':False,'published':False,'game_launches':0,'CUA_or_live_game_API_calls':0,'save_or_live_fact_writes':0,'deployments':0,
  'remaining_limits':['Machine-spot placement OPAQUE; exact original prefab references only','Saved-owner/prefab/edge acquisition and actual runtime behavior LIVE_ONLY','Earlier Spray/timer/hostile or failed final/private-issued adapters remain unsupported','Skippy has no new safe-widening evidence','No currently qualified new manual test fixture or universal runtime/all-save/release PASS'],
  'artifacts':artifacts,'local_links_verified':links,'current_state_pointer':{'path':str(W/'docs/knowledge/current-state.md'),'sha256':sha(W/'docs/knowledge/current-state.md'),'before_sha256':sha(H/'current-state.before.md')},
  'next':'No more closed-route tests. Review exact staged successor/remaining queue; any later deployment requires separate explicit authorization and guarded current-input installation/rollback. Do not rerun one-shot builders or manufacture fixtures.'}
 dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 p=H/'checkpoint.json';old=H/'checkpoint.before-completion.json';assert not old.exists();old.write_bytes(p.read_bytes())
 p.write_text(json.dumps({'state':'QR13_COMPLETE_STAGED_NOT_INSTALLED','completion':str(dest),'completion_sha256':sha(dest),'canonical_epoch':str(ep),'candidate':str(H/'candidate_01'),'installed':'QR8:02 + unchanged QR10D01/D00E',
  'new_staged_resources':3,'changed_managed_sources':2,'game_launches':0,'installations':0,'save_or_live_fact_writes':0,'next':result['next'],'report':str(H/'REPORT.md'),'handoff':str(H/'HANDOFF.md')},indent=2)+'\n',encoding='utf-8')
 print({'status':result['status'],'artifacts_pinned':len(artifacts),'independent_checks':peer['checks'],'payloads':peer['archive_payloads'],'installed':False,'ready_new_live_tests':0})
if __name__=='__main__':main()
