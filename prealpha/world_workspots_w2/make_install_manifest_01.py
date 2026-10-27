"""Pin exact 51-path successor and three temporary probe removals."""
from hashlib import sha256
from pathlib import Path
import json

H = Path(__file__).resolve().parent
W = H.parents[1]
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
old = W / "prealpha/coaster_jean_jc1/candidate_01/package"
new = H / "candidate_02/package"
probe = H.parent / "world_workspots_ww1/probe_05/package"
out = H / "candidate_02/install_manifest_01.json"
assert not out.exists(), "Preserve prior manifest"
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()
paths = sorted(p.relative_to(new).as_posix() for p in new.rglob("*") if p.is_file())
assert len(paths) == 51
assert paths == sorted(p.relative_to(old).as_posix() for p in old.rglob("*") if p.is_file())
expected_changed = {"archive/pc/mod/zzzz_PTFR_Combined.archive",
    "archive/pc/mod/zzzz_PTFR_Combined.archive.xl",
    "r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds"}
all_files = []
for rel in paths:
    before, after = digest(old / rel), digest(new / rel)
    assert digest(G / rel) == before, f"Installed production drift: {rel}"
    all_files.append({"path":rel,"before":before,"after":after})
assert {f["path"] for f in all_files if f["before"] != f["after"]} == expected_changed
probe_paths = sorted(p.relative_to(probe).as_posix() for p in probe.rglob("*") if p.is_file())
assert probe_paths == ["archive/pc/mod/zzzz_PTFR_WW1_Prototype.archive",
                       "archive/pc/mod/zzzz_PTFR_WW1_Prototype.archive.xl",
                       "r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds"]
retired = []
for rel in probe_paths:
    old_hash = digest(probe / rel)
    assert digest(G / rel) == old_hash, f"Installed probe drift: {rel}"
    retired.append({"path":rel,"before":old_hash})
proof_files = [
    H / "candidate_01/owner_proof_01.json",
    H / "candidate_02/graph_validation_01.json",
    H / "candidate_02/compile_01/result.json",
    H / "candidate_01/package_proof_01.json",
    H / "candidate_02/collisions_01.json",
    H / "manifest_02.json",
    H / "audit_02.json",
]
for path in proof_files: assert path.is_file(), path
proofs = [{"path":str(p),"sha256":digest(p)} for p in proof_files]
result = {"status":"W2_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED",
    "game_root":str(G),"backup_root":str(W / "recovery/world_workspots_w2_01"),
    "full_package_count":51,"changed_paths":3,"retired_probe_paths":3,
    "archive_members":1182,"new_owner_resources":10,"private_owners":206,
    "package_files":all_files,"retired":retired,"proofs":proofs,
    "live_scope":"One Pacifica group proven; 205 new owners source-audited and not live tested",
    "excluded":"Other combat-event and non-combat NPC families remain outside this package",
    "game_writes":0,"save_writes":0}
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
(out.with_suffix(out.suffix+".sha256")).write_text(digest(out)+"\n",encoding="ascii")
print(json.dumps({k:result[k] for k in ("status","full_package_count","changed_paths","retired_probe_paths","archive_members","private_owners")},indent=2))
