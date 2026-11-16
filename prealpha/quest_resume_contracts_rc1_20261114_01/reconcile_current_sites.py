"""Overlay exact RD10 graph deltas on the QP2 stage source index."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
OLD = HERE / "evidence_01/quests.json"
DELTA = HERE / "delta_analysis_01.json"
OUT = HERE / "current_stage_index_01.json"
SUMMARY = HERE / "reconcile_summary_01.json"
STAGE_CLASSES = {"gameJournalQuestPhase", "gameJournalQuestObjective"}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def write_new(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    assert not OUT.exists() and not SUMMARY.exists()
    quests = json.loads(OLD.read_text(encoding="utf-8"))
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    assert len(quests) == 160 and len(delta["resources"]) == 18
    changed = {row["depot"].lower() for row in delta["resources"] if row["change"] == "CHANGED"}
    overlay = defaultdict(list)
    for resource in delta["resources"]:
        for graph in resource["graphs"]:
            for site in graph["journal_sites"]:
                if site["class"] not in STAGE_CLASSES:
                    continue
                for qid in site["selected_quests"]:
                    overlay[qid, site["path"]].append({
                        "depot": resource["depot"], "sha256": resource["raw_sha256"],
                        "graph": graph["graph"], "node": site["node"],
                        "operation": site["operation"], "source": "RD10_EXACT_GRAPH_DELTA"})
    result, counts = [], Counter()
    used = set()
    for quest in quests:
        stage_rows = []
        for stage in quest["stages"]:
            key = (quest["id"], stage["path"])
            used.add(key)
            by_rid = {row["rid"]: row for row in stage["source_providers"]}
            current = []
            superseded = []
            for site in stage["source_sites"]:
                provider = by_rid[site["rid"]]
                record = {"depot": provider["depot"],
                          "sha256": provider["captured_sha256"],
                          "graph": site["graph"], "node": site["node"],
                          "operation": site["operation"],
                          "source": "QP2_EXACT_PRIVATE" if provider["state"] == "PRIVATE_EXACT_RD10"
                          else "QP2_STOCK_CAPTURE"}
                if provider["depot"].lower() in changed:
                    superseded.append(record)
                else:
                    current.append(record)
            current.extend(overlay.get(key, ()))
            dedup = {(x["depot"], x["sha256"], x["graph"], x["node"], x["operation"]): x
                     for x in current}
            current = sorted(dedup.values(), key=lambda x: (x["depot"], x["graph"], x["node"], x["operation"]))
            counts["stage_paths"] += 1
            counts["stage_paths_with_rd10_delta_sites"] += bool(overlay.get(key))
            counts["stage_paths_with_superseded_sites"] += bool(superseded)
            counts["stage_paths_without_source_sites"] += not current
            stage_rows.append({"path": stage["path"], "class": stage["class"],
                               "disposition": stage["disposition"],
                               "current_source_sites": current,
                               "superseded_qp2_sites": superseded,
                               "source_context": stage["context_lookup"],
                               "semantic_contract_status": "UNREVIEWED",
                               "runtime_owner_status": "UNQUALIFIED"})
        for key in sorted(k for k in overlay if k[0] == quest["id"] and k not in used):
            sites = overlay[key]
            counts["new_rd10_stage_references"] += 1
            stage_rows.append({"path": key[1], "class": "gameJournalQuestObjective",
                               "disposition": "NEW_RD10_STAGE_REFERENCE_UNREVIEWED",
                               "current_source_sites": sites,
                               "superseded_qp2_sites": [], "source_context": None,
                               "semantic_contract_status": "UNREVIEWED",
                               "runtime_owner_status": "UNQUALIFIED"})
        result.append({"id": quest["id"], "title": quest["title"],
                       "whole_quest_mid_resume_exception": quest["whole_quest_mid_resume_exception"],
                       "branch_exception": quest["branch_exception"],
                       "stages": stage_rows})
    assert counts["stage_paths"] == 1719 and counts["new_rd10_stage_references"] == 1
    assert len(result) == 160
    write_new(OUT, result)
    write_new(SUMMARY, {"status": "CURRENT_SOURCE_SITE_INDEX_NOT_RESUME_CONTRACTS",
                        "counts": dict(counts),
                        "inputs": {"old_ledger_sha256": sha(OLD), "delta_analysis_sha256": sha(DELTA)},
                        "new_stage_reference": ["sts_wat_nid_05",
                          "quests/street_stories/watson/northside_industrial_district/sts_wat_nid_05/sts_wat_nid_05/escape_clinic"],
                        "limits": [
                          "The stock source sites are from the QP2 capture, not a new exact RD10 extraction.",
                          "The overlay does not classify viable branch combinations, active owner or paid receipts.",
                          "A journal reference does not establish execution or an available continuation entry."]})
    print(json.dumps(dict(counts), indent=2))


if __name__ == "__main__":
    main()
