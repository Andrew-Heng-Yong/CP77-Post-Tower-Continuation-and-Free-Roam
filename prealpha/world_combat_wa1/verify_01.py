"""Validate the gated WA1 encounter probe without changing the game."""
import hashlib
import json
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent.parent
B = W / "prealpha/coaster_jean_jc1/candidate_01"
P = H / "candidate_04"
sys.path.insert(0, str(W / "prealpha/sidejobs_s29"))
import common  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


old = json.loads((B / "manifest.json").read_text(encoding="utf-8"))
new = json.loads((P / "manifest.json").read_text(encoding="utf-8"))
old_files = {r["path"]: r["sha256"] for r in old["files"]}
new_files = {r["path"]: r["sha256"] for r in new["files"]}
assert len(old_files) == len(new_files) == 51 and old_files.keys() == new_files.keys()
changed = {p for p in old_files if old_files[p] != new_files[p]}
assert changed == {
    "archive/pc/mod/zzzz_PTFR_Combined.archive",
    "archive/pc/mod/zzzz_PTFR_Combined.archive.xl",
}, changed
for rel, digest in new_files.items():
    assert sha(P / "package" / rel) == digest, rel

old_source = {str(p.relative_to(B / "archive_source")).lower(): sha(p) for p in (B / "archive_source").rglob("*") if p.is_file()}
new_source = {str(p.relative_to(P / "archive_source")).lower(): sha(p) for p in (P / "archive_source").rglob("*") if p.is_file()}
assert len(old_source) == 1172 and len(new_source) == 1173
assert all(new_source[rel] == digest for rel, digest in old_source.items())
added = set(new_source) - set(old_source)
assert added == {r"towercontinued\world_combat_wa1\ce_pac_cvi_116_probe.questphase"}

native_path = W / "diagnostics/world_npc_idle_20261026_01/combat_owners/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase.json"
native = json.loads(native_path.read_text(encoding="utf-8"))
native_graph = next(g for g in common.flatten(common.SafeResource(native), native["Data"]["RootChunk"]) if g["path"] == "root/28/18")
readback = json.loads((P / "probe_readback_01.json").read_text(encoding="utf-8"))
graphs = list(common.flatten(common.SafeResource(readback), readback["Data"]["RootChunk"]))
assert len(graphs) == 1
graph = graphs[0]
assert len(native_graph["nodes"]) == 11 and len(graph["nodes"]) == 12
assert len(native_graph["edges"]) == 13 and len(graph["edges"]) == 14
native_nodes = {n["id"]: n for n in native_graph["nodes"]}
new_nodes = {n["id"]: n for n in graph["nodes"]}
assert all(new_nodes[nid] == node for nid, node in native_nodes.items())
assert set(new_nodes) - set(native_nodes) == {65000}
gate = new_nodes[65000]
assert gate["$type"] == "questPauseConditionNodeDefinition"
condition = gate["condition"]
assert condition["operation"] == "AND"
assert {(c["type"]["factName"], c["type"]["comparisonType"], c["type"]["value"]) for c in condition["conditions"]} == {
    ("q307_main_game_killed", "GreaterOrEqual", 1),
    ("q307_ep1_killed", "GreaterOrEqual", 1),
    ("PTFRWA1_TestRequest", "GreaterOrEqual", 1),
}
expected_edges = {tuple(e) for e in native_graph["edges"] if e != [0, "Out", 2, "In"]}
expected_edges |= {(0, "Out", 65000, "In"), (65000, "Out", 2, "In")}
assert {tuple(e) for e in graph["edges"]} == expected_edges
actions = [(a["type"].get("action"), a["type"].get("spawnerReference", {}).get("$value"))
           for n in graph["nodes"] if n["$type"] == "questSpawnManagerNodeDefinition" for a in n.get("actions", [])]
assert [a[0] for a in actions] == ["Reactivate", "ResetKillCount"]
assert len({a[1] for a in actions}) == 1 and "#ce_pac_cvi_116/cs_goons_cars_com" in actions[0][1]

xl_rel = "archive/pc/mod/zzzz_PTFR_Combined.archive.xl"
before_xl = (B / "package" / xl_rel).read_bytes()
after_xl = (P / "package" / xl_rel).read_bytes()
stanza = ("    - path: towercontinued\\world_combat_wa1\\ce_pac_cvi_116_probe.questphase\r\n"
          "      parent: ep1\\quest\\ep1.quest\r\n"
          "      input:\r\n"
          "        node: [1]\r\n"
          "        socket: Out\r\n").encode("utf-8")
assert after_xl.count(stanza) == 1
assert after_xl.replace(stanza, b"") == before_xl
assert json.loads((H / "compile_01/result.json").read_text())["status"] == "PASS"
collision = json.loads((P / "collisions_01.json").read_text(encoding="utf-8-sig"))
assert collision["archives"] == 67 and collision["collisions"] == []
proof = {
    "status": "PASS",
    "baseline_resources_unchanged": 1172,
    "new_private_resources": 1,
    "native_loop_nodes_exact": 11,
    "native_loop_edges_exact": 12,
    "gate_conditions": 3,
    "package_files": 51,
    "changed_package_files": sorted(changed),
    "external_archive_collisions": 0,
    "game_writes": 0,
    "save_writes": 0,
}
(H / "validation_01.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps(proof))
