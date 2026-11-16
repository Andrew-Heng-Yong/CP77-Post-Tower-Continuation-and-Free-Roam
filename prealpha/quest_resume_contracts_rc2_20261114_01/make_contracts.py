"""Tie Step 1 contracts to the matched RD10 graph and separate saved witnesses."""

import argparse
from collections import Counter, defaultdict
from functools import lru_cache

from map_owners import Sources, ancestry, journal_refs, local_reach, walk
from prepare_review import HERE, PRIOR, REG, db_readonly, read, sha, write
from review_sources import require, verify_providers

LOGICAL = {"questLogicalAndNodeDefinition", "questLogicalXorNodeDefinition", "questLogicalOrNodeDefinition"}

# These are source locators for the existing exceptions. In particular, a
# timer that also gates a retained output cannot by itself select an exception.
REPLY_BRANCHES = {
    "sts_ep1_01": {"rid": 13744, "expiry_site": 11, "duration_hours": 3,
                    "reply_sites": [61, 62, 63, 64, 65], "expiry_edge": [11, "Out", 6, "In"]},
    "sts_ep1_03": {"rid": 12724, "expiry_site": 203, "duration_hours": 1,
                    "reply_sites": [137, 138], "expiry_edge": [136, "Out", 203, "In"],
                    "other_timer_sites": [151, 192, 195]},
    "sts_ep1_04": {"rid": 12592, "expiry_site": 6, "duration_hours": 22,
                    "reply_sites": [36, 37, 38, 39, 45, 46, 47, 48, 117, 118],
                    "expiry_edge": [6, "Out", 42, "In1"], "retained_edge": [6, "Out", 7, "In"]},
    "sts_ep1_07": {"rid": 12668, "expiry_site": 3, "duration_hours": 22,
                    "reply_sites": [25, 30, 36, 37, 38, 39], "expiry_edge": [3, "Out", 42, "In1"],
                    "retained_edge": [13, "Out", 14, "In"]},
}


def connected_edges(body):
    return {(a, ao, b, bi) for a, ao, ty_a, b, bi, ty_b in body[2] if ty_a == "Output" and ty_b == "Input"}


def checked_named_effect(params, name):
    return next((row for row in walk(params) if row.get("factName") == name), None)


def policy_boundaries(sources):
    result = {}
    for quest, details in REPLY_BRANCHES.items():
        rid = details["rid"]
        resource = sources.rows[rid]
        require(sources.seen[resource["key"], sources.locations[rid]] == resource["sha256"], "Changed exception source")
        graph = sources.graph(rid, "root")
        delays = [item for item in walk(graph[1][details["expiry_site"]]["parameters"])
                  if item.get("$type") == "questGameTimeDelay_ConditionType"]
        require(len(delays) == 1 and delays[0]["hours"] == details["duration_hours"], "Changed reply timer")
        edges = connected_edges(graph)
        require(tuple(details["expiry_edge"]) in edges, "Changed reply branch")
        require(all(site in graph[1] for site in details["reply_sites"]), "Lost reply handler")
        if "retained_edge" in details:
            require(tuple(details["retained_edge"]) in edges, "Changed retained cleanup branch")
        result[quest] = {"policy": "DEFER_ONLY_OPTIONAL_REPLY_BRANCH", "depot": resource["depot"],
                         "sha256": resource["sha256"], "graph": "root",
                         **{key: value for key, value in details.items() if key != "rid"}}
    stock = r"base\quest\minor_quests\mq036\phases\mq036_02_scavengers.questphase"
    edited = "towercontinued\\sidejobs_s29\\native\\" + stock
    escrow = []
    for depot in (stock, edited):
        rid, reason = sources.select(depot)
        require(rid is not None, f"Escrow graph unavailable: {reason}")
        graph = sources.graph(rid, "root")
        ends = {}
        for n in (197, 343, 346):
            ends[n] = graph[1][n]["parameters"]
        for n in (197, 343):
            require(ends[n]["type"]["$type"] == "questTransferItem_NodeType", "Changed escrow endpoint")
        require(checked_named_effect(ends[346], "mq036_items_retrieved"), "Changed escrow recovery receipt")
        require((343, "Out", 346, "In") in connected_edges(graph), "Transfer no longer precedes recovery receipt")
        escrow.append({"depot": depot, "sha256": sources.rows[rid]["sha256"], "graph": "root",
                       "confiscation_node": 197, "item_return_node": 343, "recovery_receipt_node": 346})
    result["mq036_overload"] = {"policy": "DEFER_OUTSTANDING_ESCROW_ONLY", "escrow_sources": escrow}
    return result


