"""Build the workspace-only P2 probe, or read-only check its installation.

Never installs, renames, deletes, or writes anything in the game/save directories.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = "PTFR_Phase2B_P2_RepairProbe"
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
MODS = GAME / "bin/x64/plugins/cyber_engine_tweaks/mods"
SAVE = Path(r"C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-11")
ARCHIVE = "TowerContinued_Phase2B_P0_DirectReturn.archive"
ARCHIVE_SHA = "DF9B68C7B8E06ACF081043592CB56620BC3F09804235F619A2C17CEA319AEF54"
BASELINE = {
    "metadata.9.json": "35DEA4566FD5E0A50D31834002B94AB7DC21A884CDD19AC4E74CB382A7031661",
    "sav.dat": "03D752C897C6F77FF93ED7D2D8B43A398BEAC119939C7199A9B3B9CF237C8EAE",
    "screenshot.png": "3C0FED7770FCDE0334B355770699216ACA99FE7F90904ADE8DFE6D696F054ADA",
}
OUTPUT = ROOT / "build/Phase2B_P2_LogFix"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def require_hash(path, expected):
    actual = sha(path)
    if actual != expected:
        raise ValueError(f"Hash mismatch: {path}; expected {expected}, got {actual}")
    return actual


def check_baseline():
    return {name: require_hash(SAVE / name, digest) for name, digest in BASELINE.items()}


def check_installed():
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    require_hash(MODS / MODULE / "init.lua", manifest["entries"][0]["sha256"])
    require_hash(GAME / "archive/pc/mod" / ARCHIVE, ARCHIVE_SHA)
    check_baseline()
    old = [name for name in ("PTFR_Phase2B_P0", "PTFR_Phase2B_P1") if (MODS / name).exists()]
    if old:
        raise ValueError("Move older recorder folders outside CET mods for this isolated test: " + ", ".join(old))
    print("INSTALL CHECK PASS: probe/required P0 archive match; ManualSave-11 hashes unchanged. Loaded disposable-copy identity still requires human verification.")


def build():
    baseline = check_baseline()
    require_hash(ROOT / "build/Phase2B_P0" / ARCHIVE, ARCHIVE_SHA)
    require_hash(GAME / "archive/pc/mod" / ARCHIVE, ARCHIVE_SHA)
    source = ROOT / "diagnostics" / MODULE / "init.lua"
    entry = MODULE + "/init.lua"
    payload = source.read_bytes()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    package = OUTPUT / (MODULE + "_LogFix.zip")
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo(entry, date_time=(2026, 9, 22, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, payload)
    with zipfile.ZipFile(package) as archive:
        assert archive.namelist() == [entry], "Unintended package members"
        assert archive.testzip() is None
        assert archive.read(entry) == payload, "Packaged bytes differ from source"
    manifest = {
        "phase": "2B-P2 targeted manual writable repair probe",
        "package": str(package), "package_sha256": sha(package),
        "entries": [{"path": entry, "bytes": len(payload), "sha256": sha(source)}],
        "extract_destination": str(MODS),
        "required_existing_archive": {"path": str(GAME / "archive/pc/mod" / ARCHIVE), "sha256": ARCHIVE_SHA},
        "older_recorders_to_move_out_manually": ["PTFR_Phase2B_P0 (if present)", "PTFR_Phase2B_P1"],
        "baseline_save_read_only": {"path": str(SAVE), "sha256": baseline},
        "validation_scope": "ZIP allowlist, byte equality, archive hashes, unchanged baseline. Offline Lua/parser tests reported separately in docs. Not installed or runtime-tested.",
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-installed", action="store_true")
    args = parser.parse_args()
    try:
        check_installed() if args.check_installed else build()
        return 0
    except (OSError, ValueError, AssertionError, zipfile.BadZipFile) as exc:
        print("NOT READY: " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
