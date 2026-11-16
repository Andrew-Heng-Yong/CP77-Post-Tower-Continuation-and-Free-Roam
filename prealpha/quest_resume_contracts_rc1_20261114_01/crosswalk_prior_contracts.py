"""Index historical per-quest reviews without treating them as current resume proof."""

import hashlib
import json
import sqlite3
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "prealpha/quest_resume_registry_20261112_01/registry_02/registry.sqlite3"
OUT = HERE / "historical_contract_crosswalk_01.json"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def main():
    assert not OUT.exists()
    assert sha(REG) == "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9"
    db = sqlite3.connect(REG.resolve().as_uri() + "?mode=ro", uri=True)
    selected = {row[0] for row in db.execute("SELECT id FROM quests WHERE selection='INCLUDE'")}
    found = subprocess.run(["rg", "--files", "prealpha", "-g", "contracts.json"],
                           cwd=ROOT, capture_output=True, text=True, check=True)
    by_quest = defaultdict(list)
    for relative in found.stdout.splitlines():
        if "/quests/" not in relative.replace("\\", "/"):
            continue
        path = ROOT / relative
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        qid = data.get("quest_id")
        if qid not in selected:
            continue
        sections = {key: {"status": section.get("status"),
                          "remaining_count": len(section.get("remaining", []))}
                    for key, section in data.get("contracts", {}).items()
                    if isinstance(section, dict)}
        by_quest[qid].append({"path": relative.replace("\\", "/"), "sha256": sha(path),
                              "source_epoch": data.get("source_epoch"),
                              "status": data.get("status"),
                              "fully_static_verified": data.get("fully_static_verified"),
                              "effective_resource": data.get("effective_resource"),
                              "effective_resource_sha256": data.get("effective_resource_sha256"),
                              "sections": sections})
    assert len(by_quest) == len(selected) == 160
    assert sum(map(len, by_quest.values())) == 165 or sum(map(len, by_quest.values())) == 166
    counts = Counter()
    for qid, records in by_quest.items():
        counts["historical_contract_files"] += len(records)
        counts["quests_with_multiple_historical_reviews"] += len(records) > 1
        counts["quests_with_any_historical_fail_section"] += any(
            section["status"] == "FAIL" for record in records for section in record["sections"].values())
        counts["quests_with_any_historical_unknown_or_opaque_section"] += any(
            section["status"] in ("UNKNOWN", "OPAQUE")
            for record in records for section in record["sections"].values())
    result = {"status": "HISTORICAL_ENTRY_PARITY_EVIDENCE_NOT_MID_QUEST_RESUME_PROOF",
              "selected_quests": len(selected), "counts": dict(counts),
              "quests": {qid: sorted(records, key=lambda row: row["path"])
                         for qid, records in sorted(by_quest.items())},
              "limits": ["Historical contracts were authored for fresh entry and parity, not arbitrary saved handler continuation.",
                         "Multiple historical reviews are retained without selecting one by directory date.",
                         "PASS and APPROVED_DEVIATION are bounded to the cited source epoch."]}
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"selected_quests": len(selected), **dict(counts)}))


if __name__ == "__main__":
    main()
