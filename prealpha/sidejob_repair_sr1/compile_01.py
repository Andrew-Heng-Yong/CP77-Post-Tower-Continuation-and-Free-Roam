"""Compile the full installed REDscript stack with the staged S29 correction."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

H = Path(__file__).resolve().parent
W = H.parent.parent
C = H / "candidate_02"
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
O = C / "compile_01"
assert not O.exists()
O.mkdir(parents=True)
S = O / "scripts"
cache = O / "cache"
cache.mkdir()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


inputs = {}
deferred = []
replacement = C / "source_scripts/r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds"
assert replacement.is_file()
replaced = 0
for name, root in [
    ("game", G / "r6/scripts"),
    ("Codeware", G / "red4ext/plugins/Codeware/Scripts"),
    ("ArchiveXL", G / "red4ext/plugins/ArchiveXL/Scripts"),
    ("TweakXL", G / "red4ext/plugins/TweakXL/Scripts"),
    ("mod_settings", G / "red4ext/plugins/mod_settings"),
]:
    for p in root.rglob("*.reds"):
        inputs[str(p)] = sha(p)
        src = replacement if p.name == "SideJobsS29.reds" and p.parent.name == "TowerContinued_SideJobs_S29" else p
        if src == replacement:
            replaced += 1
        dest = S / name / p.relative_to(root)
        if "EquipmentEx" in p.parts:
            deferred.append((src, dest))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
assert replaced == 1
for p in (G / "r6/cache").iterdir():
    if p.is_file():
        inputs[str(p)] = sha(p)
for name in ["final.redscripts", "final.redscripts.ts"]:
    shutil.copyfile(G / "r6/cache" / name, cache / name)
cli = W / "diagnostics/mod_updates_20261023_01/downloads/redscript-cli.exe"


def run(args, label):
    r = subprocess.run(list(map(str, args)), capture_output=True, text=True, timeout=240)
    log = r.stdout + r.stderr
    (O / (label + ".log")).write_text(log, encoding="utf-8")
    assert r.returncode == 0 and not re.search(r"(?m)^\[?ERROR\b", log), log[-9000:]
    assert "Output successfully saved" in log
    return log


run([cli, "compile", "-s", S, "-b", cache / "final.redscripts", "-o", cache / "cli.redscripts"], "cli")
for src, dest in deferred:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
paths = O / "compile_paths.txt"
paths.write_text("", encoding="utf-8")
log = run([G / "engine/tools/scc.exe", "-compile", S, "-compilePathsFile", paths, "-customCacheDir", cache, "-outputCacheFile", cache / "compiled.redscripts", cache / "final.redscripts"], "scc")
assert "Compilation complete" in log and "EquipmentEx.reds" in log
run([cli, "decompile", "-i", cache / "compiled.redscripts", "-o", O / "compiled.script"], "decompile")
text = (O / "compiled.script").read_text(encoding="utf-8-sig")
assert "AdoptS25DelamainPhone" in text
assert "PTFRS25_SQ025_FRESH_Finished" in text
assert "PTFR.SideJobsS29.SideJobsS29" in text
assert "EquipmentEx.OutfitSystem.GetInstance" in text
for p, h in inputs.items():
    assert sha(Path(p)) == h, p
report = {
    "status": "PASS_FULL_SCC_NOT_LIVE",
    "sources": len(list(S.rglob("*.reds"))),
    "full_scc_equipmentex": True,
    "replacement_sha256": sha(replacement),
    "compiled_sha256": sha(cache / "compiled.redscripts"),
    "input_hashes": inputs,
    "game_writes": 0,
    "save_writes": 0,
}
(O / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "input_hashes"}))
