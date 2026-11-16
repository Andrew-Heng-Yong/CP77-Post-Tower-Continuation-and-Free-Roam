"""Compile the three Cassius overlays with the installed source inventory."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

from build import HERE, INSTALL, INSTALL_SHA, checked_path, digest, load, require, verify_baseline, write_json


def registered_log(game, sources):
    for log in sorted((game / "r6/logs").glob("redscript*.log"), key=lambda p: p.stat().st_mtime_ns, reverse=True):
        text = log.read_text(encoding="utf-8-sig", errors="replace")
        registered = {(game / "r6/scripts" / line.strip()).resolve()
                      for line in text.splitlines() if line.strip().lower().endswith(".reds")}
        if registered == sources and "Compilation complete" in text:
            return checked_path(log)
    raise RuntimeError("No successful compiler registry matches the installed source inventory")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100))
    args = parser.parse_args()
    baseline = load(INSTALL, INSTALL_SHA)
    verify_baseline(baseline)
    game = Path(baseline["game_root"])
    sources = {p.resolve() for rel in ("r6/scripts", "red4ext/plugins") for p in (game / rel).rglob("*.reds")}
    registry = registered_log(game, sources)
    compiler = game / "engine/tools/scc.exe"
    caches = [game / "r6/cache" / name for name in ("final.redscripts", "final.redscripts.ts")]
    pins = {path: digest(path) for path in sorted(sources | {compiler, registry, *caches})}
    overlay = HERE / "overlay"
    changed = {path.relative_to(overlay).as_posix(): digest(path) for path in overlay.rglob("*.reds")}
    require(len(changed) == 3, "Unexpected script overlay inventory")

    out = HERE / f"compile_{args.attempt:02}"
    (out / "cache").mkdir(parents=True)
    for path in caches:
        shutil.copyfile(path, out / "cache" / path.name)
    staged = {}
    for path in sorted(sources):
        rel = path.relative_to(game).as_posix()
        src = overlay / rel if rel in changed else path
        target = out / "scripts" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        staged[rel] = digest(target)
    require({rel: staged[rel] for rel in changed} == changed, "An overlay was omitted or changed")

    paths = out / "compile_paths.txt"
    paths.write_bytes(b"")
    target = out / "cache/compiled.redscripts"
    command = [compiler, "-compile", out / "scripts", "-compilePathsFile", paths,
               "-customCacheDir", out / "cache", "-outputCacheFile", target, out / "cache/final.redscripts"]
    result = subprocess.run(list(map(str, command)), capture_output=True, encoding="utf-8",
                            errors="replace", timeout=240, creationflags=subprocess.CREATE_NO_WINDOW)
    output = result.stdout + result.stderr
    (out / "scc.log").write_text(output, encoding="utf-8")
    require(all(digest(path) == value for path, value in pins.items()), "Installed compiler inputs changed")
    require(all(digest(overlay / path) == value for path, value in changed.items()), "Overlay changed during compile")
    require(result.returncode == 0 and "Compilation complete" in output and target.is_file(), output[-12000:])
    write_json(out / "assessment.json", {
        "status": "PASS", "sources": len(staged), "registry": str(registry),
        "input_pins": {str(p): h for p, h in pins.items()}, "staged": staged,
        "overlay": changed, "compiled_sha256": digest(target),
    })
    print(f"Compiled {len(staged)} sources with the three Cassius overlays.")


if __name__ == "__main__":
    main()
