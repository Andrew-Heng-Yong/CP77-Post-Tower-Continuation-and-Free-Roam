"""Map each missing private English lipsync entry to a current native donor."""
import csv
import hashlib
import json
from pathlib import Path

W = Path(__file__).resolve().parents[2]
O = Path(__file__).resolve().parent
source = W / "research/sidejobs_s29/stefan_lipmap_01/lang_en_voice/json/base/localization/en-us.lipmap.json"
raw_source = W / "research/sidejobs_s29/stefan_lipmap_01/lang_en_voice/raw/base/localization/en-us.lipmap"
affected = W / "diagnostics/stefan_lipsync_20261025_01/affected_scenes_01.csv"
analysis = W / "diagnostics/stefan_lipsync_20261025_01/installed_audit_01/analysis_02.json"


def hpath(text):
    h = 14695981039346656037
    for b in text.lower().encode("utf-8"):
        h = ((h ^ b) * 1099511628211) & ((1 << 64) - 1)
    return h


root = json.loads(source.read_text(encoding="utf-8"))["Data"]["RootChunk"]
scene_paths = [int(x["$value"]) if isinstance(x, dict) else int(x) for x in root["scenePaths"]]
assert len(scene_paths) == len(root["sceneEntries"]) == 3527
lookup = {x: i for i, x in enumerate(scene_paths)}
assert len(lookup) == len(scene_paths)
by_depot = {x["depot"]: x for x in json.loads(analysis.read_text(encoding="utf-8"))["scenes"] if x["winning"]}
rows = []
for row in csv.DictReader(affected.open(encoding="utf-8", newline="")):
    private = row["scene"]
    donor = row["native_scene_sources"]
    native_hash, private_hash = hpath(donor), hpath(private)
    assert native_hash in lookup and private_hash not in lookup, private
    entry = root["sceneEntries"][lookup[native_hash]]
    voices = {str(x) for x in entry["actorVoiceTags"]}
    target = by_depot[private]
    needed = {a["voice_tag"] for a in target["actors"] if a["missing_registration"]}
    assert needed and needed.issubset(voices), (private, needed - voices)
    assert len(entry["actorVoiceTags"]) == len(entry["animSets"])
    rows.append({
        "archive": row["archive"],
        "private": private,
        "private_hash": private_hash,
        "donor": donor,
        "donor_hash": native_hash,
        "native_entry_index": lookup[native_hash],
        "native_voice_tags": sorted(voices),
        "required_voice_tags": sorted(needed),
        "source_scene_sha256": target["sha256"],
    })
assert len(rows) == 44 and len({r["private_hash"] for r in rows}) == 44
result = {
    "status": "44_PRIVATE_SCENE_NATIVE_ENGLISH_LIPMAP_DONORS_PINNED",
    "rows": rows,
    "native_map_raw": str(raw_source.relative_to(W)).replace("\\", "/"),
    "native_map_raw_sha256": hashlib.sha256(raw_source.read_bytes()).hexdigest().upper(),
    "native_map_json_sha256": hashlib.sha256(source.read_bytes()).hexdigest().upper(),
    "affected_csv_sha256": hashlib.sha256(affected.read_bytes()).hexdigest().upper(),
    "analysis_sha256": hashlib.sha256(analysis.read_bytes()).hexdigest().upper(),
    "game_writes": 0,
    "save_writes": 0,
}
p = O / "lipmap_plan_01.json"
assert not p.exists()
p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"registrations": len(rows), "covered_voices": sum(len(r["required_voice_tags"]) for r in rows)}))
