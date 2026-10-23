"""List nearby vanilla door nodes from already extracted clinic sectors (read only)."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "research/phase2b_p2/extracted_more/json/base/worlds/03_night_city/_compiled/default"
CENTER = (-1548.02454, 1221.40918, 12.1014214)
RADIUS_XY = 55
RADIUS_Z = 30


def val(item):
    return item.get("$value") if isinstance(item, dict) else item


def main():
    matches = []
    for path in (FOLDER / "exterior_-25_19_0_0.streamingsector.json",
                 FOLDER / "exterior_-13_9_0_1.streamingsector.json"):
        root = json.loads(path.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
        for data_index, data in enumerate(root["nodeData"]["Data"]):
            p = data.get("Position", {})
            xyz = tuple(p.get(k) for k in ("X", "Y", "Z"))
            if any(not isinstance(x, (int, float)) for x in xyz):
                continue
            xy = math.dist(xyz[:2], CENTER[:2])
            if xy > RADIUS_XY or abs(xyz[2] - CENTER[2]) > RADIUS_Z:
                continue
            index = data.get("NodeIndex")
            if not isinstance(index, int) or index >= len(root["nodes"]):
                continue
            node = root["nodes"][index].get("Data", {})
            template = val(node.get("entityTemplate", {}).get("DepotPath", {})) or ""
            ref = val(data.get("QuestPrefabRefHash", {})) or ""
            if "door" not in str(template).lower() and "door" not in str(ref).lower():
                continue
            chunks = (node.get("instanceData", {}).get("Data", {}).get("buffer", {})
                      .get("Data", {}).get("Chunks", []))
            ps = next((c.get("persistentState", {}).get("Data", {}) for c in chunks
                       if c.get("persistentState", {}).get("Data", {}).get("$type") == "DoorControllerPS"), {})
            props = ps.get("doorProperties", {})
            matches.append({"sector": path.name, "node_data": data_index,
                            "node_index": index, "distance_xy": round(xy, 2),
                            "position": xyz, "ref": ref, "template": template,
                            "controller": ps.get("$type", "UNKNOWN"),
                            "door_type": props.get("doorType", "UNKNOWN"),
                            "initial_state": props.get("initialDoorState", "UNKNOWN"),
                            "default_locked": ps.get("isLocked", "UNKNOWN"),
                            "default_interactive": ps.get("isInteractive", "UNKNOWN")})
    print(json.dumps(sorted(matches, key=lambda r: r["distance_xy"]), indent=2))


if __name__ == "__main__":
    main()
