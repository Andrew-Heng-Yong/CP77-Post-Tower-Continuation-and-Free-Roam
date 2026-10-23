"""Static scope checks for repeatable Afterlife mirror with absolute NodeRef."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from test_b0_h10_mirror_prompt import read
from test_b0_afterlife_mirror_v2 import graph_nodes, scene_nodes

ROOT = Path(__file__).resolve().parent.parent
VAL = ROOT / "research/b0_afterlife_mirror/validation_v4"
V2 = ROOT / "research/b0_afterlife_mirror/validation_v2"
FULL = (
    "$/03_night_city/c_watson/little_china/#loc_q103_afterlife/"
    "#loc_q103_afterlife_gameplay/#loc_q103_afterlife_devices/#mirror_plane_afterlife"
)
SHORT = "#mirror_plane_afterlife"


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "EXPERIMENTAL_V4_ABSOLUTE_PLANE_DISTANCE_NOT_INSTALLED"
    assert manifest["vanilla_replacements"] == []
    assert manifest["resources"] == [
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_owner.questphase",
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_scene.scene",
    ]
    archive = ROOT / "build/B0_Afterlife_Mirror_V4" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    owner2 = read(V2 / "afterlife_mirror_owner.questphase.json")
    owner4 = read(VAL / "afterlife_mirror_owner.questphase.json")
    scene2 = read(V2 / "afterlife_mirror_scene.scene.json")
    scene4 = read(VAL / "afterlife_mirror_scene.scene.json")
    assert set(graph_nodes(owner4)) == set(range(10))
    assert set(scene_nodes(scene4)) == set(scene_nodes(scene2))
    old_owner = json.dumps(owner2["Data"]["RootChunk"]["graph"], sort_keys=True)
    new_owner = json.dumps(owner4["Data"]["RootChunk"]["graph"], sort_keys=True)
    old_scene = json.dumps(scene2["Data"]["RootChunk"]["sceneGraph"], sort_keys=True)
    new_scene = json.dumps(scene4["Data"]["RootChunk"]["sceneGraph"], sort_keys=True)
    assert new_owner.count(FULL) == 1 and new_scene.count(FULL) == 1
    assert new_owner.replace(FULL, SHORT) == old_owner
    assert new_scene.replace(FULL, SHORT) == old_scene
    assert manifest["entry_gate"].startswith("Less than 4m")
    assert manifest["exit_gate"].startswith("Greater than 4m")
    print("Afterlife v4: only spatial NodeRef changed from relative to verified full world path")
    print("Static checks PASS. Live entry/rearm/cold reload remain unproven.")


if __name__ == "__main__":
    main()
