"""SC3 restores the native equipped/unequipped lifecycle using a new owner."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
W=H.parents[1]
B=W/'prealpha/skippy_coaster_sc2/candidate_01'
C=H/'candidate_01'
source=B/'package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
out=C/'script_source/PTFR_SideJobsS23.reds'
assert not out.exists()
s=source.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a))
 s=s.replace(a,b)
replace('  private let skippyLastStage: Int32;', '  private let skippyLastStatus: String;')
replace('this.skippyLastStage = -1;', 'this.skippyLastStatus = "";')
old='    if (i == 1 || i == 8) && this.Fact("PTFRSKIP_Ambient_Claimed") == 1 && this.Fact("PTFRSKIP_Ambient_Stopped") == 0 { return false; }'
replace(old,old+'\n    if (i == 1 || i == 8) && this.Fact("PTFRSKIP_SC3_Claimed") == 1 && this.Fact("PTFRSKIP_SC3_Stopped") == 0 { return false; }')
start=s.index('  private func SkippyAmbient() -> Void {')
end=s.index('  public func LC1SetupReady() -> Bool',start)
new='''  private func SkippyAmbient() -> Void {
    let game = this.GetGameInstance();
    let qs = GameInstance.GetQuestsSystem(game);
    if !IsDefined(qs) { this.skippyPreviousPresent = false; return; }
    let players = GameInstance.GetPlayerSystem(game);
    let player = IsDefined(players) ? players.GetLocalPlayerMainGameObject() as PlayerPuppet : null;
    let tower = this.Fact("PostTowerFreeRoamActive") == 1 && this.Fact("PTFRP0_DR13") == 1 &&
      this.Fact("q307_done") == 1 && this.Fact("q307_finished") == 1 &&
      this.Fact("q307_2079") == 1 && this.Fact("q307_main_game_killed") == 1 &&
      this.Fact("q307_ep1_killed") == 1 && this.Fact("q307_active") == 0 &&
      this.Fact("PTFRBASE_Suspended") == 0 && this.Fact("q305_johnny_scene_active") == 0 &&
      this.Fact("q115_point_of_no_return") == 0;
    let safe = this.running && this.warmup == 0 && tower && IsDefined(player) &&
      !player.IsDead() && !player.IsReplacer() && StartupCoverLC1.GameplayReleased(game);
    let history = SnapshotStateHS1.StartupReady(game);
    let progressed = this.Fact("mq007_skippy_enemies_total") > 0 ||
      this.Fact("mq007_skippy_50_enemies_defeated") > 0 || this.Fact("mq007_skippy_owner_known") > 0;
    let owned = this.SkippyOwned();
    let freshWanted = safe && history && this.Own(1, "Ready") == 1 && this.Own(1, "Issued") == 0 &&
      SnapshotStateHS1.Admits(game, SideJobDataS23.ID(1)) && this.Read(1).valid;
    let resumeWanted = safe && history && this.Own(8, "Ready") == 1 && this.Own(8, "Issued") == 0 &&
      this.Fact("PTFRS23_MQ007_ModeTalkConfirmed") == 1 && this.Read(8).valid;
    let storyOwns = this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1;

    // SC1's Stopped writer is followed by a Terminating output. Keep that
    // receipt: clearing it on an already-ended saved owner cannot produce a
    // new acknowledgement. For a still-active owner use its existing stop
    // watcher; for an unclaimed owner cancel Request and latch its stop guard.
    if safe {
      if this.Fact("PTFRSKIP_Ambient_Claimed") == 0 && this.Fact("PTFRSKIP_Ambient_Request") == 1 {
        qs.SetFactStr("PTFRSKIP_Ambient_Request", 0);
      }
      if this.Fact("PTFRSKIP_Ambient_Stop") == 0 {
        qs.SetFactStr("PTFRSKIP_Ambient_Stop", 1);
      }
    }
    let oldRetired = this.Fact("PTFRSKIP_Ambient_Stopped") == 1 ||
      (this.Fact("PTFRSKIP_Ambient_Claimed") == 0 && this.Fact("PTFRSKIP_Ambient_Entered") == 0 &&
       this.Fact("PTFRSKIP_Ambient_Request") == 0 && this.Fact("PTFRSKIP_Ambient_Stop") == 1);
    if this.Fact("PTFRSKIP_SC3_Claimed") == 1 && this.Fact("PTFRSKIP_SC3_Stopped") == 0 &&
      (freshWanted || resumeWanted || storyOwns) && this.Fact("PTFRSKIP_SC3_Stop") == 0 {
      qs.SetFactStr("PTFRSKIP_SC3_Stop", 1);
    }
    if this.Fact("PTFRSKIP_SC3_Claimed") == 0 && this.Fact("PTFRSKIP_SC3_Request") == 1 &&
      (freshWanted || resumeWanted || storyOwns) {
      qs.SetFactStr("PTFRSKIP_SC3_Request", 0);
    }
    // The new persistent owner waits for the exact native equipped-Skippy
    // condition and re-arms that wait after every normal native TurnOff.
    let eligible = safe && oldRetired && (progressed || (history && owned)) &&
      !freshWanted && !resumeWanted && !storyOwns && this.Fact("PTFRSKIP_SC3_Ready") == 1 &&
      this.Fact("PTFRSKIP_SC3_Claimed") == 0 && this.Fact("PTFRSKIP_SC3_Entered") == 0 &&
      this.Fact("PTFRSKIP_SC3_Stop") == 0 && this.Fact("PTFRSKIP_SC3_Stopped") == 0;
    if eligible && this.skippyPreviousPresent && this.Fact("PTFRSKIP_SC3_Request") == 0 {
      qs.SetFactStr("PTFRSKIP_SC3_Request", 1);
    }
    this.skippyPreviousPresent = eligible;
    let status = "tower/safe/history/progress/owned=" + ToString(tower) + "/" + ToString(safe) + "/" +
      ToString(history) + "/" + ToString(progressed) + "/" + ToString(owned) +
      " oldRetired=" + ToString(oldRetired) + " oldClaimed/Stop/Stopped=" +
      ToString(this.Fact("PTFRSKIP_Ambient_Claimed")) + "/" + ToString(this.Fact("PTFRSKIP_Ambient_Stop")) +
      "/" + ToString(this.Fact("PTFRSKIP_Ambient_Stopped")) + " fresh/resume/story=" +
      ToString(freshWanted) + "/" + ToString(resumeWanted) + "/" + ToString(storyOwns) +
      " ready/request/claimed/entered/active/stop/stopped=" + ToString(this.Fact("PTFRSKIP_SC3_Ready")) +
      "/" + ToString(this.Fact("PTFRSKIP_SC3_Request")) + "/" + ToString(this.Fact("PTFRSKIP_SC3_Claimed")) +
      "/" + ToString(this.Fact("PTFRSKIP_SC3_Entered")) + "/" + ToString(this.Fact("PTFRSKIP_SC3_Active")) +
      "/" + ToString(this.Fact("PTFRSKIP_SC3_Stop")) + "/" + ToString(this.Fact("PTFRSKIP_SC3_Stopped"));
    if NotEquals(status, this.skippyLastStatus) {
      this.skippyLastStatus = status;
      ModLog(n"PTFR_SkippySC3", status);
    }
  }
'''
s=s[:start]+new+s[end:]
assert 'skippyLastStage' not in s
assert 'SetFactStr("PTFRSKIP_Ambient_Stopped", 0)' not in s
out.parent.mkdir(parents=True);out.write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
(C/'script_proof_01.json').write_text(json.dumps({'status':'SC3_SCRIPT_BUILT_NOT_INSTALLED','before':sha(source),'after':sha(out),'game_writes':0,'save_writes':0},indent=2)+'\n')
print(json.dumps({'status':'SC3_SCRIPT_BUILT_NOT_INSTALLED','sha256':sha(out)}))
