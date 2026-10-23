"""Exact decoded-source delta for one official-sector alias candidate."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/misty_viktor_world"
manifest = json.loads((AUDIT / "original_lamp_alias_s1_manifest.json").read_text())
original = json.loads((AUDIT / "r7_lighting_sources/base/worlds/03_night_city/_compiled/default/exterior_-25_18_0_0.streamingsector.json").read_text())
patched = json.loads(Path(manifest["exported_json"]).read_text())
before = original["Data"]["RootChunk"]
after = patched["Data"]["RootChunk"]
assert before["nodeData"]["Data"][3901]["QuestPrefabRefHash"]["$value"] in ("0", "")
assert after["nodeData"]["Data"][3901]["QuestPrefabRefHash"]["$value"] == manifest["alias"]
assert len(after["nodeRefs"]) == len(before["nodeRefs"]) + 1
assert after["nodeRefs"][-1]["$value"] == manifest["alias"]
after["nodeData"]["Data"][3901]["QuestPrefabRefHash"] = before["nodeData"]["Data"][3901]["QuestPrefabRefHash"]
after["nodeRefs"].pop()
patched["Header"]["ExportedDateTime"] = original["Header"]["ExportedDateTime"]


def compare(x, y, path="$", differences=None):
    if differences is None:
        differences = []
    if type(x) is not type(y):
        differences.append((path, "type"))
    elif isinstance(x, dict):
        if x.keys() != y.keys():
            differences.append((path, "keys"))
        else:
            for k in x:
                compare(x[k], y[k], f"{path}.{k}", differences)
                if len(differences) >= 20:
                    break
    elif isinstance(x, list):
        if len(x) != len(y):
            differences.append((path, "length"))
        else:
            for i, (a, b) in enumerate(zip(x, y)):
                compare(a, b, f"{path}[{i}]", differences)
                if len(differences) >= 20:
                    break
    elif x != y:
        differences.append((path, (x, y)))
    return differences


differences = compare(original, patched)
if differences:
    print("FAIL: unexpected decoded sector deltas:", differences[:20])
    raise SystemExit(1)
print("PASS: one placement alias plus one nodeRefs append; all other decoded fields identical")
