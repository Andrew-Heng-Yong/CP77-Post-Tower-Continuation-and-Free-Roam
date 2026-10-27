"""Pin complete JC1 baseline and WA1 gated-test replacement paths."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent.parent
B = W / "prealpha/coaster_jean_jc1/candidate_01"
P = H / "candidate_04"
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().upper()


old = {row["path"]: row["sha256"] for row in json.loads((B / "manifest.json").read_text())["files"]}
new = {row["path"]: row["sha256"] for row in json.loads((P / "manifest.json").read_text())["files"]}
assert len(old) == len(new) == 51 and old.keys() == new.keys()
for rel, digest in old.items():
    assert sha(G / rel) == digest, ("installed RC2 drift", rel)
for rel, digest in new.items():
    assert sha(P / "package" / rel) == digest, ("candidate drift", rel)
files = [{"target": rel, "before": old[rel], "after": new[rel]} for rel in sorted(old) if old[rel] != new[rel]]
assert {row["target"] for row in files} == {
    "archive/pc/mod/zzzz_PTFR_Combined.archive",
    "archive/pc/mod/zzzz_PTFR_Combined.archive.xl",
}
proof_rels = [
    "build_01.ps1",
    "compile_01.py",
    "compile_01/result.json",
    "verify_01.py",
    "validation_01.json",
    "deploy_01.ps1",
]
proofs = [{"path": str(H / rel), "sha256": sha(H / rel)} for rel in proof_rels]
manifest = {
    "status": "WA1_GATED_TEST_SUCCESSOR_STAGED",
    "game_root": str(G),
    "backup_root": str(W / "recovery/world_combat_wa1_01"),
    "files": files,
    "package_files": [{"path": rel, "before": old[rel], "after": new[rel]} for rel in sorted(old)],
    "proofs": proofs,
    "new_install_paths": 0,
    "removed_install_paths": 0,
    "resource_changes": 1,
    "live_result": "pending",
}
out = P / "install_manifest_01.json"
assert not out.exists(), out
out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(P / "install_manifest_01.json.sha256").write_text(sha(out) + "\n", encoding="utf-8")
print(json.dumps({"replaced_files": len(files), "full_package_files": 51, "manifest_sha256": sha(out)}))
