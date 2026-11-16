"""Read the pinned pre-Tower fixture as a contract witness for the source map."""

import argparse
import struct
import sys
from collections import Counter, defaultdict

from map_owners import Sources, walk
from prepare_review import HERE, REG, db_readonly, read, sha, write
from review_sources import require, verify_providers

NATIVE_PROTOTYPE = HERE.parent / "universal_resume_20261114_01"
sys.path.insert(0, str(NATIVE_PROTOTYPE))
from read_handlers import phase_hash, saved_components, token  # noqa: E402

PRESERVATION = HERE.parent / "handler_preservation_hp1_20261112_01"
GIGS = HERE.parent / "resume_dispatcher_rd5_gigs_20261113_01"
NATIVE = HERE.parent / "quest_restoration_qr15/saved_graph_state_01"
FIXTURE = PRESERVATION / "saves_01/ManualSave-26/manifest.json"
LATCHES = {"questLogicalAndNodeDefinition": "4", "questLogicalXorNodeDefinition": "5"}


def fnv32(data):
    state = 0x811C9DC5
    for byte in data:
        state = ((state ^ byte) * 0x01000193) & 0xFFFFFFFF
    return state


def rotate32(value, bits):
    return ((value << bits) | (value >> (32 - bits))) & 0xFFFFFFFF


def journal_hash(path):
    data = path.encode("utf-8")
    h = 0x5EEDBA5E
    trim = len(data) - len(data) % 4
    for word, in struct.iter_unpack("<I", data[:trim]):
        k = rotate32((word * 0xCC9E2D51) & 0xFFFFFFFF, 15)
        h ^= (k * 0x1B873593) & 0xFFFFFFFF
        h = (rotate32(h, 13) * 5 + 0xE6546B64) & 0xFFFFFFFF
    if trim < len(data):
        tail = int.from_bytes(data[trim:], "little")
        k = rotate32((tail * 0xCC9E2D51) & 0xFFFFFFFF, 15)
        h ^= (k * 0x1B873593) & 0xFFFFFFFF
    h ^= len(data)
    h = ((h ^ (h >> 16)) * 0x85EBCA6B) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
    return h ^ (h >> 16)


def unique_rows(rows, label):
    mapped = dict(rows)
    require(len(mapped) == len(rows), f"Multiple rows for one {label} key")
    return mapped


def source_phase_addresses(scopes):
    output = defaultdict(set)
    for row in scopes:
        if row["address"] is not None and row["kind"] == "quest":
            output[tuple(row["address"])].add((row["rid"], row["graph"]))
    return output


def bind_handlers(sources, addresses, phase_index, events):
    counts = Counter()
    bound = []
    for slot, (registration, phase, node_id) in enumerate(events):
        if (registration, phase, node_id) == (0, 0, 0xFFFF):
            continue
        candidates = phase_index.get(phase, ())
        if len(candidates) != 1 or not registration or node_id >= 0xFFFF:
            counts["unbound_native_event_key"] += 1
            continue
        address, = candidates
        options = addresses.get(address, ())
        if len(options) != 1:
            counts["unmapped_or_ambiguous_source_phase"] += 1
            continue
        (rid, graph), = options
        node = sources.graph(rid, graph)[1].get(node_id)
        if node is None:
            counts["source_node_missing"] += 1
            continue
        tags = {x["$type"] for x in walk(node["parameters"]) if "$type" in x}
        matches = sorted(name for name in tags if token(name) == registration)
        if len(matches) != 1:
            counts["registered_type_unbound"] += 1
            continue
        counts["bound"] += 1
        bound.append({"slot": slot, "address": address, "node": node_id, "phase_hash": phase,
                      "source": [rid, graph], "depot": sources.rows[rid]["depot"],
                      "provider_sha256": sources.rows[rid]["sha256"],
                      "registered_class": matches[0], "definition_class": node["type"]})
    return counts, bound


