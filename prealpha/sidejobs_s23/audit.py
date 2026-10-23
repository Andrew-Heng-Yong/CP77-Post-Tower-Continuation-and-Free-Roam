"""S23 read-only source inventory. Never starts or edits a game quest.

This is a coverage audit, not a generic restart recipe. Entry writes and shared
services still require a per-family review before they can be admitted.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "prealpha/ncpd_scanner_n1"), str(ROOT / "tools")]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read, sha, walk, value

INVENTORY = ROOT / "research/sidejobs_s21_failed/inventory_02.json"
PARENT = ROOT / "research/sidejobs_s2/sacrum_audit/native_01/json/base/quest/minor_quests/minorquests.questphase.json"


def graphs(path):
    resource = SafeResource(read(path))
    return flatten(resource, resource.obj["Data"]["RootChunk"])


def inspect(path, graph_filter=None):
    for graph in graphs(path):
        if graph_filter and graph["path"] != graph_filter:
            continue
        print("GRAPH", graph["path"])
        for node in graph["nodes"]:
            payload = {k: v for k, v in node.items() if k not in ("id", "$type", "phaseGraph")}
            print(node["id"], node["$type"], json.dumps(payload, separators=(",", ":")))
        print("EDGES", json.dumps(graph["edges"], separators=(",", ":")))


def coverage(output):
    original = read(INVENTORY)
    installed = {
        "mq005_alley": "S1.1 fresh only",
        "mq032_sacrum": "S2 fresh only",
        "mq008_party": "S2 fresh only",
        "sq_q001_wakako": "S22 reward-tail resume only",
        "mq025_psycho_brawl": "S22 intro-complete/no-bout resume only",
        "sq025_delamain": "S22.1 three-completed/four-pending resume only",
        "q304_car_retrieval": "S22 accepted-message/first-door resume only",
    }
    rows = []
    pins = {str(INVENTORY.relative_to(ROOT)): sha(INVENTORY), str(PARENT.relative_to(ROOT)): sha(PARENT)}
    for job in original["jobs"]:
        candidates = job["native_root_phase_candidates"]
        sources = []
        for relative in candidates:
            path = ROOT / relative
            if not path.exists():
                raise ValueError("Missing catalogued source: " + relative)
            pins[relative] = sha(path)
            gs = graphs(path)
            writes = []
            calls = set()
            for graph in gs:
                for node in graph["nodes"]:
                    for obj in walk(node):
                        if obj.get("$type") == "questSetVar_NodeType":
                            writes.append({"graph": graph["path"], "node": node["id"], "payload": obj})
                        if "phaseResource" in obj:
                            ref = value(obj["phaseResource"].get("DepotPath"))
                            if ref and ref != "0":
                                calls.add(ref)
            sources.append({"source": relative, "graphs": len(gs), "nodes": sum(len(g["nodes"]) for g in gs),
                            "native_writes": writes, "phase_references": sorted(calls)})
        family = job["execution_owner_family"]
        parent_owner = None
        if job["id"].startswith("mq025_"):
            parent_owner = "mq025_psycho_brawl"
        elif job["id"].startswith("sq025c"):
            parent_owner = "sq025_delamain"
        rows.append({"id": job["id"], "title": job["title"], "journal_path": job["journal_path"],
                     "family": family, "existing_adapter": installed.get(job["id"]),
                     "existing_parent_adapter": installed.get(parent_owner),
                     "all_states_supported": False, "native_parent_refs": job["native_parent_refs"],
                     "sources": sources, "s23_status": "NOT_YET_IMPLEMENTED"})
    result = {"schema": 1, "status": "COVERAGE_ONLY_NOT_RESTORATION_PROOF", "roots": len(rows),
              "policy": {"current": "whitelisted post-Tower Failed OR Inactive", "future": "whitelisted pre-Tower Inactive, separately certified",
                         "preserve": "partial progress, Succeeded children, choices, rewards; Johnny voice with hidden body"},
              "jobs": rows, "source_pins": pins, "runtime_changes": 0}
    assert len(rows) == 58 and len({r["id"] for r in rows}) == 58
    if output.exists():
        raise ValueError("Immutable report already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"roots": 58, "existing_top_level_adapters": len(installed), "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", type=Path)
    parser.add_argument("--graph")
    parser.add_argument("--coverage", type=Path)
    args = parser.parse_args()
    if args.inspect:
        inspect(args.inspect, args.graph)
    elif args.coverage:
        coverage(args.coverage)
    else:
        parser.error("Choose --inspect or --coverage")
