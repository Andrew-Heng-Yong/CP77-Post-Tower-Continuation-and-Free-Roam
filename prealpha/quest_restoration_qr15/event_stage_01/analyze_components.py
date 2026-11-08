"""Decode the captured quest child framing; never opens a game save or process.

Native lifecycle semantics live in quest_handlers/ and vehicle_events/. This
script reports exact serialized membership, not quest completion or liveness.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
INPUT = HERE / "components_01"
OUTPUT = HERE / "analysis_01.json"
MASK = 0xFFFFFFFF
TARGET = (1, 0, 10, 5, 2, 50, 19)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def unpack_list(data, node_id, stride):
    if len(data) < 8 or struct.unpack_from("<I", data)[0] != node_id:
        raise ValueError("Unexpected node ID or missing header")
    count = struct.unpack_from("<I", data, 4)[0]
    if count * stride + 8 != len(data):
        raise ValueError("Declared count does not consume exact component")
    return count, data[8:]


def decode_paths(data, node_id):
    count, body = unpack_list(data, node_id, 2)
    words = struct.unpack("<" + "H" * count, body)
    paths = []
    at = 0
    while at < len(words):
        length = words[at]
        at += 1
        if at + length > len(words):
            raise ValueError("Truncated interned path")
        paths.append(tuple(words[at:at + length]))
        at += length
    return words, paths


def phase_hash(path):
    if not path or path[0] not in (0, 1):
        raise ValueError("No pinned root seed for this path")
    result = (0x811C9DC5, 0x01800013)[path[0]]
    for value in path:
        for byte in struct.pack("<H", value):
            result = ((result ^ byte) * 0x01000193) & MASK
    return result


def decode_records(data, node_id):
    count, body = unpack_list(data, node_id, 16)
    return [struct.unpack_from("<QIHH", body, at * 16) for at in range(count)]


def main():
    assert not OUTPUT.exists(), "Fresh output required"
    manifest = read(INPUT / "manifest.json")
    nodes = {row["name"]: row for row in manifest["nodes"]}
    for row in nodes.values():
        assert sha(row["path"]) == row["sha256"], row["name"]
    raw = {name: Path(row["path"]).read_bytes() for name, row in nodes.items()}
    words, paths = decode_paths(raw["customArray"], nodes["customArray"]["id"])
    events = decode_records(raw["eventManager"], nodes["eventManager"]["id"])
    instance = decode_records(raw["nodeInstanceDataManager"], nodes["nodeInstanceDataManager"]["id"])
    managed = read(INPUT / "event_records.json")["records"]
    assert events == [(int(row["u64_0"]), row["u32_8"], row["u16_12"], row["u16_14"]) for row in managed]
    selected = [p for p in paths if p[:len(TARGET)] == TARGET]
    hash_paths = defaultdict(list)
    unsupported = []
    for path in paths:
        try:
            hash_paths[phase_hash(path)].append(path)
        except ValueError:
            unsupported.append(path)
    contexts = []
    for path in selected:
        key = phase_hash(path)
        contexts.append({
            "path": path, "phase_hash_u32": str(key), "phase_hash_hex": hex(key),
            "registered_path_hash_collisions": [p for p in hash_paths[key] if p != path],
            "event_manager_phase_rows": [
                {"ordinal": index, "type_token_u64": str(row[0]), "phase_hash_u32": str(row[1]), "node_u16": row[2], "tail_u16": row[3]}
                for index, row in enumerate(events) if row[1] == key
            ],
        })
    # An empty retained QueuedData projection can be checked without inventing
    # support for a nonempty/version-dependent queue format.
    queued = raw["QueuedData"]
    empty_queued = (len(queued) == 9 and struct.unpack_from("<I", queued)[0] == nodes["QueuedData"]["id"]
                    and queued[4] == 0 and struct.unpack_from("<I", queued, 5)[0] == 0)
    assert empty_queued, "Nonempty QueuedData requires its full pinned native decoder"
    controls = []
    def malformed(name, operation):
        try:
            operation()
        except (ValueError, struct.error):
            controls.append({"name": name, "pass": True})
        else:
            raise AssertionError("Damaged actual component accepted: " + name)
    for name, decoder in [("customArray", decode_paths), ("eventManager", decode_records), ("nodeInstanceDataManager", decode_records)]:
        original = raw[name]
        node_id = nodes[name]["id"]
        malformed(name + " truncated", lambda d=original, n=node_id, f=decoder: f(d[:-1], n))
        malformed(name + " appended byte", lambda d=original, n=node_id, f=decoder: f(d + b"\0", n))
        wrong_id = bytearray(original)
        struct.pack_into("<I", wrong_id, 0, node_id ^ 1)
        malformed(name + " wrong node ID", lambda d=bytes(wrong_id), n=node_id, f=decoder: f(d, n))
        wrong_count = bytearray(original)
        struct.pack_into("<I", wrong_count, 4, 0xFFFFFFFF)
        malformed(name + " impossible count", lambda d=bytes(wrong_count), n=node_id, f=decoder: f(d, n))
    bad_path = bytearray(raw["customArray"])
    # Mutate the independently located final path-length word, not a node ID.
    final_start = len(words) - len(paths[-1]) - 1
    struct.pack_into("<H", bad_path, 8 + final_start * 2, 0xFFFF)
    malformed("customArray truncated final path", lambda: decode_paths(bytes(bad_path), nodes["customArray"]["id"]))
    assert phase_hash(TARGET + (5, 1)) == 0xA0D58F1A
    assert not unsupported, "Some registered roots lack a pinned hash seed"
    assert all(not row["registered_path_hash_collisions"] for row in contexts)
    current_ps = read(HERE.parent / "identity_01/save_inventory/capture_03/manifest.json")
    result = {
        "status": "EXACT_COMPONENT_MEMBERSHIP_NO_SETUP_COMPLETION_CERTIFICATE",
        "source_body_sha256": manifest["source_sha256"], "source_metadata_sha256": manifest["metadata_sha256"],
        "custom_array_words": len(words), "interned_paths": len(paths),
        "path_root_counts": dict(Counter(str(path[0]) if path else "empty" for path in paths)),
        "duplicate_paths": len(paths) - len(set(paths)), "target_contexts": contexts,
        "event_records": len(events),
        "event_zero_sentinel_pattern_rows": sum(row == (0, 0, 0xFFFF, 0) for row in events),
        "node_instance_record_count": len(instance),
        "node_instance_raw_rows": [[str(row[0]), row[1], row[2], row[3]] for row in instance],
        "queued_data_empty_retained_lists": True,
        "quest_debug_lines": read(INPUT / "quest_debug_lines.json")["lines"],
        "prior_controller_and_vehicle_key_matches": current_ps["candidate_matches"],
        "checks": controls, "controls_status": "PASS",
        "interpretation_limits": [
            "Initialized-path membership is not active-owner or completion proof.",
            "EventManager phase membership needs source registration/removal/restore semantics; no event rows does not prove never executed.",
            "nodeInstanceDataManager rows use a validated fixed record frame, but their internal fields are not assigned EventManager semantics.",
            "No empty current queue is interpreted as evidence that no past event was dispatched or applied.",
            "No source body is bound to the earlier JF01/JF02 loaded session.",
        ],
        "input_pins": {str(INPUT / "manifest.json"): sha(INPUT / "manifest.json"), str(INPUT / "event_records.json"): sha(INPUT / "event_records.json")},
        "game_calls": 0, "save_reads": 0, "save_writes": 0, "runtime_changes": 0,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["status", "interned_paths", "event_records", "queued_data_empty_retained_lists"]} | {"controls": len(controls), "target_event_rows": sum(len(row["event_manager_phase_rows"]) for row in contexts)}))


if __name__ == "__main__":
    main()
