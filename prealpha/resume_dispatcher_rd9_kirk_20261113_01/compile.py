"""Verify the staged REDscript against the exact current compiler inventory."""
import shutil
import subprocess
from prepare import HERE, RD8, PACKAGE, SCRIPT, baseline, read, sha, write
from pathlib import Path


def main():
    installed, _ = baseline()
    game = Path(installed["game_root"])
    prior = read(RD8 / "compile_01/result.json")
    log = game / "r6/logs/redscript_rCURRENT.log"
    log_hash = sha(log)
    registered_log = log.read_text(encoding="utf-8-sig", errors="replace")
    registered = {(game / "r6/scripts" / line.strip()).resolve() for line in registered_log.splitlines()
                  if line.strip().lower().endswith(".reds")}
    sources = {p.relative_to(game).as_posix() for root in ("r6/scripts", "red4ext/plugins")
               for p in (game / root).rglob("*.reds")}
    assert "Compilation complete" in registered_log and registered == {(game / path).resolve() for path in sources}
    assert sources == set(prior["staged_hashes"]) and len(sources) == 148
    pins = {rel: sha(game / rel) for rel in sorted(set(prior["input_pins"]) | sources)}
    assert {rel: pins[rel] for rel in sources} == prior["staged_hashes"]
    assert all(pins[rel] == digest for rel, digest in prior["input_pins"].items() if rel not in sources and not rel.endswith(".ts"))
    output = HERE / "compile_01"
    assert sha(PACKAGE / SCRIPT) == read(HERE / "evidence_01/inputs.json")["script_sha256"]
    (output / "cache").mkdir(parents=True, exist_ok=False)
    for name in ("final.redscripts", "final.redscripts.ts"):
        shutil.copyfile(game / "r6/cache" / name, output / "cache" / name)
    staged = {}
    for rel in sorted(sources):
        target = output / "scripts" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PACKAGE / rel if rel == SCRIPT else game / rel, target)
        staged[rel] = sha(target)
    paths = output / "compile_paths.txt"
    paths.write_bytes(b"")
    compiled = output / "cache/compiled.redscripts"
    args = [game / "engine/tools/scc.exe", "-compile", output / "scripts", "-compilePathsFile", paths,
            "-customCacheDir", output / "cache", "-outputCacheFile", compiled, output / "cache/final.redscripts"]
    proc = subprocess.run(list(map(str, args)), capture_output=True, encoding="utf-8", errors="replace",
                          timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    result = proc.stdout + proc.stderr
    (output / "scc.log").write_text(result, encoding="utf-8")
    assert sha(log) == log_hash and all(sha(game / rel) == digest for rel, digest in pins.items())
    assert proc.returncode == 0 and "Compilation complete" in result and compiled.is_file(), result[-5000:]
    write(output / "result.json", {"status": "PASS", "source_count": len(staged), "input_pins": pins,
                                  "staged_hashes": staged, "compiled_sha256": sha(compiled), "registry_sha256": log_hash})
    print(f"Offline compile passed for all {len(staged)} installed sources.")


if __name__ == "__main__":
    main()
