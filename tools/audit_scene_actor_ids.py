"""Validate dense scene actor IDs and typed actor/performer references.

Actor/player identities are one shared dense table in every locally inspected
vanilla scene. Performer low byte 1 identifies an actor; its upper bytes carry
the actor ID. This checker does not interpret node/event/resource IDs as actors.
"""
import argparse
import copy
import json
from pathlib import Path

UINT_MAX = (1 << 32) - 1


def walk(value, path="$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")


def audit_scene_actor_ids(scene):
    """Accept a scene RootChunk or full WolvenKit export; raise on defects."""
    if "Data" in scene and "RootChunk" in scene["Data"]:
        scene = scene["Data"]["RootChunk"]
    if scene.get("$type") != "scnSceneResource":
        raise ValueError("Expected scnSceneResource")
    cast = scene.get("actors", []) + scene.get("playerActors", [])
    ids = [int(actor["actorId"]["id"]) for actor in cast]
    if ids != list(range(len(cast))):
        raise ValueError(f"Actor/player table must be ordered dense 0..{len(cast)-1}; got {ids}")
    known = set(ids)
    actor_refs = performer_refs = 0
    for path, value in walk(scene):
        if value.get("$type") == "scnActorId":
            ident = int(value["id"])
            if ident != UINT_MAX and ident not in known:
                raise ValueError(f"Unknown actor {ident} at {path}")
            actor_refs += 1
        elif value.get("$type") == "scnPerformerId":
            ident = int(value["id"])
            if ident & 0xFF == 1:
                actor_id = ident >> 8
                if actor_id not in known:
                    raise ValueError(f"Unknown actor performer {ident} (actor {actor_id}) at {path}")
                performer_refs += 1
    return {"actor_ids": ids, "typed_actor_refs": actor_refs,
            "typed_actor_performer_refs": performer_refs}


def self_test():
    scene = {"$type": "scnSceneResource",
             "actors": [{"actorId": {"$type": "scnActorId", "id": i}} for i in (0, 1)],
             "playerActors": [{"actorId": {"$type": "scnActorId", "id": 2}}],
             "events": [{"performer": {"$type": "scnPerformerId", "id": 513},
                         "nodeId": {"$type": "scnNodeId", "id": 769}}]}
    audit_scene_actor_ids(scene)
    sparse = copy.deepcopy(scene)
    sparse["playerActors"][0]["actorId"]["id"] = 3
    sparse["events"][0]["performer"]["id"] = 769
    orphan = copy.deepcopy(scene)
    orphan["events"][0]["performer"]["id"] = 769
    reordered = copy.deepcopy(scene)
    reordered["actors"].reverse()
    for name, mutant in (("sparse cast", sparse), ("orphan performer", orphan),
                         ("misordered cast", reordered)):
        try:
            audit_scene_actor_ids(mutant)
        except ValueError:
            continue
        raise AssertionError(f"Validator accepted {name}")
    print("Actor identity self-test: dense cast accepted; sparse cast/orphan performer/misordered cast rejected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.paths and not args.self_test:
        parser.error("Provide scene JSON exports or --self-test")
    if args.self_test:
        self_test()
    for path in args.paths:
        result = audit_scene_actor_ids(json.loads(path.read_text(encoding="utf-8-sig")))
        print(f"{path}: {json.dumps(result)}")


if __name__ == "__main__":
    main()
