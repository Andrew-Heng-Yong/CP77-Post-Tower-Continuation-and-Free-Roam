"""Export a bounded, reproducible Wilson owner/anchor research slice.

Reads extracted vanilla files only. Does not build or install game resources.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "research/b0_wilson_vendor"
OWNER = ROOT / "research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json"
INDEX = ROOT / "research/phase2b_p4/vendor_analysis/analysis.json"
ANCHOR = OUT / "anchor_extract/basegame_3_nightcity/json/base/worlds/03_night_city/_compiled/default/quest_6462c5f516845efa.streamingsector.json"
RESOURCE = r"base\quest\default_dialogs.questphase"
PREFIX = RESOURCE + "::Data.RootChunk.graph.Data.nodes.5.Data.phaseGraph.Data.nodes.10.Data.phaseGraph.Data.nodes.3.Data.phaseGraph.Data"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def val(value):
    return value.get("$value") if isinstance(value, dict) else value


def compact_node(value):
    """Keep conditions in full; omit socket internals and embedded child graphs."""
    return {k: v for k, v in value.items() if k not in ("sockets", "phaseGraph")}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def graph_edges(graph, label, handles):
    """Resolve owning socket lists, including CutSource reference-only sockets."""
    def resolve(wrapper):
        key = str(wrapper.get("HandleId", wrapper.get("HandleRefId")))
        return key, handles[key]

    socket_owners = {}
    connections = {}
    for wrapper in graph["nodes"]:
        _, node = resolve(wrapper)
        for socket_wrapper in node.get("sockets", []):
            key, socket = resolve(socket_wrapper)
            assert key not in socket_owners, (label, key)
            socket_owners[key] = (node["id"], val(socket["name"]), socket["type"])
            for connection in socket.get("connections", []):
                connection_key, data = resolve(connection)
                connections[connection_key] = data
    rows = []
    for connection_key, connection in connections.items():
        source_key, _ = resolve(connection["source"])
        destination_key, _ = resolve(connection["destination"])
        source = socket_owners[source_key]
        destination = socket_owners[destination_key]
        rows.append({"graph": label, "connection_handle": connection_key,
                     "source_node_id": source[0], "source_socket": source[1], "source_type": source[2],
                     "destination_node_id": destination[0], "destination_socket": destination[1], "destination_type": destination[2]})
    return sorted(rows, key=lambda r: (r["source_node_id"], r["source_socket"], r["destination_node_id"]))


def main():
    owner = read(OWNER)["Data"]["RootChunk"]
    analysis = read(INDEX)
    outer = owner["graph"]["Data"]["nodes"][5]["Data"]["phaseGraph"]["Data"]["nodes"][10]["Data"]["phaseGraph"]["Data"]["nodes"][3]["Data"]["phaseGraph"]["Data"]
    inner = outer["nodes"][5]["Data"]["phaseGraph"]["Data"]
    outer_nodes = {n["Data"]["id"]: n["Data"] for n in outer["nodes"]}
    inner_nodes = {n["Data"]["id"]: n["Data"] for n in inner["nodes"]}
    handles = {str(v["HandleId"]): v["Data"] for v in walk(owner) if "HandleId" in v and "Data" in v}
    resolved_edges = graph_edges(outer, "outer", handles) + graph_edges(inner, "inner", handles)
    cut_edges = [e for e in resolved_edges if e["source_type"] == "CutSource"]
    assert any(e["source_node_id"] == 56 and e["destination_node_id"] == 4 for e in cut_edges)
    assert outer_nodes[12]["$type"] == "questPauseConditionNodeDefinition"
    assert val(inner_nodes[4]["sceneFile"]["DepotPath"]).endswith(r"wat_lch_gunsmith_01\wat_lch_gunsmith_01.scene")
    assert val(inner_nodes[5]["actions"][0]["type"]["Data"]["phaseName"]) == "q001_give_weapon"
    assert val(inner_nodes[9]["actions"][0]["type"]["Data"]["phaseName"]) == "q001_give_weapon"
    sector = read(ANCHOR)["Data"]["RootChunk"]
    matches = [d for d in sector["nodeData"]["Data"] if str(val(d["QuestPrefabRefHash"])).endswith("/#loading_conditions_ent_wat_lch_gunsmith_01")]
    assert len(matches) == 1
    anchor_data = matches[0]
    anchor_node = sector["nodes"][anchor_data["NodeIndex"]]["Data"]
    assert anchor_node["$type"] == "worldEntityNode"
    assert val(anchor_node["entityTemplate"]["DepotPath"]) == r"base\gameplay\devices\empty_visible_object.ent"
    evidence = {
        "status": "STATIC_RESEARCH_ONLY_NO_BUILD_OR_INSTALL",
        "sources": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in (OWNER, INDEX, ANCHOR)],
        "graph_prefix": PREFIX,
        "owner_phase_prefabs": owner["phasePrefabs"],
        "outer_nodes": [compact_node(n) for n in outer_nodes.values()],
        "inner_nodes": [compact_node(n) for n in inner_nodes.values()],
        "edges": [e for e in analysis["edges"] if e["graph"].startswith(PREFIX)],
        "resolved_socket_edges_including_cuts": resolved_edges,
        "cut_edges": cut_edges,
        "anchor": {"node": anchor_node, "node_data": anchor_data},
        "whole_anchor_prefab_census": dict(Counter(n["Data"]["$type"] for n in sector["nodes"])),
        "whole_anchor_prefab_non_entity_nodes": [compact_node(n["Data"]) for n in sector["nodes"] if n["Data"]["$type"] != "worldEntityNode"],
        "interpretation_limit": "Static references and topology do not prove current live registration, actor presence, or scene execution.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "owner_evidence.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Wilson graph: {len(outer_nodes)} outer / {len(inner_nodes)} inner nodes; {len(resolved_edges)} resolved edges including {len(cut_edges)} cut edge(s)")
    print(f"Anchor node {anchor_data['NodeIndex']}: {anchor_data['Position']}")
    print(f"Whole prefab: {evidence['whole_anchor_prefab_census']}; NOT a single-shop owner")
    print(f"Evidence: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
