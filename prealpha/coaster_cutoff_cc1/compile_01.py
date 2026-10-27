"""Compile the complete current REDscript stack with CC1's replacement S29."""
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess

H = Path(__file__).resolve().parent
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
O = H / "candidate_01" / "compile_01"
assert not O.exists()
S, C = O / "scripts", O / "cache"
C.mkdir(parents=True)
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()
pins = {}
for name, root in (("game", G / "r6/scripts"), ("Codeware", G / "red4ext/plugins/Codeware/Scripts"), ("ArchiveXL", G / "red4ext/plugins/ArchiveXL/Scripts"), ("TweakXL", G / "red4ext/plugins/TweakXL/Scripts"), ("mod_settings", G / "red4ext/plugins/mod_settings")):
    for path in root.rglob("*.reds"):
        pins[str(path)] = digest(path)
        target = S / name / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
target = S / "game/PTFR_Consolidated/PTFR_SideJobsS29.reds"
assert target.exists()
replaced = digest(target)
candidate = H / "candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
shutil.copyfile(candidate, target)
for name in ("final.redscripts", "final.redscripts.ts"):
    shutil.copyfile(G / "r6/cache" / name, C / name)
paths = O / "compile_paths.txt"
paths.write_text("")
cmd = [G / "engine/tools/scc.exe", "-compile", S, "-compilePathsFile", paths, "-customCacheDir", C, "-outputCacheFile", C / "compiled.redscripts", C / "final.redscripts"]
result = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, timeout=300)
log = result.stdout + result.stderr
(O / "scc.log").write_text(log)
assert all(digest(Path(p)) == value for p, value in pins.items())
proof = {"status": "PASS" if result.returncode == 0 and "Compilation complete" in log else "FAIL", "exit_code": result.returncode, "source_count": len(list(S.rglob("*.reds"))), "candidate_sha256": digest(candidate), "replaced_sha256": replaced, "installed_source_hashes_unchanged": True, "game_writes": 0, "save_writes": 0, "log_tail": log[-2000:]}
(O / "result.json").write_text(json.dumps(proof, indent=2) + "\n")
print(json.dumps({k: proof[k] for k in ("status", "exit_code", "source_count", "candidate_sha256")}))
assert proof["status"] == "PASS"
