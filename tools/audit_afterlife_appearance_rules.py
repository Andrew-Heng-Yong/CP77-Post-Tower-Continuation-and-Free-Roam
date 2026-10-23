"""Bounded official-source evidence for Afterlife appearance selection; no game writes.

This is a source audit, not a runtime uniqueness allocator or a rendered census.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/afterlife_world"
OUT = BASE / "appearance_rules"
SOURCE = OUT / "sources/json"
CHAR = Path("base/quest/main_quests/prologue/q005/afterlife/characters")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def value(item):
    return item.get("$value") if isinstance(item, dict) else item


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def facial_signature(appearance):
    # Ignore clothes, hats, eyes and hair: different hairstyles alone must not
    # turn an identical face into an allegedly unique person. Retain enabled
    # main h0 head geometry and its skin/material appearance, not component IDs.
    rows = []
    for component in appearance["components"]:
        mesh = value(component.get("mesh", {}).get("DepotPath", {}))
        if not mesh or not component.get("isEnabled", 1):
            continue
        name = mesh.split("\\")[-1].lower()
        if "\\characters\\head\\" not in mesh or not name.startswith("h0_"):
            continue
        # Some actual main-head meshes have "cyberware" in their filename;
        # the additional overlay component, not the filename, is excluded.
        if "cyberware" in str(value(component.get("name"))).lower():
            continue
        rows.append((mesh, value(component.get("meshAppearance")), component.get("chunkMask")))
    assert rows, "Missing main-head evidence: do not count this variant as unique"
    return sorted(set(rows))


records = {r["record"]: r["fields"] for r in read(BASE / "population_rules_records.json")["records"]}
specs = [
    ("Character.q005_afterlife_crowd_male", "q005_afterlife_crowd_male.ent", "crowd_male", 17),
    ("Character.q005_afterlife_crowd_female", "q005_afterlife_crowd_female.ent", "crowd_female", 22),
    ("Character.q005_afterlife_crowd_cyberpunk_male", "q005_afterlife_crowd_cyberpunk_male.ent", "crowd_male_cp", 7),
    ("Character.q005_afterlife_crowd_cyberpunk_female", "q005_afterlife_crowd_cyberpunk_female.ent", "crowd_female_cp", 4),
]
manifest = read(BASE / "population_r2/manifest.json")
entries = manifest["entries"]
pool_rows = []
for record, filename, entry, expected_quantity in specs:
    fields = records[record]
    template_path = SOURCE / CHAR / (filename + ".json")
    template = read(template_path)["Data"]["RootChunk"]
    names = [value(a["name"]) for a in template["appearances"]]
    pool = fields["crowdAppearanceNames"]
    assert fields["staticCommunityAppearancesDistributionEnabled"] == "True"
    assert len(pool) == len(set(pool)) and set(pool) <= set(names)
    configured = next(e for e in entries if e["entry"] == entry)
    assert configured["quantity"] == expected_quantity
    pool_rows.append({"record": record, "entry": entry, "configured_allocations_not_census": expected_quantity,
                      "record_pool": pool, "template_default": value(template["defaultAppearance"]),
                      "template_names_count": len(names), "template_sha256": sha(template_path),
                      "distribution_enabled": True, "all_pool_names_resolve": True,
                      "face_capacity_audited": entry == "crowd_male_cp"})

app_path = SOURCE / "base/characters/appearances/gang/gang__cyberpunk_ma.app.json"
app = read(app_path)["Data"]["RootChunk"]
appearances = {value(a["Data"]["name"]): a["Data"] for a in app["appearances"]}
template_path = SOURCE / CHAR / "q005_afterlife_crowd_cyberpunk_male.ent.json"
template = read(template_path)["Data"]["RootChunk"]
variants = []
by_face = defaultdict(list)
for mapping in template["appearances"]:
    name = value(mapping["name"])
    definition_name = value(mapping["appearanceName"])
    definition = appearances[definition_name]
    signature = facial_signature(definition)
    key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
    by_face[key].append(name)
    variants.append({"template_name": name, "definition_name": definition_name,
                     "parent": value(definition["parentAppearance"]),
                     "face_signature": signature, "face_key": key})
assert len(variants) == 8
assert len({v["parent"] for v in variants}) == 6
assert len(by_face) == 7
collisions = [names for names in by_face.values() if len(names) > 1]
assert len(collisions) == 1 and set(collisions[0]) == {
    "gang__cyberpunk_ma_merc_solo__lvl1_08_1", "gang__cyberpunk_ma_merc_solo__lvl1_08_2"}

# Regression criterion: even different names must collide if their face key
# matches. Choosing one variant from each key can serve seven allocations.
assert len({v["template_name"] for v in variants}) > len({v["face_key"] for v in variants})
native_checks = {
    "constructor_gates_distribution_flag_and_nonempty_pool": ("native_distribution/function_00248df4.asm", ["[rax + 0x404]", "[rbx + 0x260]", "0x140fbb190"]),
    "picker_calls_pool_builder": ("native_distribution_core/function_00fbb190.asm", ["0x1401ba1d0"]),
    "builder_draws_random_pool_index_then_removes_selected_item": ("native_distribution_core/function_001ba1d0.asm", ["[rax + 0x260]", "0x1401ba9a4", "0x1401ba2f8", "add      ebx, -1"]),
    "generator_advances_state_and_bounds_result": ("native_random/function_001ba9a4.asm", ["0x5851f42d4c957f2d", "qword ptr [rcx], rax", "div      r10d"]),
    "selected_index_swap_removed_and_array_count_decremented": ("native_distribution_erase/function_001ba2f8.asm", ["qword ptr [r8], rax", "dec      eax", "dword ptr [rcx + 0xc], eax"]),
}
checked = []
for check, (relative, tokens) in native_checks.items():
    path = OUT / relative
    text = path.read_text()
    assert all(token in text for token in tokens), check
    checked.append({"check": check, "source": relative, "sha256": sha(path)})

result = {
    "status": "SOURCE_VERIFIED_RANDOMIZED_DISTRIBUTION_FACE_UNIQUENESS_NOT_IMPLEMENTED",
    "source_scope": "Official exported resources and installed executable, not resolved live TweakXL state",
    "randomization": "Native community distribution builder shuffles the record pool using a stateful pseudo-random bounded draw. Not evidence of independent per-NPC rolls or a global face reservation.",
    "native_checks": checked,
    "pools": pool_rows,
    "cyberpunk_male": {"variants": variants, "appearance_names": 8, "parent_families": 6,
                       "main_head_mesh_and_skin_signatures": 7, "same_face_alias_groups": collisions,
                       "app_json_sha256": sha(app_path), "raw_app_sha256": sha(OUT / "sources/raw/base/characters/appearances/gang/gang__cyberpunk_ma.app"),
                       "capacity_qualification": "Seven signatures can serve the seven configured CP-male slots in isolation; this does not establish whole-bar uniqueness or rendered distinctness."},
    "required_policy": {"randomize": True, "without_replacement_key": "validated face identity, not appearance name or record ID",
                        "shared_outfits_allowed": True, "preserve_actor_counts_and_records": True,
                        "fixed_scene_and_named_cast": "Preserve authored assignments; not members of probabilistic pools",
                        "exhaustion": "Report incompatibility; never silently duplicate a face, lower crowd count, or expand a role pool"},
    "remaining": ["Audit face capacity and aliases in the other three pools and overlaps with simultaneous fixed residents",
                  "Identify and implement a scoped pre-spawn selection/reservation hook preserving native owners",
                  "Verify reservations across despawn, streaming, reload and asynchronous spawns",
                  "Runtime rendered face comparison; eight distinct names is not a pass"],
    "game_writes": False,
}
protected = {}
for receipt in (BASE / "install_receipt.json", BASE / "population_r2/install_receipt.json", BASE / "idles_r3/install_receipt.json"):
    for file in read(receipt)["files"]:
        protected[file["relative"]] = file["sha256"]
game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
for relative, expected in protected.items():
    assert sha(game / relative) == expected, relative
result["installed_afterlife_files_unchanged"] = len(protected)
(OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "native_checks": len(checked), "pools": len(pool_rows),
                  "cp_male_names": 8, "cp_male_face_signatures": 7, "same_face_alias_groups": collisions}))
