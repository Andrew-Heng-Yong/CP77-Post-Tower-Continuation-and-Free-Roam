"""Coordinator invokes inspected pure recipe; owns all new resource/script outputs."""
from pathlib import Path
import hashlib,importlib.util,json,sys
H=Path(__file__).resolve().parent;W=H.parents[1]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,sha
def main():
 out=H/'coordinator/brendan_03';assert not out.exists();out.mkdir(parents=True)
 recipe=H/'coordinator/brendan_recipe_02.py'
 spec=importlib.util.spec_from_file_location('qr13_pure_brendan_recipe',recipe);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 providers=read(H/'brendan_provider_validation_01/manifest.json');mod.validate_provider_manifest(providers)
 for r in providers['resources']:assert sha(r['raw'])==r['sha256']and sha(r['json'])==r['json_sha256']
 plan_path=H/'worker_b/revision_02/proposal.json';plan=read(plan_path)
 wrapper=read(W/'prealpha/quest_restoration_qr9/worker_b/resource_readbacks_01/resource_6.json')
 bugfix=read(next(r['json']for r in providers['resources']if r['depot'].endswith('mq037_quest_bugfixes.questphase')))
 doc=mod.build_wrapper_document(wrapper,bugfix,plan,providers)
 dest=out/'mq037.questphase.json';dest.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
 rows=[];base=Path(read(H/'baseline.json')['candidate'])
 hp='r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds';sp='r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
 hs=(base/'package'/hp).read_text(encoding='utf-8-sig');ss=(base/'package'/sp).read_text(encoding='utf-8-sig')
 helper=(H/'worker_b/redscript_shared_helper_UNEXECUTED.txt').read_text();methods=(H/'worker_b/redscript_HS1_methods_UNEXECUTED.txt').read_text()
 marker='public class SnapshotStateHS1 extends ScriptableSystem {';assert hs.count(marker)==1
 hs=hs.replace(marker,helper+'\n'+marker+'\n'+methods+'\n',1)
 marker='    if jm.HasAnyDelayedStateChanges() { sample.valid = false; sample.reason = "Journal changed during observation; waiting."; }'
 assert ss.count(marker)==1
 block='''    if i == 13 && SnapshotStateHS1.AdmitsBrendanFinalQR13(this.GetGameInstance(), paths, sample.states, names, sample.facts) {
      sample.valid = true;
      sample.reason = "Verified pre-ending earned final Theo continuation; native choices retained.";
    }
'''
 ss=ss.replace(marker,block+marker,1)
 for path,text in [(hp,hs),(sp,ss)]:
  p=out/Path(path).name;p.write_text(text,encoding='utf-8');rows.append({'path':path,'source':str(p),'sha256':sha(p),'before_sha256':sha(base/'package'/path)})
 result={'status':'COORDINATOR_EARNED_FINAL_PROPOSAL_PENDING_TYPED_AND_PEER_REVIEW','source_plan':str(plan_path),'source_plan_sha256':sha(plan_path),
  'recipe':str(recipe),'recipe_sha256':sha(recipe),'resources':[{'depot':plan['runtime_resource'],'proposed_json':str(dest),'proposed_json_sha256':sha(dest)}],
  'redscript_changes':rows,'game_writes':0,'save_writes':0}
 (out/'serialization_plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print({'resources':1,'redscript_changes':len(rows),'output':str(out)})
if __name__=='__main__':main()
