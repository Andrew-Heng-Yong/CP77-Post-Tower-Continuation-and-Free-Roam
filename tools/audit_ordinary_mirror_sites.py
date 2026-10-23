"""Map simple vanilla mirror leaves to their world-sector owners.

This is an inventory, not an activation allowlist. A simple graph shape does
not establish that a site is reachable or story-safe after The Tower.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTROL = ROOT / "research/b0_mirror_investigation/extracted/json/base/open_world/scenes/mirrors/mirror_interactions_control.questphase.json"
BLOCKS = ROOT / "research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default"
EXTRACTED = ROOT / "research/b0_mirror_rollout/vanilla_ordinary/json"
EXCLUDED = {6, 7, 9, 10, 11, 12, 24, 37}


def val(obj: object) -> str:
    if isinstance(obj, dict):
        return str(obj.get("$value", ""))
    return str(obj)


def nested(obj: object):
    if isinstance(obj, dict):
        yield obj
        for item in obj.values():
            yield from nested(item)
    elif isinstance(obj, list):
        for item in obj:
            yield from nested(item)


def main() -> None:
    control = json.loads(CONTROL.read_text(encoding="utf-8"))["Data"]["RootChunk"]
    outer = next(n["Data"] for n in control["graph"]["Data"]["nodes"] if n["Data"]["id"] == 42)
    descriptors = []
    for block in (BLOCKS / "blocks/all.streamingblock.json", BLOCKS / "ep1/blocks/all.streamingblock.json"):
        doc = json.loads(block.read_text(encoding="utf-8"))["Data"]["RootChunk"]
        for descriptor in doc["descriptors"]:
            ref = val(descriptor.get("questPrefabNodeRef", {}))
            if "#mirror_scene_" in ref:
                descriptors.append({"block": str(block.relative_to(ROOT)), "ref": ref,
                                    "sector": val(descriptor["data"]["DepotPath"]),
                                    "category": descriptor.get("category"),
                                    "variants": descriptor.get("variants", [])})
    records = []
    for node in outer["phaseGraph"]["Data"]["nodes"]:
        phase = node["Data"]
        if phase["$type"] != "questPhaseNodeDefinition":
            continue
        contents = [n["Data"] for n in phase["phaseGraph"]["Data"]["nodes"]]
        scenes = [n for n in contents if n["$type"] == "questSceneNodeDefinition"]
        if len(scenes) != 1:
            continue
        scene = scenes[0]
        # The scene filename and prefab spelling differ at some sites: use the
        # marker prefix, then reconcile against the registered prefab refs.
        marker = val(scene["sceneLocation"]["nodeRef"])
        guessed = marker.replace("#mirror_sm_", "#mirror_", 1)
        exact = [d for d in descriptors if d["ref"].endswith("/" + guessed)]
        triggers = sorted({val(x["triggerAreaRef"]) for n in contents for x in nested(n)
                           if "triggerAreaRef" in x})
        facts = sorted({val(x["factName"]) for n in contents for x in nested(n)
                        if "factName" in x})
        records.append({"id": phase["id"], "scene": val(scene["sceneFile"]["DepotPath"]),
                        "marker": marker, "guessed_prefab": guessed, "triggers": triggers,
                        "facts": facts, "simple_shape": phase["id"] not in EXCLUDED,
                        "descriptor_matches": exact})
    simple = [r for r in records if r["simple_shape"]]
    print(f"leaves={len(records)} simple={len(simple)} descriptor_matches={sum(len(r['descriptor_matches']) == 1 for r in simple)}")
    print("id\tscene\ttrigger\tsector\tcategory\tflags")
    for r in simple:
        matches = r["descriptor_matches"]
        flags = []
        if len(matches) != 1:
            flags.append(f"descriptor_count={len(matches)}")
        if len(r["triggers"]) != 1:
            flags.append(f"trigger_count={len(r['triggers'])}")
        if r["facts"]:
            flags.append("facts=" + ",".join(r["facts"]))
        scene_path = EXTRACTED / (r["scene"].replace("\\", "/") + ".json")
        if scene_path.exists():
            scene_doc = json.loads(scene_path.read_text(encoding="utf-8"))["Data"]["RootChunk"]
            scene_refs = sorted({val(x["triggerAreaRef"]) for x in nested(scene_doc)
                                 if "triggerAreaRef" in x})
            scene_facts = sorted({val(x["factName"]) for x in nested(scene_doc)
                                  if "factName" in x})
            scene_types = sorted({x.get("$type", "") for x in nested(scene_doc)
                                  if "factName" in x})
            if scene_refs != r["triggers"]:
                flags.append("scene_trigger=" + ",".join(scene_refs))
            if scene_facts:
                flags.append("scene_facts=" + ",".join(scene_facts))
            if "questFactsDBManagerNodeDefinition" in scene_types:
                flags.append("scene_fact_writer")
        if matches:
            sector_path = EXTRACTED / (matches[0]["sector"].replace("\\", "/") + ".json")
            if sector_path.exists():
                sector_doc = json.loads(sector_path.read_text(encoding="utf-8"))["Data"]["RootChunk"]
                nodes = sector_doc.get("nodes", [])
                if len(nodes) != 1 or nodes[0]["Data"]["$type"] != "worldTriggerAreaNode":
                    flags.append("sector_nodes=" + ",".join(n["Data"]["$type"] for n in nodes))
        print(f"{r['id']}\t{Path(r['scene']).name}\t{','.join(r['triggers'])}\t"
              f"{matches[0]['sector'] if matches else '-'}\t"
              f"{matches[0]['category'] if matches else '-'}\t{','.join(flags)}")


if __name__ == "__main__":
    main()
