"""Reconcile RD10 source providers and the journal's path and class metadata."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import json

from prepare_review import HERE, PRIOR, REG, ROOT, db_readonly, depot_key, read, sha, write

COMBINED = "archive/pc/mod/zzzz_PTFR_Combined.archive"
JOURNAL_EXTRACTION = ROOT / "research/sidejobs_s28/journal_variants_05/extraction.json"
JOURNAL_TYPES = {"gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective"}
BASE_JOURNAL = r"base\journal\cooked_journal.journal"
EP1_JOURNAL = r"ep1\journal\cooked_journal.journal"
MAP_PIN_ENUMS = {"Zzz22_CityTourLandmark", "Zzz21_ServicePointGlamdocVariant"}
HS3 = HERE.parent / "history_capture_hs3_20261112_01/observations/capture_20261112_01/assessment.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_providers(capture):
    input_name = capture.get("input_file", "inputs.json")
    require(input_name in {"inputs.json", "inputs_02.json"}, "Unexpected provider plan location")
    inputs = HERE / input_name
    plan = read(inputs)
    require(capture["input_sha256"] == sha(inputs), "Provider plan differs from capture")
    game = Path(plan["game_root"])
    expected = {
        (row["key"], Path(row["archive"]).relative_to(game).as_posix()): row["sha256"]
        for row in plan["qp2_providers"]
    }
    expected.update({(row["key"], COMBINED): row["sha256"] for row in plan["rd10_members"]})
    observed = {(row["key"], row["archive"]): row["sha256"] for row in capture["providers"]}
    require(len(observed) == len(capture["providers"]), "Duplicate provider capture row")
    require(observed == expected, "Watched archive payloads or providers differ from the pinned inputs")
    absent = set(plan.get("scanned_without_known_provider", {}).values())
    require({key for key, _ in observed} == set(plan["keys"]) - absent, "Unexpected provider presence or absence")
    return plan, observed


def graph_body(db, rid):
    queries = (
        "SELECT root_type,support_json FROM resources WHERE rid=?",
        "SELECT path,kind,inputs_json FROM graphs WHERE rid=? ORDER BY path",
        "SELECT graph,id,type,from_any_input,parameters_json,sockets_json FROM nodes WHERE rid=? ORDER BY graph,id",
        """SELECT graph,source,source_socket,source_type,destination,destination_socket,destination_type
           FROM edges WHERE rid=? ORDER BY 1,2,3,4,5,6,7""",
        "SELECT graph,node,kind,details_json FROM boundaries WHERE rid=? ORDER BY 1,2,3,4",
    )
    return [list(map(tuple, db.execute(query, (rid,)))) for query in queries]


def compare_graph_variants(db, plan):
    results = []
    for row in plan["prior_collisions"]:
        if row["depot"] == BASE_JOURNAL:
            continue
        a_id, b_id = row["provider_ids"]
        left, right = graph_body(db, a_id), graph_body(db, b_id)
        require(left[1] and right[1], f"Graph unavailable: {row['depot']}")
        candidates = [item for item in plan["qp2_providers"] if item["rid"] in (a_id, b_id)]
        fields = ["root_support", "graphs_and_inputs", "typed_nodes_and_sockets", "edges", "decode_boundaries"]
        matches = {key: a == b for key, a, b in zip(fields, left, right, strict=True)}
        support_a, support_b = (json.loads(body[0][0][1]) for body in (left, right))
        platform_fields = []
        for support in (support_a, support_b):
            platforms = {}
            for embedded in support["embedded_resources"]:
                platforms[embedded["depot"]] = embedded["parameters"].pop("cookingPlatform", None)
            platform_fields.append(platforms)
        platform_diffs = [
            {"embedded_depot": name, "values": [platform_fields[0][name], platform_fields[1][name]]}
            for name in sorted(platform_fields[0].keys() & platform_fields[1].keys())
            if platform_fields[0][name] != platform_fields[1][name]
        ]
        comparable = all(value for name, value in matches.items() if name != "root_support")
        comparable = comparable and support_a == support_b and platform_fields[0].keys() == platform_fields[1].keys()
        calls = [item for item in left[2] if item[2] == "questPhaseNodeDefinition"]
        diffs = {key: [len(a), len(b)] for key, a, b in zip(fields, left, right, strict=True)}
        results.append({"depot": row["depot"], "providers": candidates,
                        "normalized_comparison": matches, "rows_per_provider": diffs,
                        "embedded_cooking_platform_differences": platform_diffs,
                        "phase_call_node_count": len(calls),
                        "contract_input": "SAME_GRAPH_AND_PREFAB_REFERENCES" if comparable else "CHECK_EXACT_PROVIDER"})
    return results


def journal_tree(document):
    root = document["Data"]["RootChunk"]
    require(root["$type"] == "gameJournalResource", "Incorrect journal root type")
    handles = {}
    pending = [root]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if "HandleId" in item and "Data" in item:
                previous = handles.setdefault(str(item["HandleId"]), item["Data"])
                require(previous == item["Data"], "Conflicting journal handle definition")
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    entries = {}
    stack = [(root["entry"], (), frozenset())]
    while stack:
        wrapper, parent, ancestors = stack.pop()
        handle = str(wrapper.get("HandleId", wrapper.get("HandleRefId", "")))
        if "HandleRefId" in wrapper:
            require(handle in handles, "Dangling journal entry handle")
            entry = handles[handle]
        else:
            entry = wrapper.get("Data", wrapper)
        require(not handle or handle not in ancestors, "Journal tree has a cycle")
        require(entry["$type"].startswith("gameJournal"), "Invalid journal entry class")
        entry_id = entry.get("id", "")
        require(isinstance(entry_id, str) and "/" not in entry_id, "Invalid journal ID")
        parts = parent + ((entry_id,) if entry_id else ())
        location = "/".join(parts)
        require(location not in entries, f"Duplicate journal path: {location}")
        entries[location] = {
            "class": entry["$type"],
            "authored_optional": entry.get("optional"),
            "authored_counter": entry.get("counter"),
        }
        stack.extend((child, parts, ancestors | ({handle} if handle else set()))
                     for child in entry.get("entries", []))
    return entries


def current_journals(plan, capture, observed):
    extraction = read(JOURNAL_EXTRACTION)
    require(extraction["status"] == "EXTRACTED_CURRENT_JOURNAL_PATH_CLASS_METADATA_ONLY",
            "Unexpected journal extraction scope")
    require(extraction["tool_sha256"] == capture["decoder_sha256"], "Journal decoder changed")
    require(sha(ROOT / extraction["script"]) == extraction["script_sha256"], "Journal extraction source changed")
    game = Path(plan["game_root"])
    official = defaultdict(list)
    pins = {JOURNAL_EXTRACTION.relative_to(ROOT).as_posix(): sha(JOURNAL_EXTRACTION)}
    official_keys = set()
    for item in extraction["variants"] + extraction["ep1_variants"]:
        path = item["depot"]
        key = depot_key(path)
        arc = Path(item["archive"]).relative_to(game).as_posix()
        require(observed.get((key, arc)) == item["sha256"], f"Journal raw provider changed: {arc}")
        official_keys.add((key, arc))
        require(item["metadata_only"] is True, "Invalid journal evidence scope")
        enums = item["ignored_enums"]
        require(all(event["enum_type"] == "WolvenKit.RED4.Types.Enums+gamedataMappinVariant"
                    and event["original"] in MAP_PIN_ENUMS and event["metadata_placeholder"] == 0
                    for event in enums), "Unknown parse substitution in retained journal evidence")
        require(len(enums) == len({event["position"] for event in enums}), "Repeated journal anomaly position")
        require(sha(ROOT / item["raw"]) == item["sha256"], "Retained journal input changed")
        require(sha(ROOT / item["json"]) == item["json_sha256"], "Retained journal export changed")
        pins[item["json"]] = item["json_sha256"]
        official[path].append((arc, item["sha256"], journal_tree(read(ROOT / item["json"])), len(enums)))
    require(set(official) == {BASE_JOURNAL, EP1_JOURNAL}, "Missing official journal depot")
    require({key for key in observed if key[0] in {depot_key(BASE_JOURNAL), depot_key(EP1_JOURNAL)}} == official_keys,
            "Unreviewed provider for official journal")
    require(len(official[BASE_JOURNAL]) == 2 and len(official[EP1_JOURNAL]) == 1, "Unexpected official variants")
    return official, pins


def check_journal_extensions(db, plan, capture, observed, roots, include_all_paths=False):
    outputs = []
    game = Path(plan["game_root"])
    for record in capture["journal_bindings"]:
        require(isinstance(record["journal"], list), "Unreviewed ArchiveXL journal format")
        for depot in record["journal"]:
            variants = list(db.execute("SELECT * FROM resources WHERE key=?", (depot_key(depot),)))
            require(len(variants) == 1, f"Unreviewed XL journal provider: {depot}")
            item, = variants
            arc = Path(item["archive"]).relative_to(game).as_posix()
            require(observed.get((item["key"], arc)) == item["sha256"], "XL journal resource changed")
            source = Path(item["export_path"])
            require(sha(source) == item["export_sha256"], "XL journal export changed")
            paths = journal_tree(read(source))
            # ArchiveXL may use an anchored path as a child ID. journal_tree
            # intentionally rejects it until the extension's merge is traced.
            overlap = {path: meta for path, meta in paths.items()
                       if any(path == root or path.startswith(root + "/") for root in roots)}
            result = {"depot": depot, "configuration": record["path"], "archive": arc,
                      "sha256": item["sha256"], "selected_tree_overlaps": overlap}
            if include_all_paths:
                result["all_paths"] = list(paths)
            outputs.append(result)
    return outputs


def hs3_journal_rows(plan):
    exports = read(HS3)["exports"]
    run = next(item for item in exports if item["header"]["schema"] == 3)
    source = Path(run["path"])
    require(source.is_relative_to(Path(plan["game_root"])), "Unexpected HS3 export location")
    require(sha(source) == run["sha256"], "Recorded HS3 export changed")
    doc = read(source)
    require(all(doc.get(key) == value for key, value in run["header"].items()), "HS3 header changed")
    require(len(doc["rows"]) == run["rows"], "HS3 row inventory mismatch")
    rows = {}
    for row in doc["rows"]:
        definition = row["definition"]
        if definition["kind"] != "journal":
            continue
        key = (definition["path"], definition["class"])
        require(key not in rows, f"Duplicate HS3 journal observation: {key}")
        rows[key] = {field: row[field] for field in ["state", "counter", "optional", "tracked", "stable"]}
    return rows, run["sha256"]


def journal_readback(db, source_index, official, observations):
    official_order = [*official[BASE_JOURNAL], *official[EP1_JOURNAL]]
    indices = [entries for _, _, entries, _ in official_order]
    rows = []
    quest_names = {row["id"]: row for row in source_index}
    for quest in db.execute("SELECT id,journal_root FROM quests WHERE selection='INCLUDE' ORDER BY id"):
        qid, root = quest
        prior = quest_names[qid]["stages"]
        known = {row["path"]: row for row in prior}
        relevant_paths = {root, *known}
        for index in indices:
            relevant_paths.update(path for path, meta in index.items()
                                  if path.startswith(root + "/") and meta["class"] in JOURNAL_TYPES)
        quest_rows = []
        for path in sorted(relevant_paths):
            variants = [index.get(path) for index in indices]
            stage = known.get(path)
            if path == root:
                cls = "gameJournalQuest"
                classification = "QUEST_ROOT"
            elif stage:
                cls = stage["class"]
                classification = "INDEXED_GRAPH_REFERENCE" if stage["current_source_sites"] else "DEFINITION_WITHOUT_DIRECT_GRAPH_SITE"
            else:
                cls = next(meta["class"] for meta in variants if meta is not None)
                classification = "ADDITIONAL_JOURNAL_DEFINITION"
            observation = observations.get((path, cls))
            relevant = variants[2:] if path.startswith("ep1/") else variants[:2]
            agreement = all(meta is not None and meta["class"] == cls for meta in relevant)
            quest_rows.append({"path": path, "class": cls, "classification": classification,
                               "expected_provider_path_and_class_match": agreement,
                               "provider_metadata": variants, "hs3_pre_cutoff": observation})
        rows.append({"id": qid, "title": quest_names[qid]["title"], "rows": quest_rows})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=int, default=1)
    parser.add_argument("--out", type=int, required=True)
    args = parser.parse_args()
    capture_path = HERE / f"capture_{args.capture:02d}/providers.json"
    out = HERE / f"analysis_{args.out:02d}"
    require(not out.exists(), "Fresh review output required")
    capture = read(capture_path)
    plan, observed = verify_providers(capture)
    source_index = read(PRIOR / "current_stage_index_01.json")
    official, pins = current_journals(plan, capture, observed)
    observations, history_hash = hs3_journal_rows(plan)
    with db_readonly(REG / "registry_02/registry.sqlite3") as db:
        variant_rows = compare_graph_variants(db, plan)
        roots = [row[0] for row in db.execute("SELECT journal_root FROM quests WHERE selection='INCLUDE'")]
        extensions = check_journal_extensions(db, plan, capture, observed, roots)
        rows = journal_readback(db, source_index, official, observations)
    flat = [row for quest in rows for row in quest["rows"]]
    initial = [row for row in flat if row["classification"] == "DEFINITION_WITHOUT_DIRECT_GRAPH_SITE"]
    require(len(initial) == 43, "Expected 43 original definition-only rows")
    summary = {
        "quests": len(rows), "matched_archive_payloads": len(observed), "archives": len(capture["archives"]),
        "xl_files": len(capture["xl_files"]), "xl_phase_bindings": len(capture["phase_bindings"]),
        "scanned_depots_without_provider": len(plan.get("scanned_without_known_provider", {})),
        "normalized_graph_and_prefab_variants_agree": sum(
            item["contract_input"] == "SAME_GRAPH_AND_PREFAB_REFERENCES" for item in variant_rows),
        "journal_row_counts": dict(Counter(row["classification"] for row in flat)),
        "journal_expected_class_mismatches": sum(not row["expected_provider_path_and_class_match"] for row in flat),
        "definition_only_by_class": dict(Counter(row["class"] for row in initial)),
        "hs3_observed_definition_only_states": dict(Counter(
            str(row["hs3_pre_cutoff"]["state"]) if row["hs3_pre_cutoff"] and row["hs3_pre_cutoff"]["stable"]
            else "UNKNOWN" for row in initial)),
    }
    out.mkdir()
    write(out / "source_review.json", {
        "summary": summary, "provider_capture_sha256": sha(capture_path), "journal_inputs": pins,
        "hs3_observation_sha256": history_hash, "graph_variants": variant_rows, "journal_extensions": extensions,
        "journal_provider_order": [
            {"depot": depot, "archive": arc, "sha256": digest, "entries": len(entries), "mappin_enum_events": events}
            for depot in [BASE_JOURNAL, EP1_JOURNAL]
            for arc, digest, entries, events in official[depot]
        ],
        "quests": rows,
    })
    print(summary)


if __name__ == "__main__":
    main()
