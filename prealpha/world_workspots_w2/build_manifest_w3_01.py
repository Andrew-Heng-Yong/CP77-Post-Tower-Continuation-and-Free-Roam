"""Pin the 51-path W3 successor and its read-only source evidence."""
from hashlib import sha256
from pathlib import Path
import json
import zipfile

H = Path(__file__).resolve().parent
W = H.parents[1]
C = H / "candidate_04"
P = C / "package"
old = json.loads((H / "candidate_02/install_manifest_01.json").read_text(encoding="utf-8"))
out = C / "install_manifest_01.json"
assert not out.exists(), "Preserve existing manifest"
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()
replacements = {
    "archive/pc/mod/zzzz_PTFR_Combined.archive",
    "archive/pc/mod/zzzz_PTFR_Combined.archive.xl",
    "r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds",
}
files = []
for f in old["package_files"]:
    path = f["path"]
    before = f["after"]
    assert digest(H / "candidate_02/package" / path) == before
    after = digest(P / path)
    assert (before != after) == (path in replacements), path
    files.append({"path": path, "before": before, "after": after})
assert len(files) == 51
assert len([x for x in P.rglob("*") if x.is_file()]) == 51

evidence = [
    H / "audit_03.json", H / "manifest_03.json", H / "candidate_03/graph_validation_01.json",
    C / "compile_01/result.json", C / "package_proof_01.json", C / "collisions_01.json",
]
assert all(p.is_file() for p in evidence)
m = {
    "status": "W3_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED",
    "game_root": old["game_root"],
    "backup_root": str(W / "recovery/world_workspots_w3_01"),
    "full_package_count": 51,
    "changed_paths": 3,
    "retired_probe_paths": 0,
    "archive_members": 1183,
    "private_owners": 237,
    "spawner_ids": 245,
    "package_files": files,
    "retired": [],
    "proofs": [{"path": str(p), "sha256": digest(p)} for p in evidence],
    "live_scope": "One Pacifica group user-confirmed; other generated owners await gameplay proof",
    "excluded": "Other combat-event and non-combat NPC families remain outside verified scope",
    "game_writes": 0,
    "save_writes": 0,
}
out.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
(Path(str(out) + ".sha256")).write_text(digest(out) + "\n", encoding="ascii")

dist = C / "dist"
dist.mkdir(exist_ok=False)
zip_path = dist / "Post-Tower-Continuation-and-Free-Roam-W3-unreleased.zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for f in files:
        z.write(P / f["path"], f["path"])
with zipfile.ZipFile(zip_path) as z:
    names = z.namelist()
    assert names == [f["path"] for f in files]
    assert all(sha256(z.read(f["path"])).hexdigest().upper() == f["after"] for f in files)
zip_proof = {
    "status": "UNRELEASED_FULL_51_PATH_ZIP_VERIFIED", "path": str(zip_path),
    "sha256": digest(zip_path), "members": 51, "public_release": False, "game_writes": 0,
}
zp = C / "zip_proof_01.json"
zp.write_text(json.dumps(zip_proof, indent=2) + "\n", encoding="utf-8")
Path(str(zp) + ".sha256").write_text(digest(zp) + "\n", encoding="ascii")
print(json.dumps({"manifest": digest(out), "zip": digest(zip_path), "paths": len(files)}))
