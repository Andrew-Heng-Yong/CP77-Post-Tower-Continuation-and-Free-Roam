"""Pin the RD5 baseline and generate the narrow Meet Kirk admission."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RD7 = HERE.parent / "resume_dispatcher_rd7_kirk_20261113_01"
sys.path.insert(0, str(HERE.parent / "resume_dispatcher_rd6_batch50_20261113_01"))
from review_batch import RD5, MANIFEST, SNAPSHOTS, load_baseline, pinned, read, readonly, sha, write

SCRIPT = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
HISTORY = SCRIPT.replace("SideJobsS29", "HistorySnapshotHS1")
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
TAG = "PTFRS29_mq017_streetkid_"
ROOT = "quests/minor_quest/mq017_streetkid"
PHASE = ROOT + "/mq017_streetkid"
OBJECTIVE = PHASE + "/01_meet_kirk"


def replace(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def main():
    game, members, xl = load_baseline()
    manifest = read(RD5 / MANIFEST[0])
    proof = read(RD7 / "evidence_04/assessment.json")
    graph = RD7 / "graph_05"
    receipt = read(pinned(graph, ("readback.json", proof["readback_sha256"])))
    watch = read(pinned(RD7 / "evidence_02", ("provider_watch.json", proof["provider_watch_sha256"])))
    parts = watch["parts"]
    parts["root"] |= {"raw": str(graph / "root.questphase"), "raw_sha256": receipt["raw_sha256"]}
    with readonly("registry") as db:
        providers = {rid: dict(db.execute("SELECT * FROM resources WHERE rid=?", (rid,)).fetchone())
                     for rid in (14764, 14599)}
    for row in providers.values():
        assert members[row["depot"]] == row["sha256"]
    for row in parts.values():
        assert sha(row["raw"]) == row["raw_sha256"] and row["depot"] not in members
    phone = {"raw": str(graph / "kirk.questphase"), "raw_sha256": receipt["phone"]["raw_sha256"],
             "depot": providers[14599]["depot"]}
    assert sha(phone["raw"]) == phone["raw_sha256"]
    folder = game / "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1"
    snapshot = read(pinned(folder, SNAPSHOTS["extended"]))
    assert snapshot["origin"] == "pre_native_cleanup"
    journal, facts = {}, {}
    for row in snapshot["rows"]:
        definition = row["definition"]
        if definition["kind"] == "journal":
            index = len(journal)
            journal[definition["path"], definition["class"]] = (index, row)
        elif definition["kind"] == "fact":
            facts[definition["name"]] = (len(facts), row)
    assert len(journal) == 4982 and len(facts) == 18685
    journals = []
    for (path, kind), (index, row) in journal.items():
        if not path.startswith(ROOT) or kind not in ("gameJournalQuest", "gameJournalQuestPhase",
                                                      "gameJournalQuestObjective", "gameJournalQuestDescription"):
            continue
        history = 2 if path in (ROOT, PHASE, OBJECTIVE, OBJECTIVE + "/description") else 1
        assert row["stable"] and row["state"] == history
        journals.append({"path": path, "class": kind, "index": index, "history": history,
                         "live": 4 if path in (ROOT, PHASE, OBJECTIVE) else history})
    assert len(journals) == 18
    match = {k: 0 for k in facts if k.startswith("mq017_")}
    match |= {"mq017_started": 1, "q001_done": 1, "q005_done": 1, "q101_enable_side_content": 1,
              "sq018_done": 1, "ep1_standalone": 0, "holo_kirk_calls_v_start_count": 2,
              "holo_kirk_calls_v_end_count": 1, "holo_kirk_calls_v_interrupted": 1,
              "holo_v_calls_kirk_start_count": 0, "holo_v_calls_kirk_end_count": 0,
              "holo_kirk_calls_v_rejected_branch": 0}
    assert all(facts[k][1]["stable"] and facts[k][1]["value"] == v for k, v in match.items())
    history_source = (game / HISTORY).read_text(encoding="utf-8-sig")
    for row in journals:
        assert f'if i=={row["index"]} {{ return "{row["path"]}"; }}' in history_source
    for name in match:
        assert f'if i=={facts[name][0]} {{ return "{name}"; }}' in history_source
    stage = HERE / "candidate_01/package" / SCRIPT
    path = game / SCRIPT
    source = path.read_text(encoding="utf-8-sig")
    rows = [
        "  private let kirkPrevious: Bool;",
        "  private func KirkEligible() -> Bool {",
        '    if !this.Unclaimed(1) || this.Own(1, "Permit") != 0 || this.Own(1, "ResumeClaimed") != 0 ||',
        '      this.Own(1, "ResumePhoneReleased") != 0 || this.Fact("PTFRS29_PHONE_kirk_Issued") != 0 ||',
        '      this.Fact("PTFRPH3_Entered") != 1 || this.Fact("PTFRPH3_Ready") != 1 { return false; }',
        "    let game = this.GetGameInstance();",
        "    let history = CaptureArchiveHS3.Get(game);",
        "    if !IsDefined(history) || !history.GlobalFileReadyHS4() { return false; }",
    ]
    for row in journals:
        rows.append(f'    if history.JournalState({row["index"]}) != {row["history"]} || '
                    f'ResumeDispatcherRD1.Journal(game, "{row["path"]}", "{row["class"]}") != {row["live"]} {{ return false; }}')
    for name, expected in match.items():
        rows.append(f'    if history.FactValue({facts[name][0]}) != {expected} || this.Fact("{name}") != {expected} {{ return false; }}')
    rows += [
        f'    let objective = GameInstance.GetJournalManager(game).GetEntryByString("{OBJECTIVE}", "gameJournalQuestObjective") as JournalQuestObjective;',
        "    let jm = GameInstance.GetJournalManager(game);",
        "    let phone = GameInstance.GetPhoneManager(game);",
        "    return IsDefined(objective) && jm.GetObjectiveCurrentCounter(objective) == 0 &&",
        "      !jm.GetIsObjectiveOptional(objective) && IsDefined(phone) && !phone.IsPhoneCallActive();",
        "  }",
        "  private func PollKirkResume(safe: Bool) -> Void {",
        "    let current = safe && this.KirkEligible();",
        "    let permit = current && this.kirkPrevious ? 1 : 0;",
        "    this.kirkPrevious = current;",
        "    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());",
        f'    if IsDefined(qs) && this.Own(1, "ResumePermit") != permit {{ qs.SetFactStr("{TAG}ResumePermit", permit); }}',
        "  }",
    ]
    source = replace(source, "  private let previous: array<SideJobSampleS29>;",
                     "  private let previous: array<SideJobSampleS29>;\n" + "\n".join(rows))
    source = replace(source, "  public func Restored() -> Void {\n    this.epoch += 1; this.warmup = 3; ArrayClear(this.previous);\n    let i = 0; let empty: SideJobSampleS29;",
                     f'''  public func Restored() -> Void {{
    this.kirkPrevious = false;
    let qs = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if IsDefined(qs) && this.Own(1, "ResumePermit") == 1 {{ qs.SetFactStr("{TAG}ResumePermit", 0); }}
    this.epoch += 1; this.warmup = 3; ArrayClear(this.previous);
    let i = 0; let empty: SideJobSampleS29;''')
    source = replace(source, "    this.RestoreMQ018MessageContact();",
                     "    this.RestoreMQ018MessageContact();\n    this.PollKirkResume(this.warmup == 0 && this.Common() && this.Safe());")
    source = replace(source, '  private func Unclaimed(i: Int32) -> Bool {\n    return this.Own(i, "Ready") == 1',
                     '  private func Unclaimed(i: Int32) -> Bool {\n    return (i != 1 || this.Own(i, "ResumeClaimed") == 0) && this.Own(i, "Ready") == 1')
    stage.parent.mkdir(parents=True)
    stage.write_text(source, encoding="utf-8", newline="\n")
    out = HERE / "evidence_01"
    out.mkdir()
    write(out / "inputs.json", {"game": str(game), "archive_source": manifest["archive_source"], "xl": xl,
          "archive_sha256": manifest["archive_sha256"], "members": members, "parts": parts, "phone": phone,
          "wrapper": providers[14764], "journals": journals, "facts": match, "tag": TAG,
          "script_sha256": sha(stage), "graph_proof_sha256": sha(RD7 / "evidence_04/assessment.json")})


if __name__ == "__main__":
    main()
