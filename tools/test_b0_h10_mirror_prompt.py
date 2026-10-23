"""Validate the bounded H10 world-prompt candidate after building it."""

from __future__ import annotations

import copy
import json
from collections import deque
from pathlib import Path

from report_scene_route import scalars, unwrap


ROOT = Path(__file__).resolve().parent.parent
PROMPT = ROOT / "research/b0_h10_mirror_prompt/validation"
MANUAL = ROOT / "research/b0_h10_vonly_mirror/validation"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def nodes(scene: dict) -> dict[int, dict]:
    return {
        item["Data"]["nodeId"]["id"]: item["Data"]
        for item in scene["Data"]["RootChunk"]["sceneGraph"]["Data"]["graph"]
    }


def targets(node: dict) -> list[int]:
    return [
        dest["nodeId"]["id"]
        for socket in node.get("outputSockets", [])
        for dest in socket.get("destinations", [])
    ]


def reachable(graph: dict[int, dict], start: int) -> set[int]:
    seen: set[int] = set()
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        assert current in graph, f"Missing scene node {current}"
        seen.add(current)
        queue.extend(targets(graph[current]))
    return seen


def path_avoiding(graph: dict[int, dict], start: int, end: int, blocked: set[int]) -> list[int] | None:
    queue = deque([(start, [start])])
    seen: set[int] = set()
    while queue:
        current, path = queue.popleft()
        if current == end:
            return path
        if current in seen or current in blocked:
            continue
        seen.add(current)
        queue.extend((next_id, path + [next_id]) for next_id in targets(graph[current]))
    return None


def scene_check() -> None:
    scene = read(PROMPT / "mirror_prompt.scene.json")
    reviewed = read(MANUAL / "h10_v_mirror.scene.json")
    expected = copy.deepcopy(reviewed)
    expected["Header"]["ExportedDateTime"] = scene["Header"]["ExportedDateTime"]
    prior = nodes(expected)
    assert targets(prior[434]) == [220]
    assert targets(prior[242]) == [2]
    entry_dest = prior[434]["outputSockets"][0]["destinations"]
    entry_dest[0]["nodeId"]["id"] = 509
    exit_monitor = copy.deepcopy(entry_dest[0])
    exit_monitor["nodeId"]["id"] = 1112
    entry_dest.append(exit_monitor)
    prior[242]["outputSockets"][0]["destinations"][0]["nodeId"]["id"] = 509
    assert targets(prior[1112]) == [1109]
    prior[1112]["outputSockets"][0]["destinations"][0]["nodeId"]["id"] = 1104
    assert expected == scene, "Prompt scene changed beyond the four reviewed edge edits"
    graph = nodes(scene)
    entries = {
        unwrap(entry["name"]): entry["nodeId"]["id"]
        for entry in scene["Data"]["RootChunk"]["entryPoints"]
    }
    assert entries["in_mirror"] == 434
    assert set(targets(graph[434])) == {509, 1112}
    assert all(
        destination["isockStamp"]["ordinal"] == 0
        and destination["isockStamp"]["name"] == 0
        for destination in graph[434]["outputSockets"][0]["destinations"]
    )
    assert targets(graph[509]) == [220]
    assert targets(graph[242]) == [509]
    assert graph[220]["mode"] == "attachToWorld"
    assert graph[220]["shapeParams"]["Data"]["customActivationRange"] == 1.60000002

    visited = reachable(graph, entries["in_mirror"])
    assert 2 in visited, "H10 exit path must end the scene"
    assert {1112, 1104, 220, 226, 242, 509}.issubset(visited)
    assert not {1, 6, 10, 43, 47, 1095, 1098, 1101, 1114, 1339, 1602, 1084, 988, 1000, 1003}.intersection(visited)
    choices = {
        item["nodeId"]["id"]: {unwrap(option.get("caption")) for option in item.get("options", [])}
        for item in (graph[node_id] for node_id in visited)
        if item["$type"] == "scnChoiceNode"
    }
    assert choices == {220: {"mirror"}, 226: {"leave"}}, choices
    for acquired, released in [
        (853, 866), (860, 867), (441, 445), (443, 446),
        (609, 614), (476, 484), (1077, 1080), (224, 497),
    ]:
        assert {acquired, released}.issubset(visited), (acquired, released)
    facts = {
        str(value)
        for node_id in visited
        for value in scalars(graph[node_id].get("questNode", {}).get("Data", {}), "factName")
    }
    assert facts == {"mq000_mirror_blinders_closed"}, facts
    root = scene["Data"]["RootChunk"]
    assert all(not prop["spawnDespawnParams"]["spawnOnStart"] for prop in root["props"])
    assert all(not actor["spawnDespawnParams"]["spawnOnStart"] for actor in root["actors"])
    assert any(actor["actorName"] == "johnny_mirror" for actor in root["actors"])
    print(f"Prompt scene: {len(visited)} reachable nodes; mirror/leave only; exact four edge edits; no start-spawn actors/props")
    # This is a known HOLD, not a safe-exit proof: an outside-triggered end
    # can still bypass normal action inverses on teleport/forced exit.
    inverses = {497, 614, 484, 866, 867, 445, 446}
    bypass = path_avoiding(graph, 1112, 2, inverses)
    assert bypass is not None, "Reassess the asynchronous-exit design before changing this safety check"
    print("HOLD: forced outside exit bypasses active mirror cleanup: " + " -> ".join(map(str, bypass)))


def gate_check() -> None:
    old = read(MANUAL / "manual_gate.questphase.json")["Data"]["RootChunk"]
    new = read(PROMPT / "prompt_gate.questphase.json")["Data"]["RootChunk"]
    expected = copy.deepcopy(old)
    node = next(item["Data"] for item in expected["graph"]["Data"]["nodes"] if item.get("Data", {}).get("id") == 7)
    assert node["sceneFile"]["DepotPath"]["$value"] == "towercontinued\\b0_h10_vonly_mirror\\h10_v_mirror.scene"
    node["sceneFile"]["DepotPath"]["$value"] = "towercontinued\\b0_h10_mirror_prompt\\mirror_prompt.scene"
    assert expected == new, "Manual gate changed beyond the scene resource path"
    print("Quest gate: identical to tested manual gate except its mod-owned scene path")


if __name__ == "__main__":
    scene_check()
    gate_check()
