"""Verify TH1 against its pinned source in memory. No generated game files."""

import hashlib
import json
import operator
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "johnny_batch4_jb3"
PATCH = HERE / "source.patch"
PINS = json.loads((HERE / "provenance.json").read_bytes())
HUNK = re.compile(rb"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def apply_in_memory(original, hunks):
    lines = original.splitlines(keepends=True)
    output = []
    cursor = 0
    for header, body in hunks:
        old_start, old_count, new_start, new_count = (int(v or 1) for v in HUNK.fullmatch(header).groups())
        start = old_start - 1 if old_count else old_start
        assert cursor <= start
        output.extend(lines[cursor:start])
        cursor = start
        offset = len(output)
        assert offset == (new_start - 1 if new_count else new_start)
        for row in body:
            kind, payload = row[:1], row[1:]
            assert kind in (b" ", b"-", b"+"), row
            if kind != b"+":
                assert lines[cursor] == payload
                cursor += 1
            if kind != b"-":
                output.append(payload)
        assert cursor - start == old_count and len(output) - offset == new_count
    return b"".join(output + lines[cursor:])


def load_sources():
    manifest = (BASELINE / "deployment_01/installed_manifest_01.json").read_bytes()
    assert sha(manifest) == PINS["installed_manifest_sha256"]
    manifest = json.loads(manifest)
    assert manifest["core_epoch"] == PINS["core_epoch"]
    assert manifest["archive_sha256"] == PINS["archive_sha256"]
    exact_files = {row["path"]: row["sha256"] for row in manifest["core_files"]}
    originals, patched, seen = {}, {}, set()
    chunks = re.split(rb"(?m)^diff --git ", PATCH.read_bytes())[1:]
    for chunk in chunks:
        lines = chunk.splitlines(keepends=True)
        path = lines[1].removeprefix(b"--- a/").rstrip().decode()
        assert path in PINS["files"] and path not in seen
        seen.add(path)
        assert lines[2].rstrip().decode() == "+++ b/" + path
        original = (BASELINE / "candidate_01/package" / path).read_bytes()
        assert sha(original) == PINS["files"][path]["before"] == exact_files[path]
        starts = [i for i, line in enumerate(lines) if line.startswith(b"@@")]
        hunks = [(lines[a].rstrip(), lines[a + 1:b]) for a, b in zip(starts, starts[1:] + [len(lines)])]
        result = apply_in_memory(original, hunks)
        assert sha(result) == PINS["files"][path]["after"]
        originals[Path(path).name] = original.decode().replace("\r\n", "\n")
        patched[Path(path).name] = result.decode().replace("\r\n", "\n")
    assert seen == set(PINS["files"])
    return originals, patched


def completion_gate(source):
    body = source.split("public static func CompletionBlocker", 1)[1].split("public static func Active", 1)[0]
    assert 'let ponr = q.GetFact(n"q115_point_of_no_return");' in body
    rules = re.findall(r'if ([^{}]+?)\s*\{\s*return n"([^"]*)";\s*\}', body)
    assert len(rules) == body.count("return n") - 1
    assert body.rstrip().endswith('return n"";\n  }')

    def blocker(facts, quests_defined=True):
        for expression, result in rules:
            for term in expression.split("||"):
                term = term.strip()
                if term == "!IsDefined(q)":
                    matched = not quests_defined
                else:
                    match = re.fullmatch(r'(?:q\.GetFact\(n"(\w+)"\)|(ponr))\s*(==|!=)\s*(\d+)', term)
                    assert match, term
                    key = match[1] or "q115_point_of_no_return"
                    compare = operator.eq if match[3] == "==" else operator.ne
                    matched = compare(facts.get(key, 0), int(match[4]))
                if matched:
                    return result
        return ""

    return blocker


def test_gate(source):
    gate = completion_gate(source)
    direct = dict.fromkeys([
        "q307_done", "q307_finished", "q307_2079", "q307_main_game_killed",
        "q307_ep1_killed", "PostTowerFreeRoamActive", "PTFRP0_DR13",
    ], 1)
    rooftop = dict.fromkeys([
        "q115_point_of_no_return", "q307_start", "q307_point_of_no_return",
        "q307_rooftop_q115_seated", "q307_q115_call_done", "q307_confirm_av_done",
        "PTFRP0_DR02", "PTFRP0_DR07", "PTFRP0_DR12", "PTFRPA2_Started",
        "PTFRPA2_Teleported", "PTFRPA3_CoverReleased", "PTFRPA4_CameraAligned", "PTFRPA2_ControlReady",
    ], 1)
    assert gate(direct) == ""
    assert gate(direct, quests_defined=False) == "quest_system_unavailable"
    assert gate({"q115_point_of_no_return": 1, "q115_active": 1}) == "tower_cleanup_pending"
    assert gate(direct | {"q115_point_of_no_return": 1}) == "q115_rooftop_unverified"
    assert gate(direct | {"q115_point_of_no_return": 2}) == "q115_route_conflict"
    for prior_call in (0, 1):
        facts = direct | rooftop | {"q307_q115_unified_call_done": 1 - prior_call, "q115_active": 1}
        assert gate(facts) == ""
        assert gate(facts | {"PTFRPA2_Fault": 2}) == ""  # Read-only recovery admission.
        assert gate(facts | {"PTFRPA2_Finished": 1}) == ""
    for key in direct:
        assert gate(direct | {key: 0})
        assert gate(direct | rooftop | {key: 0})
    for key in rooftop.keys() - {"q115_point_of_no_return"}:
        assert gate(direct | rooftop | {key: 0})
    for key in ("q307_active", "q305_johnny_scene_active", "q307_q115_wait", "q307_rooftop_chicken",
                "q307_debug_reset", "q115_var_test_def", "q115_suicide_ending"):
        assert gate(direct | rooftop | {key: 1})
    active = source.split("public static func Active", 1)[1].split("public static func Area", 1)[0]
    assert 'q.GetFact(n"q115_point_of_no_return") == 0 || q.GetFact(n"PTFRPA2_Fault") == 0' in active


def test_preservation(before, after):
    for name in before:
        persistent = re.compile(r"(?m)^\s*(?:private|public|protected) persistent let .*?$")
        assert persistent.findall(before[name]) == persistent.findall(after[name]), name
        # Moving the H10 request block must preserve the exact existing writes.
        writes = re.compile(r'(?:SetFact(?:Str)?|SetOwned|SetOwn|this\.Set)\([^;\n]*')
        assert Counter(writes.findall(before[name])) == Counter(writes.findall(after[name])), name
    name = "PTFR_RestorationBaseline.reds"
    geometry = before[name].split("    // PTFRB0H10_geometry\n", 1)[1].split("    // Coyote public mirror\n", 1)[0]
    assert after[name].split("    // PTFRB0H10_geometry\n", 1)[1].split("\n  }\n", 1)[0] + "\n" == geometry
    assert after[name].index("if housingOnly { this.Schedule(epoch,1.0); return; }") < after[name].index("WilsonLeaseH2.Reconcile(game);")
    startup = after[name].split("private func Startup(", 1)[1].split("private func RequestH10Geometry(", 1)[0]
    assert startup.index("if housingOnly") < startup.index("// PTFRB0NIDG_auto")
    assert startup.index("IsSavingLocked") < startup.index("if housingOnly")
    name = "PTFR_RestrictionsR1.reds"
    cf1 = "// ORIGINAL: r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/CyberwarePreservationCF1.reds"
    assert before[name].split(cf1, 1)[1] == after[name].split(cf1, 1)[1]
    name = "PTFR_LoadingCoverLC1.reds"
    adapters = "// ORIGINAL: r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds"
    assert before[name].split(adapters, 1)[0] == after[name].split(adapters, 1)[0]
    assert 'this.Now()-this.stableSince<1.0' in after[name]
    assert 'this.completedSteps=12;' in after[name]


def test_recovery(source):
    recovery = source.split("public class SnapshotRecoveryHS1", 1)[1].split("public class SnapshotRecoveryTickHS1", 1)[0]
    exact = recovery.split("private func ExactFailedPreparation()", 1)[1].split("private func SetOwned", 1)[0]
    predicates = re.findall(r'this.Fact\(n"(\w+)"\)==(\d+)', exact)
    assert dict(predicates) == dict(PTFRPA2_Fault="2", PTFRPA2_Prepared="0", PTFRPA2_Reveal="0", PTFRPA2_Finished="0")
    poll = recovery.split("public func Poll", 1)[1]
    assert poll.index("this.BaseBlocker()") < poll.index("this.originalFault=2") < poll.index('SetOwned(n"PTFRPA2_Fault",0)')
    finish = poll.index('SetOwned(n"PTFRPA2_Finished",1)')
    for check in ('this.Fact(n"PTFRPA2_Prepared")!=1', 'this.Fact(n"PTFRPA2_Reveal")!=1',
                  "arrival.Completed()", "housing.HousingReadyForReveal()", "world.H10GeometryReady()",
                  "world.H10ActionsArmed()", "profile.LC1PhysicalReady()", "chrome.PTFRR2Ready(player)", "this.stable<4"):
        assert poll.index(check, poll.index("if this.phase!=2")) < finish, check
    for check in ("SnapshotStateHS1.StartupReady(game)", "housing.LC1RecoveryHealthy()",
                  "body.PTFRR3Faulted()", "chrome.PTFRR2Healthy()", "arrival.LC1ControlReady()",
                  "profile.LC1LedgerValid(player)"):
        assert recovery.index(check) < recovery.index("private func ExactFailedPreparation"), check


if __name__ == "__main__":
    before, after = load_sources()
    test_gate(after["PTFR_RestrictionsR1.reds"])
    test_preservation(before, after)
    test_recovery(after["PTFR_HistorySnapshotHS1.reds"])
    print("PASS: five exact source deltas, direct and rooftop gate fixtures, recovery and preservation checks")
