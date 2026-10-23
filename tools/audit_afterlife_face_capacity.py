"""Audit head/skin collisions across the four official random appearance pools.

Source signatures and matching feasibility are not a live rendered guarantee.
Does not install, change probabilities, replace records, or modify the game.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/afterlife_world"
OUT = BASE / "appearance_rules"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def value(item):
    return item.get("$value") if isinstance(item, dict) else item


def face(definition):
    rows = []
    for c in definition.get("components", []):
        mesh = value(c.get("mesh", {}).get("DepotPath", {}))
        if not mesh or not c.get("isEnabled", 1):
            continue
        if "\\characters\\head\\" not in mesh or not mesh.split("\\")[-1].lower().startswith("h0_"):
            continue
        if "cyberware" in str(value(c.get("name"))).lower():
            continue
        rows.append((mesh, value(c.get("meshAppearance")), c.get("chunkMask")))
    return sorted(set(rows))


audit = read(OUT / "audit.json")
by_resource = defaultdict(list)
for pool in audit["pools"]:
    template = next((OUT / "sources/json").rglob(pool["record"].split(".")[-1] + ".ent.json"))
    for mapping in read(template)["Data"]["RootChunk"]["appearances"]:
        if value(mapping["name"]) in pool["record_pool"]:
            by_resource[value(mapping["appearanceResource"]["DepotPath"])].append({
                "record": pool["record"], "entry": pool["entry"],
                "template_name": value(mapping["name"]), "definition": value(mapping["appearanceName"])})

variants, sources = [], []
for depot, mappings in sorted(by_resource.items()):
    relative = Path(*depot.split("\\"))
    roots = [OUT / "sources", OUT / "other_sources"]
    source_root = next(r for r in roots if (r / "json" / (str(relative) + ".json")).is_file())
    json_path = source_root / "json" / (str(relative) + ".json")
    raw_path = source_root / "raw" / relative
    definitions = {value(a["Data"]["name"]): a["Data"] for a in read(json_path)["Data"]["RootChunk"]["appearances"]}
    parents = defaultdict(list)
    for name, definition in definitions.items():
        parents[value(definition.get("parentAppearance"))].append(name)
    for mapping in mappings:
        definition = definitions[mapping["definition"]]
        signature = face(definition)
        mapping.update({"resource": depot, "parent": value(definition.get("parentAppearance")),
                        "children": parents[mapping["definition"]], "head_skin_components": signature,
                        "face_key": hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest() if signature else None})
        variants.append(mapping)
    sources.append({"resource": depot, "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                    "json_sha256": hashlib.sha256(json_path.read_bytes()).hexdigest()})
    del definitions

pools = []
for pool in audit["pools"]:
    entries = [v for v in variants if v["record"] == pool["record"]]
    groups = defaultdict(list)
    for v in entries:
        if v["face_key"]:
            groups[v["face_key"]].append(v["template_name"])
    pools.append({"entry": pool["entry"], "configured_allocations_not_census": pool["configured_allocations_not_census"],
                  "appearance_names": len(entries), "head_skin_signatures": len(groups),
                  "no_head_evidence": [v["template_name"] for v in entries if not v["face_key"]],
                  "with_children": [v["template_name"] for v in entries if v["children"]],
                  "alias_groups": [g for g in groups.values() if len(g) > 1],
                  "isolated_capacity_sufficient": len(groups) >= pool["configured_allocations_not_census"]})

# Bipartite matching catches shared face keys across different record pools.
# This is a capacity check only; it is not a game allocator and does not assign
# identities, probabilities or persisted appearances to actual NPCs.
slots = []
for pool in pools:
    keys = sorted({v["face_key"] for v in variants if v["entry"] == pool["entry"] and v["face_key"]})
    for i in range(pool["configured_allocations_not_census"]):
        slots.append((f'{pool["entry"]}:{i}', keys))
held = {}


def match(slot, seen):
    for key in slots[slot][1]:
        if key in seen:
            continue
        seen.add(key)
        if key not in held or match(held[key], seen):
            held[key] = slot
            return True
    return False


matched = sum(match(i, set()) for i in range(len(slots)))
result = {"status": "SOURCE_CAPACITY_ONLY_NO_RUNTIME_FIX", "pools": pools, "sources": sources,
          "variants": variants, "combined_required": len(slots), "combined_maximum_matching": matched,
          "combined_source_capacity_sufficient": matched == len(slots),
          "limitations": ["Main-head and skin-component equality is a conservative audit key, not visual QA",
                          "Parent-child appearance resolution must be verified before treating parent names as fixed faces",
                          "Excludes fixed scene/named residents and live third-party overrides",
                          "Allocation, reservation, streaming, reload and renderer behavior not implemented or proven"]}
(OUT / "face_capacity.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in ("variants", "sources", "limitations")}, indent=2))
