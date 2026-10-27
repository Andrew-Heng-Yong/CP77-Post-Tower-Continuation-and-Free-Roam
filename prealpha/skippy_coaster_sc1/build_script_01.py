"""Generate the scoped Skippy ambient request/release logic in existing S23 module."""
from hashlib import sha256
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parents[1]
source = W / "prealpha/world_workspots_w2/candidate_04/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds"
dest = H / "candidate_05/script_source/PTFR_SideJobsS23.reds"
assert not dest.exists()
text = source.read_text(encoding="utf-8")


def replace_once(old, new):
    global text
    assert text.count(old) == 1, (old[:80], text.count(old))
    text = text.replace(old, new)


replace_once("  private let previous: array<SideJobSampleS23>;", "  private let previous: array<SideJobSampleS23>;\n  private let skippyPreviousPresent: Bool;")
replace_once("    this.epoch += 1; this.warmup = 3; this.legacyFreshPrevious = false; ArrayClear(this.previous);",
             "    this.epoch += 1; this.warmup = 3; this.legacyFreshPrevious = false; this.skippyPreviousPresent = false; ArrayClear(this.previous);")
replace_once(
    "    return this.running && this.warmup == 0 && this.Common() && this.Safe() &&\n      this.Own(i, \"Ready\") == 1 && this.Own(i, \"Issued\") == 0 && this.Own(i, \"Finished\") == 0 && this.Own(i, \"Fault\") == 0;",
    "    if (i == 1 || i == 8) && this.Fact(\"PTFRSKIP_Ambient_Claimed\") == 1 && this.Fact(\"PTFRSKIP_Ambient_Stopped\") == 0 { return false; }\n"
    "    return this.running && this.warmup == 0 && this.Common() && this.Safe() &&\n      this.Own(i, \"Ready\") == 1 && this.Own(i, \"Issued\") == 0 && this.Own(i, \"Finished\") == 0 && this.Own(i, \"Fault\") == 0;",
)
method = '''  private func SkippyOwned() -> Bool {
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    let tx = GameInstance.GetTransactionSystem(this.GetGameInstance());
    if !IsDefined(players) || !IsDefined(tx) { return false; }
    let player = players.GetLocalPlayerMainGameObject() as PlayerPuppet;
    return IsDefined(player) && tx.GetItemQuantity(player, ItemID.CreateQuery(t"Items.mq007_skippy")) >= 1;
  }
  private func SkippyAmbient() -> Void {
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) { this.skippyPreviousPresent = false; return; }
    // The native Skippy quest is retired by the completed Tower transition.
    // Claim only its ambient gun controller, never pickup, mode, journal or reward nodes.
    let safe = this.running && this.warmup == 0 && this.Common() && this.Safe() &&
      StartupCoverLC1.GameplayReleased(this.GetGameInstance());
    let resumeWanted = safe && this.Own(8, "Ready") == 1 &&
      this.Own(8, "Issued") == 0 && this.Fact("PTFRS23_MQ007_ModeTalkConfirmed") == 1 &&
      this.Read(8).valid;
    let freshWanted = safe && this.Own(1, "Ready") == 1 &&
      this.Own(1, "Issued") == 0 &&
      SnapshotStateHS1.Admits(this.GetGameInstance(), SideJobDataS23.ID(1)) &&
      this.Read(1).valid;
    if this.Fact("PTFRSKIP_Ambient_Claimed") == 1 && this.Fact("PTFRSKIP_Ambient_Stopped") == 0 &&
      (freshWanted || resumeWanted || this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1) {
      if this.Fact("PTFRSKIP_Ambient_Stop") == 0 { qs.SetFactStr("PTFRSKIP_Ambient_Stop", 1); }
    }
    if this.Fact("PTFRSKIP_Ambient_Claimed") == 0 && this.Fact("PTFRSKIP_Ambient_Request") == 1 &&
      (freshWanted || resumeWanted || this.Own(1, "Issued") == 1 || this.Own(8, "Issued") == 1) {
      qs.SetFactStr("PTFRSKIP_Ambient_Request", 0);
    }
    let eligible = safe && this.SkippyOwned() && !freshWanted && !resumeWanted &&
      this.Own(1, "Issued") == 0 && this.Own(8, "Issued") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Ready") == 1 &&
      this.Fact("PTFRSKIP_Ambient_Claimed") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Entered") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Stop") == 0 &&
      this.Fact("PTFRSKIP_Ambient_Stopped") == 0;
    if eligible && this.skippyPreviousPresent && this.Fact("PTFRSKIP_Ambient_Request") == 0 {
      qs.SetFactStr("PTFRSKIP_Ambient_Request", 1);
    }
    this.skippyPreviousPresent = eligible;
  }
'''
replace_once("  public func LC1SetupReady() -> Bool", method + "  public func LC1SetupReady() -> Bool")
replace_once("    this.legacyFreshPrevious = fresh;\n    let i = 0;", "    this.legacyFreshPrevious = fresh;\n    this.SkippyAmbient();\n    let i = 0;")
dest.parent.mkdir(parents=True)
dest.write_text(text, encoding="utf-8")
print({"before_sha256": sha256(source.read_bytes()).hexdigest().upper(),
       "after_sha256": sha256(dest.read_bytes()).hexdigest().upper()})
