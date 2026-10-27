"""Classify retired combat-event prefab owners; no game or save writes."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "diagnostics/world_npc_idle_20261026_02/families/census_03.json"
OUT = Path(__file__).resolve().parent / "audit_01.json"

def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest().upper()

assert not OUT.exists(), "Preserve previous evidence; create a successor"
data = json.loads(SOURCE.read_text(encoding="utf-8"))
assert len(data["rows"]) == 477 and len(data["sectors"]) == 374
sectors = {s["full_ref"]: s for s in data["sectors"]}
seen = set()
groups = []
excluded = []
for row in data["rows"]:
    reason = None
    ref = row.get("full_ref")
    sector = sectors.get(ref)
    if not ref or not sector or not sector.get("parsed"):
        reason = "unresolved_or_missing_exact_resource"
    elif row["asset_classification"] != "SUPPORT_SHAPED_SOURCE_NOT_ELIGIBILITY_ALLOWLIST":
        reason = row["asset_classification"].lower()
    elif not row.get("community_spawners") and not row.get("registry_evidence"):
        reason = "no_exact_community_identity"
    elif any(not p["inactive_on_start"] for p in sector["population_spawners"]):
        reason = "automatic_population_spawner"
    elif sector.get("outside_node_refs") or sector.get("outside_placements"):
        reason = "prefab_membership_outside_scope"
    elif sector.get("unclassified_nodes") or sector.get("suspicious_nested_types"):
        reason = "unclassified_payload"
    elif ref in seen:
        reason = "duplicate_prefab_owner_reference"
    if reason:
        excluded.append({"candidate_index": row["candidate_index"], "reason": reason,
                         "source": row["source"], "node_path": row["node_path"], "prefab": ref})
        continue
    seen.add(ref)
    community_refs = row.get("community_spawners") or [e["ref"] for e in row["registry_evidence"]]
    if any(not community.startswith(ref + "/") for community in community_refs):
        excluded.append({"candidate_index": row["candidate_index"],
                         "reason": "community_outside_prefab", "prefab": ref})
        continue
    groups.append({
        "candidate_index": row["candidate_index"], "source": row["source"],
        "node_path": row["node_path"], "prefab": ref,
        "community_refs": sorted(set(community_refs)), "asset_sha256": sector["winner"]["raw_sha256"],
        "resource": row["resource"], "node_types": row["node_types"],
        "inline_types": row["native_inline_node_types"],
        "binding": row["binding_classification"],
    })
assert len(groups) + len(excluded) == 477
assert len({g["prefab"] for g in groups}) == len(groups)
result = {
    "status": "STATIC_SUPPORT_CANDIDATES_NOT_PRODUCTION_ALLOWLIST",
    "input_sha256": digest(SOURCE), "rows": 477, "candidate_groups": len(groups),
    "excluded_rows": len(excluded), "exclusions": dict(Counter(x["reason"] for x in excluded)),
    "groups": groups, "excluded": excluded,
    "limits": [
        "Live NPC spawner and entry binding is not verified for these groups",
        "Exact prefab activation and absence of duplicate owners is not established",
        "This census covers only open-world combat-event owners, not all NPC families",
        "No game changes or deployment authorization are implied by source classification",
    ],
}
OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("status", "rows", "candidate_groups", "excluded_rows", "exclusions")}, indent=2))
