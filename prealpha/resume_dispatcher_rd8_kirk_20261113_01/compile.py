"""Compile the exact current registered source inventory with the RD8 overlay."""
import shutil
import subprocess
from prepare import HERE, RD5, SCRIPT, load_baseline, read, sha, write


def main():
    game, _, _ = load_baseline()
    old = read(RD5 / "compile_01/result.json")
    assert old["status"] == "PASS"
    scripts = {p.relative_to(game).as_posix() for root in ("r6/scripts", "red4ext/plugins")
               for p in (game / root).rglob("*.reds")}
    assert scripts == set(old["staged_hashes"])
    engine_inputs = set(old["input_pins"]) - scripts
    pins = {path: sha(game / path) for path in sorted(scripts | engine_inputs)}
    assert {k: pins[k] for k in scripts} == old["staged_hashes"]
    assert all(pins[k] == old["input_pins"][k] for k in engine_inputs if not k.endswith(".ts"))
    registry = game / "r6/logs/redscript_rCURRENT.log"
    registry_sha = sha(registry)
    log = registry.read_text(encoding="utf-8-sig", errors="replace")
    registered = {(game / "r6/scripts" / line.strip()).resolve() for line in log.splitlines()
                  if line.strip().lower().endswith(".reds")}
    assert "Compilation complete" in log and registered == {(game / path).resolve() for path in scripts}
    package = HERE / "candidate_01/package"
    output = HERE / "compile_01"
    assert not output.exists()
    assert sha(package / SCRIPT) == read(HERE / "evidence_01/inputs.json")["script_sha256"]
    (output / "cache").mkdir(parents=True)
    for name in ("final.redscripts", "final.redscripts.ts"):
        shutil.copyfile(game / "r6/cache" / name, output / "cache" / name)
    staged = {}
    for rel in sorted(scripts):
        target = output / "scripts" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(package / rel if rel == SCRIPT else game / rel, target)
        staged[rel] = sha(target)
    paths = output / "compile_paths.txt"
    paths.write_bytes(b"")
    compiled = output / "cache/compiled.redscripts"
    args = [game / "engine/tools/scc.exe", "-compile", output / "scripts", "-compilePathsFile", paths,
            "-customCacheDir", output / "cache", "-outputCacheFile", compiled, output / "cache/final.redscripts"]
    proc = subprocess.run(list(map(str, args)), capture_output=True, encoding="utf-8", errors="replace",
                          timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    log = proc.stdout + proc.stderr
    (output / "scc.log").write_text(log, encoding="utf-8")
    assert sha(registry) == registry_sha and all(sha(game / path) == digest for path, digest in pins.items())
    assert proc.returncode == 0 and "Compilation complete" in log and compiled.is_file(), log[-5000:]
    write(output / "result.json", {"status": "PASS", "source_count": len(staged), "input_pins": pins,
                                  "staged_hashes": staged, "compiled_sha256": sha(compiled),
                                  "registry_sha256": registry_sha})
    print(f"Offline compile passed for all {len(staged)} installed source paths.")


if __name__ == "__main__":
    main()
