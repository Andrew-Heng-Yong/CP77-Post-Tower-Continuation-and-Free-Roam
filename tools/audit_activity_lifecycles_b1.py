"""Source-linked B1 lifecycle findings; refuses to call this runtime admission."""
import json
from pathlib import Path

from audit_activity_batches_b1 import OUT, flatten, references, stable_write
from catalog_gig_rollout_r2 import ROOT, read, sha, value, walk
from test_gig_pilot_r1 import Resource

PAIR = ROOT / "research/gig_restoration/rollout_r2/live_pair.json"
GIG_IDS = ("sts_wat_kab_101", "sts_wat_kab_102", "sts_wat_kab_107", "sts_wat_nid_05")
SIDE_STATUS = {
    "mq011_wilson": "DEFER_COMPLEX_PHONE_CONTEST_SCENE_REWARDS",
    "mq013_punks": "DEFER_SHARED_RACE_VENDOR_AND_PASSIVE_ACTIVE_STAGE_AUDIT",
    "mq030_melisa": "DEFER_JOHNNY_SCENE_AND_FOLLOWUP_ADAPTER",
}


def scene_summary(path):
    obj = read(path)
    r = Resource(obj)
    actors = [{"name": v.get("actorName", v.get("playerName")), "type": v["$type"],
               "acquisition": v.get("acquisitionPlan"),
               "community": v.get("communityParams"),
               "spawn": v.get("spawnDespawnParams"),
               "context": v.get("findActorInContextParams")}
              for v in walk(obj) if v.get("$type") in ("scnActorDef", "scnPlayerActorDef")]
    effects = [r.payload(v) for v in walk(obj) if v.get("$type") in
               ("questSetVar_NodeType", "questGiveReward_NodeType", "questAddRemoveItem_NodeType",
                "questInjectLoot_NodeType", "questGiveItem_NodeType")]
    return {"source": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path),
            "actors": actors, "johnny_cast": any(str(a["name"]).casefold() == "johnny" for a in actors),
            "facts": sorted({str(value(v["factName"])) for v in walk(obj) if "factName" in v}),
            "effects": effects, "phase_references": references(obj, "phaseResource"),
            "scene_references": references(obj, "sceneFile")}


def index_inventory(folder):
    base = OUT / folder
    inventory = read(base / "inventory.json")
    result = {}
    for item in inventory:
        raw = base / "raw" / Path(item["resource"].replace("\\", "/"))
        js = base / "json" / Path(item["resource"].replace("\\", "/") + ".json")
        assert sha(raw) == item["raw_sha256"], item["resource"]
        if item["json_sha256"] is None:
            assert item.get("decode_error") and not js.exists(), item["resource"]
            continue  # Undecoded != empty. Community-body review remains pending.
        assert sha(js) == item["json_sha256"], item["resource"]
        result[item["resource"]] = js
    return result


def condition_value(node, facts):
    """Conservative fact-only evaluator for an already identified source node.

    NOT a quest scheduler: timers, triggers, journal conditions, missing facts,
    and other native conditions are unknown, never assumed successful.
    """
    if node.get("$type") == "questLogicalCondition":
        results = [condition_value(c, facts) for c in node["conditions"]]
        if node["operation"] == "AND":
            return False if False in results else True if all(r is True for r in results) else None
        if node["operation"] == "OR":
            return True if True in results else False if all(r is False for r in results) else None
        return None
    if node.get("$type") != "questFactsDBCondition":
        return None
    var = node.get("type", {})
    if var.get("$type") != "questVarComparison_ConditionType" or var.get("factName") not in facts:
        return None
    a, b = facts[var["factName"]], var["value"]
    if type(a) is not int or type(b) is not int:
        return None
    return {"Equal": a == b, "NotEqual": a != b, "Greater": a > b, "GreaterOrEqual": a >= b,
            "Less": a < b, "LessOrEqual": a <= b}.get(var["comparisonType"])


