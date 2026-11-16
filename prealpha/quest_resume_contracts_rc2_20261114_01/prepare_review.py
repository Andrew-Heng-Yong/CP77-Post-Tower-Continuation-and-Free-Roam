"""Select the exact RD10 provider inputs for Step 1. Writes only this workspace."""

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = HERE.parent / "quest_resume_registry_20261112_01"
PRIOR = HERE.parent / "quest_resume_contracts_rc1_20261114_01"
RD10 = HERE.parent / "resume_dispatcher_rd10_kirk_20261113_01"
EXTENSIONS = (".quest", ".questphase", ".scene", ".journal", ".gamedef")
ROOTS = (r"base\quest\cyberpunk2077.quest", r"ep1\quest\ep1.quest")
PINNED = {
    REG / "registry_02/registry.sqlite3": "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9",
    RD10 / "deployment_01/installed_manifest_01.json": "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8",
    RD10 / "archive_01/readback.json": "5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81",
}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, data):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def db_readonly(path):
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return closing(db)


def depot_key(depot):
    if depot.isdecimal():
        return depot
    key = 0xCBF29CE484222325
    for byte in depot.lower().replace("/", "\\").encode("utf-8"):
        key = ((key ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return str(key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-owner-map", type=int, metavar="ANALYSIS")
    args = parser.parse_args()
    target = HERE / ("inputs_02.json" if args.from_owner_map is not None else "inputs.json")
    if target.exists():
        raise FileExistsError(target)
    for path, expected in PINNED.items():
        if sha(path) != expected:
            raise ValueError(f"Input drift: {path}")
    manifest_path = RD10 / "deployment_01/installed_manifest_01.json"
    archive_readback = RD10 / "archive_01/readback.json"
    manifest = read(manifest_path)
    readback = read(archive_readback)
    installed = manifest["core_files"] + manifest["required_files"]
    if (manifest["core_epoch"], len(manifest["core_files"]), len(manifest["required_files"])) != (
        "RD10_MEET_KIRK_CONTENT_LOCK", 51, 26
    ):
        raise ValueError("RD10 baseline differs from the reviewed installation")
    if readback["archive_sha256"] != manifest["archive_sha256"]:
        raise ValueError("RD10 archive readback mismatch")
    for item in installed:
        path = Path(manifest["game_root"]) / item["path"]
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise ValueError(f"Installed baseline changed: {item['path']}")

    # Include the whole indexed source/registered-resource scope of selected
    # quests, plus their possible callers. Reverse calls are leads only.
    with db_readonly(REG / "registry_02/registry.sqlite3") as db:
        resources = [dict(row) for row in db.execute(
            "SELECT rid, depot, key, archive, sha256, role, status, root_type FROM resources")]
        by_rid = {row["rid"]: row for row in resources}
        seeds = {row[0] for row in db.execute("""
            SELECT DISTINCT rid FROM quest_resources
            JOIN quests ON quests.id=quest_resources.quest_id
            WHERE quests.selection='INCLUDE'
        """)}
        reverse = defaultdict(set)
        for rid, depot in db.execute("SELECT rid,target FROM calls"):
            reverse[depot_key(depot)].add(rid)
        scope = set(seeds)
        pending = list(seeds)
        while pending:
            for rid in reverse.get(by_rid[pending.pop()]["key"], ()):
                if rid not in scope:
                    pending.append(rid)
                    scope.add(rid)
        selected_quest_count = db.execute("SELECT count(*) FROM quests WHERE selection='INCLUDE'").fetchone()[0]
    assert selected_quest_count == 160

    watched = set(by_rid[rid]["key"] for rid in scope)
    watched.update(depot_key(path) for path in ROOTS)
    watched.update(row["key"] for row in resources if row["depot"].endswith(".journal"))
    # Include every distinct stock variant identified by the earlier census
    # even if it appears only in a separate activity.
    collisions = read(REG / "registry_02/summary.json")["provider_collisions"]
    watched.update(depot_key(row["depot"]) for row in collisions)
    current_members = [
        {"key": depot_key(row["depot"]), **row}
        for row in readback["members"] if row["depot"].endswith(EXTENSIONS)
    ]
    watched.update(row["key"] for row in current_members)
    new_names = set()
    if args.from_owner_map is not None:
        owner_map_path = HERE / f"analysis_{args.from_owner_map:02d}/owner_map.json"
        owner_map = read(owner_map_path)
        used = {site["scope"] for quest in owner_map["quests"] for stage in quest["stages"]
                for site in stage["sites"] if site["route"] in ("NATIVE", "INSTALLED_XL") and site["operation"] == "WRITE"}
        # Scopes are emitted after their parents. Follow the subtrees of
        # selected stage writers, while keeping unrelated world branches out.
        for row in owner_map["scopes"]:
            if row["parent"] in used:
                used.add(row["index"])
        new_names.update(row["target"] for row in owner_map["boundaries"]
                         if row["reason"] == "UNVERIFIED_PROVIDER" and row.get("parent") in used)
        new_names.update(row["binding"][field] for row in owner_map["xl_unbound"] for field in ("parent", "path"))
        watched.update(map(depot_key, new_names))
    expected = [row for row in resources if row["key"] in watched]
    depots = defaultdict(set)
    for row in expected + current_members:
        depots[row["key"]].add(row["depot"])
    for key, names in depots.items():
        if any(depot_key(name) != key for name in names):
            raise ValueError(f"Unexpected depot key alias: {key}")

    pins = {relative(path): digest for path, digest in PINNED.items()}
    if args.from_owner_map is not None:
        pins[relative(owner_map_path)] = sha(owner_map_path)
    write(target, {
        "core_epoch": manifest["core_epoch"], "game_root": manifest["game_root"],
        "verified_installed_files": len(installed), "installed": installed,
        "inputs": pins,
        "phase_roots": list(ROOTS), "watched_depots": len(watched),
        "seed_resources": len(seeds), "resources_with_callers": len(scope),
        "keys": sorted(watched, key=int), "qp2_providers": expected,
        "rd10_members": current_members, "prior_collisions": collisions,
        "scanned_without_known_provider": {
            name: depot_key(name) for name in sorted(new_names) if depot_key(name) not in depots
        },
    })
    print(f"Verified {len(installed)} RD10 files. Selected {len(watched)} depot keys.")


if __name__ == "__main__":
    main()
