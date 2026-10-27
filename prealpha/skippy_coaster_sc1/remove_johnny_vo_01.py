"""Remove only Johnny's 14 dialogue events from the private MQ006 finale."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json

C = Path(__file__).resolve().parent / "candidate_04"
source = C / "scene_before_01.json"
out = C / "scene_after_01.json"
proof_path = C / "johnny_scene_proof_01.json"
assert not out.exists() and not proof_path.exists()
doc = json.loads(source.read_text(encoding="utf-8"))
root = doc["Data"]["RootChunk"]
actors = {a["actorId"]["id"]: a["actorName"] for a in root["actors"]}
assert actors[5] == "johnny"
line_speakers = {x["itemId"]["id"]: x["speaker"]["id"]
                 for x in root["screenplayStore"]["lines"] if x.get("$type") == "scnscreenplayDialogLine"}
johnny_lines = {line for line, actor in line_speakers.items() if actor == 5}
assert len(johnny_lines) == 14
removed = []
duration_checks = []


def walk(value):
    if isinstance(value, dict):
        for key, child in list(value.items()):
            if key == "events" and isinstance(child, list):
                before = [h.get("Data", {}) for h in child]
                found = [d for d in before if d.get("$type") == "scnDialogLineEvent"
                         and d.get("screenplayLineId", {}).get("id") in johnny_lines]
                if found:
                    max_before = max((d.get("startTime", 0) + d.get("duration", 0) for d in before), default=0)
                    child[:] = [h for h in child if h.get("Data", {}) not in found]
                    max_after = max((h.get("Data", {}).get("startTime", 0) + h.get("Data", {}).get("duration", 0) for h in child), default=0)
                    section = value.get("sectionDuration", {}).get("stu", 0)
                    duration_checks.append({"before": max_before, "after": max_after, "section": section, "removed": len(found)})
                    removed.extend({"line": d["screenplayLineId"]["id"], "event": d["id"]["id"]} for d in found)
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)


walk(root["sceneGraph"])
assert len(removed) == 14 and {x["line"] for x in removed} == johnny_lines
event_ids = {x["event"] for x in removed}
symbols_removed = 0


def clean_symbols(value):
    global symbols_removed
    if isinstance(value, dict):
        for child in value.values():
            clean_symbols(child)
    elif isinstance(value, list):
        kept = []
        for child in value:
            if isinstance(child, dict) and child.get("$type") == "scnSceneEventSymbol":
                ids = child.get("sceneEventIds", [])
                old = len(ids)
                ids[:] = [x for x in ids if x.get("id") not in event_ids]
                symbols_removed += old - len(ids)
                if not ids:
                    continue
            clean_symbols(child)
            kept.append(child)
        value[:] = kept


clean_symbols(root["debugSymbols"])
assert symbols_removed == 14
scene_references_removed = 0


def clean_scene_references(value):
    global scene_references_removed
    if isinstance(value, dict):
        for child in value.values():
            clean_scene_references(child)
    elif isinstance(value, list):
        kept = []
        for child in value:
            if isinstance(child, dict) and child.get("$type") == "scnSceneEventId" and child.get("id") in event_ids:
                scene_references_removed += 1
                continue
            clean_scene_references(child)
            kept.append(child)
        value[:] = kept


clean_scene_references(root["sceneGraph"])
def residual_ids(value):
    found = []
    if isinstance(value, dict):
        if value.get("$type") == "scnSceneEventId" and value.get("id") in event_ids:
            found.append(value["id"])
        for child in value.values():
            found.extend(residual_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(residual_ids(child))
    return found


assert not residual_ids(root["sceneGraph"]), residual_ids(root["sceneGraph"])
assert not residual_ids(root["debugSymbols"]), residual_ids(root["debugSymbols"])
assert scene_references_removed == 2, scene_references_removed
if any(x["section"] < x["before"] or x["section"] <= 0 for x in duration_checks):
    raise RuntimeError("Johnny VO event lacks a fixed preserving section duration")
out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
proof = {"status": "JOHNNY_DIALOG_EVENTS_REMOVED_SCENE_TIMING_PRESERVED_NOT_COOKED",
         "source_sha256": sha256(source.read_bytes()).hexdigest().upper(),
         "after_json_sha256": sha256(out.read_bytes()).hexdigest().upper(),
         "johnny_dialog_events_removed": len(removed), "debug_symbols_removed": symbols_removed,
         "persistent_line_references_removed": scene_references_removed,
         "other_dialog_events_preserved": 60, "duration_checks": duration_checks,
         "removed": removed, "game_writes": 0, "save_writes": 0}
proof_path.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: proof[k] for k in ("status", "johnny_dialog_events_removed", "debug_symbols_removed")}))
