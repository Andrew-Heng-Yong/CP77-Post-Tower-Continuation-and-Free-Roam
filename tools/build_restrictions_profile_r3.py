"""Compile validated modular JSON into a deterministic REDscript definition."""
import argparse
import hashlib
import json
from pathlib import Path
import validate_restriction_profile as definition

ROOT = definition.ROOT
OUT = ROOT / "redscript/PTFR_Restrictions_R3"


def generate(profile=definition.DEFAULT):
    bundle, inputs = definition.load_bundle(profile)
    checked = definition.validate_bundle(bundle)
    strict, strict_inputs = definition.load_bundle(definition.PROFILES / "tower_strict/profile.json")
    strict_checked = definition.validate_bundle(strict)
    strict_hash = hashlib.sha256(json.dumps(strict, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()
    assert strict_hash == "117BF6C7A6E0FE29A4E64C7A0583DB9E3A9914D5FE8C42F82637D5D6DB8DE1E1", "Reviewed strict predecessor changed"
    inputs.update(strict_inputs)
    digest = hashlib.sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()
    manifest = bundle["profile"]
    catalogue = bundle["catalogue"]["perks"]
    audit = definition.read_json(ROOT / "research/restriction_profiles/body_stats_design/body_catalogue_records.json")
    records = {r["hash"]: r for r in audit["reference_closure"]}
    records.update({r["hash"]: r for r in audit["records"]})
    named = {r["name"]: r for r in audit["records"]}
    enum = lambda record: "gamedataNewPerkType." + record.removeprefix("NewPerks.")
    lines = ["module PTFR.RestrictionsR3", "", "// Generated from profiles/; do not hand-edit. Build-time loader, not hot reload.",
             "public abstract class ProfileDefinition {",
             f'  public static func ID() -> String {{ return "{manifest["profile_id"]}"; }}',
             f'  public static func Revision() -> Int32 {{ return {manifest["revision"]}; }}',
             f'  public static func Fingerprint() -> String {{ return "{digest}"; }}',
             f'  public static func Health() -> Float {{ return {float(bundle["vitals"]["health"]["value"]):.6f}; }}',
             "  public static func CyberwareAllowed(id: TweakDBID) -> Bool {"]
    ids = sorted(x for group in bundle["cyberware"]["categories"].values() for x in group)
    lines.append("    return " + " ||\n      ".join(f'id == t"{x}"' for x in ids) + ";\n  }")
    for method, selected in (
        ("AllowedPerks", bundle["perks"]["allowed_records"]),
        ("OtherBlocked", [x for x in checked["blocked_perks"] if not x.startswith(("NewPerks.Body_", "NewPerks.Espionage_"))]),
        ("PreviousStrictBlocked", [x for x in strict_checked["blocked_perks"] if not x.startswith(("NewPerks.Body_", "NewPerks.Espionage_"))]),
    ):
        lines += [f"  public static func {method}() -> array<gamedataNewPerkType> {{", "    let result: array<gamedataNewPerkType>;"]
        lines += [f"    ArrayPush(result, {enum(x)});" for x in selected]
        lines += ["    return result;", "  }"]
    lines += ["}", "", "public abstract class ProfileCatalogue {",
              "  public static func Valid() -> Bool {",
              "    if EnumInt(gamedataNewPerkType.Count) != 189 { return false; }"]
    expected_trees = {"Body": "Body", "Espionage": "Espionage", "Cool": "Cool", "Tech": "TechnicalAbility", "Intelligence": "Intelligence", "Reflexes": "Reflexes"}
    for category, tree in expected_trees.items():
        count = sum(x["category"] == category for x in catalogue)
        lines += [f'    let tree{category} = TweakDBInterface.GetAttributeDataRecord(t"NewPerks.{tree}AttributeData");',
                  f"    if !IsDefined(tree{category}) || tree{category}.GetPerksCount() != {count} {{ return false; }}"]
    for index, row in enumerate(catalogue):
        lines.append(f"    if !ProfileCatalogue.R{index}() {{ return false; }}")
    lines += ["    return true;", "  }"]
    for index, row in enumerate(catalogue):
        record = named[row["record"]]
        fields = record["fields"]
        tier = records[fields["tier"]["hash"]]["fields"]["requiredAttributePoints"]
        lines += [f"  private static func R{index}() -> Bool {{",
                  f"    let record = RPGManager.GetNewPerkRecord({enum(row['record'])});",
                  f'    if !IsDefined(record) || record.GetID() != t"{row["record"]}" || !IsDefined(record.Attribute()) ||',
                  f'      record.Attribute().GetID() != t"NewPerks.{expected_trees[row["category"]]}AttributeData" ||',
                  f"      record.GetLevelsCount() != {row['ranks']} || !IsDefined(record.Tier()) || record.Tier().RequiredAttributePoints() != {tier} {{ return false; }}",
                  "    let deps: array<wref<NewPerk_Record>>; record.RequiresPerks(deps);",
                  f"    if ArraySize(deps) != {len(row['requires'])} {{ return false; }}"]
        for n, dep in enumerate(row["requires"]):
            lines.append(f'    if !IsDefined(deps[{n}]) || deps[{n}].GetID() != t"{dep}" {{ return false; }}')
        lines += [f'    let levels = TweakDBInterface.GetForeignKeyArray(record.GetID() + t".levels");',
                  f"    if ArraySize(levels) != {row['ranks']} {{ return false; }}"]
        for n, level in enumerate(fields["levels"]):
            lines.append(f"    if TDBID.ToNumber(levels[{n}]) != {level['hash']}ul {{ return false; }}")
            child = records[level["hash"]]
            if child.get("missing"):
                assert row["record"] == "NewPerks.Tech_Central_Perk_3_3" and level["hash"] == "91068214685"
                lines.append(f"    if IsDefined(record.GetLevelsItem({n})) {{ return false; }} // exact stock absent binding")
            else:
                package = child["fields"]["dataPackage"]["hash"]
                lines.append(f"    if !IsDefined(record.GetLevelsItem({n})) {{ return false; }}")
                lines.append(f'    if TDBID.ToNumber(TweakDBInterface.GetForeignKeyDefault(levels[{n}] + t".dataPackage")) != {package}ul {{ return false; }}')
        lines += ["    return true;", "  }"]
    lines += ["}", ""]
    return "\n".join(lines), inputs, checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    text, inputs, checked = generate()
    path = OUT / "ProfileDefinition.generated.reds"
    if args.write:
        OUT.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        assert path.read_text(encoding="utf-8") == text, "Generated profile is stale; regenerate before testing"
    print(json.dumps({"generated": str(path), "sha256": definition.sha256(path), "inputs": inputs, "counts": checked["perk_counts"]}, indent=2))


if __name__ == "__main__":
    main()
