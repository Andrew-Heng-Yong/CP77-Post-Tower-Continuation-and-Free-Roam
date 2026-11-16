"""Stage an exact HS4 successor with the shared dispatcher and stage readers."""
import argparse
from difflib import unified_diff
import re
import shutil
from common import HERE, HISTORY, RED_DIR, baseline, read, sha, write


def replace_once(text, before, after):
    assert text.count(before)==1, before[:140]
    return text.replace(before,after,1)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',required=True,type=int);args=parser.parse_args()
    out=HERE/f'candidate_{args.attempt:02d}';assert not out.exists()
    manifest,game=baseline();package=out/'package'
    for row in manifest['core_files']:
        dst=package/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(game/row['path'],dst)
        assert sha(dst)==row['sha256']
    changes={}
    old=(game/HISTORY).read_text(encoding='utf-8-sig')
    new=replace_once(old,'import PTFR.RestorationBaseline.*','import PTFR.RestorationBaseline.*\nimport PTFR.LoadingCoverLC1.*')
    new=replace_once(new,'public class SnapshotStateHS1 extends ScriptableSystem {',
        'public class SnapshotStateHS1 extends ScriptableSystem {\n'+(HERE/'history_readers.reds').read_text())
    new=replace_once(new,'    return state==1 || state==2;','    return ResumeDispatcherRD1.HistoryAdmits(state);')
    for fragment in ('dispatcher.reds','analysis_03/contracts.reds','coordinator.reds'):
        new+='\n'+(HERE/fragment).read_text(encoding='utf-8')
    changes[HISTORY]=(old,new)

    rel=RED_DIR+'/PTFR_SideJobsS22.reds';old=(game/rel).read_text(encoding='utf-8-sig')
    new=replace_once(old,'  private func Read(i: Int32) -> SideJobSampleS22 {', '''  private func Read(i: Int32) -> SideJobSampleS22 {
    let history=SnapshotStateHS1.Get(this.GetGameInstance());
    if i==2 && IsDefined(history) && history.HistoryRootRD1("q304_car_retrieval")==2 { return this.ReadEarnedRD1(); }''')
    new=replace_once(new,'  private func Same(a: SideJobSampleS22, b: SideJobSampleS22) -> Bool {', '''  private func ReadEarnedRD1() -> SideJobSampleS22 {
    let sample: SideJobSampleS22;let game=this.GetGameInstance();
    let observed=ResumeContractsRD1.Read1(game,true);let history=SnapshotStateHS1.Get(game);
    sample.states=observed.values;sample.reason=observed.reason;
    if !IsDefined(history) { return sample; }
    let live=ResumeDispatcherRD1.Journal(game,"ep1/quests/minor_quest/q304_car_retrieval","gameJournalQuest");
    let decision=ResumeDispatcherRD1.Decide(history.HistoryRootRD1("q304_car_retrieval"),live,
      this.Own(2,"Issued"),false,this.Common(),false,observed.valid);
    sample.valid=Equals(decision,ResumeDecisionRD1.EarnedStage);return sample;
  }
  private func Same(a: SideJobSampleS22, b: SideJobSampleS22) -> Bool {''')
    changes[rel]=(old,new)

    rel=RED_DIR+'/PTFR_SideJobsS23.reds';old=(game/rel).read_text(encoding='utf-8-sig')
    new=replace_once(old,'    let storyOwns = this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1;', '''    let delivery=StageResumeRD1.Get(game);
    let deliveryWanted=IsDefined(delivery) && delivery.DeliveryWanted();
    let storyOwns = this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1 || this.Fact("PTFRRD1_MQ007_DELIVERY_Issued")==1;''')
    assert new.count('(freshWanted || resumeWanted || storyOwns)')==2
    new=new.replace('(freshWanted || resumeWanted || storyOwns)','(freshWanted || resumeWanted || deliveryWanted || storyOwns)')
    new=replace_once(new,'      !freshWanted && !resumeWanted && !storyOwns && this.Fact("PTFRSKIP_SC3_Ready") == 1 &&',
        '      !freshWanted && !resumeWanted && !deliveryWanted && !storyOwns && this.Fact("PTFRSKIP_SC3_Ready") == 1 &&')
    new=replace_once(new,'    // The new persistent owner waits for the exact native equipped-Skippy', '''    // Fence an unclaimed SC3 request as well as waiting for an executing
    // owner's real Stopped acknowledgement. Never manufacture Stopped.
    if deliveryWanted && this.Fact("PTFRSKIP_SC3_Stop")==0 { qs.SetFactStr("PTFRSKIP_SC3_Stop",1); }
    // The new persistent owner waits for the exact native equipped-Skippy''')
    changes[rel]=(old,new)
    for rel,(old,new) in changes.items():
        assert re.findall(r'\bpersistent let [^;]+;',old)==re.findall(r'\bpersistent let [^;]+;',new)
        (package/rel).write_text(new,encoding='utf-8',newline='\n')
    (out/'scripts.patch').write_text(''.join(''.join(unified_diff(a.splitlines(True),b.splitlines(True),fromfile=rel,tofile=rel)) for rel,(a,b) in changes.items()),encoding='utf-8')
    write(out/'script_manifest.json',{'status':'SCRIPTS_STAGED_NATIVE_RESOURCES_PENDING','baseline':manifest['core_epoch'],
        'changed_sources':{rel:sha(package/rel) for rel in changes},'preserved_persistent_declarations':True,
        'contracts':'analysis_03/contracts.json','contracts_sha256':sha(HERE/'analysis_03/contracts.json')})
    print('Staged three script changes; native adapters and package qualification remain pending.')


if __name__=='__main__':main()
