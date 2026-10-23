"""Read-only bounded questShowWorldNode precedent index from extracted vanilla files."""
import json
import hashlib
import bisect
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
roots = [ROOT / "research"]
result = subprocess.run(["rg", "-l", "--no-messages", "-g", "*.json", "questShowWorldNode_NodeType", *map(str, roots)], capture_output=True, text=True)
rows = []


def visit(item, path, ancestry=()):
    if isinstance(item, dict):
        current = ancestry
        if "id" in item and "$type" in item:
            current += ((item["$type"], item["id"]),)
        if item.get("$type") == "questShowWorldNode_NodeType":
            rows.append({"resource": str(path.relative_to(ROOT)), "ancestry": current, "action": item})
        for child in item.values():
            if isinstance(child, (dict, list)):
                visit(child, path, current)
    elif isinstance(item, list):
        for child in item:
            visit(child, path, ancestry)


for filename in result.stdout.splitlines():
    path = Path(filename)
    if path.name.endswith((".scene.json", ".questphase.json")):
        visit(json.loads(path.read_text(encoding="utf-8-sig")), path)
output = ROOT / "research/misty_viktor_world/r7_showworld_precedents.json"
output.write_text(json.dumps({"status": "READ_ONLY_SOURCE_INDEX", "rows": rows}, indent=2), encoding="utf-8")
print(json.dumps({"rows": len(rows), "light_named": [r for r in rows if any(w in str(r["action"]).lower() for w in ("light", "lamp", "neon"))]}, indent=2))

# Resolve the sole light-named positive against the actual compiled world node.
sector_path = ROOT / "research/misty_viktor_world/r7_showworld_sources/json/base/worlds/03_night_city/_compiled/default/exterior_-23_15_0_0.streamingsector.json"
if sector_path.exists():
    sector = json.loads(sector_path.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
    alias = "#mq016_02_afterlife_netrunner_light"
    actions = [r for r in rows if r["action"]["objectRef"].get("$value") == alias]
    assert len(actions) == 2
    assert {(r["ancestry"][-1][1], r["action"]["show"]) for r in actions} == {(790, 0), (792, 1)}
    targets = []
    for index, datum in enumerate(sector["nodeData"]["Data"]):
        if str(datum["QuestPrefabRefHash"].get("$value", "")).endswith("/" + alias):
            node = sector["nodes"][datum["NodeIndex"]]["Data"]
            assert node["$type"] == "worldStaticLightNode"
            targets.append({"data_index": index, "node_index": datum["NodeIndex"], "node": node, "placement": datum})
    assert len(targets) == 1 and targets[0]["data_index"] == 2359 and targets[0]["node_index"] == 1862
    raw_path = Path(str(sector_path).replace("\\json\\", "\\raw\\").removesuffix(".json"))
    proof = {"status": "POSITIVE_VANILLA_STATIC_LIGHT_SHOWWORLD_PRECEDENT", "indexed_actions": len(rows), "actions": actions, "target": targets[0], "source_json": str(sector_path.relative_to(ROOT)), "source_json_sha256": hashlib.sha256(sector_path.read_bytes()).hexdigest(), "source_raw": str(raw_path.relative_to(ROOT)), "source_raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(), "parse_notes": "Export accepted InvalidDefaultValue warnings and the unrelated WorldWidgetComponent.widgetResource rRef/raRef mismatch; target worldStaticLightNode fields were not modified. Source was not repacked.", "semantics": "The same single static-light NodeRef receives show0 then show1 in the vanilla scene, with componentName=None/isPlayer0. This is a direct static-light use, not entity/group inference.", "limits": "Does not establish a NodeRef for the alias-less Misty fixture or prove new runtime rendering/rearm."}
    target_range = bisect.bisect_right(sector["variantIndices"], 2359) - 1
    proof["registration_metadata"] = {
        "placement_id": targets[0]["placement"]["Id"],
        "quest_prefab_ref": targets[0]["placement"]["QuestPrefabRefHash"],
        "uk_hash1": targets[0]["placement"]["UkHash1"],
        "cooked_prefab_data": targets[0]["placement"]["CookedPrefabData"],
        "node_definition_has_NodeRef_field": any("noderef" in key.lower() for key in targets[0]["node"]),
        "sector_nodeRefs_indices": [i for i, ref in enumerate(sector["nodeRefs"]) if str(ref.get("$value", "")).endswith("/" + alias)],
        "sector_level": sector["level"],
        "sector_category": sector["category"],
        "sector_persistentNodeIndex": sector["persistentNodeIndex"],
        "persistentNodes_count": len(sector.get("persistentNodes") or []),
        "variant_range_index": target_range,
        "variant_range_bounds": [sector["variantIndices"][target_range], sector["variantIndices"][target_range+1] if target_range+1 < len(sector["variantIndices"]) else len(sector["nodeData"]["Data"])],
    }
    (ROOT / "research/misty_viktor_world/r7_showworld_static_light_proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
