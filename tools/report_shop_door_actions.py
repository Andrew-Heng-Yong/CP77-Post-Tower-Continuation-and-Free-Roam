"""Report vanilla device actions on the clinic/Misty/Zetatech door aliases."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    ROOT / "research/q307_extracted/json/ep1/quest/main_quests/q307/phases/q307_06_viktor.questphase.json",
    ROOT / "research/q307_extracted/json/ep1/quest/main_quests/q307/scenes/q307_06_viktor.scene.json",
    ROOT / "research/phase2b_p2/extracted_more/json/base/quest/main_quests/prologue/q001/phases/q001_path_to_diner.questphase.json",
)
ALIASES = ("misty", "zetatech", "ripperdoc_gate")


def val(item):
    return item.get("$value") if isinstance(item, dict) else item


def walk(item):
    if isinstance(item, dict):
        if item.get("$type") == "questDeviceManager_NodeTypeParams":
            ref = val(item.get("objectRef", {})) or ""
            if any(alias in ref.lower() for alias in ALIASES):
                yield (ref, val(item.get("deviceAction", {})), val(item.get("deviceControllerClass", {})))
        for child in item.values():
            yield from walk(child)
    elif isinstance(item, list):
        for child in item:
            yield from walk(child)


def main():
    for path in PATHS:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for ref, action, controller in walk(data):
            print(f"{path.name}\t{ref}\t{action}\t{controller}")


if __name__ == "__main__":
    main()
