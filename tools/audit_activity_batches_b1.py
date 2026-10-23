"""Read-only structural review of the selected activities.

Writes a separate B1 audit, never the installed R3 definition or older evidence.
Catalogue coverage is not freshness, unlock, replay, or restoration proof.
"""
from collections import Counter
import json
from pathlib import Path

from catalog_gig_rollout_r2 import ROOT, read, sha, value, walk
from test_gig_pilot_r1 import Resource

OUT = ROOT / "research/activity_batches_b1"
DEFINITION = ROOT / "research/activity_state_r3/definition.json"
GIGS = ROOT / "research/gig_restoration/rollout_r2/catalogue.json"
PARENT = ROOT / "research/afterlife_world/nix_sources/json/base/quest/minor_quests/minorquests.questphase.json"
REVIEW = {"mq011_wilson": "mq011", "mq013_punks": "mq013", "mq030_melisa": "mq030"}


def flatten(resource, root):
    graphs = []

    def visit(graph, path):
        nodes = resource.nodes(graph)
        graphs.append({"path": path, "nodes": [resource.payload(n) for n in nodes.values()],
                       "edges": [list(e) for e in sorted(resource.edges(graph))]})
        for ident, node in nodes.items():
            nested = resource.d(node.get("phaseGraph", {}))
            if isinstance(nested, dict) and "nodes" in nested:
                visit(nested, path + "/" + str(ident))
    visit(root["graph"], "root")
    return graphs


def references(root, field):
    values = []
    for v in walk(root):
        if field in v:
            ref = v[field]
            if isinstance(ref, dict) and "DepotPath" in ref:
                ref = ref["DepotPath"]
            path = value(ref)
            if path is not None and path != "0":
                values.append(str(path))
    return sorted(set(values))


def family(job):
    ident = job["id"]
    if job["category"] == "gig":
        return "dogtown_gig" if ident.startswith("sts_ep1_") else "base_fixer_gig"
    if ident.startswith(("sq025", "sq024", "07_nc_")):
        return "linked_vehicle_chain"
    if ident.startswith("mq025"):
        return "linked_boxing_chain"
    if ident.startswith("mq037"):
        return "linked_brendan_chain"
    if ident.startswith(("mq303", "mq305", "wst_ep1_", "q304", "sts_ep1_")):
        return "dlc_side_owner"
    if not job.get("native_fact_sources"):
        return "side_binding_unresolved"
    return "base_side_owner"


def stable_write(path, obj):
    data = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    # Re-running an identical read-only audit is safe; changed findings get a new
    # revision rather than silently overwriting the recorded source review.
    if path.exists() and path.read_text(encoding="utf-8") != data:
        raise ValueError("Changed B1 evidence; write a separately reviewed revision: " + str(path))
    if not path.exists():
        path.write_text(data, encoding="utf-8")


def build():
    definition = read(DEFINITION)
    gig_definition = read(GIGS)
    catalogue = {j["id"]: j for j in gig_definition["jobs"]}
    assert len(definition["jobs"]) == 128
    assert len({j["id"] for j in definition["jobs"]}) == 128
    sources = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in (DEFINITION, GIGS, PARENT)}
    rows = []
    for job in definition["jobs"]:
        if job["category"] == "gig":
            gig = catalogue[job["id"]]
            native = gig["native_resources"]
            source_names = sorted({r["source"] for r in native})
            owner_count = len(native)
        else:
            source_names = job.get("native_fact_sources", [])
            owner_count = None  # Prefix fact-source count is NOT an owner count.
        for name in source_names:
            p = ROOT / name
            expected = definition["source_inputs"].get(name, gig_definition["source_inputs"].get(name))
            actual = sha(p)
            assert expected is not None and actual == expected, (name, "unpinned/changed native source")
            sources[name] = actual
        adapter = "G1_resume" if job["id"] == "sts_wat_nid_02" else "S1_fresh" if job["id"] == "mq005_alley" else None
        rows.append({"id": job["id"], "title": job["selected_title"], "category": job["category"],
                     "family": family(job), "journal_entries": len(job["journal_entries"]),
                     "catalogued_native_resource_count": owner_count, "source_files": source_names,
                     "adapter": adapter, "completed_replay": False,
                     "admission": "EXISTING_PER_OWNER_GUARDS" if adapter else "UNIMPLEMENTED_NOT_ADMITTED"})

    parent = Resource(read(PARENT))
    parent_graphs = flatten(parent, parent.obj["Data"]["RootChunk"])
    reviews = []
    for ident, prefix in REVIEW.items():
        job = next(j for j in definition["jobs"] if j["id"] == ident)
        owner = ROOT / f"research/activity_state_r3/native_sources/json/base/quest/minor_quests/{prefix}/{prefix}.questphase.json"
        resource = Resource(read(owner))
        root = resource.obj["Data"]["RootChunk"]
        graphs = flatten(resource, root)
        bindings = [{"graph": g["path"], "node": n["id"], "payload": n,
                     "incoming": [e for e in g["edges"] if e[2] == n["id"]]}
                    for g in parent_graphs for n in g["nodes"]
                    if str(value(n.get("phaseResource", {}).get("DepotPath"))).endswith(f"\\{prefix}\\{prefix}.questphase")]
        assert len(bindings) == 1, (ident, "ambiguous normal parent binding")
        reviews.append({"id": ident, "title": job["selected_title"],
                        "source": str(owner.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": sha(owner), "parent_binding": bindings[0],
                        "phase_prefabs": root.get("phasePrefabs"), "graphs": graphs,
                        "scene_paths": references(root, "sceneFile"),
                        "facts": sorted({v["factName"] for v in walk(root) if "factName" in v}),
                        "review_status": "STRUCTURAL_REVIEW_ONLY_SCENE_AND_LIFECYCLE_AUDIT_REQUIRED"})
        sources[str(owner.relative_to(ROOT)).replace("\\", "/")] = sha(owner)
    return {"schema": 1, "status": "OFFLINE_BATCH_PLANNING_NOT_NEW_RESTORATION",
            "jobs": rows, "family_counts": dict(sorted(Counter(r["family"] for r in rows).items())),
            "implemented_adapters": 2, "remaining_adapters": 126, "completed_replay_adapters": 0,
            "source_inputs": sources, "next_source_review": reviews, "parent_graphs": parent_graphs,
            "game_writes": 0, "save_writes": 0, "runtime_newly_admitted": 0,
            "limitations": ["Prefix source coverage does not prove a physical owner binding.",
                            "Inactive journal and zero facts alone do not prove fresh/unlocked.",
                            "Shared families do not authorize restarting their parent quest.",
                            "No new adapter or completed replay is implemented by this index."]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = build()
    stable_write(OUT / "structural_review.json", result)
    print(json.dumps({"status": result["status"], "families": result["family_counts"],
                      "remaining_adapters": result["remaining_adapters"],
                      "review": [{k: r[k] for k in ("id", "title", "scene_paths")} for r in result["next_source_review"]]}, indent=2))


if __name__ == "__main__":
    main()
