"""Compile the rebased REDscript against the full JB3 input set offline."""

from pathlib import Path
import shutil
import subprocess

from stage import HERE, OUT, PRE, SCRIPT, baseline, pinned, plain, read, sha, write


def main():
    out = HERE / "compile_01"
    assert not out.exists()
    installed, _, _ = baseline()
    game = Path(installed["game_root"])
    previous = read(pinned(
        PRE / "johnny_batch3_jb2/compile_01/result.json",
        "8D5731BE8538272DAEE2A34B84924BAE292A7E120BD4DBE8ED79AAF68D0D2605",
    ))
    inputs = {p for root in ("r6/scripts", "red4ext/plugins") for p in (game / root).rglob("*.reds")}
    log = game / "r6/logs/redscript_rCURRENT.log"
    plain(log)
    log_hash = sha(log)
    registered = set()
    for line in log.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line.lower().endswith(".reds"):
            registered.add(game / "r6/scripts" / line)
    assert inputs == registered == {Path(p) for p in previous["sources"]}
    assert len(inputs) == previous["source_count"]

    scripts, cache = out / "scripts", out / "cache"
    cache.mkdir(parents=True)
    exe = game / "engine/tools/scc.exe"
    plain(exe)
    pins = {exe: previous["input_pins"][str(exe)], log: log_hash}
    src_hashes = {}
    for p in sorted(inputs):
        plain(p)
        digest = previous["sources"][str(p)]["sha256"]
        pins[p] = digest
        relative = p.relative_to(game)
        if relative.as_posix() == SCRIPT:
            origin = OUT / "package" / SCRIPT
            target_hash = read(OUT / "inputs.json")["script_sha256"]
        else:
            origin, target_hash = p, digest
        dest = scripts / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pinned(origin, target_hash), dest)
        pinned(dest, target_hash)
        src_hashes[str(relative)] = target_hash
    for name in ("final.redscripts", "final.redscripts.ts"):
        p = game / "r6/cache" / name
        plain(p)
        if name.endswith(".ts"):
            assert p.stat().st_size == 16
            pins[p] = sha(p)
        else:
            pins[p] = previous["input_pins"][str(p)]
        shutil.copyfile(pinned(p, pins[p]), cache / name)
        pinned(cache / name, pins[p])
    for p, digest in pins.items():
        pinned(p, digest)

    paths = out / "compile_paths.txt"
    paths.write_bytes(b"")
    output = cache / "compiled.redscripts"
    command = [exe, "-compile", scripts, "-compilePathsFile", paths,
               "-customCacheDir", cache, "-outputCacheFile", output, cache / "final.redscripts"]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=180,
                          creationflags=subprocess.CREATE_NO_WINDOW, cwd=out)
    report = proc.stdout + proc.stderr
    (out / "scc.log").write_text(report, encoding="utf-8")
    for p, digest in pins.items():
        pinned(p, digest)
    assert proc.returncode == 0 and "Compilation complete" in report and output.is_file(), report[-5000:]
    write(out / "result.json", {
        "status": "PASS_CURRENT_INPUT_OFFLINE_COMPILE", "source_count": len(inputs),
        "input_pins": {str(p): d for p, d in pins.items()}, "sources": src_hashes,
        "candidate_script_sha256": sha(OUT / "package" / SCRIPT),
        "compiled_sha256": sha(output), "game_writes": 0, "save_writes": 0,
    })
    print(f"Compiled all {len(inputs)} registered REDscript inputs.")


if __name__ == "__main__":
    main()
