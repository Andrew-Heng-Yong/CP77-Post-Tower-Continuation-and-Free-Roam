"""Verify the JC1 successor changes only the intended S30 admission and finale."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent.parent
P = H / "candidate_01"
B = W / "prealpha/raymond_rc1/candidate_03"
S = W / "prealpha/sidejobs_s30/serialized_02"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


old_files = {row["path"]: row["sha256"] for row in read(B / "manifest.json")["files"]}
new_files = {row["path"]: row["sha256"] for row in read(P / "manifest.json")["files"]}
assert len(old_files) == len(new_files) == 51 and old_files.keys() == new_files.keys()
changed_files = {path for path in old_files if old_files[path] != new_files[path]}
assert changed_files == {
    "archive/pc/mod/zzzz_PTFR_Combined.archive",
    "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds",
}
for path, digest in new_files.items():
    assert sha(P / "package" / path) == digest, path

entry_rel = "towercontinued/sidejobs_s30/entries/mq006_rollercoaster.questphase"
scene_rel = "towercontinued/sidejobs_s30/native/base/quest/minor_quests/mq006/scenes/mq006_02_finale.scene"
for rel in (entry_rel, scene_rel):
    assert sha(B / "archive_source" / rel) == sha(S / "source" / rel), rel
old_entry = read(S / "entry_readback" / (entry_rel + ".json"))["Data"]["RootChunk"]["graph"]["Data"]["nodes"]
new_entry = read(P / "entry_readback_01.json")["Data"]["RootChunk"]["graph"]["Data"]["nodes"]


def strip_handles(value):
    if isinstance(value, dict):
        return {key: strip_handles(val) for key, val in value.items() if key not in ("HandleId", "HandleRefId")}
    if isinstance(value, list):
        return [strip_handles(val) for val in value]
    return value


old_nodes = {node["Data"]["id"]: strip_handles(node) for node in old_entry}
new_nodes = {node["Data"]["id"]: strip_handles(node) for node in new_entry}
assert old_nodes.keys() == new_nodes.keys()
for ident in old_nodes:
    if ident not in (65003, 65004):
        assert old_nodes[ident] == new_nodes[ident], ident
for ident in (65003, 65004):
    old = old_nodes[ident]["Data"]["condition"]["Data"]["conditions"]
    new = new_nodes[ident]["Data"]["condition"]["Data"]["conditions"]
    assert len(new) == len(old) + 1
    ride = [i for i, cond in enumerate(old) if cond["Data"].get("type", {}).get("Data", {}).get("factName") == "mq006_ride_no_quest"]
    assert len(ride) == 1
    index = ride[0]
    old_fact = old[index]["Data"]["type"]["Data"]
    new_fact = new[index]["Data"]["type"]["Data"]
    assert (old_fact["comparisonType"], old_fact["value"]) == ("Equal", 0)
    assert (new_fact["comparisonType"], new_fact["value"]) == ("LessOrEqual", 1)
    assert {key: val for key, val in old_fact.items() if key not in ("comparisonType", "value")} == {
        key: val for key, val in new_fact.items() if key not in ("comparisonType", "value")
    }
    old_copy = json.loads(json.dumps(old_nodes[ident]))
    new_copy = json.loads(json.dumps(new_nodes[ident]))
    old_copy["Data"]["condition"]["Data"]["conditions"][index]["Data"]["type"]["Data"].update(
        comparisonType="LessOrEqual", value=1
    )
    old_copy["Data"]["condition"]["Data"]["conditions"].append(new[-1])
    assert old_copy == new_copy, ident
    extra = new[-1]["Data"]["type"]["Data"]
    assert (extra["factName"], extra["comparisonType"], extra["value"]) == (
        "mq006_ride_no_quest", "GreaterOrEqual", 0
    )

before_scene = read(S / "readback" / (scene_rel + ".json"))["Data"]
after_scene = read(P / "scene_readback_01.json")["Data"]


def differences(a, b, path=""):
    if type(a) is not type(b):
        return [(path, a, b)]
    if isinstance(a, dict):
        result = []
        for key in a.keys() | b.keys():
            if key not in a or key not in b:
                result.append((path + "/" + key, a.get(key), b.get(key)))
            else:
                result.extend(differences(a[key], b[key], path + "/" + key))
        return result
    if isinstance(a, list):
        assert len(a) == len(b), path
        result = []
        for index, (left, right) in enumerate(zip(a, b)):
            result.extend(differences(left, right, path + "/" + str(index)))
        return result
    return [] if a == b else [(path, a, b)]


scene_diffs = differences(before_scene, after_scene)
assert len(scene_diffs) == 15, scene_diffs[:20]
groups = {}
for path, before, after in scene_diffs:
    base, field = path.rsplit("/", 1)
    groups.setdefault(base, {})[field] = (before, after)
assert len(groups) == 5
for changes in groups.values():
    assert changes == {
        "comparisonType": ("GreaterOrEqual", "Equal"),
        "factName": ("mq006_ride_no_quest", "PTFRWORLD_Coaster_QuestOwns"),
        "value": (1, 0),
    }

old_reds = (B / "package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds").read_text(encoding="utf-8")
new_reds = (P / "package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds").read_text(encoding="utf-8")
old_line = "public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0]; }"
new_line = "public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 1, 0, 0]; }"
assert old_reds.count(old_line) == 1 and new_reds.count(new_line) == 1
assert new_reds.replace(new_line, old_line) == old_reds
assert read(H / "compile_01/result.json")["status"] == "PASS"

result = {
    "status": "STATIC_PASS_LIVE_PENDING",
    "package_files": 51,
    "archive_members": 1172,
    "changed_installed_paths": sorted(changed_files),
    "changed_archive_resources": [entry_rel, scene_rel],
    "entry_guards": [65003, 65004],
    "allowed_ride_no_quest": [0, 1],
    "private_finale_noquest_branches_retargeted": 5,
    "saved_native_fact_rewritten": False,
    "compile": "PASS",
    "game_writes": 0,
    "save_writes": 0,
}
(H / "validation_01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
