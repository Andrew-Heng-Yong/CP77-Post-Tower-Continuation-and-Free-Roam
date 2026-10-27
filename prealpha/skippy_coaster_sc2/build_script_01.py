"""SC2: let native Skippy ambient admission run without body/side-job gates."""
from hashlib import sha256
from pathlib import Path
import json

H=Path(__file__).resolve().parent
W=H.parents[1]
base=W/'prealpha/skippy_coaster_sc1/candidate_07/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
out=H/'candidate_01/script_source/PTFR_SideJobsS23.reds'
assert not out.exists()
s=base.read_text(encoding='utf-8')
def replace_one(a,b):
 global s
 assert s.count(a)==1,(a[:75],s.count(a))
 s=s.replace(a,b)
replace_one('  private let skippyPreviousPresent: Bool;',
            '  private let skippyPreviousPresent: Bool;\n  private let skippyLastStage: Int32;')
replace_one('this.skippyPreviousPresent = false; ArrayClear(this.previous);',
            'this.skippyPreviousPresent = false; this.skippyLastStage = -1; ArrayClear(this.previous);')
start=s.index('  private func SkippyAmbient() -> Void {')
end=s.index('  public func LC1SetupReady() -> Bool',start)
old=s[start:end]
new='''  private func SkippyAmbient() -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) { this.skippyPreviousPresent = false; return; }
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    let player = IsDefined(players) ? players.GetLocalPlayerMainGameObject() as PlayerPuppet : null;
    // This ambient gun branch does not respec V or change story ownership.
    // Its native quest gate independently verifies the exact Skippy item.
    let tower = this.Fact("PostTowerFreeRoamActive") == 1 && this.Fact("PTFRP0_DR13") == 1 &&
      this.Fact("q307_done") == 1 && this.Fact("q307_finished") == 1 &&
      this.Fact("q307_2079") == 1 && this.Fact("q307_main_game_killed") == 1 &&
      this.Fact("q307_ep1_killed") == 1 && this.Fact("q307_active") == 0 &&
      this.Fact("PTFRBASE_Suspended") == 0 && this.Fact("q305_johnny_scene_active") == 0 &&
      this.Fact("q115_point_of_no_return") == 0;
    let safe = this.running && this.warmup == 0 && tower && IsDefined(player) &&
      !player.IsDead() && !player.IsReplacer() && StartupCoverLC1.GameplayReleased(this.GetGameInstance());
    let history = SnapshotStateHS1.StartupReady(this.GetGameInstance());
    let progressed = this.Fact("mq007_skippy_enemies_total") > 0 ||
      this.Fact("mq007_skippy_50_enemies_defeated") > 0 ||
      this.Fact("mq007_skippy_owner_known") > 0;
    let owned = this.SkippyOwned();
    let freshWanted = safe && history && this.Own(1, "Ready") == 1 &&
      this.Own(1, "Issued") == 0 &&
      SnapshotStateHS1.Admits(this.GetGameInstance(), SideJobDataS23.ID(1)) &&
      this.Read(1).valid;
    let resumeWanted = safe && history && this.Own(8, "Ready") == 1 &&
      this.Own(8, "Issued") == 0 && this.Fact("PTFRS23_MQ007_ModeTalkConfirmed") == 1 &&
      this.Read(8).valid;
    if this.Fact("PTFRSKIP_Ambient_Claimed") == 1 && this.Fact("PTFRSKIP_Ambient_Stopped") == 0 &&
      (freshWanted || resumeWanted || this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1) {
      if this.Fact("PTFRSKIP_Ambient_Stop") == 0 { qs.SetFactStr("PTFRSKIP_Ambient_Stop", 1); }
    }
    if this.Fact("PTFRSKIP_Ambient_Claimed") == 0 && this.Fact("PTFRSKIP_Ambient_Request") == 1 &&
      (freshWanted || resumeWanted || this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1) {
      qs.SetFactStr("PTFRSKIP_Ambient_Request", 0);
    }
    // A progressed Skippy state is independent of the history snapshot and
    // transaction quantity while equipped. For a fresh gun, wait for the
    // history check so its one-time story owner can take precedence.
    let eligible = safe && (progressed || (history && owned)) && !freshWanted && !resumeWanted &&
      this.Own(1, "Issued") == 0 && this.Own(8, "Issued") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Claimed") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Entered") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Stop") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Stopped") == 0;
    if eligible && this.skippyPreviousPresent && this.Fact("PTFRSKIP_Ambient_Request") == 0 {
      qs.SetFactStr("PTFRSKIP_Ambient_Request", 1);
    }
    this.skippyPreviousPresent = eligible;
    let stage = 0;
    if safe { stage = 1; }
    if eligible { stage = 2; }
    if this.Fact("PTFRSKIP_Ambient_Request") == 1 { stage = 3; }
    if this.Fact("PTFRSKIP_Ambient_Claimed") == 1 { stage = 4; }
    if this.Fact("PTFRSKIP_Ambient_Entered") == 1 { stage = 5; }
    if this.Fact("PTFRSKIP_Ambient_Stopped") == 1 { stage = 6; }
    if stage != this.skippyLastStage {
      this.skippyLastStage = stage;
      ModLog(n"PTFR_SkippySC2", "stage=" + ToString(stage) + " tower/safe/history/progress/owned=" +
        ToString(tower) + "/" + ToString(safe) + "/" + ToString(history) + "/" +
        ToString(progressed) + "/" + ToString(owned) + " fresh/resume=" +
        ToString(freshWanted) + "/" + ToString(resumeWanted) + " ready/request/claimed/entered/stop/stopped=" +
        ToString(this.Fact("PTFRSKIP_Ambient_Ready")) + "/" +
        ToString(this.Fact("PTFRSKIP_Ambient_Request")) + "/" +
        ToString(this.Fact("PTFRSKIP_Ambient_Claimed")) + "/" +
        ToString(this.Fact("PTFRSKIP_Ambient_Entered")) + "/" +
        ToString(this.Fact("PTFRSKIP_Ambient_Stop")) + "/" +
        ToString(this.Fact("PTFRSKIP_Ambient_Stopped")));
    }
  }
'''
s=s[:start]+new+s[end:]
out.parent.mkdir(parents=True)
out.write_text(s,encoding='utf-8')
proof={'status':'SC2_SCRIPT_BUILT_NOT_PACKED','before_sha256':sha256(base.read_bytes()).hexdigest().upper(),'after_sha256':sha256(out.read_bytes()).hexdigest().upper(),'changed_paths':1,'game_writes':0,'save_writes':0}
(H/'candidate_01/script_proof_01.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
