"""Validate modular profile definitions. Read-only: no runtime or deployment path.

The installed R1/R2.2 systems do not consume these JSON files. A successful
definition check is deliberately distinct from runtime readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "profiles"
DEFAULT = PROFILES / "active.json"
CATEGORIES = {
    "FrontalCortexCW", "SystemReplacementCW", "ArmsCW", "EyesCW",
    "MusculoskeletalSystemCW", "HandsCW", "NervousSystemCW",
    "CardiovascularSystemCW", "IntegumentarySystemCW", "LegsCW",
}
SMART = {
    "NewPerks.Intelligence_Inbetween_Right_2", "NewPerks.Intelligence_Master_Perk_4",
    "NewPerks.Intelligence_Right_Milestone_2", "NewPerks.Intelligence_Right_Milestone_3",
    "NewPerks.Intelligence_Right_Perk_2_1", "NewPerks.Intelligence_Right_Perk_2_2",
    "NewPerks.Intelligence_Right_Perk_3_1", "NewPerks.Intelligence_Right_Perk_3_2",
}
PRESERVE = {
    "other_attributes", "character_level", "skill_levels", "xp",
    "inventory_and_parts", "personal_link", "story_facts",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def nonfinite(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    return json.loads(path.read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique_object, parse_constant=nonfinite)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def keys(value, expected, label):
    require(type(value) is dict and set(value) == set(expected.split()),
            f"Unexpected/missing {label} fields")


def constant(value, expected, label):
    # Python's True == 1 must not validate a Boolean as a numeric schema value.
    require(type(value) is type(expected) and
            json.dumps(value, sort_keys=True) == json.dumps(expected, sort_keys=True),
            f"Unsupported {label}: {value!r}")


def strings(value, label):
    require(type(value) is list and all(type(x) is str and x for x in value),
            f"{label} must be an array of nonempty strings")
    require(len(value) == len(set(value)), f"Duplicate {label}")
    return set(value)


def local_file(base, reference, boundary):
    require(type(reference) is str and reference and not Path(reference).is_absolute()
            and ":" not in reference and "\\" not in reference,
            "References must be relative slash-separated file paths")
    target = (base / reference).resolve()
    require(target.is_relative_to(boundary.resolve()) and target.is_file(),
            "Missing/out-of-scope profile reference")
    return target


def load_bundle(path=DEFAULT):
    path = Path(path).resolve()
    require(path.is_relative_to(PROFILES.resolve()), "Profile must be inside profiles/")
    selector_inputs = {}
    if path == DEFAULT.resolve():
        selector = read_json(path)
        keys(selector, "schema_version profile", "active profile selector")
        constant(selector["schema_version"], 1, "selector schema")
        selector_inputs[str(path.relative_to(ROOT))] = sha256(path)
        path = local_file(PROFILES, selector["profile"], PROFILES)
        require(path != DEFAULT.resolve(), "Recursive active profile selector")
    manifest = read_json(path)
    keys(manifest, "schema_version profile_id revision name activation persistence migration modules catalogue", "profile")
    constant(manifest["schema_version"], 1, "profile schema")
    require(type(manifest["revision"]) is int and manifest["revision"] > 0, "Invalid revision")
    for field in ("profile_id", "name"):
        require(type(manifest[field]) is str and manifest[field].strip(), f"Invalid {field}")
    constant(manifest["activation"], "explicit_full_nerf_after_genuine_tower_completion", "activation")
    constant(manifest["persistence"], "save_local_id_revision_and_resolved_hash", "persistence")
    constant(manifest["migration"], "explicit_extension_no_replayed_refunds", "migration")
    keys(manifest["modules"], "vitals nerf_rules cyberware perks", "module references")
    inputs = {**selector_inputs, str(path.relative_to(ROOT)): sha256(path)}
    bundle = {"profile": manifest}
    for name, reference in manifest["modules"].items():
        module_path = local_file(path.parent, reference, PROFILES)
        bundle[name] = read_json(module_path)
        inputs[str(module_path.relative_to(ROOT))] = sha256(module_path)
    catalog_path = local_file(path.parent, manifest["catalogue"], PROFILES)
    bundle["catalogue"] = read_json(catalog_path)
    inputs[str(catalog_path.relative_to(ROOT))] = sha256(catalog_path)
    return bundle, inputs


def catalogue_records(catalogue):
    keys(catalogue, "schema_version catalogue_id game_version scope sources perks approved_other_bans limits", "catalogue")
    constant(catalogue["schema_version"], 1, "catalogue schema")
    constant(catalogue["catalogue_id"], "cp2077_231_modern_188", "catalogue ID")
    constant(catalogue["game_version"], "2.31", "catalogue game version")
    # Source pins are not permissions. Independently match the compact roster
    # against the original stock record/tree audit, not just its stated counts.
    sources = {}
    for source in catalogue["sources"]:
        keys(source, "path sha256", "catalogue source")
        path = local_file(ROOT, source["path"], ROOT / "research/restriction_profiles/body_stats_design")
        require(source["path"] not in sources, "Duplicate source")
        require(sha256(path) == source["sha256"], "Catalogue source hash mismatch")
        sources[source["path"]] = read_json(path)
    base = "research/restriction_profiles/body_stats_design/"
    require(set(sources) == {base + name for name in ("body_catalogue_records.json", "other_perk_policy.json", "other_perk_tree_records.json")}, "Unexpected source set")
    audit = sources[base + "body_catalogue_records.json"]
    by_hash = {r["hash"]: r for r in audit["records"] + audit["reference_closure"]}
    expected = {r["name"]: r for r in audit["records"] if r["type"] == "gamedataNewPerk_Record" and r["name"] != "NewPerks.Cool_Right_Perk_3_3"}
    rows = {}
    for row in catalogue["perks"]:
        keys(row, "record category name ranks requires unresolved_levels", "catalogue perk")
        record = row["record"]
        require(record in expected and record not in rows, "Unknown/duplicate catalogue perk")
        original = expected[record]["fields"]
        constant(row["category"], original["enumName"].split("_")[0], "perk category")
        constant(row["ranks"], len(original["levels"]), "perk rank count")
        require(row["requires"] == [by_hash[r["hash"]]["name"] for r in original["requiresPerks"]], "Changed prerequisite graph")
        strings(row["unresolved_levels"], "unresolved level IDs")
        rows[record] = row
    require(set(rows) == set(expected) and len(rows) == 188, "Incomplete stock catalogue")
    other = sources[base + "other_perk_policy.json"]
    originally_proposed = {p["record"] for p in other["perks"] if p["classification"] in {
        "proposed_core", "dependency_core", "proposed_full_nerf", "dependency_full_nerf", "decision_smart"}}
    require(strings(catalogue["approved_other_bans"], "approved other bans") == originally_proposed
            and len(originally_proposed) == 74, "Approved selection differs from the 69 plus five decision")
    for p in other["perks"]:
        require(rows[p["record"]]["unresolved_levels"] == p["unresolved_level_references"], "Changed unresolved level evidence")
    return rows


def validate_bundle(bundle):
    vitals, rules, chrome, perks = (bundle[n] for n in ("vitals", "nerf_rules", "cyberware", "perks"))
    for name in ("vitals", "nerf_rules", "cyberware", "perks"):
        constant(bundle[name]["schema_version"], 1, f"{name} schema")
        constant(bundle[name]["module"], name, f"{name} module")
    keys(vitals, "schema_version module health stamina modifier_ownership", "vitals")
    keys(vitals["health"], "mode value current_policy", "health")
    constant(vitals["health"]["mode"], "fixed_final_maximum", "health mode")
    value = vitals["health"]["value"]
    require(type(value) in (int, float) and math.isfinite(value) and 1 <= value <= 100000,
            "Health maximum must be a finite number from 1 to 100000")
    constant(vitals["health"]["current_policy"], "clamp_without_healing", "current health policy")
    constant(vitals["stamina"], {"mode": "unchanged"}, "stamina policy")
    constant(vitals["modifier_ownership"], "mod_owned_only", "modifier ownership")
    keys(rules, "schema_version module body relic smart_targeting refunds preserve incompatible_catalogue allowed_implant_in_removed_slot", "nerf rules")
    constant(rules["body"], {"target": 3, "refund_attribute_points": True, "block_increase": True}, "Body policy")
    constant(rules["relic"], {"hide_category": True, "block_direct_open": True, "refund_points": True}, "Relic policy")
    constant(rules["smart_targeting"], {"allowed": False, "tattoo_exception": "appearance_only", "scope": "active_cyberware_restriction", "weapons": "preserve_ownership"}, "smart-targeting policy")
    constant(rules["refunds"], {"purchased_ranks_only": True, "order": "dependents_first", "method": "native_guarded_sale", "repeat_policy": "journal_no_replay", "reversal": "none"}, "refund policy")
    require(strings(rules["preserve"], "preserved systems") == PRESERVE, "Preservation policy changed")
    constant(rules["incompatible_catalogue"], "refuse_before_mutation", "incompatible catalogue policy")
    constant(rules["allowed_implant_in_removed_slot"], "require_safe_relocation_or_refuse", "slot safety policy")
    keys(chrome, "schema_version module selection outside_list vendor_purchase function_denials_override_item_permission categories preserve_outside_selectable_categories", "cyberware")
    constant(chrome["selection"], "whitelist", "cyberware selection")
    constant(chrome["outside_list"], "block_installation_and_unequip_safely", "cyberware restriction")
    constant(chrome["vendor_purchase"], "inventory_only_for_restricted_items", "purchase policy")
    constant(chrome["function_denials_override_item_permission"], True, "function-denial priority")
    require(set(chrome["categories"]) == CATEGORIES, "All ten cyberware categories are required")
    allowed_chrome = set()
    for area, ids in chrome["categories"].items():
        group = strings(ids, f"{area} records")
        require(not (group & allowed_chrome), "Cyberware record belongs to multiple categories")
        require(all(x.startswith("Items.") and "*" not in x for x in group), "Cyberware IDs must be exact")
        allowed_chrome |= group
    # V1 only supports the reviewed model map. New models need their own audit.
    expected_chrome = {"Items.AdvancedKiroshiOpticsBare" + tier for tier in (
        "Common", "CommonPlus", "Uncommon", "UncommonPlus", "Rare", "RarePlus",
        "Epic", "EpicPlus", "Legendary", "LegendaryPlus", "LegendaryPlusPlus")}
    require(set(chrome["categories"]["EyesCW"]) <= expected_chrome, "Unaudited optic")
    expected_chrome |= {"Items.CasiusTattoo", "Items.AdvancedCasiusTattoo"}
    require(allowed_chrome <= expected_chrome, "Unaudited cyberware exception")
    require(all(not ids for area, ids in chrome["categories"].items() if area not in ("EyesCW", "HandsCW")), "Unaudited category exception")
    require(set(chrome["categories"]["HandsCW"]) <= {"Items.CasiusTattoo", "Items.AdvancedCasiusTattoo"}, "Unaudited Hands exception")
    require(strings(chrome["preserve_outside_selectable_categories"], "built-ins") == {"PersonalLink", "BaseFists", "Splinter"}, "Built-in preservation changed")
    keys(perks, "schema_version module selection catalogue_id outside_list unknown_or_changed_catalogue allowed_records", "perks")
    constant(perks["selection"], "whitelist", "perk selection")
    constant(perks["outside_list"], "refund_purchased_ranks_and_block", "perk restriction")
    constant(perks["unknown_or_changed_catalogue"], "refuse_before_mutation", "unknown perk policy")
    rows = catalogue_records(bundle["catalogue"])
    constant(perks["catalogue_id"], bundle["catalogue"]["catalogue_id"], "selected catalogue")
    allowed = strings(perks["allowed_records"], "allowed perks")
    require(allowed <= rows.keys(), "Whitelist contains an unknown/obsolete perk")
    require(not (SMART & allowed), "Smart-targeting ban conflicts with perk whitelist")
    require(not any(rows[p]["category"] in ("Body", "Espionage") for p in allowed), "Body/Relic ban conflicts with perk whitelist")
    for p in allowed:
        require(set(rows[p]["requires"]) <= allowed, f"Allowed perk has blocked prerequisite: {p}")
    blocked = rows.keys() - allowed
    by_category = {}
    for p, row in rows.items():
        entry = by_category.setdefault(row["category"], {"allowed": 0, "blocked": 0})
        entry["allowed" if p in allowed else "blocked"] += 1
    unresolved = {p: rows[p]["unresolved_levels"] for p in blocked if rows[p]["unresolved_levels"]}
    # Definition validation alone never certifies an executable adapter.
    return {
        "definition_valid": True, "runtime_ready": False, "game_writes": 0,
        "max_hp": value, "stamina": "unchanged", "cyberware_allowed_records": len(allowed_chrome),
        "perk_counts": {"catalogue": len(rows), "allowed": len(allowed), "blocked": len(blocked)},
        "perks_by_category": by_category, "blocked_perks": sorted(blocked),
        "unresolved_level_bindings": unresolved,
        "runtime_blockers": [
            "Definition validation alone does not verify the matching compiled runtime. Use the CLI runtime evidence check.",
        ],
    }


def verify_installed():
    current = ROOT / "research/restriction_profiles/profile_implant_r3_2/install_receipt.json"
    expected_status = "INSTALLED_PROFILE_IMPLANT_R3_2_LIVE_PENDING"
    if not current.exists():
        current = ROOT / "research/restriction_profiles/profile_hp_r3_1/install_receipt.json"
        expected_status = "INSTALLED_PROFILE_HP_R3_1_LIVE_PENDING"
    if not current.exists():
        current = ROOT / "research/restriction_profiles/profile_r3/install_receipt.json"
        expected_status = "INSTALLED_PROFILE_R3_LIVE_PENDING"
    if current.exists():
        receipt = read_json(current)
        require(receipt["status"] == expected_status, "Profile receipt status mismatch")
        tests = read_json(current.parent / "tests.json")
        require(sha256(current.parent / "tests.json") == receipt["tests_sha256"], "R3 tested build changed")
        game = Path(receipt["game_root"])
        checked = {}
        for source, digest in tests["checked_sources"].items():
            relative = source.replace("redscript/", "r6/scripts/")
            require(sha256(game / relative) == digest, "Installed R3 source mismatch: " + relative)
            checked[relative] = digest
        return checked
    receipt = read_json(ROOT / "research/restriction_profiles/relic_r2_2/install_receipt.json")
    game = Path(receipt["game_root"])
    checked = {}
    for file in receipt["files"]:
        path = game / file["relative"]
        require(sha256(path) == file["sha256"], "Installed R2.2 receipt mismatch")
        checked[file["relative"]] = sha256(path)
    for relative in ("PTFR_Restrictions_R1/CyberwarePolicy.reds", "PTFR_Restrictions_R1/EquipmentHooks.reds",
                     "PTFR_Restrictions_R1/RipperdocHooks.reds", "PTFR_Restrictions_R2/BodyCatalogue.reds"):
        path = game / "r6/scripts" / relative
        expected = "D9CF279E8FB15BA2319CB6CFBB1D2B1E71656B691986D202D9F89CEA95D3CBD1" if relative.endswith("CyberwarePolicy.reds") else sha256(ROOT / "redscript" / relative)
        require(sha256(path) == expected, "Installed restriction source mismatch")
        checked["r6/scripts/" + relative] = sha256(path)
    return checked


def runtime_evidence(bundle):
    """Offline build readiness only. Does not infer live behavior from compilation."""
    path = ROOT / "research/restriction_profiles/profile_implant_r3_2/tests.json"
    expected_status = "PASS_PROFILE_IMPLANT_R3_2_OFFLINE_LIVE_PENDING"
    if not path.exists():
        path = ROOT / "research/restriction_profiles/profile_hp_r3_1/tests.json"
        expected_status = "PASS_PROFILE_HP_R3_1_OFFLINE_LIVE_PENDING"
    if not path.exists():
        path = ROOT / "research/restriction_profiles/profile_r3/tests.json"
        expected_status = "PASS_PROFILE_R3_OFFLINE_LIVE_PENDING"
    if not path.exists(): return {"runtime_ready": False, "live_verified": False}
    tests = read_json(path)
    resolved = hashlib.sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()
    matching = tests.get("resolved_sha256") == resolved and tests.get("status") == expected_status
    matching = matching and tests.get("equipmentex_full_compile") and tests.get("source_contracts")
    matching = matching and all(sha256(ROOT / source) == digest for source, digest in tests["checked_sources"].items())
    return {"runtime_ready": bool(matching), "live_verified": False,
            "runtime_blockers": [] if matching else ["Runtime evidence does not match this definition/source build."],
            "runtime_evidence": str(path), "runtime_readiness_scope": "offline compiled adapter, not in-game verification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", type=Path, default=DEFAULT)
    parser.add_argument("--require-runtime", action="store_true", help="Exit 3 if adapters are not ready; never installs")
    parser.add_argument("--verify-installed", action="store_true", help="Read-only installed-source hash comparison")
    args = parser.parse_args()
    try:
        bundle, inputs = load_bundle(args.profile)
        result = validate_bundle(bundle)
        result.update(runtime_evidence(bundle))
        result["inputs"] = inputs
        result["resolved_sha256"] = hashlib.sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()
        if args.verify_installed:
            result["installed_sources_unchanged"] = verify_installed()
        print(json.dumps(result, indent=2))
        return 3 if args.require_runtime and not result["runtime_ready"] else 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"definition_valid": False, "runtime_ready": False, "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
