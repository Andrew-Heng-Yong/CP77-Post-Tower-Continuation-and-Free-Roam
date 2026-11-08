"""Native EventManager layout and full-width parent/node address checks.

The managed parser splits the native UInt32 node ID into two UInt16 fields.
This successor uses the native width; the earlier raw-frame reports remain.
"""
from pathlib import Path
import json
import struct
from analyze_components import HERE, INPUT, read, sha, phase_hash, decode_paths


def native_records(data, node_id):
    if len(data) < 8 or struct.unpack_from("<I", data)[0] != node_id:
        raise ValueError("Wrong node header")
    count = struct.unpack_from("<I", data, 4)[0]
    if 8 + count * 16 != len(data):
        raise ValueError("Wrong record frame")
    return list(struct.iter_unpack("<QII", data[8:]))


def exact_rows(records, context, node_id):
    return [(index, row) for index, row in enumerate(records) if row[1] == context and row[2] == node_id]


def cname(value):
    result = 0xCBF29CE484222325
    for byte in value.encode("utf-8"):
        result = ((result ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return result


def main():
    output = HERE / "native_layout_01.json"
    assert not output.exists(), "Fresh output required"
    manifest = read(INPUT / "manifest.json")
    nodes = {row["name"]: row for row in manifest["nodes"]}
    assert sha(nodes["eventManager"]["path"]) == nodes["eventManager"]["sha256"]
    records = native_records(Path(nodes["eventManager"]["path"]).read_bytes(), nodes["eventManager"]["id"])
    managed = read(INPUT / "event_records.json")["records"]
    assert records == [(int(row["u64_0"]), row["u32_8"], row["u16_12"] | (row["u16_14"] << 16)) for row in managed]
    binding_path = HERE.parent / "saved_graph_state_01/inspector_review_01/root_binding_decode_01.json"
    binding = read(binding_path)
    ancestor = []
    for step in binding["source_ancestry_steps"]:
        parent = tuple(step["phase_path_before"])
        context = phase_hash(parent)
        node = step["phase_node"]
        selected = exact_rows(records, context, node)
        ancestor.append({"parent_path": parent, "phase_hash_u32": str(context), "phase_node_u32": node,
                         "serialized_rows": [{"ordinal": index, "type_token_u64": str(row[0]), "node_id_u32": row[2]} for index, row in selected]})
    checks = []
    def ck(name, result):
        assert result, name
        checks.append({"name": name, "pass": True})
    ck("Native full32 nodeID and managed two16 fields agree for every row", len(records) == len(managed))
    ck("Current capture upper nodeID halves are zero", all(row[2] <= 0xFFFF for row in records))
    ck("Root phase-node type token matches exact class CName", exact_rows(records, phase_hash((1,)), 0)[0][1][0] == cname("questPhaseNodeDefinition"))
    previous = read(HERE / "ancestor_membership_01.json")["route"]
    ck("Current eight ancestor results unchanged under full32 comparison", all(
        [r["ordinal"] for r in current["serialized_rows"]] == [r["ordinal"] for r in old["serialized_handler_rows"]]
        for current, old in zip(ancestor, previous)) and len(ancestor) == len(previous) == 8)
    # Damaging the upper half of a real matched row must not alias the low16 ID.
    index, matched = exact_rows(records, phase_hash((1,)), 0)[0]
    changed = list(records)
    changed[index] = (matched[0], matched[1], matched[2] | 0x10000)
    ck("Upper-half mutation rejected by exact native address query", not exact_rows(changed, matched[1], 0))
    ck("A low16-only implementation would accept that damaged address", any((row[2] & 0xFFFF) == 0 and row[1] == matched[1] for row in changed))
    ck("Native free-slot sentinel is preserved as nodeID32 0000FFFF", sum(row == (0, 0, 0xFFFF) for row in records) == 5148)
    data = {
        "status": "NATIVE_FULL32_ADDRESS_QUERY_VERIFIED_NO_SETUP_RECEIPT",
        "native_record": {"type_token": "UInt64+0", "phase_hash": "UInt32+8", "node_id": "UInt32+12"},
        "records": len(records), "ancestor_route": ancestor, "checks": checks,
        "scope": "Native structure width and exact saved address membership; no runtime dispatch or past completion inferred.",
        "correction": "The managed Unknown4/raw tail16 is the upper half of native nodeID32, not a separate flag. All current values are0, so prior current membership results stand. Future queries must compare the full32-bit nodeID.",
        "pins": {str(INPUT / "manifest.json"): sha(INPUT / "manifest.json"), str(binding_path): sha(binding_path),
                 str(HERE / "ancestor_membership_01.json"): sha(HERE / "ancestor_membership_01.json")},
        "game_calls": 0, "save_reads": 0, "runtime_changes": 0,
    }
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": data["status"], "controls": len(checks), "ancestor_matches": sum(len(row["serialized_rows"]) for row in ancestor)}))


if __name__ == "__main__":
    main()
