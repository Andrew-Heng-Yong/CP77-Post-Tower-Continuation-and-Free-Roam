"""Stage the removal of legacy resume admission while retaining fresh restoration."""

from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
sys.path.insert(0, str(PREALPHA / "universal_resume_live_candidate_20261115_01"))
from candidate_common import digest, load, pin, require, write_json

BEFORE = PREALPHA / "mid_quest_resume_archive_20261115_01/stage_02/deployment_01/installed_manifest_01.json"
BEFORE_SHA = "35B2CE7B75DBACD202E902A9969F002042B151127FD13BAA636851180747F9CF"
PREFIX = "r6/scripts/PTFR_Consolidated"
STAGE = HERE / "stage_03"
SCRIPT_STAGE = HERE / "stage_06"


class Edit:
    def __init__(self, text):
        self.text = text

    def replace(self, old, new, count=1):
        pattern = rb"\r?\n".join(re.escape(line.encode()) for line in old.split("\n"))
        matches = list(re.finditer(pattern, self.text))
        require(len(matches) == count, f"Expected {count} source matches: {old[:140]}")
        for match in reversed(matches):
            self.apply(match.start(), match.end(), new)

    def section(self, start, end, new=""):
        opening, closing = start.encode(), end.encode()
        require(self.text.count(opening) == 1, f"Nonunique source boundary: {start}")
        offset = self.text.index(opening)
        self.apply(offset, self.text.index(closing, offset), new)

    def apply(self, start, end, new):
        line_end = self.text.find(b"\n", start)
        newline = b"\r\n" if self.text[line_end - 1:line_end] == b"\r" else b"\n"
        self.text = self.text[:start] + newline.join(part.encode() for part in new.split("\n")) + self.text[end:]


def history(edit):
    edit.section("// UNEXECUTED: insert INSIDE existing SnapshotStateHS1, without altering fields.",
                 "  private persistent let schema: Int32;")
    edit.section("public enum ResumeDecisionRD1 {", "public abstract class ResumeDispatcherRD1 {")
    edit.section("  public static func Decide(history: Int32", "  public static func HistoryAdmits(history: Int32")
    edit.replace("    return history==1 || history==2;", "    return history==1;")
    edit.replace("    // Failed in the accepted baseline remains failed; Active needs an existing supported resume adapter.",
                 "    // A fresh restoration requires an Inactive root in accepted history.")
    edit.section("  public static func Receipt(game: GameInstance,names: array<String>)", "public class StageResumeRD1 extends ScriptableSystem {", "}\n\n")
    edit.section(
        "public class StageResumeRD1 extends ScriptableSystem {",
        "  let owner=StageResumeRD1.Get(gameInstance);if IsDefined(owner) { owner.Restored(); }",
        """// Keep the historical system identity and revoke only unclaimed admission.
public class StageResumeRD1 extends ScriptableSystem {
  public static func Get(game: GameInstance) -> ref<StageResumeRD1> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.HistorySnapshotHS1.StageResumeRD1") as StageResumeRD1;
  }
  private func OnAttach() -> Void { this.Restored(); }
  public func Restored() -> Void {
    let qs=GameInstance.GetQuestsSystem(this.GetGameInstance());
    if IsDefined(qs) && qs.GetFactStr("PTFRRD1_MQ007_DELIVERY_Issued")==0 &&
       qs.GetFactStr("PTFRRD1_MQ007_DELIVERY_Permit")!=0 {
      qs.SetFactStr("PTFRRD1_MQ007_DELIVERY_Permit",0);
    }
  }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
""")


def side_jobs_22(edit):
    edit.replace("    let value = allowed && StartupCoverLC1.GameplayReleased(this.GetGameInstance()) ? 1 : 0;",
                 "    let value = 0;")
    edit.replace("  private func Permit(i: Int32, allowed: Bool) -> Void {",
                 "  private func ClearPermit(i: Int32) -> Void {")
    edit.replace('      if this.Own(i, "Issued") == 0 { this.Permit(i, false); }', '      this.ClearPermit(i);')
    edit.section("  private func Read(i: Int32) -> SideJobSampleS22 {", "  public func LC1SetupReady()")
    edit.section("    if ArraySize(this.previous) != SideJobDataS22.Count()", "      if this.running && this.warmup==0",
                 """    let i = 0;
    while i < SideJobDataS22.Count() {
      this.ClearPermit(i);
      i += 1;
    }
""")
    edit.replace("  private let previous: array<SideJobSampleS22>;\n", "")
    edit.replace("this.running = false; this.epoch += 1; ArrayClear(this.previous);",
                 "this.running = false; this.epoch += 1;")
    edit.replace("    this.epoch += 1; this.warmup = 3; ArrayClear(this.previous);\n    let i = 0; let empty: SideJobSampleS22;",
                 "    this.epoch += 1; this.warmup = 3;\n    let i = 0;")
    edit.replace("      ArrayPush(this.previous, empty);\n", "")
    edit.replace("    let sample = this.Read(i);\n", "")
    edit.replace('      " currentMatch=" + ToString(sample.valid) + " safe=" + ToString(this.Safe()) + " | " + sample.reason + " Issued owners are not restarted.";',
                 '      " | Mid-journey admission archived. Existing issued owners retain their progress.";')


