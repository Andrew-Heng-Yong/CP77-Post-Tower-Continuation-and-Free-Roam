"""Compile the fresh 51-path WO2 candidate with every current registered source."""

from pathlib import Path
import json
import shutil
import subprocess

from prepare_candidate import BASE, BASE_SHA, GAME, HERE, OUT, SCRIPT, check_rows, plain, sha


def write_json(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def main() -> None:
    base = json.loads(BASE.read_text(encoding="utf-8-sig"))
    assert sha(BASE) == BASE_SHA
    candidate = json.loads((OUT / "core_manifest_01.json").read_text(encoding="utf-8-sig"))
    assert candidate["status"] == "STAGED_OFFLINE" and candidate["changed_paths"] == [SCRIPT]
    check_rows(base["core_files"] + base["required_files"])
    all_sources = {path for root in (GAME / "r6/scripts", GAME / "red4ext/plugins")
                   for path in root.rglob("*.reds")}
    registry = GAME / "r6/logs/redscript_rCURRENT.log"
    compiler = GAME / "engine/tools/scc.exe"
    cache_inputs = [GAME / "r6/cache" / name for name in ("final.redscripts", "final.redscripts.ts")]
    registered = set()
    for line in registry.read_text(encoding="utf-8-sig").splitlines():
        row = line.strip()
        if not row.lower().endswith(".reds"):
            continue
        path = Path(row)
        registered.add(path if path.is_absolute() else GAME / "r6/scripts" / path)
    assert "Compilation complete" in registry.read_text(encoding="utf-8-sig")
    if all_sources != registered:
        raise RuntimeError(f"REDscript registration mismatch: {len(all_sources)} files / {len(registered)} logged")
    assert len(all_sources) == 149
    inputs = {str(path): sha(path) for path in sorted(all_sources | {registry, compiler, *cache_inputs})}
    for path in all_sources | {registry, compiler, *cache_inputs}:
        plain(path)
    output = OUT / "compile_01"
    output.mkdir(exist_ok=False)
    scripts = output / "scripts"
    staged = {}
    for path in sorted(all_sources):
        relative = path.relative_to(GAME).as_posix()
        src = OUT / "package" / SCRIPT if relative == SCRIPT else path
        dst = scripts / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        staged[relative] = sha(dst)
    assert [r for r, h in staged.items() if h != inputs[str(GAME / r)]] == [SCRIPT]
    cache = output / "cache"
    cache.mkdir()
    for path in cache_inputs:
        shutil.copyfile(path, cache / path.name)
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
    if result.returncode != 0 or "Compilation complete" not in log or not image.is_file():
        raise RuntimeError(f"SCC failure {result.returncode}: {log[-5000:]}")
    assert all(sha(Path(path)) == value for path, value in inputs.items()), "Compiler input changed"
    check_rows(base["core_files"] + base["required_files"])
    write_json(output / "assessment.json", {
        "status": "PASS", "registered_sources": len(registered), "staged_sources": staged,
        "input_hashes": inputs, "changed_sources": [SCRIPT], "compiled_sha256": sha(image),
        "game_writes": 0, "save_writes": 0,
    })
    print(f"PASS: {len(registered)} registered sources; one script overlay; offline SCC compile")


if __name__ == "__main__":
    main()
