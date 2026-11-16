"""Select new or changed graph members between the pinned QP2 registry and RD10."""

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "prealpha/quest_resume_registry_20261112_01/registry_02/registry.sqlite3"
RD10 = ROOT / "prealpha/resume_dispatcher_rd10_kirk_20261113_01"
OUT = Path(__file__).resolve().parent / "delta_input_01.json"
EXTENSIONS = (".quest", ".questphase", ".scene", ".journal", ".gamedef")


def sha(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest().upper()


def main():
    assert not OUT.exists()
    assert sha(REG) == "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9"
    db = sqlite3.connect(REG.resolve().as_uri() + "?mode=ro", uri=True)
    old = {depot.lower(): digest for depot, digest in db.execute(
        "SELECT depot,sha256 FROM resources WHERE role='PTFR'")}
    manifest_path = RD10 / "deployment_01/installed_manifest_01.json"
    readback_path = RD10 / "archive_01/readback.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    readback = json.loads(readback_path.read_text(encoding="utf-8-sig"))
    archive = Path(manifest["game_root"]) / "archive/pc/mod/zzzz_PTFR_Combined.archive"
    assert manifest["core_epoch"] == "RD10_MEET_KIRK_CONTENT_LOCK"
    assert sha(archive) == manifest["archive_sha256"] == readback["archive_sha256"]
    items = []
    for row in readback["members"]:
        depot = row["depot"]
        if not depot.lower().endswith(EXTENSIONS):
            continue
        previous = old.get(depot.lower())
        if previous == row["sha256"]:
            continue
        items.append({"depot": depot, "sha256": row["sha256"],
                      "prior_sha256": previous, "change": "NEW" if previous is None else "CHANGED"})
    assert len(items) == 18
    with OUT.open("x", encoding="utf-8", newline="\n") as file:
        json.dump({"archive": str(archive), "archive_sha256": sha(archive),
                   "manifest_sha256": sha(manifest_path), "readback_sha256": sha(readback_path),
                   "members": sorted(items, key=lambda row: row["depot"])}, file, indent=2)
        file.write("\n")
    print(f"Selected {len(items)} new or changed RD10 graph members")


if __name__ == "__main__":
    main()