def side_jobs_23(edit):
    edit.replace('    if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }',
                 '    if !IsDefined(qs) || this.Own(i, "Issued") != 0 ||\n'
                 '       (i == 13 && this.Fact("PTFRQR13_MQ037_FinalSupportHeld") == 1) { return; }')
    edit.section('    if i == 13 && SnapshotStateHS1.Admits(this.GetGameInstance(), SideJobDataS23.ID(i)) && SnapshotStateHS1.AdmitsBrendanFinalQR13',
                 '    if i == 13 && this.Own(i, "Entered") == 0')
    edit.replace('    if i != 13 && !SnapshotStateHS1.Admits(this.GetGameInstance(),SideJobDataS23.ID(i)) { return false; }',
                 '    if i == 8 || !SnapshotStateHS1.Admits(this.GetGameInstance(),SideJobDataS23.ID(i)) { return false; }')
    edit.section('    let resumeWanted = safe && history', '    let storyOwns =')
    edit.replace('(freshWanted || resumeWanted || deliveryWanted || storyOwns)', '(freshWanted || storyOwns)', count=2)
    edit.replace('!freshWanted && !resumeWanted && !deliveryWanted && !storyOwns', '!freshWanted && !storyOwns')
    edit.replace('    if deliveryWanted && this.Fact("PTFRSKIP_SC3_Stop")==0 { qs.SetFactStr("PTFRSKIP_SC3_Stop",1); }\n', '')
    edit.replace('" fresh/resume/story=" +', '" fresh/story=" +')
    edit.replace('ToString(freshWanted) + "/" + ToString(resumeWanted) + "/" + ToString(storyOwns)',
                 'ToString(freshWanted) + "/" + ToString(storyOwns)')


def side_jobs_29(edit):
    edit.section("  private func KirkEligible() -> Bool {", "  public static func Get(game: GameInstance) -> ref<SideJobsS29>")
    edit.replace("  private let kirkPrevious: Bool;\n", "")
    edit.replace("    this.kirkPrevious = false;\n", "")
    edit.replace("    this.PollKirkResume(this.warmup == 0 && this.Common() && this.Safe());\n", "")


def activity(edit):
    edit.section("public abstract class RiteResumeRD5 {", "public class NativeGigsU9 extends ScriptableSystem {")
    edit.section("  private let ritePrevious: ref<ResumeObservationRD1>;", "  private let running: Bool;")
    edit.replace("    this.ritePrevious=null;\n", "")
    edit.replace("    this.PollRiteResume(safe);\n", "")


EDITS = {
    "PTFR_HistorySnapshotHS1": history,
    "PTFR_SideJobsS22": side_jobs_22,
    "PTFR_SideJobsS23": side_jobs_23,
    "PTFR_SideJobsS29": side_jobs_29,
    "PTFR_ActivityStateR3": activity,
}


def main():
    baseline = load(BEFORE, BEFORE_SHA)
    game = Path(baseline["game_root"])
    known = {row["path"]: row for row in baseline["core_files"]}
    changes = {}
    for name, change in EDITS.items():
        relative = f"{PREFIX}/{name}.reds"
        record = known[relative]
        source = pin(game / relative, record["sha256"], record["bytes"])
        edit = Edit(source.read_bytes())
        change(edit)
        saved = rb"^.*\bpersistent let [^\r\n]+"
        require(re.findall(saved, edit.text, re.MULTILINE) ==
                re.findall(saved, source.read_bytes(), re.MULTILINE), f"Saved layout drift: {relative}")
        output = SCRIPT_STAGE / "package" / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            require(output.read_bytes() == edit.text, f"Existing staged source differs: {relative}")
        else:
            with output.open("xb") as stream:
                stream.write(edit.text)
        changes[relative] = dict(before=record["sha256"], after=digest(output), bytes=len(edit.text))
    write_json(SCRIPT_STAGE / "script_changes.json", changes)
    print(f"Staged {len(changes)} script replacements with unchanged persistent declarations.")


if __name__ == "__main__":
    main()
