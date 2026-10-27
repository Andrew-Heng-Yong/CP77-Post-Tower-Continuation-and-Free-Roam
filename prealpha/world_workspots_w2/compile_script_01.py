"""Compile W2 as a 51-file successor, excluding the additive WW1 script."""
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
OUT = HERE / "candidate_01/compile_01"
assert not OUT.exists(), "Preserve compile evidence"
S, C = OUT / "scripts", OUT / "cache"
C.mkdir(parents=True)
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()
pins = {}
for name, root in (("game", GAME / "r6/scripts"),
                   ("Codeware", GAME / "red4ext/plugins/Codeware/Scripts"),
                   ("ArchiveXL", GAME / "red4ext/plugins/ArchiveXL/Scripts"),
                   ("TweakXL", GAME / "red4ext/plugins/TweakXL/Scripts"),
                   ("mod_settings", GAME / "red4ext/plugins/mod_settings")):
    for path in root.rglob("*.reds"):
        pins[str(path)] = digest(path)
        target = S / name / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
probe = S / "game/PTFR_WW1_Prototype/WW1Probe.reds"
assert probe.exists() and digest(probe) == "53923E0F1E1F6A760ABFA3FF6278B50B5882A4B51A2394DE4764038ACB68D8EB"
probe.unlink()
candidate = HERE / "candidate_01/script_source/PTFR_RestorationBaseline.reds"
target = S / "game/PTFR_Consolidated/PTFR_RestorationBaseline.reds"
assert target.exists()
replaced = digest(target)
shutil.copyfile(candidate, target)
for name in ("final.redscripts", "final.redscripts.ts"):
    shutil.copyfile(GAME / "r6/cache" / name, C / name)
paths = OUT / "compile_paths.txt"
paths.write_text("", encoding="utf-8")
cmd = [GAME / "engine/tools/scc.exe", "-compile", S, "-compilePathsFile", paths,
       "-customCacheDir", C, "-outputCacheFile", C / "compiled.redscripts", C / "final.redscripts"]
result = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, timeout=300)
log = result.stdout + result.stderr
(OUT / "scc.log").write_text(log, encoding="utf-8")
assert all(digest(Path(p)) == h for p, h in pins.items())
proof = {"status": "PASS" if result.returncode == 0 and "Compilation complete" in log else "FAIL",
         "exit_code": result.returncode, "source_count": len(list(S.rglob("*.reds"))),
         "candidate_sha256": digest(candidate), "replaced_sha256": replaced,
         "compiled_sha256": digest(C / "compiled.redscripts") if (C / "compiled.redscripts").exists() else None,
         "installed_source_hashes_unchanged": True, "game_writes": 0, "save_writes": 0,
         "log_tail": log[-3500:]}
(OUT / "result.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps(proof, indent=2))
assert proof["status"] == "PASS"