def scope_set(owner_map, quest):
    """Start at direct stage writers and follow their connected descendant scopes."""
    scopes = owner_map["scopes"]
    direct = {s["scope"] for t in quest["stages"] for s in t["sites"]
              if s["operation"] == "WRITE" and s["route"] in ("NATIVE", "INSTALLED_XL")}
    relevant = set(direct)
    for scope in scopes:
        if scope["parent"] in relevant:
            relevant.add(scope["index"])
    support = {row["index"] for sid in direct for row in ancestry(scopes, sid)}
    return relevant, support


def capture_sites(sources, owner_map):
    @lru_cache(maxsize=96)
    def connected(rid, graph, entry):
        reached, failure = local_reach(sources, rid, graph, entry)
        require(failure is None, "Owner map lost its connected entry")
        return reached[0]

    selectors = {}
    by_scope = {}
    for quest in owner_map["quests"]:
        used, support = scope_set(owner_map, quest)
        selectors[quest["id"]] = {"body_scope_ids": sorted(used), "ancestor_scope_ids": sorted(support)}
    for idx in sorted({idx for selection in selectors.values() for idx in selection["body_scope_ids"]}):
        scope = owner_map["scopes"][idx]
        rid, graph = scope["rid"], scope["graph"]
        body = sources.graph(rid, graph)
        rows = []
        for nid in sorted(connected(rid, graph, scope["entry"])):
            node = body[1][nid]
            classes, fields = set(), {}
            for item in walk(node["parameters"]):
                kind = item.get("$type", "")
                if kind in LOGICAL or kind in ("questGameTimeDelay_ConditionType", "questRealtimeDelay_ConditionType"):
                    classes.add(kind)
                elif kind in ("questGiveReward_NodeType", "questTransferItem_NodeType", "questAddRemoveItem_NodeType",
                              "questAchievementManagerNodeDefinition", "questJournalQuestObjectiveCounter_NodeType",
                              "questJournalEntryState_ConditionType", "questVarComparison_ConditionType"):
                    classes.add(kind)
                elif kind == "questSetVar_NodeType" and item.get("setExactValue") == 0:
                    classes.add(kind)
                    if item.get("factName"):
                        fields["incremented_fact"] = item["factName"]
                elif kind in ("questSceneNodeDefinition", "questUseWorkspotNodeDefinition", "questCombatNodeDefinition",
                              "questSpawnManagerNodeDefinition", "questContentTokenCondition",
                              "questCutControlNodeDefinition", "questVehicleNodeDefinition"):
                    classes.add(kind)
            if classes:
                rows.append({"node": nid, "types": sorted(classes), **fields})
        # The raw typed parameters remain in the provider graph. This index
        # identifies which native checkpoint fields need a reader by class.
        by_scope[idx] = rows
    return selectors, by_scope


def delamain_join(sources, witness):
    latch, = [row for row in witness["saved_logical_signals"]
              if row["address"] == [0, 2, 82, 5, 48, 79] and row["node"] == 198]
    rid, graph = latch["source"]
    require(latch["value"] == 70 and latch["signaled_inputs"] == ["In2", "In3", "In7"],
            "Unexpected Epistrophy saved checkpoint")
    body = sources.graph(rid, graph)
    legs = {port: source for source, source_port, dest, port in connected_edges(body)
            if dest == latch["node"] and source_port == "Out1"}
    require(set(legs) == set(latch["authored_input_order"]), "Missing Epistrophy completion input")
    cars = {}
    for port, child in sorted(legs.items()):
        phase_name = f"{graph}/{child}"
        sources_in_phase = sources.graph(rid, phase_name)
        require(sources_in_phase is not None, "Missing Epistrophy child phase")
        names = sorted({path for node in sources_in_phase[1].values() for path, _ in journal_refs(node["parameters"])
                        if path.startswith("quests/side_quest/sq025c")})
        cars[port] = {"caller_node": child, "child_graph": phase_name, "journal_references": names,
                      "signaled": port in latch["signaled_inputs"]}
    require((198, "Out1", 287, "In2") in connected_edges(body), "Epistrophy join no longer feeds continuation")
    return {"phase": sources.rows[rid], "saved_latch": latch, "car_phase_inputs": cars,
            "continuation_edge": [198, "Out1", 287, "In2"],
            "handoff": "Carry the native AND value and the seven original child receipts together. "
                       "Await the four unsignaled inputs. Preserve already granted car credit and the separate family payout."}


def status(row, stage_sites, children):
    if not row["expected_provider_path_and_class_match"]:
        return "GRAPH_REFERENCE_WITHOUT_CURRENT_JOURNAL_DEFINITION"
    if (row["class"] == "gameJournalQuestPhase" and children
            and not any(s["operation"] == "WRITE" for s in stage_sites)):
        return "JOURNAL_CONTAINER"
    if any(s["route"] == "NATIVE" and s["operation"] == "WRITE" for s in stage_sites):
        return "NATIVE_EXECUTION_CHECKPOINT_REQUIRED"
    if stage_sites:
        return "JOURNAL_SITE_REQUIRES_ORIGINAL_OWNER_BINDING"
    if row["classification"] == "INDEXED_GRAPH_REFERENCE":
        return "NO_REACHED_SITE_FROM_REVIEWED_ROOTS"
    return "JOURNAL_METADATA_WITHOUT_MAPPED_EXECUTION_SITE"


