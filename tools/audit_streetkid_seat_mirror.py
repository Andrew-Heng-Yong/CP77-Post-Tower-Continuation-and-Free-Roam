"""Report the q000 El Coyote workspots, mirror device events and scene inputs."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PHASE = ROOT / "research/b0_second_mirror/streetkid/json/base/quest/main_quests/prologue/q000/phases/q000_kid_01_coyote.questphase.json"
SCENE = ROOT / "research/b0_second_mirror/streetkid_scene/json/base/quest/main_quests/prologue/q000/scenes/q000_kid_01a_bar_activities.scene.json"


def visit(value: object, path: str = "$"):
    if isinstance(value, dict):
        yield path, value
        for key, item in value.items():
            yield from visit(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from visit(item, f"{path}[{index}]")


def values(value: object, key: str) -> list[str]:
    result = []
    for _, item in visit(value):
        if key in item:
            found = item[key]
            if isinstance(found, dict):
                found = found.get("$value", found)
            result.append(str(found))
    return result


def main() -> None:
    phase = json.loads(PHASE.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
    scene = json.loads(SCENE.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
    print("q000 workspot/device/scene nodes:")
    for path, node in visit(phase):
        kind = node.get("$type", "")
        if kind not in {"questUseWorkspotNodeDefinition", "questDeviceManagerNodeDefinition", "questSceneNodeDefinition"}:
            continue
        print(json.dumps({
            "path": path, "id": node.get("id"), "type": kind,
            "nodeRefs": values(node, "nodeRef"),
            "workspotNodes": values(node, "workspotNode"),
            "functions": values(node, "function"),
            "sceneFiles": values(node, "sceneFile"),
            "inputNames": values(node, "inputName"),
        }, ensure_ascii=False))
    print("bar activity entries:", json.dumps([
        {"name": item["name"].get("$value"), "node": item["nodeId"]["id"]}
        for item in scene["entryPoints"]
    ]))
    print("bar scene has mirror reference:", "mirror" in json.dumps(scene).lower())


if __name__ == "__main__":
    main()
