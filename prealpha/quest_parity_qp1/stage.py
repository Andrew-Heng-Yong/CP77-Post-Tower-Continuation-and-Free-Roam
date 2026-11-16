"""Stage the verified JB3 inputs and carry forward the two reviewed fixes."""

import hashlib
import json
from pathlib import Path
import shutil
import stat

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
WS = PRE.parent
OUT = HERE / "candidate_01"
INSTALLED = PRE / "johnny_batch4_jb3/deployment_01/installed_manifest_01.json"
INSTALLED_SHA = "DB5E4119003F7E1BFDD6C1AB91AE9D186EB20380AFC69D61F1A889964EACC596"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
SCRIPT = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
LIPMAP = r"towercontinued\sidejob_repair_sr1\en-us.lipmap"
AUDIT = WS / "diagnostics/quest_animation_parity_20261110_01"
TRUCK = r"base\quest\minor_quests\mq017\scenes\mq017_streetkid_03_confront_thugs.scene"
PRIVATE_TRUCK = "towercontinued\\sidejobs_s29\\native\\" + TRUCK


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().upper()


def pinned(path, digest):
    path = Path(path)
    assert sha(path) == digest, path
    return path


def write(path, obj):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def plain(path):
    assert all(not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
               for p in (path, *path.parents)), path


def inventory(root, depots=False):
    rows = {}
    for p in root.rglob("*"):
        assert not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, p
        if p.is_file():
            name = p.relative_to(root).as_posix()
            rows[name.replace("/", "\\") if depots else name] = sha(p)
    return rows


def baseline():
    installed = read(pinned(INSTALLED, INSTALLED_SHA))
    assert installed["core_epoch"] == "JB3"
    assert len(installed["core_files"]) == 51 and len(installed["required_files"]) == 26
    game = Path(installed["game_root"])
    for row in installed["core_files"] + installed["required_files"]:
        p = game / row["path"]
        plain(p)
        pinned(p, row["sha256"])
    base = Path(installed["source_candidate"])
    base_manifest = pinned(base / "package_manifest.json", installed["package_manifest_sha256"])
    package = read(base_manifest)
    assert package["files"] == installed["core_files"]
    return installed, base, package


def rebase_bartmoss(base, prior_hash):
    prior = PRE / "quest_restoration_qr19/candidate_01/package" / SCRIPT
    prior = pinned(prior, "B64201D6F59327BD2BC2E7A71015DFB05245A66BCD7234F59DAD76D5588149D0")
    prior_text = prior.read_text(encoding="utf-8-sig")
    proposal = PRE / "quest_restoration_qr20/proposal_02" / Path(SCRIPT).name
    qr20 = pinned(proposal, "885ED18E546356A5507108D859A67BD5A64EFD6B44E3A4D05F0674DE3AD15125")
    after = qr20.read_text(encoding="utf-8-sig")
    start = "  private func RestoreMQ018MessageContact() -> Void {\n"
    anchor = "  private func Unclaimed(i: Int32) -> Bool {"
    tick = "    this.AdoptS25DelamainPhone();\n"
    call = "    this.RestoreMQ018MessageContact();\n"
    method = after[after.index(start):after.index(anchor)]
    assert after.replace(method, "", 1).replace(call, "", 1) == prior_text
    current = pinned(base / "package" / SCRIPT, prior_hash).read_bytes()
    newline = b"\r\n" if b"\r\n" in current else b"\n"
    method_b = method.encode().replace(b"\n", newline)
    tick_b = tick.encode().replace(b"\n", newline)
    call_b = call.encode().replace(b"\n", newline)
    anchor_b = anchor.encode()
    assert current.count(tick_b) == current.count(anchor_b) == 1
    assert method_b not in current and call_b not in current
    out = current.replace(tick_b, tick_b + call_b, 1).replace(anchor_b, method_b + anchor_b, 1)
    assert out.replace(method_b, b"", 1).replace(call_b, b"", 1) == current
    return out


def main():
    assert not OUT.exists(), "Fresh candidate required"
    installed, base, package = baseline()
    raw, files = base / "archive_source", base / "package"
    plain(raw)
    plain(files)
    assert inventory(raw, depots=True) == package["source_resources"]
    core = {r["path"]: r["sha256"] for r in installed["core_files"]}
    assert inventory(files) == core
    assert len(package["source_resources"]) == 1636

    staged = PRE / "monk_lipsync_ml1/candidate_01"
    monk = read(staged / "package_manifest.json")
    assert monk["status"] == "STAGED_ML1_READBACK_VERIFIED"
    assert monk["before_installed_manifest_sha256"] == INSTALLED_SHA
    assert monk["changed_depots"] == [LIPMAP]
    lipmap = pinned(staged / "archive_source" / LIPMAP, monk["after_map_sha256"])
    pinned(lipmap, "8CF46F202E58185AE366175C22BC72EE79623439F7010DDFC034BAEB0D96BE43")

    capture = read(AUDIT / "pass_01/capture.json")
    truck = {}
    for k, depot, is_stock in [("stock", TRUCK, True), ("before", PRIVATE_TRUCK, False)]:
        row, = [r for r in capture["providers"] if r["depot"] == depot]
        assert row["stock" if is_stock else "owned"]
        pinned(row["raw"], row["sha256"])
        pinned(row["json"], row["json_sha256"])
        truck[k] = row
    assert truck["before"]["sha256"] == package["source_resources"][PRIVATE_TRUCK]
    assert truck["stock"]["sha256"] == "06FE494FCE2C2CB270D5BD82DF0ED5BC567F4C6DE4AA1279C9C481E1F81DB7C2"
    script = rebase_bartmoss(base, core[SCRIPT])

    shutil.copytree(raw, OUT / "archive_source")
    shutil.copytree(files, OUT / "package")
    shutil.copyfile(lipmap, OUT / "archive_source" / LIPMAP)
    target = OUT / "package" / SCRIPT
    target.write_bytes(script)
    write(OUT / "inputs.json", {
        "baseline": "JB3", "installed_sha256": INSTALLED_SHA,
        "archive_sha256": installed["archive_sha256"], "truck": truck,
        "lipmap_sha256": sha(lipmap), "script_sha256": sha(target),
    })
    print(f"Staged 51 JB3 paths, the exact ML1 lip map and the QR20 script delta ({sha(target)}).")


if __name__ == "__main__":
    main()
