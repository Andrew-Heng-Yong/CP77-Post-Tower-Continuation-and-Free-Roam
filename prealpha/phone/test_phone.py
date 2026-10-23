"""Validate the actual phone wrapper delta and source-backed admission semantics.

This does not simulate the game's scheduler or claim a live call passed.
"""
import copy
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from catalog_gig_rollout_r2 import read, sha, walk
from review_stock_shark_u2 import graph
from test_rite_g2 import SafeResource

OUT = ROOT / "research/pre_alpha_clean/phone"
SOURCE = ROOT / "research/gig_restoration/gig_phone_u9"
SCRIPT = ROOT / "prealpha/phone/scripts/GigPhoneU9.reds"


def evaluate(c, facts):
    if c["$type"] == "questLogicalCondition":
        assert c["operation"] == "AND"
        return all(evaluate(x, facts) for x in c["conditions"])
    t = c["type"]
    assert t["comparisonType"] == "Equal"
    if "factName" in t:
        return facts.get(t["factName"], 0) == t["value"]
    return facts.get(t["factName1"], 0) == facts.get(t["factName2"], 0)


def main():
    old = read(SOURCE / "manifest.json")
    built = read(OUT / "manifest.json")
    pins = {}
    for f in old["files"]:
        assert sha(ROOT / f["source"]) == f["sha256"]
    for p, h in old["source_pins"].items():
        assert sha(ROOT / p) == h
        pins[p] = h
    before = graph(SOURCE / "support_wrapper.json")["root"]
    after = graph(OUT / "support_wrapper.json")["root"]
    expected = copy.deepcopy(before)
    removed = []
    for node in expected["nodes"]:
        if node["id"] == 2:
            assert node["type"]["value"] == 1
            node["type"]["value"] = 2
        if node["id"] in (3, 4):
            conditions = node["condition"]["conditions"]
            gone = [c for c in conditions if "factName1" in c.get("type", {})]
            assert len(gone) == 16
            assert {(c["type"]["factName1"], c["type"]["factName2"]) for c in gone} == set(map(tuple, old["balances"]))
            removed.extend(gone)
            node["condition"]["conditions"] = [c for c in conditions if c not in gone]
    assert after == expected, "Wrapper changed outside admitted equality/revision delta"
    n = {x["id"]: x for x in after["nodes"]}
    previous = {x["id"]: x for x in before["nodes"]}
    assert n[3]["condition"] == n[4]["condition"]
    assert len(removed) == 32
    facts = dict(old["guard_pairs"])
    assert evaluate(n[3]["condition"], facts)
    cases = 1
    for start, end in old["balances"]:
        for a, b in itertools.product((0, 1, 2, 6, 14, 1000), repeat=2):
            f = dict(facts, **{start: a, end: b})
            assert evaluate(n[3]["condition"], f)
            assert evaluate(previous[3]["condition"], f) == (a == b)
            cases += 1
    # Regress the genuine pre-ending historical mismatches independently of
    # all transient protocol/owned/lifecycle guards, then perturb EVERY guard.
    mismatch = dict(facts)
    for c, a, b in (("dino", 2, 1), ("mr_hands", 13, 10), ("muamar", 7, 6), ("reggie", 14, 6), ("wakako", 4, 2)):
        mismatch[f"holo_{c}_calls_v_start_count"] = a
        mismatch[f"holo_{c}_calls_v_end_count"] = b
    assert evaluate(n[3]["condition"], mismatch)
    assert not evaluate(previous[3]["condition"], mismatch)
    for fact in facts:
        for offset in (-1, 1):
            bad = dict(mismatch)
            bad[fact] += offset
            assert not evaluate(n[3]["condition"], bad), fact
            cases += 1
    # All eight stock controller graphs admit calls via request/queue/setup
    # predicates; none compares the historical start and end counters.
    native = []
    for contact in old["contacts"]:
        p = SOURCE / f"sources/json/base/quest/holocalls/{contact}/{contact}_holocall.questphase.json"
        cleanup_path = SOURCE / f"sources/json/base/quest/holocalls/{contact}/{contact}_cleanup.questphase.json"
        g = graph(p)["root"]
        cleanup = graph(cleanup_path)["root"]
        prefix = f"holo_{contact}_calls_v_"
        tested = [x.get("factName", "") for x in walk(g)]
        lifetime = {f"holo_{contact}_calls_v_start_count", f"holo_{contact}_calls_v_end_count", f"holo_v_calls_{contact}_start_count", f"holo_v_calls_{contact}_end_count"}
        assert not lifetime.intersection(tested)
        assert {prefix + "start_activate", prefix + "start_activate_count", "holo_setup_active", "holo_setup_started"} <= set(tested)
        writes = [x for x in walk(cleanup) if x.get("$type") == "questSetVar_NodeType"]
        assert not lifetime.intersection(x.get("factName", "") for x in writes)
        pins[str(p.relative_to(ROOT))] = sha(p)
        pins[str(cleanup_path.relative_to(ROOT))] = sha(cleanup_path)
        cleanup_comparisons = [x for x in walk(cleanup) if x.get("$type") == "questVarVsVarComparison_ConditionType"]
        assert {x["factName1"] for x in cleanup_comparisons} == {f"holo_{contact}_calls_v_start_count", f"holo_v_calls_{contact}_start_count"}
        assert all(x["comparisonType"] == "Greater" for x in cleanup_comparisons)
        native.append({"contact": contact, "controller": str(p.relative_to(ROOT)), "controller_lifetime_counter_conditions": 0, "cleanup_lifetime_counter_writes": 0, "native_cleanup_comparisons_preserved": cleanup_comparisons})
    scenes = []
    for relative in (
        "research/gig_restoration/stock_shark_u2/sources/json/base/quest/holocalls/reggie/reggie_holocall.scene.json",
        "research/gig_restoration/padre_phone_u5/sources/json/base/quest/holocalls/padre/padre_holocall.scene.json",
    ):
        p = ROOT / relative
        raw = read(p)
        writes = [x for x in walk(raw) if x.get("$type") == "questSetVar_NodeType" and re.search(r"(?<!activate)_count$", x.get("factName", "")) and (x["factName"].endswith("start_count") or x["factName"].endswith("end_count"))]
        assert len(writes) == 4
        assert all(x["setExactValue"] == 0 and x["value"] == 1 for x in writes)
        scenes.append({"scene": relative, "increments": writes})
        pins[relative] = sha(p)
    source = SCRIPT.read_text(encoding="utf-8")
    data = (SCRIPT.parent / "GigPhoneDataU9.generated.reds").read_text(encoding="utf-8")
    idle_body = re.search(r"func IdleProtocol\(\) -> Bool \{([^}]+)\}", source).group(1)
    assert "this.AllZero(GigPhoneDataU9.IdleFacts())" in idle_body
    assert "Balance" not in idle_body
    for function, values in (("IdleFacts", old["idle_facts"]), ("PredecessorFacts", old["predecessor_facts"]), ("BalanceStarts", [x[0] for x in old["balances"]]), ("BalanceEnds", [x[1] for x in old["balances"]])):
        body = re.search(r"func " + function + r"\(\).*?return (\[.*?\]);", data).group(1)
        assert json.loads(body) == values
    assert source.count(".SetFact(") == 1
    assert 'SetFact(StringToName("PTFRU9_Support_"+s),v)' in source
    assert 'this.Own("Revision")!=2' in source
    assert 'this.Own("Revision")==2' in source
    assert "GigDataB7" not in source
    for needed in ("NativeGigDataU9.LegacyTags(i)", "NativeGigDataU9.LegacyOwnerFacts(i)", "epoch!=this.epoch", "this.OriginalLifetimeClosed()", "this.LegacyIdle()", "this.LivePhoneIdle()", 'this.Own("Request")!=0 || this.Own("Issued")!=0', "!GameInstance.GetPhoneManager(this.GetGameInstance()).IsPhoneCallActive()"):
        assert needed in source
    for f in built["resources"]:
        assert sha(ROOT / f["source"]) == f["sha256"]
    result = {
        "status": "PASS_PREALPHA_PHONE_SOURCE_AND_GUARD_REGRESSION",
        "predicate_cases": cases,
        "wrapper_exact_delta": True,
        "native_controller_evidence": native,
        "scene_counter_evidence": scenes,
        "source_pins": pins,
        "pinned_predecessor_unchanged": True,
        "new_script_sha256": sha(SCRIPT),
        "manifest_sha256": sha(OUT / "manifest.json"),
        "full_package_compile": "Parent consolidation step required",
        "live_call_test": "Pending fresh ending run; static admission validation only",
        "interpretation": "Stock controller startup uses transient request/queue/setup predicates. The inspected original scenes count separate start and end branch events cumulatively. These totals are not a native startup precondition; mismatches alone do not prove an active call. Actual active/queued calls, shared protocol flags, shutdown/owner guards and live PhoneSystem readiness still block startup. Native cleanup DOES compare start>end to invoke end-scene branches during a future reset. All those cleanup comparisons remain unchanged, and reset/interruption behavior with historical differences remains a required live check.",
    }
    (OUT / "tests.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"], cases)


if __name__ == "__main__":
    main()
