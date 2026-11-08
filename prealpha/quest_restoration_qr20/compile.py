"""Stage the full current compiler inputs and compile only in the workspace."""
from pathlib import Path
import shutil
import stat
import subprocess

from build import HERE, SCRIPT, checked, read, sha, write


def safe(path):
    assert all(not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
               for p in (path, *path.parents)), path


def main():
    out = HERE / "compile_02"
    assert not out.exists()
    prior = read(HERE.parent / "quest_restoration_qr14/verification/compile_01/result.json")
    installed = read(HERE.parent / "quest_restoration_qr19/deployment_01/installed_manifest_01.json")
    game = Path(installed["game_root"])
    roots = (game / "r6/scripts", game / "red4ext/plugins")
    found = {p for root in roots for p in root.rglob("*.reds")}
    log = game / "r6/logs/redscript_rCURRENT.log"
    safe(log)
    log_sha = sha(log)
    listed = {line.strip() for line in log.read_text(encoding="utf-8-sig").splitlines()
              if line.strip().lower().endswith(".reds")}
    registered = {Path(s) if Path(s).is_absolute() else game / "r6/scripts" / s for s in listed}
    assert found == registered == {Path(p) for p in prior["runtime_registered_sources"]}, "Compiler source inventory drift"
    core = {game / row["path"]: row["sha256"] for row in installed["core_files"] if row["path"].endswith(".reds")}
    fixed = {game / "r6/cache" / n for n in ("final.redscripts", "final.redscripts.ts")}
    timestamp = game / "r6/cache/final.redscripts.ts"
    exe = game / "engine/tools/scc.exe"
    pins = {}
    for p in sorted(found | fixed | {exe}):
        safe(p)
        if p == timestamp:
            # Normal game runs refresh this timestamp sidecar. The real
            # bytecode cache below still has to match its prior pinned hash.
            assert p.stat().st_size == 16
            digest = sha(p)
        else:
            digest = core.get(p, prior["input_pins"][str(p)])
        checked(p, digest)
        pins[str(p)] = digest
    script = read(HERE / "proposal_02/plan.json")["script"]
    assert script["path"] == SCRIPT
    overlay = checked(script["source"], script["sha256"])
    scripts = out / "scripts"
    cache = out / "cache"
    cache.mkdir(parents=True)
    for p in sorted(found):
        dest = scripts / p.relative_to(game)
        dest.parent.mkdir(parents=True, exist_ok=True)
        origin = overlay if p == game / SCRIPT else p
        shutil.copyfile(origin, dest)
        checked(dest, script["sha256"] if p == game / SCRIPT else pins[str(p)])
    for p in fixed:
        shutil.copyfile(p, cache / p.name)
        checked(cache / p.name, pins[str(p)])
    compile_paths = out / "compile_paths.txt"
    compile_paths.write_bytes(b"")
    output = cache / "compiled.redscripts"
    command = list(map(str, (exe, "-compile", scripts, "-compilePathsFile", compile_paths, "-customCacheDir",
                             cache, "-outputCacheFile", output, cache / "final.redscripts")))
    process = subprocess.run(command, capture_output=True, text=True, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    report = process.stdout + process.stderr
    (out / "scc.log").write_text(report, encoding="utf-8")
    for path, digest in pins.items():
        checked(path, digest)
    checked(log, log_sha)
    assert process.returncode == 0 and "Compilation complete" in report and output.is_file(), report[-6000:]
    write(out / "result.json", {"status": "PASS_CURRENT_INPUT_OFFLINE_COMPILE", "source_count": len(found),
                              "input_pins": pins, "runtime_log_sha256": log_sha, "command": command,
                              "candidate_script_sha256": script["sha256"], "output_sha256": sha(output)})
    print(f"Compiled with {len(found)} sources: {sha(output)}")


if __name__ == "__main__":
    main()
