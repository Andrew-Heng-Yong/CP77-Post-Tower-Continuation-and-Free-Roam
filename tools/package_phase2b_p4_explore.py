"""Workspace-only P4 ZIP build and read-only installation/fixture checks."""
import argparse
import json
import zipfile

from package_phase2b_p2 import ROOT, GAME, MODS, ARCHIVE, ARCHIVE_SHA, sha, require_hash, check_baseline

MODULE = "PTFR_Phase2B_P4_Explore"
SOURCE = ROOT / "diagnostics" / MODULE
OUTPUT = ROOT / "build/Phase2B_P4_Explore"
FILES = ("init.lua", "ptfr_p4_survey.lua", "ptfr_p4_target.lua")
PACKAGE = OUTPUT / (MODULE + ".zip")
MANIFEST = OUTPUT / "manifest.json"
REVIEW = ROOT / "research/phase2b_p4/destination_independent_math.json"


def build():
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    assert review.get("static_review_passed") is True, "Static independent destination approval required before build"
    baseline = check_baseline()
    require_hash(GAME / "archive/pc/mod" / ARCHIVE, ARCHIVE_SHA)
    assert {p.name for p in SOURCE.iterdir() if p.is_file()} == set(FILES), "Unexpected source package members"
    payloads = {MODULE + "/" + name: (SOURCE / name).read_bytes() for name in FILES}
    joined = b"\n".join(payloads.values()).decode("utf-8")
    for forbidden in (":SetFact", ":ChangeEntryState", ":ExecutePSAction", ":QueueEvent", "PerformFastTravel(",
                      ":RemoveStatusEffect", ":ApplyStatusEffect", "Override(", "Game.Set", "SpawnPlayerVehicle("):
        assert forbidden not in joined, "Forbidden world mutation/wrapper: " + forbidden
    assert joined.count("facility:Teleport(") == 1, "Exactly one low-level teleport dispatch site required"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PACKAGE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.namelist() == list(payloads) and archive.testzip() is None
        assert all(archive.read(name) == payload for name, payload in payloads.items())
    manifest = {"probe": "Phase2B-P4-explore", "package": str(PACKAGE), "package_sha256": sha(PACKAGE),
                "entries": [{"path": MODULE + "/" + name, "sha256": sha(SOURCE / name)} for name in FILES],
                "static_review": {"path": str(REVIEW), "sha256": sha(REVIEW), "passed": True},
                "baseline_save_hashes_unchanged": baseline,
                "required_existing_archive": {"name": ARCHIVE, "sha256": ARCHIVE_SHA},
                "new_archive": False, "agent_installed_or_runtime_tested": False,
                "extract_into": str(MODS), "sole_game_mutation": "One explicit low-level Teleport call",
                "readiness": "Core/ground/navmesh/clearance checks required; optional survey errors are nonblocking"}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def installed():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for row in manifest["entries"]:
        require_hash(MODS / row["path"], row["sha256"])
    require_hash(GAME / "archive/pc/mod" / ARCHIVE, ARCHIVE_SHA)
    check_baseline()
    old = [p.name for p in MODS.iterdir() if p.is_dir() and p.name.startswith("PTFR_") and p.name != MODULE]
    if old:
        raise ValueError("Preserve logs, then manually move older PTFR recorder/probe folders OUTSIDE mods: " + ", ".join(old))
    print("INSTALL CHECK PASS: three Lua files and P0 archive match; original ManualSave-11 hashes unchanged. Confirm the loaded disposable-copy identity yourself.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-installed", action="store_true")
    args = parser.parse_args()
    try:
        installed() if args.check_installed else build()
        return 0
    except (OSError, ValueError, AssertionError, KeyError, zipfile.BadZipFile) as exc:
        print("BUILD/INSTALL CHECK FAILED: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
