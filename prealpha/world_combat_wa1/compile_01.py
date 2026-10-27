"""Compile the complete installed stack against the WA1 candidate scripts."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent.parent
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
P = H / "candidate_04/package"
O = H / "compile_01"
assert not O.exists(), O
S = O / "scripts"
C = O / "cache"
C.mkdir(parents=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


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
        dest = S / name / path.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)

for staged in (P / "r6/scripts/PTFR_Consolidated").glob("*.reds"):
    assert sha(staged) == sha(G / "r6/scripts/PTFR_Consolidated" / staged.name), staged

for name in ("final.redscripts", "final.redscripts.ts"):
    shutil.copyfile(G / "r6/cache" / name, C / name)
paths = O / "compile_paths.txt"
paths.write_text("", encoding="utf-8")
command = [
    G / "engine/tools/scc.exe",
    "-compile",
    S,
    "-compilePathsFile",
    paths,
    "-customCacheDir",
    C,
    "-outputCacheFile",
    C / "compiled.redscripts",
    C / "final.redscripts",
]
result = subprocess.run(list(map(str, command)), capture_output=True, text=True, timeout=240)
log = result.stdout + result.stderr
(O / "scc.log").write_text(log, encoding="utf-8")
for path, digest in pins.items():
    assert sha(Path(path)) == digest, path
proof = {
    "status": "PASS" if result.returncode == 0 and "Compilation complete" in log else "FAIL",
    "source_count": len(list(S.rglob("*.reds"))),
    "exit_code": result.returncode,
    "tail": log[-2000:],
    "compiled_sha256": sha(C / "compiled.redscripts") if (C / "compiled.redscripts").exists() else None,
    "game_writes": 0,
    "save_writes": 0,
}
(O / "result.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps(proof))
assert proof["status"] == "PASS"
