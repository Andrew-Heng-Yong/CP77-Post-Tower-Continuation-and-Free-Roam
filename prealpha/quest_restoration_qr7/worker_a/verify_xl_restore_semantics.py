"""Read-only source applicability of standard root-quest registration on restore."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
def body(text,signature):
 start=text.index('{',text.index(signature));depth=1;i=start+1
 while depth:
  depth+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[start:i]
def run(o):
 assert not o.exists();p=W/'research/framework_pr63_01/archivexl/src/App/Extensions/QuestPhase/Extension.cpp';cp=p.with_name('Config.cpp');s=p.read_text();c=cp.read_text();package=W/'research/framework_pr63_01/package.json';pkg=read(package);dll=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/red4ext/plugins/ArchiveXL/ArchiveXL.dll');T=[]
 def ck(n,b):T.append({'name':n,'pass':bool(b)});assert b,n
 ck('installed ArchiveXL DLL matches pinned framework build lineage',sha(dll)==pkg['files']['red4ext/plugins/ArchiveXL/ArchiveXL.dll']);load=body(s,'bool App::QuestPhaseExtension::Load()');restore=body(s,'void App::QuestPhaseExtension::OnGameRestored(');patch=body(s,'bool App::QuestPhaseExtension::PatchPhase(');start=body(s,'void App::QuestPhaseExtension::OnQuestStart(')
 ck('source hooks actual game restored callback', 'HookBefore<Raw::QuestsSystem::OnGameRestored>(&OnGameRestored)'in load);ck('root quest resource registrations enter forced-start set','Red::IsInstanceOf<Red::questQuestResource>(aPhaseResource)'in patch and 's_forced[aPhaseResource->path].insert(modPhaseNode->id)'in patch)
 ck('restore checks saved per-phase engine fact before force-start','if (!factManager->GetFact(phaseFactId))'in restore and 'Red::QuestNodeKey phaseNodeKey{questNodeHash, phaseNodeId}'in restore and 'Red::FactID phaseFactId{phaseNodeKey}'in restore)
 ck('restore starts new owner at In1 then records engine receipt',restore.index('Red::DynArray<Red::CName> phaseNodeSockets{"In1"}')<restore.index('Raw::QuestsSystem::ForceStartNode')<restore.index('factManager->SetFact(phaseFactId, 1)'))
 ck('normal quest start records the same phase engine receipts','Red::QuestNodeKey phaseNodeKey{questNodeHash, phaseNodeId}'in start and 'factManager->SetFact(phaseFactId, 1)'in start)
 ck('no configured forceStart switch is needed or read','forceStart'not in c and 'FillConnection(phaseNode["input"], phaseData.input)'in c)
 capture=read(H/'ronald_namespace_inputs_01/manifest.json');parent=next(x for x in capture['matching_providers']if x['depot']==r'ep1\quest\ep1.quest');ck('current actual parent is root quest resource',Resource(read(Path(parent['json']))).normalize()['type']=='questQuestResource')
 plan=read(W/'prealpha/quest_restoration_qr7/worker_b/registration_plan_01.json');ck('proposed binding has only standard existing input shape',plan['quest']['input']=={'node':[1],'socket':'Out'}and set(plan['quest'])=={'parent','path','input','append_after_existing','derived_key','derived_crc_ccitt_false','collision_inventory_gate'})
 write(o/'evidence.json',{'status':'PASS_PINNED_ARCHIVEXL_ROOT_REGISTRATION_RESTORE_SOURCE_APPLICABILITY','checks':T,'framework_package':str(package),'framework_package_sha256':sha(package),'framework_ArchiveXL_commit':pkg['sources']['ArchiveXL']['commit'],'installed_DLL_sha256':sha(dll),'extension_source':str(p),'extension_source_sha256':sha(p),'config_source':str(cp),'config_source_sha256':sha(cp),'native_parent_raw_sha256':parent['raw_sha256'],'registration_plan_sha256':sha(W/'prealpha/quest_restoration_qr7/worker_b/registration_plan_01.json'),'meaning':'The standard new EP1 root-quest phase registration is intentionally started at In1 on restore when its own generated-phase engine receipt is absent. ArchiveXL records that receipt and skips an already-recorded phase. No explicit forceStart YAML field is introduced. Thus new Ronald owner code may begin waiting on an existing save; its source-reviewed Tower/contact/private future-Armed guards, rather than absence of startup, bound acquisition. Existing saved quest descendants are not restarted by this registration.','limits':['Source proof in the locally pinned framework build lineage, with installed DLL hash matched. This is not fresh DLL decompilation or observed engine scheduling.','The native generic forced-start mechanism does not itself prove all saved-owner transitions. Future-only arming and lifecycle contracts remain separately reviewed source behavior; in-game reload fixtures remain LIVE_ONLY.'],'candidate_or_runtime_writes':0});print({'checks':len(T),'evidence':str(o/'evidence.json')})
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