def bind_latches(sources, addresses, phase_index, projected):
    requested_tables = {name: unique_rows(projected["native_tables"][name], "native table " + name)
                        for name in LATCHES.values()}
    candidates = defaultdict(list)
    for phase, native_paths in phase_index.items():
        if len(native_paths) != 1:
            continue
        address, = native_paths
        matches = addresses.get(address, ())
        if len(matches) != 1:
            continue
        (rid, graph), = matches
        for node in sources.graph(rid, graph)[1].values():
            store = LATCHES.get(node["type"])
            if store is None:
                continue
            key = fnv32(struct.pack("<II", node["id"], phase))
            mask = requested_tables[store].get(key)
            if not mask:
                continue
            inputs = [socket["name"] for socket in node["sockets"] if socket["type"] == "Input"]
            consumed = [name for i, name in enumerate(inputs) if mask & (1 << i)]
            valid = (0 < len(inputs) <= 32 and len(inputs) == len(set(inputs))
                     and mask < (1 << len(inputs))
                     and (mask.bit_count() == 1 if store == "5" else mask != (1 << len(inputs)) - 1))
            candidates[store, key].append({"address": address, "source": [rid, graph], "node": node["id"],
                                            "class": node["type"], "table": int(store), "key": key, "value": mask,
                                            "authored_input_order": inputs, "signaled_inputs": consumed,
                                            "valid_layout_and_mask": valid})
    resolved = [rows[0] for rows in candidates.values() if len(rows) == 1 and rows[0]["valid_layout_and_mask"]]
    blocked = [{"key": [store, key], "candidates": rows} for (store, key), rows in candidates.items()
               if len(rows) != 1 or not rows[0]["valid_layout_and_mask"]]
    return resolved, blocked


def observed_quests(review, projected, all_paths):
    save_rows = unique_rows(projected["journal_hash_and_state"], "journal")
    candidate_hashes = defaultdict(set)
    for path in all_paths:
        candidate_hashes[journal_hash(path)].add(path)
    output = []
    for quest in review["quests"]:
        rows = []
        for row in quest["rows"]:
            path = row["path"]
            key = journal_hash(path)
            matches = candidate_hashes[key]
            eligible = len(matches) == 1 and row["expected_provider_path_and_class_match"]
            rows.append({"path": path, "class": row["class"], "hash": key,
                         "save_state": save_rows.get(key) if eligible else None,
                         "lookup_status": ("MATCHING_SERIALIZED_ROW" if key in save_rows else "UNSERIALIZED")
                         if eligible else "MISSING_DEFINITION_OR_AMBIGUOUS_HASH"})
        output.append({"id": quest["id"], "title": quest["title"], "rows": rows})
    return output


