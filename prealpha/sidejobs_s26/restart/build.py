"""Build an additive, manual, read-only S26 capture. Never runs an old builder."""
import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def build(revision):
    assert re.fullmatch(r"capture_\d{2}", revision)
    out = HERE / "build" / revision
    assert not out.exists(), "Immutable output exists"
    donor = ROOT / "prealpha/sidejobs_s23/capture/build/capture_02"
    old = read(donor / "build.json")
    assert sha(donor / "build.json") == "DB5C2529D306B312047757A8A06D94607525710556C630B1A9BB17B34051F524"
    assert sha(donor / "data.json") == old["files"]["data.json"]
    coverage_path = ROOT / "prealpha/sidejobs_s25/build/s25_04/coverage.json"
    coverage = read(coverage_path)
    d = copy.deepcopy(read(donor / "data.json"))
    assert len(d["jobs"]) == len(coverage["jobs"]) == 58
    assert [r["id"] for r in d["jobs"]] == [r["id"] for r in coverage["jobs"]]
    probe = ROOT / "prealpha/sidejobs_s26/cassius/probe.lua"
    pins = [Path(__file__), HERE / "init.lua", HERE / "policy.json", HERE / "analyze.py", donor / "build.json", donor / "data.json", coverage_path,
            probe, ROOT / "prealpha/sidejobs_s26/cassius/test_probe.py", ROOT / "research/sidejobs_s26/cassius/probe_tests_01.json",
            ROOT / "research/sidejobs_s26/cassius/native_records_02.json",
            ROOT / "prealpha/sidejobs_s25/build/s25_04/SideJobsS22.reds",
            ROOT / "research/sidejobs_s22/the_gig/native_01/json/base/quest/main_quests/prologue/q001/phases/q101_wakako_reward.questphase.json",
            ROOT / "research/restriction_profiles/body_stats_design/current_base.script",
            ROOT / "research/restriction_profiles/ban_design/decompiled_current/core/systems/journalManager.script",
            ROOT / "research/gig_restoration/probe_api_findings.json",
            ROOT / "diagnostics/PTFR_FreshGigsB5/init.lua",
            ROOT / "prealpha/sidejobs_s2/admission.json"]
    # Literal runtime tag mappings supplement human-readable coverage labels.
    extra = {"mq025_psycho_brawl": ["PTFRS22_MQ025"], "sq025_delamain": ["PTFRS22_SQ025"],
             "q304_car_retrieval": ["PTFRS22_Q304"], "sq_q001_wakako": ["PTFRS22_SQ_Q001"]}
    suffixes = ["Ready", "Request", "Permit", "Issued", "Entered", "Finished", "Fault"]
    for row, cov in zip(d["jobs"], coverage["jobs"]):
        tags = {r["owner"] for r in cov["bounded_routes"] if re.fullmatch(r"PTFR[A-Za-z0-9_]+", r["owner"])}
        tags.update(extra.get(row["id"], []))
        row["owners"] = [{"tag": tag, "facts": [tag + "_" + suffix for suffix in suffixes]} for tag in sorted(tags)]
        row["graph_liveness"] = "NOT_OBSERVED: owned facts are not node-state/retirement proof"
        row["reward_history"] = "UNKNOWN: current journal/facts/items are not a complete payout ledger"
    # These names are present in source-backed native The Gig reward flow.
    gig = next(r for r in d["jobs"] if r["id"] == "sq_q001_wakako")
    gig["facts"] = sorted(set(gig["facts"]) | {"q001_wakako_reward_given", "sq_q001_add_reward", "sq_q001_done", "sq_q001_active"})
    d["context_facts"] = sorted(set(d["context_facts"]) | {
        "q307_debug_reset", "q115_point_of_no_return", "q305_johnny_scene_active", "holo_setup_active", "holo_setup_started",
        "PTFRS22_SQ025_SupportIssued", "PTFRS23_MQ007_ModeTalkConfirmed",
        "PTFRS2_MQ032_AuthorizedRoute", "PTFRS2_MQ032_Denied", "PTFRS2_MQ032_Fault"})
    d["items"] = [
        {"id": "Items.YakuzaTattoo", "jobs": ["sq_q001_wakako"], "purpose": "Native reward-completion alternative; current player quantity only"},
        {"id": "Items.AdvancedYakuzaTattoo", "jobs": ["sq_q001_wakako"], "purpose": "Native reward-completion alternative; current player quantity only"}
    ]
    d["schema"] = 2
    d["kind"] = "S26_READ_ONLY_RESTART_AND_SERVICE_CAPTURE"
    d["policy"] = read(HERE / "policy.json")
    d["donor_catalogue_sha256"] = sha(donor / "data.json")
    d["coverage_sha256"] = sha(coverage_path)
    d["owner_suffix_limit"] = "Standard diagnostic fact names only; absent names read as zero. Neither zero nor one proves executable graph state."
    d["vendor_stock"] = "Capture does not query or generate vendor stock. Optional explicit ArmCassius buffers existing native stock/UI fields only after normal user shop events; unavailable fields remain Unknown. No stock getters, initialization, restock or forced purchase."
    out.mkdir(parents=True)
    (out / "data.json").write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
    (out / "init.lua").write_text(probe.read_text(encoding="utf-8-sig") + "\n" + (HERE / "init.lua").read_text(encoding="utf-8-sig"), encoding="utf-8")
    manifest = {"status": "BUILT_READ_ONLY_CAPTURE_NOT_RESTORATION", "schema": 1,
                "jobs": 58, "journals": sum(len(r["journals"]) for r in d["jobs"]),
                "facts": sum(len(r["facts"]) for r in d["jobs"]), "root_only": [],
                "owner_observations": sum(len(r["owners"]) for r in d["jobs"]), "item_queries": len(d["items"]),
                "automatic_callbacks": 0, "native_writes": 0, "save_writes": 0,
                "manual_observers": ["Vendor.OnVendorMenuOpen", "RipperDocGameController.PrepareVendorItems", "RipperDocGameController.OnSlotClick"],
                "manual_observer_count": 3, "observers_registered_at_load": 0, "capture_stops_manual_observation": True,
                "files": {name: sha(out / name) for name in ["init.lua", "data.json"]},
                "source_pins": {p.relative_to(ROOT).as_posix(): sha(p) for p in pins},
                "installed_module": "PTFR_SideJobsCaptureS26", "manual_command": 'print(GetMod("PTFR_SideJobsCaptureS26").Capture())',
                "limits": "Source catalogue and manual native getter observations; no executable graph liveness, retirement or payout-history proof. No restart implementation."}
    (out / "build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ["status", "jobs", "journals", "facts", "owner_observations", "item_queries"]}))


if __name__ == "__main__":
    build(sys.argv[1])
