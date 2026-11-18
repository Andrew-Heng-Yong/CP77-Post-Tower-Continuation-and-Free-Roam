"""Stage BV1 against the exact installed LC5 Core and compile all live sources offline."""

import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
BASELINE = ROOT / "prealpha/credits_cover_lc5_20261116_01/work/deployment_01/installed_manifest_01.json"
BASELINE_SHA = "02E089A382D01A0542BA804CAA6B2892D2A411B8C25F755A8C503C1483D703DF"
COMPILE = ROOT / "prealpha/credits_cover_lc5_20261116_01/candidate_01/compile_01/assessment.json"
COMPILE_SHA = "4329983EF68EF37AF0A788BC2CBD77AE858AA0CB1B483CBC5BA01E40F8951D54"
RELATIVES = (
    "r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds",
    "r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds",
)
OUTPUT = HERE / "candidate_01"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def plain(path: Path) -> None:
    for member in (path, *path.parents):
        if member.exists() and member.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError(f"Reparse path refused: {member}")


def checked(path: Path, expected: str) -> None:
    plain(path)
    if not path.is_file() or sha(path) != expected:
        raise RuntimeError(f"Input drift: {path}")


def record(root: Path, relative: str) -> dict:
    path = root / relative
    plain(path)
    return {"path": relative, "bytes": path.stat().st_size, "sha256": sha(path)}


def verify_rows(root: Path, rows: list[dict]) -> None:
    for row in rows:
        actual = record(root, row["path"])
        if actual != {key: row[key] for key in ("path", "bytes", "sha256")}:
            raise RuntimeError(f"Protected file drift: {row['path']}")


def write_json(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def main() -> None:
    checked(BASELINE, BASELINE_SHA)
    checked(COMPILE, COMPILE_SHA)
    baseline = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    compiled_before = json.loads(COMPILE.read_text(encoding="utf-8-sig"))
    assert baseline["core_epoch"] == "LC5_CREDITS_COVER"
    assert compiled_before["status"] == "PASS"
    assert len(baseline["core_files"]) == 51 and len(compiled_before["staged_sources"]) == 149
    assert len(baseline["required_files"]) == 47
    verify_rows(GAME, baseline["core_files"] + baseline["required_files"])

    source_inventory = {path.relative_to(GAME).as_posix()
                        for base in (GAME / "r6/scripts", GAME / "red4ext/plugins")
                        for path in base.rglob("*.reds")}
    assert source_inventory == set(compiled_before["staged_sources"])
    for relative, expected in compiled_before["staged_sources"].items():
        checked(GAME / relative, expected)
    current_inputs = {}
    for path, expected in compiled_before["installed_inputs"].items():
        live = Path(path)
        plain(live)
        if not live.is_file():
            raise RuntimeError(f"Missing compiler input: {live}")
        actual = sha(live)
        if live.name == "final.redscripts.ts":
            # The engine rewrites this 16-byte cache timestamp on launch.
            assert live.stat().st_size == 16
        elif live == GAME / RELATIVES[0]:
            assert actual == compiled_before["staged_sources"][RELATIVES[0]]
        else:
            assert actual == expected, f"Compiler input drift: {live}"
        current_inputs[path] = actual

    candidates = {relative: HERE / "source_02" / Path(relative).name for relative in RELATIVES}
    for relative, path in candidates.items():
        plain(path)
        assert path.is_file() and sha(path) != compiled_before["staged_sources"][relative]
    plain(OUTPUT)
    OUTPUT.mkdir(exist_ok=False)
    package = OUTPUT / "package"
    core_after = []
    for row in baseline["core_files"]:
        relative = row["path"]
        source = candidates.get(relative, GAME / relative)
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        core_after.append(record(package, relative))
    changed = [old["path"] for old, new in zip(baseline["core_files"], core_after)
               if any(old[key] != new[key] for key in ("bytes", "sha256"))]
    assert changed == list(RELATIVES)

    proof = OUTPUT / "compile_01"
    sources = proof / "scripts"
    cache = proof / "cache"
    cache.mkdir(parents=True)
    staged_sources = {}
    for relative in sorted(source_inventory):
        source = candidates.get(relative, GAME / relative)
        target = sources / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        staged_sources[relative] = sha(target)
    assert {r for r in staged_sources if staged_sources[r] != compiled_before["staged_sources"][r]} == set(RELATIVES)
    for name in ("final.redscripts", "final.redscripts.ts"):
        shutil.copyfile(GAME / "r6/cache" / name, cache / name)
    (proof / "compile_paths.txt").write_bytes(b"")
    compiler = GAME / "engine/tools/scc.exe"
    command = [compiler, "-compile", sources, "-compilePathsFile", proof / "compile_paths.txt",
               "-customCacheDir", cache, "-outputCacheFile", cache / "compiled.redscripts",
               cache / "final.redscripts"]
    result = subprocess.run([str(part) for part in command], cwd=proof, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=140,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    log = result.stdout + result.stderr
    (proof / "scc.log").write_text(log, encoding="utf-8")
    if result.returncode or "Compilation complete" not in log or not (cache / "compiled.redscripts").is_file():
        raise RuntimeError(f"SCC failed (exit {result.returncode}): {log[-4000:]}")

    verify_rows(GAME, baseline["core_files"] + baseline["required_files"])
    verify_rows(package, core_after)
    assert source_inventory == {path.relative_to(GAME).as_posix()
                                for base in (GAME / "r6/scripts", GAME / "red4ext/plugins")
                                for path in base.rglob("*.reds")}
    for path, expected in current_inputs.items():
        checked(Path(path), expected)
    for relative, expected in compiled_before["staged_sources"].items():
        checked(GAME / relative, expected)
    for relative, path in candidates.items():
        checked(path, staged_sources[relative])
    write_json(proof / "assessment.json", {
        "status": "PASS", "baseline_sha256": BASELINE_SHA, "predecessor_compile_sha256": COMPILE_SHA,
        "source_count": len(staged_sources), "staged_sources": staged_sources,
        "installed_inputs": current_inputs,
        "changed_sources": changed, "compiled_sha256": sha(cache / "compiled.redscripts"),
        "game_writes": 0, "save_writes": 0,
    })
    write_json(OUTPUT / "core_manifest_01.json", {
        "status": "STAGED_OFFLINE", "baseline_sha256": BASELINE_SHA,
        "core_files": core_after, "changed_paths": changed,
        "required_files": baseline["required_files"],
        "compile_assessment_sha256": sha(proof / "assessment.json"),
    })
    print(f"PASS: {len(staged_sources)} source compile; {len(core_after)} Core files; {len(changed)} reviewed replacements")


if __name__ == "__main__":
    main()
