"""Check the actual ancestor PhaseNode handler addresses as well as children.

A handler for a phase node is registered in its parent's phase hash. Searching
only the descendant phase hash would miss that owner. Membership is serialized
membership, not proof of actual engine execution or past node completion.
"""
from pathlib import Path
import json
from analyze_components import HERE, INPUT, read, sha, phase_hash, decode_records, decode_paths


def main():
    output = HERE / "ancestor_membership_01.json"
    assert not output.exists(), "Fresh output required"
    binding_path = HERE.parent / "saved_graph_state_01/inspector_review_01/root_binding_decode_01.json"
    binding = read(binding_path)
    manifest = read(INPUT / "manifest.json")
    nodes = {row["name"]: row for row in manifest["nodes"]}
    for row in nodes.values():
        assert sha(row["path"]) == row["sha256"]
    assert binding["source_body_sha256"] == manifest["source_sha256"]
    records = decode_records(Path(nodes["eventManager"]["path"]).read_bytes(), nodes["eventManager"]["id"])
    _, paths = decode_paths(Path(nodes["customArray"]["path"]).read_bytes(), nodes["customArray"]["id"])
    result = []
    for step in binding["source_ancestry_steps"]:
        parent_path = tuple(step["phase_path_before"])
        node_id = step["phase_node"]
        context_hash = phase_hash(parent_path)
        rows = [
            {"ordinal": index, "type_token_u64": str(row[0]), "phase_hash_u32": str(row[1]), "node_u16": row[2], "tail_u16": row[3]}
            for index, row in enumerate(records) if row[1] == context_hash and row[2] == node_id
        ]
        result.append({"source_depot": step["depot"], "source_graph": step["graph"],
                       "parent_path": parent_path, "phase_node": node_id, "phase_hash_u32": str(context_hash),
                       "parent_path_in_registry": parent_path in paths, "serialized_handler_rows": rows})
    data = {"status": "EXACT_SOURCE_ANCESTOR_ADDRESSES_QUERIED_NO_HISTORY_RECEIPT",
            "source_body_sha256": manifest["source_sha256"], "route": result,
            "source_binding": {"path": str(binding_path), "sha256": sha(binding_path)},
            "input_manifest_sha256": sha(INPUT / "manifest.json"),
            "limits": "Rows are queried at exact parent-context/node pairs; this is not actual dispatch, original setup completion or current physical lease proof.",
            "game_calls": 0, "save_reads": 0, "runtime_changes": 0}
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": data["status"], "route_nodes": len(result),
                      "serialized_matching_rows": sum(len(row["serialized_handler_rows"]) for row in result)}))


if __name__ == "__main__":
    main()