def control_owners(bound, sha_body):
    """Compare the raw event binding to exact prior fixture owner prefixes."""
    pin = read(PRESERVATION / "checkpoint.json")["artifacts"]
    path = PRESERVATION / "analysis_01/save_comparison.json"
    require(sha(path) == pin["analysis_01/save_comparison.json"], "Preservation controls changed")
    fixture = read(path)["ManualSave-26"]
    require(fixture["source_sha256"] == sha_body, "Wrong preservation fixture")
    result = []

    def add(qid, address, expected):
        prefix = tuple(address)
        matches = [row for row in bound if row["address"][:len(prefix)] == prefix]
        observed = Counter((row["address"], row["node"]) for row in matches)
        result.append({"id": qid, "phase_address": prefix, "expected_count": len(expected),
                       "matches_prior": observed == Counter(expected), "handlers": matches})

    for qid, case in fixture["cases"].items():
        add(qid, case["root_path"], [(tuple(row["path"]), row["node"]) for row in case["handlers"]])
    batch_path = GIGS / "evidence_01/batch_assessment.json"
    require(sha(batch_path) == "E12CFF4425667D6A4DBDD3CB4A48D9F161CED530ABC058FC62AD3B088FEE7354",
            "Interrupted gig fixture controls changed")
    batch = read(batch_path)
    for case in batch["stages"]:
        for owner in case["source_owner_paths"]:
            witness = owner["controls"]["ManualSave-26"]
            prefix = [step[2] for step in owner["source_path"]]
            add(case["id"], prefix, [(tuple(path), node) for path, node in witness["descendant_nodes"]])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=int, default=2)
    parser.add_argument("--sources", type=int, default=4)
    parser.add_argument("--owners", type=int, default=5)
    parser.add_argument("--out", type=int, required=True)
    args = parser.parse_args()
    out = HERE / f"analysis_{args.out:02d}"
    require(not out.exists(), "Fresh saved-state review output required")
    owner_path = HERE / f"analysis_{args.owners:02d}/owner_map.json"
    owners = read(owner_path)
    source_path = HERE / f"analysis_{args.sources:02d}/source_review.json"
    review = read(source_path)
    capture_path = HERE / f"capture_{args.capture:02d}/providers.json"
    capture = read(capture_path)
    require(owners["source_review_sha256"] == sha(source_path), "Wrong source review for owner map")
    require(review["provider_capture_sha256"] == sha(capture_path), "Wrong provider capture for review")
    plan, seen = verify_providers(capture)
    projection_path = HERE / "save_projection_01.json"
    projected = read(projection_path)
    require(sha(FIXTURE) == projected["fixture_manifest_sha256"], "Saved native fixture manifest changed")
    save_sha, phase_index, events, freezer = saved_components(FIXTURE)
    require(save_sha == projected["save_sha256"] and projected["save_version"] == 277, "Mismatched save projection")
    native_proof = read(NATIVE / "native_28.json")
    require(native_proof["exe_sha256"] == projected["engine_sha256"], "Saved latch provenance changed")
    addresses = source_phase_addresses(owners["scopes"])

    with db_readonly(REG / "registry_02/registry.sqlite3") as db:
        sources = Sources(db, plan, seen, review)
        counts, handlers = bind_handlers(sources, addresses, phase_index, events)
        signals, uncertain = bind_latches(sources, addresses, phase_index, projected)
        # Include every path in the current complete journal trees in the hash
        # collision check, including unsupported roots and unrelated classes.
        from review_sources import current_journals, check_journal_extensions
        official, _ = current_journals(plan, capture, seen)
        all_paths = {path for variants in official.values() for _, _, index, _ in variants for path in index}
        extension_paths = check_journal_extensions(db, plan, capture, seen, (), include_all_paths=True)
        all_paths.update(p for ext in extension_paths for p in ext["all_paths"])
        quest_rows = observed_quests(review, projected, all_paths)
    controls = control_owners(handlers, save_sha)
    roots_active = {quest["id"] for quest in quest_rows
                    if any(row["class"] == "gameJournalQuest" and row["save_state"] == 2 for row in quest["rows"])}
    parallel = [
        {"id": q["id"], "objectives": [row["path"] for row in q["rows"]
                                      if row["class"] == "gameJournalQuestObjective" and row["save_state"] == 2]}
        for q in quest_rows if q["id"] in roots_active
    ]
    summary = {
        "native_handler_rows": dict(counts),
        "latch_rows_bound_to_known_class_and_socket_order": dict(Counter(row["class"] for row in signals)),
        "latch_rows_with_conflicting_matches_or_values": len(uncertain),
        "latch_rows_nonzero_by_table": {key: sum(bool(value) for _, value in projected["native_tables"][key])
                                      for key in LATCHES.values()},
        "prior_owner_controls": len(controls),
        "prior_owner_controls_match": sum(row["matches_prior"] for row in controls),
        "quest_roots_active": len(roots_active),
        "quests_with_concurrent_active_objectives": sum(len(x["objectives"]) > 1 for x in parallel),
        "freezer_groups_saved": len(freezer),
    }
    out.mkdir()
    write(out / "saved_witness.json", {
        "summary": summary, "save_sha256": save_sha, "projection_sha256": sha(projection_path),
        "owner_map_sha256": sha(owner_path), "native_source_review_sha256": sha(NATIVE / "native_28.json"),
        "root_active_quests": sorted(roots_active), "active_objectives_in_same_save": parallel,
        "journal_states": quest_rows, "saved_registrations": handlers, "controls": controls,
        "saved_logical_signals": signals, "unqualified_logical_signals": uncertain,
        "limits": ["Registration rows show saved registrations and authored identities in the matched phase map.",
                   "Mask interpretation is bounded to the pinned executable, unique mapped address and known node class.",
                   "Cached paths can survive retirement. Missing values and out-of-scope addresses do not prove retirement."],
    })
    print(summary)


if __name__ == "__main__":
    main()
