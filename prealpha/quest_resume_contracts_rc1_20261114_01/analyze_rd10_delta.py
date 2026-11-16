"""Index RD10 graph changes without promoting source references to live contracts."""

import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG_DIR = ROOT / "prealpha/quest_resume_registry_20261112_01"
sys.path.insert(0, str(REG_DIR))
from model import effects, journal_refs, load_export, normalize, resource_refs, walk  # noqa: E402


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def main():
    source = HERE / "delta_capture_01/manifest.json"
    target = HERE / "delta_analysis_01.json"
    assert not target.exists()
    capture = json.loads(source.read_text(encoding="utf-8-sig"))
    registry_path = REG_DIR / "registry_02/registry.sqlite3"
    assert sha(registry_path) == "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9"
    db = sqlite3.connect(registry_path.resolve().as_uri() + "?mode=ro", uri=True)
    roots = list(db.execute("SELECT id,journal_root FROM quests WHERE selection='INCLUDE'"))
    rows, affected = [], defaultdict(set)
    for row in capture["rows"]:
        path = Path(row["export"])
        assert sha(path) == row["export_sha256"]
        normalized = normalize(load_export(path))
        graph_rows = []
        all_refs, all_calls = set(), set()
        site_count, reward_count = 0, 0
        for graph in normalized["graphs"]:
            graph_sites = []
            for node in graph["nodes"]:
                params = node["parameters"]
                refs = journal_refs(params)
                write = any(x.get("$type") == "questJournalNodeDefinition" for x in walk(params))
                for stage_path, stage_class in refs:
                    matched = [qid for qid, root in roots
                               if stage_path == root or stage_path.startswith(root + "/")]
                    for qid in matched:
                        affected[qid].add(row["depot"])
                    graph_sites.append({"node": node["id"], "path": stage_path,
                                        "class": stage_class, "operation": "WRITE" if write else "READ",
                                        "selected_quests": matched})
                all_refs.update(resource_refs(params))
                for x in walk(params):
                    for field in ("phaseResource", "sceneFile"):
                        if field in x:
                            all_calls.update(resource_refs(x[field]))
                reward_count += len(effects(params))
            site_count += len(graph_sites)
            graph_rows.append({"graph": graph["path"], "kind": graph["kind"],
                               "nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
                               "journal_sites": graph_sites,
                               "unresolved_connections": len(graph.get("unresolved_connections", [])),
                               "unresolved_scene_destinations": len(graph.get("unresolved_scene_destinations", []))})
        rows.append({"depot": row["depot"], "change": row["change"],
                     "raw_sha256": row["sha256"], "export_sha256": row["export_sha256"],
                     "graphs": graph_rows, "journal_site_count": site_count,
                     "potential_reward_inventory_effects": reward_count,
                     "support_resource_references": resource_refs(normalized["support"]),
                     "node_resource_references": sorted(all_refs),
                     "called_phase_or_scene_resources": sorted(all_calls)})
    result = {"status": "RD10_GRAPH_DELTA_SOURCE_ONLY", "source_sha256": sha(source),
              "resource_count": len(rows),
              "selected_quest_matches": {qid: sorted(depots) for qid, depots in sorted(affected.items())},
              "resources": rows,
              "limits": ["Prefix matching does not prove caller feasibility or active ownership.",
                         "Indexed effects are potential sites, not paid rewards or safe replay receipts.",
                         "New phase ownership and current XL registration require separate review."]}
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"resources": len(rows), "selected_quest_matches": len(affected),
                      "journal_sites": sum(row["journal_site_count"] for row in rows),
                      "potential_effects": sum(row["potential_reward_inventory_effects"] for row in rows)}))


if __name__ == "__main__":
    main()
