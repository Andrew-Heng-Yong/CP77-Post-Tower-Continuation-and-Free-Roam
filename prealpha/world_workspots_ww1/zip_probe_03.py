"""Create a three-file optional probe archive, separate from production JC1."""
import hashlib
import json
import zipfile
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent.parent
P = H / "probe_03"
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
manifest = json.loads((P / "manifest_01.json").read_text(encoding="utf-8"))
compile_result = json.loads((P / "compile_01/result.json").read_text(encoding="utf-8"))
collisions = json.loads((P / "collisions_01.json").read_text(encoding="utf-8"))
baseline = json.loads((W / "prealpha/coaster_jean_jc1/candidate_01/manifest.json").read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


assert manifest["status"] == "ADDITIVE_CVI116_PROBE_STAGED_NOT_INSTALLED"
assert manifest["addon_paths"] == 3 and manifest["existing_ptfr_paths_replaced"] == 0
assert compile_result["status"] == "PASS" and compile_result["source_count"] == 65
assert not collisions["collisions"] and collisions["installed_archives"] >= 67
assert len(baseline["files"]) == 51
for row in baseline["files"]:
    assert sha(G / row["path"]) == row["sha256"], row["path"]
assert len(manifest["files"]) == 3
for row in manifest["files"]:
    assert sha(P / "package" / row["path"]) == row["sha256"]
    assert not (G / row["path"]).exists(), "Probe path already installed: " + row["path"]
assert not any(row["path"] in {b["path"] for b in baseline["files"]} for row in manifest["files"])

target = P / "Post-Tower-Continuation-and-Free-Roam-WW1-Scav-probe-unreleased.zip"
assert not target.exists(), "Preserve ZIP; make a successor"
with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for row in sorted(manifest["files"], key=lambda r: r["path"]):
        name = row["path"].replace("\\", "/")
        info = zipfile.ZipInfo(name, (2026, 10, 26, 18, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, (P / "package" / row["path"]).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == {r["path"] for r in manifest["files"]}
    for row in manifest["files"]:
        assert hashlib.sha256(z.read(row["path"])).hexdigest().upper() == row["sha256"]

receipt = {
    "status": "THREE_ADDITIVE_FILE_PROBE_ZIP_READY_NOT_INSTALLED",
    "zip": str(target.relative_to(W)), "sha256": sha(target),
    "files": manifest["files"], "original_jc1_installed_files_verified": 51,
    "installed_archive_collision_count": 0,
    "full_stack_script_compile": "PASS_65_SOURCES",
    "game_writes": 0, "save_writes": 0, "live_result": "UNPROVEN",
    "future_production_rule": "Fold approved fix into a complete 51-path JC1 successor; remove all prototype addon paths first",
}
proof = P / "zip_receipt_01.json"
assert not proof.exists()
proof.write_text(json.dumps(receipt, indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status": receipt["status"], "zip": receipt["zip"],
                  "sha256": receipt["sha256"], "files": len(receipt["files"]),
                  "baseline_verified": receipt["original_jc1_installed_files_verified"]},indent=2))
