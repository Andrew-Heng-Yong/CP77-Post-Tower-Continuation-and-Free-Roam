"""Compile all installed scripts plus the separate WW1 prototype script."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

H = Path(__file__).resolve().parent
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
O = H / "probe_04/compile_01"
assert not O.exists(), "Compile evidence is immutable; use successor"
S, C = O / "scripts", O / "cache"
C.mkdir(parents=True)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


pins = {}
for name, root in [
    ("game", G / "r6/scripts"),
    ("Codeware", G / "red4ext/plugins/Codeware/Scripts"),
    ("ArchiveXL", G / "red4ext/plugins/ArchiveXL/Scripts"),
    ("TweakXL", G / "red4ext/plugins/TweakXL/Scripts"),
    ("mod_settings", G / "red4ext/plugins/mod_settings"),
]:
    for path in root.rglob("*.reds"):
        pins[str(path)] = sha(path)
        target = S / name / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)

candidate = H / "probe_04/package/r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds"
target = S / "game/PTFR_WW1_Prototype/WW1Probe.reds"
assert not target.exists()
target.parent.mkdir(parents=True)
shutil.copyfile(candidate, target)
for name in ("final.redscripts", "final.redscripts.ts"):
    shutil.copyfile(G / "r6/cache" / name, C / name)
paths = O / "compile_paths.txt"
paths.write_text("", encoding="utf-8")
cmd = [G / "engine/tools/scc.exe", "-compile", S, "-compilePathsFile", paths,
       "-customCacheDir", C, "-outputCacheFile", C / "compiled.redscripts", C / "final.redscripts"]
result = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, timeout=240)
log = result.stdout + result.stderr
(O / "scc.log").write_text(log, encoding="utf-8")
for path, digest in pins.items():
    assert sha(Path(path)) == digest, path
proof = {"status": "PASS" if result.returncode == 0 and "Compilation complete" in log else "FAIL",
         "exit_code": result.returncode, "source_count": len(list(S.rglob("*.reds"))),
         "candidate_script_sha256": sha(candidate),
         "compiled_sha256": sha(C / "compiled.redscripts") if (C / "compiled.redscripts").exists() else None,
         "installed_source_hashes_unchanged": True, "game_writes": 0, "save_writes": 0,
         "log_tail": log[-3000:]}
(O / "result.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
print(json.dumps(proof,indent=2))
assert proof["status"] == "PASS"
