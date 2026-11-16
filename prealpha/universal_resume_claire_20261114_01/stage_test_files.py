"""Assemble and read back the three-file local development payload."""

import argparse
import json
from pathlib import Path
import shutil
import zipfile

from verify_candidate import HERE, RD10, digest


def main():
    parser = argparse.ArgumentParser()
    for name in ("assessment", "archive", "attempt"):
        parser.add_argument("--" + name, required=True, type=int)
    args = parser.parse_args()
    out = HERE / f"candidate_{args.attempt:02}"
    proof = HERE / f"evidence_{args.assessment:02}/assessment.json"
    assessment = json.loads(proof.read_bytes())
    assert assessment["status"] == "WORKSPACE_CANDIDATE_CHECKED"
    archive = HERE / f"archive_{args.archive:02}"
    readback = json.loads((archive/"readback.json").read_bytes())
    assert readback["graph"] == assessment["graph"]
    assert readback["changed_payloads"] == assessment["archive_changes"]
    assert readback["members"] == 1749 and readback["unchanged"] == 1747
    script = assessment["script"]["changed_source"]
    plugin = "red4ext/plugins/PTFR_ClaireReply/PTFR_ClaireReply.dll"
    archive_path = "archive/pc/mod/zzzz_PTFR_Combined.archive"
    layout = {
        archive_path: (archive/"zzzz_PTFR_Combined.archive", readback["packed"]),
        script: (HERE/f"compile_{assessment['compile']:02}/scripts"/script,
                 assessment["script"]["source_sha256"]),
        plugin: (HERE/f"build_{assessment['build']:02}/PTFR_ClaireReply.dll",
                 assessment["native"]["build"]["dll_sha256"]),
    }
    baseline_file = RD10/"deployment_01/installed_manifest_01.json"
    assert digest(baseline_file) == assessment["script"]["manifest_sha256"]
    baseline = json.loads(baseline_file.read_bytes())
    game = Path(baseline["game_root"])
    original = {row["path"]: row["sha256"] for row in baseline["core_files"]}
    assert not (game/plugin).exists() and not (game/plugin).parent.exists()
    assert all(digest(game/rel) == original[rel] for rel in layout.keys() - {plugin})
    saved = Path(baseline["save_root"])/"ManualSave-26/sav.dat"
    save_digest = "6BEFAEE9EA1FA77A515C5A1EC9C867EA5B5DACB166D637D24B1423260E9C2AA4"
    assert digest(saved) == save_digest
    out.mkdir(exist_ok=False)
    paths = []
    package = out / "package"
    for rel, (src, expected) in layout.items():
        assert digest(src) == expected
        target = package/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        assert digest(target) == expected
        paths.append({"path":rel,"before_sha256":original.get(rel),"after_sha256":expected,
                      "bytes":target.stat().st_size})
    target = out/"PTFR_ClaireReply_test.zip"
    with zipfile.ZipFile(target,"x",compression=zipfile.ZIP_DEFLATED) as zip_file:
        for item in paths:
            zip_file.write(package/item["path"],item["path"])
    from hashlib import sha256
    with zipfile.ZipFile(target) as zip_file:
        assert zip_file.testzip() is None
        assert sorted(zip_file.namelist()) == sorted(layout)
        for item in paths:
            assert sha256(zip_file.read(item["path"])).hexdigest().upper() == item["after_sha256"]
    assert digest(saved) == save_digest
    result = {
        "status":"LOCAL_TEST_PAYLOAD_VERIFIED",
        "predecessor":"RD10_MEET_KIRK_CONTENT_LOCK",
        "predecessor_manifest_sha256":digest(baseline_file),
        "assessment_sha256":digest(proof),
        "archive_readback_sha256":digest(archive/"readback.json"),
        "manual_save_26_sha256":save_digest,
        "zip_sha256":digest(target),
        "files":paths,
        "installed":False,
        "gameplay_exercised":False,
    }
    (out/"manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Staged and verified three changes against the installed RD10 and Manual Save 26 hashes.")


if __name__ == "__main__":
    main()