def compile_contracts(review, owner_map, witness, policy, selectors):
    route_map = {q["id"]: {s["path"]: s["sites"] for s in q["stages"]} for q in owner_map["quests"]}
    fixtures = {q["id"]: {row["path"]: row["save_state"] for row in q["rows"]} for q in witness["journal_states"]}
    source = {q["id"]: q for q in read(PRIOR / "current_stage_index_01.json")}
    controls = defaultdict(list)
    for idx, row in enumerate(witness["controls"]):
        controls[row["id"]].append(idx)
    output = []
    for q in review["quests"]:
        qid = q["id"]
        routes, fixture = route_map[qid], fixtures[qid]
        path_rows = []
        for row in q["rows"]:
            path, cls = row["path"], row["class"]
            if cls == "gameJournalQuest":
                continue
            sites = routes.get(path, [])
            children = [s["path"] for s in q["rows"] if s["path"].startswith(path + "/")
                        and s["class"] == "gameJournalQuestObjective" and routes.get(s["path"])]
            path_rows.append({"path": path, "class": cls, "state_contract": status(row, sites, children),
                              "native_and_installed_sites": sites, "associated_objectives": children,
                              "same_save_state": fixture[path], "separate_hs3_gate_observation": row["hs3_pre_cutoff"]})
        output.append({"id": qid, "title": q["title"], "whole_quest_exception": source[qid]["whole_quest_mid_resume_exception"],
                       "scoped_exception": policy.get(qid), "scope_selectors": selectors[qid],
                       "saved_owner_control_indices": controls[qid], "paths": path_rows})
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=int, required=True)
    args = parser.parse_args()
    out = HERE / f"analysis_{args.out:02d}"
    require(not out.exists(), "Fresh contract output required")
    capture_path = HERE / "capture_02/providers.json"
    review_path = HERE / "analysis_04/source_review.json"
    owner_path = HERE / "analysis_05/owner_map.json"
    witness_path = HERE / "analysis_06/saved_witness.json"
    capture, review, owners, witness = map(read, (capture_path, review_path, owner_path, witness_path))
    require(review["provider_capture_sha256"] == sha(capture_path), "Wrong provider capture")
    require(owners["source_review_sha256"] == sha(review_path), "Wrong source review")
    require(witness["owner_map_sha256"] == sha(owner_path), "Wrong saved witness")
    plan, seen = verify_providers(capture)
    with db_readonly(REG / "registry_02/registry.sqlite3") as db:
        sources = Sources(db, plan, seen, review)
        policy = policy_boundaries(sources)
        epistrophy = delamain_join(sources, witness)
        selectors, by_scope = capture_sites(sources, owners)
    contracts = compile_contracts(review, owners, witness, policy, selectors)
    require(len(contracts) == 160 and sum(q["whole_quest_exception"] for q in contracts) == 4, "Roster policy drift")
    require(sum(q["scoped_exception"] is not None for q in contracts) == 5, "Scoped exception drift")
    require(len(witness["controls"]) == 25 and all(row["matches_prior"] for row in witness["controls"]),
            "A previous saved-owner control failed")
    state_counts = Counter(p["state_contract"] for q in contracts for p in q["paths"])
    frontier = {idx for q in contracts for idx in q["scope_selectors"]["body_scope_ids"]}
    boundaries = [x for x in owners["boundaries"] if x.get("parent") in frontier]
    summary = {"quests": len(contracts), "state_contracts": dict(state_counts),
               "source_obligation_scopes": len(by_scope), "relevant_trace_boundaries": dict(Counter(
                   item["reason"] for item in boundaries)), "whole_quest_exceptions": 4, "scoped_exceptions": 5,
               "runtime_exact_resume_admissions": 0}
    out.mkdir()
    write(out / "contracts.json", {
        "input_sha256": {str(p.relative_to(HERE)): sha(p) for p in (review_path, owner_path, witness_path)},
        "summary": summary, "quests": contracts, "pending_handler_and_effect_sites_by_scope": by_scope,
        "relevant_trace_boundaries": boundaries, "epistrophy_parallel_join": epistrophy,
        "limits": ["These contracts identify exact source and saved evidence to capture. They do not start a handler.",
                   "Every callback, lease, active scene or reward transaction depends on the live cutoff checkpoint."],
    })
    print(summary)


if __name__ == "__main__":
    main()
