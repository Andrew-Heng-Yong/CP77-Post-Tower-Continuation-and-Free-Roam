"""Check the typed graph readback independently of the graph editor."""

from collections import Counter
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "phone_support_ph1"))
from model import model, read, sha, walk

SERIALIZED = HERE / "serialized_01"
NATIVE = (HERE.parents[1] / "diagnostics/vanilla_parity_20261029_01"
          / "pass_02/raw/basegame_4_gamedata")
DEPPATH = "base\\quest\\side_quests\\sq030\\phases"
CONTRACTS = {
    "sq030_msg_left_01": ([0, 2, 7, 8, 15, 16], 26, "AA1CA14796E5CD6E9CA21C06500DAF738B299575075B85F14B5427010AA19586"),
    "sq030_msg_left_02": ([0], None, "240EA55337113736362FE17A0792C85C7ADFFD603E6F22DE6B4FB5B399E765A9"),
    "sq030_msg_left_03": ([0, 2, 6, 7, 19, 20, 30, 31], 11, "A8F8F3D0ADA8BA23510CECDEE091DB32FA0B114C64310A936EB3B821A2C655CF"),
}
TOWER = {
    "PostTowerFreeRoamActive": 1, "PTFRP0_DR13": 1, "q307_active": 0,
    "q307_done": 1, "q307_finished": 1, "q307_2079": 1,
}
RESUMABLE = {"questInputNodeDefinition", "questGameManagerNodeDefinition", "questPauseConditionNodeDefinition"}


def sockets(path):
    data = read(path)["Data"]
    root = data["RootChunk"]
    handles = {v["HandleId"]: v["Data"] for v in walk(data) if "HandleId" in v}

    def chunk(h):
        return h["Data"] if "Data" in h else handles[h["HandleRefId"]]

    def key(h):
        return h.get("HandleId", h.get("HandleRefId"))

    graph = chunk(root["graph"])
    owners = {}
    definitions = {}
    for h in graph["nodes"]:
        node = chunk(h)
        for s in node["sockets"]:
            sock = chunk(s)
            point = (node["id"], sock["name"]["$value"])
            assert key(s) not in owners and point not in definitions
            owners[key(s)] = point
            definitions[point] = sock

    edges = {}
    for point, sock in definitions.items():
        edges[point] = []
        for h in sock["connections"]:
            link = chunk(h)
            edge = (*owners[key(link["source"])], *owners[key(link["destination"])])
            assert point in (edge[:2], edge[2:])
            edges[point].append(edge)
    assert all(count == 2 for count in Counter(edge for links in edges.values() for edge in links).values())
    assert all(len(links) == len(set(links)) for links in edges.values())
    shell = {**data, "RootChunk": {k: v for k, v in root.items() if k != "graph"}}
    return shell, {p: s["type"] for p, s in definitions.items()}, edges


def reachable(edges, source):
    visited = set()
    pending = [source]
    while pending:
        node = pending.pop()
        for edge in edges:
            if edge[0] == node and edge not in visited:
                visited.add(edge)
                pending.append(edge[2])
    return visited


def verify_gate(node):
    assert node["$type"] == "questConditionNodeDefinition"
    condition = node["condition"]
    assert condition["$type"] == "questLogicalCondition" and condition["operation"] == "AND"
    facts = {}
    for c in condition["conditions"]:
        assert c["$type"] == "questFactsDBCondition"
        t = c["type"]
        assert t["$type"] == "questVarComparison_ConditionType" and t["comparisonType"] == "Equal"
        assert t["factName"] not in facts
        facts[t["factName"]] = t["value"]
    assert facts == TOWER


def verify_phase(row, providers):
    depot = row["depot"]
    name = Path(depot).stem
    assert depot == f"{DEPPATH}\\{name}.questphase"
    boundaries, expiry, json_pin = CONTRACTS[name]
    vanilla = NATIVE / depot
    original = vanilla.with_suffix(".questphase.json")
    raw = SERIALIZED / vanilla.name
    readback = raw.with_suffix(".questphase.json")
    assert sha(vanilla) == providers[name]["sha256"] and sha(original) == json_pin
    assert sha(raw) == row["sha256"] and sha(readback) == row["readback_sha256"]
    old, new = model(original), model(readback)
    assert list(old) == list(new) == ["root"]
    old, new = old["root"], new["root"]
    assert list(new["nodes"]) == list(old["nodes"]) + [100 + source for source in boundaries]
    assert all(new["nodes"][i] == n for i, n in old["nodes"].items())
    old_shell, old_types, old_links = sockets(original)
    new_shell, new_types, new_links = sockets(readback)
    assert old_shell == new_shell and all(new_types[p] == t for p, t in old_types.items())

    def sends(edge):
        return edge[3] == "Active" and old["nodes"][edge[2]]["$type"] == "questJournalNodeDefinition"

    assert set(boundaries) == {
        i for i, n in old["nodes"].items() if n["$type"] in RESUMABLE
        and any(sends(e) for e in reachable(old["edges"], i))
    }
    expected = set(old["edges"])
    for source in boundaries:
        gate = 100 + source
        stop = 1 if source == 0 else expiry
        verify_gate(new["nodes"][gate])
        assert {name: t for (i, name), t in new_types.items() if i == gate} == {
            "CutDestination": "CutDestination", "In": "Input", "True": "Output", "False": "Output",
        }
        rerouted = old_links[(source, "Out")]
        expected.difference_update(rerouted)
        allowed = [(gate, "False", b, s) for _, _, b, s in rerouted]
        expected.update(allowed)
        expected.update({(source, "Out", gate, "In"), (gate, "True", stop, "In")})
        assert new_links[(gate, "False")] == allowed
        cleanup = reachable(new["edges"], stop)
        assert not any(sends(e) for e in cleanup)
        cleanup_nodes = {stop, *(e[2] for e in cleanup)}
        assert cleanup_nodes - {e[0] for e in cleanup} == {1}
        assert new["nodes"][1]["type"] == "Terminating"
        assert all(new["nodes"][i]["$type"] in {
            "questOutputNodeDefinition", "questConditionNodeDefinition",
            "questLogicalXorNodeDefinition", "questJournalNodeDefinition",
        } for i in cleanup_nodes)
    assert set(new["edges"]) == expected
    return {
        "depot": depot, "sha256": row["sha256"], "native_nodes_preserved": len(old["nodes"]),
        "verified_boundaries": boundaries, "expiry_node": expiry,
    }


if __name__ == "__main__":
    assert __debug__, "Run verification with assertions enabled"
    manifest = read(SERIALIZED / "manifest.json")
    rows = [verify_phase(row, manifest["providers"]) for row in manifest["resources"]]
    assert len(rows) == len(CONTRACTS) == 3
    assert {Path(row["depot"]).stem for row in rows} == set(CONTRACTS)
    result = {"status": "PASS_TYPED_JUDY_TRAVEL_GUARDS", "resources": rows, "gameplay": "UNTESTED"}
    with (HERE / "verification.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(f"Verified {sum(len(row['verified_boundaries']) for row in rows)} native message boundaries")
