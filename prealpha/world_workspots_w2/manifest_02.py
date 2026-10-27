"""Identity manifest limited to exact native owner/prefab correspondence."""
from hashlib import sha256
from pathlib import Path
import json

H = Path(__file__).resolve().parent
old, audit, native = (H / x for x in ("manifest_01.json", "audit_02.json", "native_validation_01.json"))
out = H / "manifest_02.json"
assert not out.exists(), "Preserve old manifest"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: sha256(p.read_bytes()).hexdigest().upper()
m, a, n = map(read, (old, audit, native))
assert (m["owner_count"], a["exact_authored_candidates"], n["failed_count"]) == (237, 206, 31)
good = {g["candidate_index"] for g in a["groups"]}
native_ok = {g["id"] for g in n["results"] if g["exact"]}
assert good == native_ok
groups = [g for g in m["groups"] if g["id"] in good]
assert len(groups) == 206
hashes = [h for g in groups for h in g["spawner_hashes"]]
assert len(hashes) == len(set(hashes)) == 212
ww1 = next(g for g in groups if g["id"] == 183)
assert ww1["prefix"] == "PTFRWW1_CVI116_" and ww1["spawner_hashes"] == ["13399962301655001666"]
result = {"status": "EXACT_NATIVE_IDENTITY_CANDIDATES_NOT_DEPLOYABLE",
          "input_pins": [{"path": str(p), "sha256": sha(p)} for p in (old, audit, native)],
          "owner_count": 206, "spawner_count": 212, "live_proven_owner_id": 183,
          "groups": groups,
          "limits": ["205 groups have no live patrol proof",
                     "Unresolved and content-bearing families are excluded",
                     "No production package or game file was changed"]}
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("status", "owner_count", "spawner_count", "live_proven_owner_id")}, indent=2))
