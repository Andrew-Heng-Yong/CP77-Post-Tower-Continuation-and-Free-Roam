"""Require the authored quest prefab to match the decoded world prefab."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
old = HERE / "audit_01.json"
validation = HERE / "native_validation_01.json"
lookup = HERE / "mismatch_resolution_01.json"
decoded = HERE / "decoded_mismatch_02.json"
out = HERE / "audit_02.json"
assert not out.exists(), "Preserve audit evidence"

def read(p: Path): return json.loads(p.read_text(encoding="utf-8-sig"))
def digest(p: Path): return sha256(p.read_bytes()).hexdigest().upper()

a, v, l, d = map(read, (old, validation, lookup, decoded))
assert a["candidate_groups"] == 237 and v["owner_count"] == 237
assert v["failed_count"] == l["count"] == l["found"] == d["count"] == 31
bad = {row["id"] for row in v["failures"]}
assert len(bad) == 31
good = [g for g in a["groups"] if g["candidate_index"] not in bad]
assert len(good) == 206 and any(g["candidate_index"] == 183 for g in good)
by_id = {r["id"]: r for r in l["rows"]}
dec = {r["id"]: r for r in d["rows"]}
mismatch = []
for row in v["failures"]:
    ident = row["id"]
    original = next(g for g in a["groups"] if g["candidate_index"] == ident)
    native = by_id[ident]["native_ref"]
    actual = read(Path(dec[ident]["json"]))
    assert actual["full_ref"] == native
    assert not any(c.startswith(native + "/") for c in original["community_refs"])
    outside_refs = sum(not ref.startswith(native + "/") for ref in actual["node_refs"])
    outside_placements = sum(p["quest_ref"] != "0" and not p["quest_ref"].startswith(native + "/") for p in actual["placements"])
    mismatch.append({"id": ident, "authored_prefab": native,
                     "registry_prefab": original["prefab"],
                     "community_refs": original["community_refs"],
                     "authored_resource": by_id[ident]["native_resource"],
                     "outside_node_refs": outside_refs,
                     "outside_placements": outside_placements,
                     "reason": "community owner and exact authored prefab paths differ"})
result = {
    "status": "EXACT_AUTHORED_SUPPORT_COHORT_NOT_DEPLOYABLE",
    "input_pins": [{"path": str(p), "sha256": digest(p)} for p in (old, validation, lookup, decoded)],
    "census_rows": 477, "exact_authored_candidates": len(good),
    "mismatched_authored_paths": len(mismatch),
    "other_excluded_rows": len(a["excluded"]),
    "groups": good, "mismatch": mismatch,
    "limitations": [
        "Only one Pacifica group has a live actor and patrol result",
        "205 other groups still need actor matching and duplicate-owner safeguards",
        "Other combat-event assets, courier families, and El Coyote actors remain outside this candidate cohort",
        "No production resource, script, package, or game installation has been changed",
    ],
}
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("status", "census_rows", "exact_authored_candidates", "mismatched_authored_paths", "other_excluded_rows")}, indent=2))
