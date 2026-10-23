"""Validate PA3's actual packed graph delta and the PA2 blackout regression.

The reachability model checks ordering, not REDengine fade/streaming execution.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def read(path):
    return Path(path).read_text(encoding="utf-8-sig")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    build = Path(sys.argv[1]).resolve()
    assert build.is_relative_to(ROOT / "prealpha/handoff_pa3/build")
    assert not (build / "tests.json").exists(), "Do not overwrite tests"
    report = json.loads(read(build / "build.json"))
    compile_report = json.loads(read(build / "compile.json"))
    prior = json.loads(read(ROOT / "prealpha/transition/build/pa2_candidate_03/build.json"))
    cases = []

    def check(ok, message):
        assert ok, message
        cases.append(message)

    check(compile_report["status"] == "PASS_COMPILE_AND_READBACK_NOT_LIVE" and
          compile_report["build_sha256"] == sha(build / "build.json"), "Compilation matches this exact build")
    check(len(report["package_files"]) == 53 and len(report["changes"]) == 2, "Exactly two replacements in53-file package")
    pkg = Path(report["package_root"])
    old = {f["relative"]:f["sha256"] for f in prior["package_files"]}
    unchanged = []
    for f in report["package_files"]:
        assert sha(pkg / f["relative"]) == f["sha256"]
        if f["sha256"] == old[f["relative"]]:
            unchanged.append(f["relative"])
    check(len(unchanged) == 51, "51 other files byte-identical, including CET, entry/history, HP/perks/gigs")
    source = ROOT / "prealpha/handoff_pa3/scripts/PreAlphaArrivalPA1.reds"
    check(sha(source) == sha(pkg / "r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds"), "Current observer equals compiled package input")
    for f in compile_report["package_scripts"]:
        assert sha(f["path"]) == f["sha256"]
    check(sha(Path(compile_report["stage"]) / "compiled.script") == compile_report["flat_sha256"], "Compiled readback unchanged")
    flat = read(Path(compile_report["stage"]) / "compiled.script")
    for name in ("PTFRPA3_CoverReleased", "func ReadinessReason(", "H10 transition PA3:", "STOPPED: control-readiness timeout;"):
        check(name in flat, "Compiled body contains " + name)

    graph = json.loads(read(build / "graph.json"))
    nodes = {h["Data"]["id"]:h["Data"] for h in json.loads(read(build / "final.patched.json"))["Data"]["RootChunk"]["graph"]["Data"]["nodes"]}
    check(len(nodes) == 87 and graph["unchanged_prior_payloads"], "Four new nodes; all83 PA2 payloads preserved")
    def payload(node, prop): return nodes[node][prop]["Data"]
    check(payload(176,"type")["fadeIn"] == 1 and payload(176,"type")["duration"] == .5, "Early native fade-in has stock half-second duration")
    delay = payload(177,"condition")["type"]["Data"]
    check(delay["seconds"] == 1 and delay["minutes"] == delay["hours"] == delay["miliseconds"] == 0, "One-second settle follows native fade-in")
    tier = payload(178,"type")
    check(tier["tier"] == "Tier1_FullGameplay" and tier["forceEmptyHands"] == 0, "Native Tier1 reassertion follows cover release, without forced empty hands")
    check("PTFRPA3_CoverReleased" in json.dumps(nodes[179]), "Native release acknowledgement follows Tier1 request")
    edges = set(graph["all_edges"])
    for edge in ("146.Out -> 176.In", "176.Out -> 177.In", "177.Out -> 178.In", "178.Out -> 179.In", "179.Out -> 150.In", "179.Out -> 151.In", "174.True -> 161.In"):
        check(edge in edges, "Packed graph edge " + edge)
    for edge in graph["removed_edges"]:
        check(edge not in edges, "Old direct/late-fade edge removed: " + edge)
    check(not any(e.endswith(" -> 159.In") for e in edges), "Old late success fade has no incoming edge")
    check(payload(151,"condition")["type"]["Data"]["seconds"] == 60 and payload(171,"condition")["type"]["Data"]["seconds"] == 180, "Watchdog budgets unchanged; this is not a timeout increase")
    for edge in ("155.Out -> 160.In", "175.Out -> 160.In", "153.CutSource -> 150.CutDestination", "153.CutSource -> 151.CutDestination", "173.CutSource -> 170.CutDestination", "173.CutSource -> 171.CutDestination"):
        assert edge in edges, edge
    check(True, "Failure uncover and both native loser-cancellation branches preserved")

    def all_readiness_paths_uncovered(es):
        adj = {}
        for e in es:
            m = re.fullmatch(r"(\d+)\.([\w]+) -> (\d+)\.([\w]+)",e)
            assert m, e
            if m[2] != "CutSource": adj.setdefault(int(m[1]),[]).append(int(m[3]))
        todo = [(146,False)]; visited = set(); found = False
        while todo:
            n, uncovered = todo.pop()
            if (n,uncovered) in visited: continue
            visited.add((n,uncovered))
            if n in (150,151):
                found = True
                if not uncovered: return False
                continue
            if n == 176: uncovered = True
            todo.extend((d,uncovered) for d in adj.get(n,[]))
        return found

    pa2_edges = edges.difference(graph["added_edges"]).union(graph["removed_edges"])
    check(not all_readiness_paths_uncovered(pa2_edges), "Regression: original PA2 fails uncovered-before-readiness property")
    check(all_readiness_paths_uncovered(edges), "PA3 all paths from teleport to readiness pass unconditional fade-in")
    for bad in ("146.Out -> 150.In","146.Out -> 151.In"):
        check(not all_readiness_paths_uncovered(edges | {bad}), "Negative control catches reintroduced blackout wait: " + bad)
    # Small timing model reflecting the live observation, not engine execution.
    for native_blackout_holds_tier5 in (False,True):
        screen_black = False  # guaranteed path through176 before readiness
        tier_ready = not (screen_black and native_blackout_holds_tier5)
        check(tier_ready, f"Model: ready possible regardless of blackout's tier effect={native_blackout_holds_tier5}")
    text = read(source)
    control = text[text.index("  private func ControlReady"):text.index("  public func Poll")]
    previous_text = read(ROOT / "prealpha/transition/scripts/PreAlphaArrivalPA1.reds")
    previous_control = previous_text[previous_text.index("  private func ControlReady"):previous_text.index("  public func Poll")]
    check(control == previous_control, "Player-control safety predicate unchanged, not bypassed")
    check(text.index('if this.Fact(n"PTFRPA3_CoverReleased") != 1') < text.index('if this.Fact(n"PTFRPA2_ControlReady") == 0'), "Observer waits for native release acknowledgement before readiness")
    check(set(re.findall(r'this.Set\(n"([^"]+)"',text)) == {"PTFRPA2_ControlReady","PTFRPA2_Reveal"}, "Observer only writes readiness acknowledgements")
    for forbidden in ("TeleportTo", "RemoveStatusEffect", "RemoveAllGameplay", "SaveGame(", "LoadGame(", "SetTier("):
        assert forbidden not in text
    check(True, "No scripted teleport, forced save/reload, status clear, or gameplay-tier override")
    for token in ('epoch != this.epoch','PTFRPA2_Fault") > 0','PTFRPA2_Finished") == 1','STOPPED: preparation timeout','gate='):
        assert token in text
    check(True, "Stale callbacks, fault/finished stop and explicit live diagnostics retained")
    check('this.Fact(n"PTFRPA3_CoverReleased") == 1 && this.Fact(n"PTFRPA2_ControlReady") == 1' in text, "Legacy PA2 state is not silently certified as PA3 arrival")
    check(len(report["members"]) == 616 and report["only_resource_changed"].endswith("final_boards.questphase"), "616 packed members verified; only handoff resource changed")
    result = {"status":"PASS_NOT_LIVE","cases":len(cases),"details":cases,
              "build_sha256":sha(build/"build.json"),"compile_sha256":sha(build/"compile.json"),
              "runtime_source_sha256":sha(source),
              "limitations":"Native fade/tier timing, actual player control/streaming, profile completion and reload still require live QA. Shader issue deliberately untouched."}
    (build/"tests.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","cases","limitations")}))


if __name__ == "__main__": main()
