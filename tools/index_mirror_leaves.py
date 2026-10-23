"""Print a bounded inventory of vanilla general-mirror controller leaves."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / (
    "research/b0_mirror_investigation/extracted/json/base/open_world/"
    "scenes/mirrors/mirror_interactions_control.questphase.json"
)


def walk(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def values(value: object, key: str) -> set[str]:
    found: set[str] = set()
    for obj in walk(value):
        if key not in obj:
            continue
        v = obj[key]
        if isinstance(v, dict):
            v = v.get("$value", v)
        if isinstance(v, (str, int, float)):
            found.add(str(v))
    return found


def main() -> None:
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    root = doc["Data"]["RootChunk"]["graph"]["Data"]
    outer = next(item["Data"] for item in root["nodes"] if item["Data"]["id"] == 42)
    leaves = []
    for item in outer["phaseGraph"]["Data"]["nodes"]:
        node = item["Data"]
        if node["$type"] != "questPhaseNodeDefinition":
            continue
        inner = node["phaseGraph"]["Data"]
        scenes = [i["Data"] for i in inner["nodes"] if i["Data"]["$type"] == "questSceneNodeDefinition"]
        if len(scenes) != 1:
            continue
        scene = scenes[0]["sceneFile"]["DepotPath"]["$value"]
        conditions = [i["Data"]["condition"]["Data"] for i in inner["nodes"]
                      if i["Data"]["$type"] in ("questPauseConditionNodeDefinition", "questConditionNodeDefinition")]
        gates = sorted({c["$type"] for c in conditions})
        facts = sorted({name for c in conditions for name in values(c, "factName")})
        triggers = sorted({name for c in conditions for name in values(c, "triggerAreaRef")})
        writers = sorted({i["Data"]["type"]["Data"]["factName"] for i in inner["nodes"]
                          if i["Data"]["$type"] == "questFactsDBManagerNodeDefinition"})
        leaves.append((node["id"], scene.rsplit("\\", 1)[-1], ",".join(triggers),
                       ",".join(gates), ",".join(facts), ",".join(writers)))
    print("id,scene,triggers,condition_types,fact_readers,fact_writers")
    for row in sorted(leaves):
        print(",".join(json.dumps(value) for value in row))
    print(f"TOTAL_MIRROR_LEAVES={len(leaves)}")


if __name__ == "__main__":
    main()
