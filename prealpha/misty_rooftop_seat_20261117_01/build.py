"""Stage Misty's rooftop seat and compile the registered REDscript sources."""

import hashlib
import json
import shutil
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
BASE = ROOT.parent / "misty_rooftop_lift_20261117_01/installed_manifest.json"
BASE_SHA = "B738804793E5E669D71F72E9FB7755B2786D2B25E3B0A212681F10427C9EF5C0"
EXE = "bin/x64/Cyberpunk2077.exe"
EXE_SHA = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"
REDS = "r6/scripts/PTFR_Consolidated/PTFR_MistyViktorAuto.reds"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
XL = ARCHIVE + ".xl"
CHANGED = (ARCHIVE, XL, REDS)


def plain(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise RuntimeError(f"Linked path refused: {part}")


def safe(root: Path, relative: str) -> Path:
    parts = relative.split("/")
    if any(not p or p in {".", ".."} or p.endswith((".", " ")) or ":" in p or "\\" in p for p in parts):
        raise RuntimeError(f"Unsafe relative path: {relative}")
    path = root.joinpath(*parts)
    if not path.absolute().is_relative_to(root.absolute()):
        raise RuntimeError(f"Path escapes root: {path}")
    plain(path)
    return path


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def row(root: Path, relative: str) -> dict:
    path = safe(root, relative)
    return {"path": relative, "bytes": path.stat().st_size, "sha256": sha(path)}


def read(path: Path) -> dict:
    plain(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value: dict) -> None:
    plain(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def verify_rows(root: Path, rows: list[dict]) -> None:
    for expected in rows:
        actual = row(root, expected["path"])
        if any(actual[k] != expected[k] for k in ("bytes", "sha256")):
            raise RuntimeError(f"File drift: {root / expected['path']}")


def verified_baseline() -> dict:
    plain(BASE)
    if sha(BASE) != BASE_SHA:
        raise RuntimeError("Installed baseline manifest drift")
    base = read(BASE)
    if base["core_epoch"] != "MISTY_ROOFTOP_LIFT" or len(base["core_files"]) != 51:
        raise RuntimeError("Wrong installed baseline")
    verify_rows(GAME, base["core_files"] + base["required_files"] + base["archivexl_files"] + base["ifp_files"])
    if sha(safe(GAME, EXE)) != EXE_SHA:
        raise RuntimeError("Game executable no longer matches the inspected implementation")
    return base


def compiler_sources() -> dict[str, Path]:
    files = {}
    for root in ("r6/scripts", "red4ext/plugins"):
        for path in safe(GAME, root).rglob("*.reds"):
            plain(path)
            files[path.relative_to(GAME).as_posix()] = path
    return dict(sorted(files.items()))


def compile_overlay(source: Path, output: Path) -> dict:
    all_sources = compiler_sources()
    registry = safe(GAME, "r6/logs/redscript_rCURRENT.log")
    registry_text = registry.read_text(encoding="utf-8-sig")
    registered = set()
    for line in registry_text.splitlines():
        name = line.strip()
        if name.lower().endswith(".reds"):
            path = Path(name)
            registered.add(path if path.is_absolute() else GAME / "r6/scripts" / path)
    if "Compilation complete" not in registry_text or set(all_sources.values()) != registered or REDS not in all_sources:
        raise RuntimeError(f"Compiler source census mismatch ({len(registered)} registered / {len(all_sources)} present)")
    compiler = safe(GAME, "engine/tools/scc.exe")
    cache_inputs = [safe(GAME, f"r6/cache/{name}") for name in ("final.redscripts", "final.redscripts.ts")]
    auxiliary = {str(p): sha(p) for p in (registry, compiler, *cache_inputs)}
    input_hashes = {name: sha(path) for name, path in all_sources.items()}
    output.mkdir(exist_ok=False)
    scripts = output / "scripts"
    cache = output / "cache"
    cache.mkdir()
    staged = {}
    for name, path in all_sources.items():
        dest = safe(scripts, name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source if name == REDS else path, dest)
        staged[name] = sha(dest)
    if [name for name, digest in staged.items() if digest != input_hashes[name]] != [REDS]:
        raise RuntimeError("Expected one REDscript change")
    for path in cache_inputs:
        dest = cache / path.name
        shutil.copyfile(path, dest)
        if sha(dest) != auxiliary[str(path)]:
            raise RuntimeError("Staged cache drift")
    paths = output / "compile_paths.txt"
    paths.write_bytes(b"")
    image = cache / "compiled.redscripts"
    cmd = [compiler, "-compile", scripts, "-compilePathsFile", paths,
           "-customCacheDir", cache, "-outputCacheFile", image, cache / "final.redscripts"]
    result = subprocess.run([str(part) for part in cmd], cwd=output, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=180,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    log = result.stdout + result.stderr
    (output / "scc.log").write_text(log, encoding="utf-8")
    if result.returncode or "Compilation complete" not in log or not image.is_file():
        raise RuntimeError(f"SCC failed ({result.returncode}): {log[-6000:]}")
    if compiler_sources() != all_sources or any(sha(path) != input_hashes[name] for name, path in all_sources.items()):
        raise RuntimeError("Live REDscript source changed during compile")
    if any(sha(Path(path)) != digest for path, digest in auxiliary.items()):
        raise RuntimeError("Live compiler/cache input changed")
    proof = {"status": "PASS", "registered_sources": len(registered), "changed_sources": [REDS],
             "source_before": input_hashes, "source_after": staged, "auxiliary_inputs": auxiliary,
             "compiled_sha256": sha(image), "game_writes": 0, "save_writes": 0}
    write(output / "assessment.json", proof)
    return proof


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", choices=("candidate_01", "candidate_02", "candidate_03"))
    output = ROOT / parser.parse_args().candidate
    base = verified_baseline()
    asset_output = ROOT / "work/pack_01"
    assets = read(asset_output / "readback.json")
    if assets["status"] != "MEMBERS_VERIFIED" or assets["baseline_sha256"] != BASE_SHA:
        raise RuntimeError("Unverified rooftop seat assets")
    asset_rows = assets["package_files"]
    if {item["path"] for item in asset_rows} != {ARCHIVE, XL}:
        raise RuntimeError("Unexpected rooftop asset inventory")
    verify_rows(asset_output / "package", asset_rows)
    package = output / "package"
    package.mkdir(parents=True, exist_ok=False)
    for old in base["core_files"]:
        relative = old["path"]
        if relative == REDS:
            src = ROOT / "source" / Path(relative).name
        elif relative in (ARCHIVE, XL):
            src = safe(asset_output / "package", relative)
        else:
            src = safe(GAME, relative)
        plain(src)
        target = safe(package, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
    files = [row(package, item["path"]) for item in base["core_files"]]
    changed = {old["path"] for old, new in zip(base["core_files"], files, strict=True) if old != new}
    if changed != set(CHANGED):
        raise RuntimeError(f"Unexpected staged changes: {changed}")
    proof = compile_overlay(safe(package, REDS), output / "compile_01")
    verified_baseline()
    write(output / "core_manifest.json", {"status": "STAGED_OFFLINE", "baseline_sha256": BASE_SHA,
          "core_files": files, "changed_paths": list(CHANGED),
          "asset_assessment_sha256": sha(asset_output / "readback.json"),
          "compile_assessment_sha256": sha(output / "compile_01/assessment.json")})
    print(f"Compiled {proof['registered_sources']} registered REDscript inputs. Staged 51 Core files.")


if __name__ == "__main__":
    main()
