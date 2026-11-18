"""Verify the packed seat repair and stage the complete local payload."""

from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / "misty_rooftop_seat_20261117_01"
sys.path.insert(0, str(PREVIOUS))
from build import ARCHIVE, EXE, EXE_SHA, GAME, read, row, safe, sha, verify_rows, write
from deploy import archive_environment, verify_providers
from validate import scene_check


BASELINE = PREVIOUS / "installed_manifest.json"
BASELINE_SHA = "8261F9C3E9B228B636E71A432AF6D715207F3A688E3AC1EC5393772A0194A738"
ASSETS = ROOT / "work/pack_01"
CANDIDATE = ROOT / "candidate_01"
SEAT_DEPOT = r"towercontinued\misty_rooftop_seat\sit.scene"
FEMALE_ANIM_SET = r"base\animations\player\female\body\player_locomotion_johnny_guitar.anims"


def verified_baseline() -> dict:
    if sha(BASELINE) != BASELINE_SHA:
        raise RuntimeError("Installed rooftop seat manifest drift")
    manifest = read(BASELINE)
    verify_rows(GAME, manifest["core_files"] + manifest["required_files"] +
                manifest["archivexl_files"] + manifest["ifp_files"])
    if sha(safe(GAME, EXE)) != EXE_SHA:
        raise RuntimeError("Game executable drift")
    return manifest


def verify_scene(assets: dict) -> None:
    prior = read(PREVIOUS / "work/pack_01/readback.json")
    prior_scene = next(resource for resource in prior["private_resources"] if resource["depot"] == SEAT_DEPOT)
    captured = assets["captured_providers"][SEAT_DEPOT][0]
    before_path = ASSETS / "before.scene.json"
    after_path = ASSETS / "packed.scene.json"
    if (sha(Path(captured["raw"])) != assets["changed_member"]["before"] or
        assets["changed_member"]["before"] != prior_scene["sha256"] or
        assets["before_json_sha256"] != sha(before_path) or assets["after_json_sha256"] != sha(after_path) or
        sha(ASSETS / "packed.scene") != assets["changed_member"]["after"]):
        raise RuntimeError("Seat readback changed")
    before = read(before_path)["Data"]["RootChunk"]
    after_file = read(after_path)
    after = after_file["Data"]["RootChunk"]
    old_refs = before["resouresReferences"]
    new_refs = after["resouresReferences"]
    if (len(old_refs["gameplayAnimSets"]) != 1 or len(old_refs["gameplayAnimNames"]) != 2 or
        not (len(new_refs["gameplayAnimSets"]) == len(new_refs["gameplayAnimNames"]) == 2)):
        raise RuntimeError("Unexpected stand-up animation tables")
    female_ref = new_refs["gameplayAnimSets"].pop()
    if female_ref["asyncAnimSet"]["DepotPath"]["$value"] != FEMALE_ANIM_SET or after != before:
        raise RuntimeError("Repaired scene contains an unrelated change")
    scene_check(after_file, read(PREVIOUS / "work/scene_01/manifest.json"))


def main() -> None:
    base = verified_baseline()
    proof = read(ASSETS / "readback.json")
    old_archive = next(r for r in base["core_files"] if r["path"] == ARCHIVE)
    if (proof["status"] != "MEMBERS_VERIFIED" or proof["baseline_sha256"] != BASELINE_SHA or
        proof["scene_depot"] != SEAT_DEPOT or proof["checked_members"] != 1751 or proof["preserved_members"] != 1750 or
        proof["package_file"]["path"] != ARCHIVE):
        raise RuntimeError("Unqualified repair archive")
    verify_rows(ASSETS / "package", [proof["package_file"]])
    environment = archive_environment(GAME)
    verify_providers({"archives": proof["archive_provider_scan"]}, environment, old_archive)
    previous_plan = Path(base["installation_plan"])
    if sha(previous_plan) != base["installation_plan_sha256"]:
        raise RuntimeError("Active installation proof drift")
    if environment["xl"] != read(previous_plan)["archive_environment"]["xl"]:
        raise RuntimeError("The last qualified ArchiveXL configurations changed")
    verify_scene(proof)

    package = CANDIDATE / "package"
    package.mkdir(parents=True, exist_ok=False)
    for item in base["core_files"]:
        relative = item["path"]
        src = safe(ASSETS / "package" if relative == ARCHIVE else GAME, relative)
        target = safe(package, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
    rows = [row(package, item["path"]) for item in base["core_files"]]
    changed = [a["path"] for a, b in zip(rows, base["core_files"], strict=True) if a != b]
    if changed != [ARCHIVE] or next(r for r in rows if r["path"] == ARCHIVE) != proof["package_file"]:
        raise RuntimeError("Unexpected staged file delta")
    verified_baseline()
    write(CANDIDATE / "core_manifest.json", {
        "status": "STAGED_OFFLINE",
        "baseline_sha256": BASELINE_SHA,
        "core_files": rows,
        "changed_paths": changed,
        "asset_assessment_sha256": sha(ASSETS / "readback.json"),
        "preserved_archive_members": proof["preserved_members"],
        "changed_scene": SEAT_DEPOT,
        "verified_existing_xl_files": len(environment["xl"]) + 1,
        "gameplay": "PENDING",
    })
    print("Staged 51 files. Only the combined archive changed, and only its chair scene differs.")


if __name__ == "__main__":
    main()
