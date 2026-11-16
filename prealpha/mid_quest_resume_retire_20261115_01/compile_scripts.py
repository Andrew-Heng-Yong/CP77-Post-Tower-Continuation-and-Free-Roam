"""Compile the complete installed REDscript inventory with the staged changes."""

import shutil
import subprocess

from pathlib import Path
from prepare_scripts import BEFORE, BEFORE_SHA, SCRIPT_STAGE, digest, load, pin, require, write_json


def main():
    baseline = load(BEFORE, BEFORE_SHA)
    game = Path(baseline["game_root"])
    sources = {p for root in ("r6/scripts", "red4ext/plugins") for p in (game / root).rglob("*.reds")}
    registry = None
    for path in sorted((game / "r6/logs").glob("redscript*.log"), key=lambda p: p.stat().st_mtime_ns, reverse=True):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        recorded = {(game / "r6/scripts" / line.strip()).resolve()
                    for line in text.splitlines() if line.strip().lower().endswith(".reds")}
        if recorded == sources and "Compilation complete" in text:
            registry = path
            break
    require(registry and len(sources) == 148, "Registered source inventory drift")
    compiler = game / "engine/tools/scc.exe"
    caches = [game / "r6/cache" / name for name in ("final.redscripts", "final.redscripts.ts")]
    inputs = {path: digest(path) for path in sorted(sources | {registry, compiler, *caches})}
    code = SCRIPT_STAGE / "script_changes.json"
    replacements = load(code, digest(code))
    out = SCRIPT_STAGE / "compile"
    (out / "cache").mkdir(parents=True)
    for path in caches:
        shutil.copyfile(path, out / "cache" / path.name)
    staged = {}
    for path in sorted(sources):
        relative = path.relative_to(game).as_posix()
        source = (pin(SCRIPT_STAGE / "package" / relative, replacements[relative]["after"])
                  if relative in replacements else path)
        target = out / "scripts" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        staged[relative] = digest(target)
    paths = out / "compile_paths.txt"
    paths.write_bytes(b"")
    image = out / "cache/compiled.redscripts"
    command = [compiler, "-compile", out / "scripts", "-compilePathsFile", paths,
               "-customCacheDir", out / "cache", "-outputCacheFile", image, out / "cache/final.redscripts"]
    result = subprocess.run(list(map(str, command)), capture_output=True, encoding="utf-8",
                            errors="replace", timeout=140, creationflags=subprocess.CREATE_NO_WINDOW)
    log = result.stdout + result.stderr
    (out / "scc.log").write_text(log, encoding="utf-8")
    require(result.returncode == 0 and "Compilation complete" in log and image.is_file(), log[-14000:])
    compiled = image.read_bytes()
    for symbol in (b"ResumeContractsRD1", b"KirkEligible", b"RiteResumeRD5", b"ReadEarnedRD1",
                   b"ReadExecutionCheckpoint", b"CassiusResumeBridge", b"ReadNorthsideRD3"):
        require(symbol not in compiled, f"Active resume code remains: {symbol!r}")
    require(all(digest(path) == sha for path, sha in inputs.items()), "Compiler inputs changed")
    write_json(out / "assessment.json", dict(status="PASS", sources=len(staged), staged=staged,
               input_pins={str(path): sha for path, sha in inputs.items()}, compiled_sha256=digest(image)))
    print(f"All {len(staged)} registered sources compiled without the removed resume routines.")


if __name__ == "__main__":
    main()