def build():
    structural = read(OUT / "structural_review.json")
    catalogue_path = ROOT / "research/gig_restoration/rollout_r2/catalogue.json"
    catalogue = {j["id"]: j for j in read(catalogue_path)["jobs"]}
    pair = read(PAIR)
    assert len(pair["pair"]) == 2 and {s["world"] for s in pair["pair"]} == {"PRE_TOWER", "POST_TOWER"}
    source_inputs = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                     for p in (OUT / "structural_review.json", catalogue_path, PAIR)}
    side_index = index_inventory("native_sources")
    gig_index = index_inventory("gig_sources")
    inventories = [OUT / f / "inventory.json" for f in ("native_sources", "gig_sources")]
    source_inputs.update({str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in inventories})
    decode_gaps = [item for p in inventories for item in read(p) if item.get("decode_error")]
    library = {}
    for ident in GIG_IDS:
        for meta in catalogue[ident]["native_resources"]:
            p = ROOT / meta["source"]
            assert sha(p) == meta["sha256"], meta["source"]
            source_inputs[meta["source"]] = sha(p)
            obj = read(p)
            library[meta["depot_path"]] = (Resource(obj), obj["Data"]["EmbeddedFiles"][meta["embedded_index"]]["Content"], meta)

    def closure(first, index):
        pending, seen, resources, scenes, unresolved = [first], set(), [], [], []
        while pending:
            depot = pending.pop()
            if depot in seen:
                continue
            seen.add(depot)
            if depot.endswith(".questphase"):
                if depot in library:
                    r, root, meta = library[depot]
                    graphs = flatten(r, root)
                    resources.append({"depot": depot, "binding": meta, "graphs": graphs,
                                      "phase_prefabs": root.get("phasePrefabs", [])})
                    pending.extend(references(root, "phaseResource"))
                    pending.extend(references(root, "sceneFile"))
                elif depot in index:
                    p = index[depot]; r = Resource(read(p)); root = r.obj["Data"]["RootChunk"]
                    source_inputs[str(p.relative_to(ROOT)).replace("\\", "/")] = sha(p)
                    resources.append({"depot": depot, "source": str(p.relative_to(ROOT)).replace("\\", "/"),
                                      "sha256": sha(p), "graphs": flatten(r, root),
                                      "phase_prefabs": root.get("phasePrefabs", [])})
                    pending.extend(references(root, "phaseResource"))
                    pending.extend(references(root, "sceneFile"))
                else:
                    unresolved.append(depot)
            elif depot.endswith(".scene"):
                if depot in index:
                    row = scene_summary(index[depot]); scenes.append(row)
                    source_inputs[row["source"]] = row["sha256"]
                    pending.extend(row["phase_references"]); pending.extend(row["scene_references"])
                else:
                    unresolved.append(depot)
            else:
                unresolved.append(depot)  # Nonzero hashed/unrecognized reference is not resolved coverage.
        return {"resources": resources, "scenes": scenes, "unresolved": sorted(unresolved)}

    sides = []
    for row in structural["next_source_review"]:
        first = row["source"].split("native_sources/json/", 1)[1][:-5].replace("/", "\\")
        data = closure(first, side_index)
        assert not data["unresolved"], (row["id"], data["unresolved"])
        sides.append({"id": row["id"], "title": row["title"], "disposition": SIDE_STATUS[row["id"]], **data})
    gigs = []
    for ident in GIG_IDS:
        job = catalogue[ident]
        # Catalogue order is embedded-file order, NOT owner hierarchy. Begin at
        # the world-prefab owner or scene/combat dependencies can be omitted.
        owners = [m["depot_path"] for m in job["native_resources"]
                  if library[m["depot_path"]][1].get("phasePrefabs")]
        assert len(owners) == 1, (ident, "missing/ambiguous world-prefab owner")
        first = owners[0]
        data = closure(first, gig_index)
        assert not data["unresolved"], (ident, data["unresolved"])
        snapshots = []
        for capture in pair["pair"]:
            snapshot = capture["snapshot"]
            snapshots.append({"world": capture["world"], "utc": capture["utc"],
                              "journal": {e["path"]: snapshot["journal"][e["path"]] for e in job["journal_entries"]},
                              "local_facts": {f: snapshot["facts"].get(f) for f in job["fact_names"]}})
        gigs.append({"id": ident, "title": job["selected_title"], "captures": snapshots, **data,
                     "disposition": "NEXT_EXACT_STARTED_STAGE_RESUME_AUDIT" if ident == "sts_wat_nid_05" else "DEFER_NORMAL_DISTRICT_GATE_BLOCKED_ON_CAPTURED_PAIR"})

    # Exact local tier alternatives feeding normal In1, not guesses from titles.
    # Source POI waits remain separate; these are gate observations, NOT native
    # scheduler execution proof or permission to create tiers/POIs.
    kab_source = ROOT / catalogue["sts_wat_kab_107"]["native_resources"][0]["source"]
    r = Resource(read(kab_source)); graph = r.obj["Data"]["RootChunk"]["graph"]
    nodes, edges = r.nodes(graph), r.edges(graph)
    witnesses = {
        "sts_wat_kab_107": ([0, 2, 155, 153, 152, 112, 128, 118, 19], [0, 2, 155, 154, 152, 127, 128, 118, 19]),
        "sts_wat_kab_102": ([0, 2, 155, 153, 152, 111, 126, 117, 22], [0, 2, 155, 154, 152, 125, 126, 117, 22]),
        "sts_wat_kab_101": ([0, 3, 91, 144, 102, 139, 122, 67, 17], [0, 3, 145, 144, 138, 139, 122, 67, 17]),
    }
    gates = []
    for ident, routes in witnesses.items():
        for route in routes:
            assert all(any(e[0] == a and e[2] == b for e in edges) for a, b in zip(route, route[1:])), (ident, route)
        condition_nodes = [153, 154] if ident != "sts_wat_kab_101" else [91, 145]
        evaluations = [{"world": s["world"], "nodes": [{"node": n, "condition": r.payload(nodes[n])["condition"],
                        "fact_only_value": condition_value(r.payload(nodes[n])["condition"], s["snapshot"]["facts"])}
                       for n in condition_nodes]} for s in pair["pair"]]
        assert all(v["fact_only_value"] is False for ev in evaluations for v in ev["nodes"])
        gates.append({"id": ident, "source": str(kab_source.relative_to(ROOT)).replace("\\", "/"),
                      "normal_route_witnesses": routes, "evaluations": evaluations,
                      "limitation": "Selected source route witnesses are not a full scheduler or alternate-entry proof. Do not force tiers, POIs or debug starts."})
    return {"schema": 1, "revision": 3,
            "supersedes": "lifecycle_review_r2.json (same findings; explicit reference scope and fail-closed unknown references added)",
            "initial_review_correction": "lifecycle_review.json started from catalogue order, not the prefab owner; revision 2 corrected its incomplete scene closure.",
            "status": "SOURCE_AUDIT_NO_NEW_RUNTIME_ADAPTER", "source_inputs": source_inputs,
            "closure_scope": ["quest phaseResource", "quest sceneFile", "same fields in decoded scenes"],
            "side_jobs": sides, "gigs": gigs, "kabuki_gate_review": gates,
            "next_adapter": {"id": "sts_wat_nid_05", "title": "Rite of Passage", "mode": "resume",
                             "required_remaining_review": ["Safe resume entry bypassing repeated start/prebrief.",
                                                           "Clinic recording ownership/device stage and profile-compatible access.",
                                                           "Reward/counter single-claim bridge and native departure cleanup.",
                                                           "Fixer retaliation/after-gig world ownership and cross-job journal effects.",
                                                           "Save-local baseline admission and override dispatch, compiler/graph/model/deployment checks."]},
            "newly_restored": 0, "installed_changes": 0, "game_writes": 0, "save_writes": 0,
            "community_decode_gaps": decode_gaps,
            "completed_replay_implemented": False}


def main():
    result = build(); stable_write(OUT / "lifecycle_review_r3.json", result)
    print(json.dumps({"status": result["status"], "sides": [{"id": j["id"], "disposition": j["disposition"],
                      "scenes": len(j["scenes"]), "johnny_cast": any(s["johnny_cast"] for s in j["scenes"])} for j in result["side_jobs"]],
                      "gigs": [{"id": j["id"], "disposition": j["disposition"], "scenes": len(j["scenes"]),
                                "johnny_cast": any(s["johnny_cast"] for s in j["scenes"])} for j in result["gigs"]],
                      "next": result["next_adapter"]}, indent=2))


if __name__ == "__main__":
    main()
