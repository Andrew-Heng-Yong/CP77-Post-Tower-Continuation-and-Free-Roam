"""Build a source-bound review ledger for the any-point quest resume contracts.

This is a read-only analysis of pinned databases and the RD10 installation. It
does not infer live ownership, feasible branches, paid rewards, or admission.
The output directory must be fresh so earlier evidence cannot be overwritten.
"""

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "prealpha/quest_resume_registry_20261112_01"
RD10 = ROOT / "prealpha/resume_dispatcher_rd10_kirk_20261113_01"
EXPECTED = {
    "registry": "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9",
    "contexts": "4E7F581B2F8AFA7AF25708602EF93AA1C0E4BC8B16FDE43A333E798792A661B7",
}
WHOLE_EXCEPTIONS = {
    "wst_ep1_05", "mq058_semimaru_crystalcoat",
    "wst_ep1_11_bill_meeting", "sts_ep1_08_steven_meeting_night_city",
}
BRANCH_EXCEPTIONS = {
    "sts_ep1_01": "Optional post-debrief Anderson replies and expiry",
    "sts_ep1_03": "Optional post-Rinder-debrief reply and expiry",
    "sts_ep1_04": "Optional debrief replies and expiry",
    "sts_ep1_07": "Optional debrief replies and expiry",
    "mq036_overload": "Gear-confiscation-to-recovery window",
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def db_open(path):
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def write_new(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = (Path(__file__).resolve().parent / args.out).resolve()
    assert out.parent == Path(__file__).resolve().parent and not out.exists()

    registry_path = REG / "registry_02/registry.sqlite3"
    contexts_path = REG / "contexts_01/contexts.sqlite3"
    assert digest(registry_path) == EXPECTED["registry"]
    assert digest(contexts_path) == EXPECTED["contexts"]
    manifest_path = RD10 / "deployment_01/installed_manifest_01.json"
    readback_path = RD10 / "archive_01/readback.json"
    manifest, readback = read(manifest_path), read(readback_path)
    assert manifest["core_epoch"] == "RD10_MEET_KIRK_CONTENT_LOCK"
    assert readback["archive_sha256"] == manifest["archive_sha256"]
    assert len(readback["members"]) == manifest["archive_payloads"] == 1748
    game_root = Path(manifest["game_root"])
    installed = manifest["core_files"] + manifest["required_files"]
    assert len(manifest["core_files"]) == 51 and len(manifest["required_files"]) == 26
    for item in installed:
        actual = game_root / item["path"]
        assert actual.is_file() and digest(actual) == item["sha256"], actual
    packed = {item["depot"].lower(): item["sha256"] for item in readback["members"]}
    assert len(packed) == 1748

    registry, contexts = db_open(registry_path), db_open(contexts_path)
    resources = {row["rid"]: dict(row) for row in registry.execute(
        "SELECT rid,depot,role,sha256,status,archive FROM resources")}
    selected = [dict(row) for row in registry.execute(
        "SELECT id,title,category,journal_root,record_json FROM quests WHERE selection='INCLUDE' ORDER BY id")]
    assert len(selected) == 160
    assert WHOLE_EXCEPTIONS <= {row["id"] for row in selected}
    assert BRANCH_EXCEPTIONS.keys() <= {row["id"] for row in selected}

    counts = Counter()
    rows = []
    changed_private = defaultdict(set)
    for quest in selected:
        qid = quest["id"]
        source_quest = json.loads(quest["record_json"])
        context_quest = json.loads(contexts.execute(
            "SELECT record_json FROM quests WHERE id=?", (qid,)).fetchone()[0])
        stages = []
        for raw in contexts.execute(
            "SELECT record_json FROM stages WHERE quest_id=? ORDER BY path", (qid,)):
            stage = json.loads(raw[0])
            providers = []
            locations = []
            reviewed_features = Counter()
            writer_inputs = set()
            root_ordinals = set()
            for rid, graph, node in stage["source_sites"]:
                source = resources[rid]
                site = json.loads(contexts.execute(
                    "SELECT record_json FROM sites WHERE rid=? AND graph=? AND node=?",
                    (rid, graph, node)).fetchone()[0])
                current_hash = packed.get(source["depot"].lower()) if source["role"] == "PTFR" else None
                state = ("PRIVATE_EXACT_RD10" if current_hash == source["sha256"] else
                         "PRIVATE_SOURCE_DRIFT" if source["role"] == "PTFR" else
                         "STOCK_CAPTURE_ONLY")
                if state == "PRIVATE_SOURCE_DRIFT":
                    changed_private[qid].add(source["depot"])
                providers.append({"rid": rid, "depot": source["depot"],
                                  "captured_sha256": source["sha256"],
                                  "rd10_sha256": current_hash, "state": state})
                if site["operation"] == "WRITE":
                    writer_inputs.update(site["journal_write_inputs"])
                root_ordinals.update(site["registered_root_ordinals"])
                for kind, relations in site["feature_relations"].items():
                    reviewed_features[kind] += sum(
                        relation["relation"] != "UNRELATED_LOCAL_BRANCH"
                        for relation in relations)
                locations.append({"rid": rid, "graph": graph, "node": node,
                                  "operation": site["operation"]})
            unique_providers = {row["rid"]: row for row in providers}
            blockers = []
            if not locations:
                blockers.append("NO_DECODED_STAGE_SITE")
            if any(row["state"] == "PRIVATE_SOURCE_DRIFT" for row in unique_providers.values()):
                blockers.append("RD10_PRIVATE_SOURCE_CHANGED_OR_NEW")
            if qid in WHOLE_EXCEPTIONS:
                disposition = "WHOLE_QUEST_MID_RESUME_EXCEPTION"
            else:
                disposition = "CONTRACT_REVIEW_REQUIRED"
                blockers += ["BRANCH_FEASIBILITY_NOT_PROVED",
                             "SAVED_OWNER_AND_SUPPORT_NOT_PROVED",
                             "ONE_TIME_RECEIPTS_NOT_PROVED"]
            stages.append({
                "path": stage["path"], "class": stage["class"],
                "disposition": disposition, "blockers": blockers,
                "source_sites": locations, "source_providers": list(unique_providers.values()),
                "journal_writer_input_names": sorted(writer_inputs),
                "source_reachable_registration_ordinals": sorted(root_ordinals),
                "local_feature_site_counts": dict(sorted(reviewed_features.items())),
                "context_lookup": [qid, stage["path"]],
                "contract_invariant": "Resume only from an ending-session checkpoint after original owner, branch, support and receipt proof; never reissue earlier setup or rewards.",
            })
            counts["selected_stage_paths"] += 1
            counts["stage_paths_with_private_drift"] += "RD10_PRIVATE_SOURCE_CHANGED_OR_NEW" in blockers
            counts["stage_paths_without_decoded_site"] += "NO_DECODED_STAGE_SITE" in blockers
        rows.append({
            "id": qid, "title": quest["title"], "category": quest["category"],
            "journal_root": quest["journal_root"],
            "whole_quest_mid_resume_exception": qid in WHOLE_EXCEPTIONS,
            "branch_exception": BRANCH_EXCEPTIONS.get(qid),
            "history_snapshot_index": context_quest["snapshot_index"],
            "source_registered_root_ordinals": context_quest["registered_handlers"],
            "old_source_owner_rids": {
                "stock": context_quest["native_source_owners"],
                "private": context_quest["private_source_owners"],
            },
            "qp2_snapshot_catalogue_row": source_quest.get("snapshot_index"),
            "stages": stages,
        })
    assert counts["selected_stage_paths"] == 1719
    counts["selected_quests"] = len(rows)
    counts["whole_quest_exceptions"] = len(WHOLE_EXCEPTIONS)
    counts["quest_branch_exceptions"] = len(BRANCH_EXCEPTIONS)
    counts["quests_with_private_stage_source_drift"] = len(changed_private)
    counts["runtime_qualified_exact_resume_contracts"] = 0

    out.mkdir()
    write_new(out / "summary.json", {
        "status": "SOURCE_REVIEW_LEDGER_NOT_SAFE_RESUME_CONTRACTS",
        "counts": dict(counts), "private_stage_source_drift": {
            qid: sorted(depots) for qid, depots in sorted(changed_private.items())},
        "inputs": {"registry_sha256": digest(registry_path),
                   "contexts_sha256": digest(contexts_path),
                   "rd10_manifest_sha256": digest(manifest_path),
                   "rd10_readback_sha256": digest(readback_path)},
        "limits": [
            "QP2 source routes do not include later RD10 private phases or source changes.",
            "Captured graph connectivity does not establish branch feasibility or saved owner liveness.",
            "Source reward and inventory locations do not establish paid/claimed receipts.",
            "The full base journal definition is opaque in the pinned WolvenKit decoder.",
            "No runtime admission, game, save, or installed file was changed.",
        ]})
    write_new(out / "quests.json", rows)
    print(json.dumps({"output": str(out), "counts": dict(counts)}, indent=2))


if __name__ == "__main__":
    main()
