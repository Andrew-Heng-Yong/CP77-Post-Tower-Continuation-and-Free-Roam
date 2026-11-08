"""Validate report links/data, immutable evidence, and named runtime preservation."""
from pathlib import Path
import argparse
import collections
import csv
import datetime
import hashlib
import json
import re

H = Path(__file__).resolve().parent
Q = H.parent
W = H.parents[2]


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    out = H / a.output
    assert out.resolve().is_relative_to(H) and not out.exists(), "Fresh stage output required"
    checked = []

    def pin(p, expected):
        p = Path(p)
        actual = sha(p)
        assert actual == expected, (str(p), expected, actual)
        checked.append({"path": str(p), "sha256": actual})

    before = read(H / "runtime_pins_before.json")
    for r in before["files"]:
        pin(r["path"], r["sha256"])
    assert len(before["files"]) == 59
    readiness = Q / "readiness.json"
    pin(readiness, "7CE055438AE2ED27F99D468CBA32CECA03FB6EDF3216F596970DE2E0DAC1E4CD")
    for r in read(readiness)["artifacts"].values():
        pin(r["path"], r["sha256"])

    reports = ["deployment_01/completion.json",
        "observations/S00_20261102_01/completion.json",
        "observations/S00_20261102_01/confirmation_01/completion.json",
        "observations/S03_20261102_01/completion.json",
        "observations/WILSON_20261102_01/completion.json",
        "observations/WILSON_20261102_01/confirmation_01/completion.json",
        "observations/WILSON_RELOAD_20261102_01/completion.json",
        "observations/S05_20261102_01/completion.json",
        "observations/S05_20261102_02/completion.json",
        "observations/S05_20261102_02/shop_return_confirmation_01/completion.json"]
    for name in reports:
        d = read(Q / name)
        items = d.get("artifacts", [])
        if isinstance(items, dict):
            items = items.values()
        for r in items:
            pin(r["path"], r["sha256"])

    data = read(H / "results.json")
    original = data["observations"]
    additional = data["additional_observations"]
    coverage = read(H / "coverage.json")
    counts = dict(collections.Counter(r["status"] for r in original))
    assert counts == coverage["original_subcase_status_counts"]
    assert len(original) == coverage["original_subcases"] == 26
    assert len({(r["test_id"], r["variant"]) for r in original}) == 26
    assert len(additional) == coverage["functional_observation_rows"] == 9
    assert all(r["status"] == "PASS" for r in additional)
    assert "No gameplay has been executed" not in data["status_rule"]
    with (H / "results.csv").open(encoding="utf-8", newline="") as f:
        csv_rows = list(csv.DictReader(f))
    assert [(r["test_id"], r["variant"], r["status"]) for r in csv_rows] == [(r["test_id"], r["variant"], r["status"]) for r in original]
    with (H / "functional_results.csv").open(encoding="utf-8", newline="") as f:
        functional_csv = list(csv.DictReader(f))
    assert [json.loads(r["evidence_json"]) for r in functional_csv] == additional
    assert len({r["observation_key"] for r in functional_csv}) == len(additional)

    links = []
    for p in [Q / "report.md", H / "HANDOFF.md", W / "PROJECT.md", W / "ROADMAP.md", W / "docs/knowledge/current-state.md"]:
        for target in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
            if target.startswith(("http:", "https:", "#")):
                continue
            path = p.parent / target.strip("<>").split("#")[0]
            assert path.exists(), (str(p), target)
            links.append({"source": str(p), "target": target})
    for r in read(H / "docs_before.json"):
        pin(r["backup"], r["before_sha256"])

    out.mkdir()
    result = {"status": "PASS_REPORT_TRACEABILITY_DATA_AND_NAMED_RUNTIME_PRESERVATION",
        "verified_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "original_subcases": len(original), "original_status_counts": counts,
        "additional_functional_observations": len(additional), "json_csv_parity": True,
        "local_links_checked": len(links), "pin_checks_including_repeated_references": len(checked),
        "installed_runtime_payloads_unchanged": 53, "master_and_backup_files_unchanged": 6,
        "historical_evidence_pins_unchanged": True,
        "new_gameplay_or_engine_API_test": False, "runtime_source_edits": 0,
        "game_launches": 0, "save_or_fact_writes": 0, "builds_or_deployments": 0,
        "limits": "Named runtime/master hashes and linked evidence only. No new gameplay, API callback proof, full six-external-dependency check or whole-save-tree equality is claimed.",
        "checked_pins": checked, "links": links}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["status", "original_subcases", "additional_functional_observations", "local_links_checked", "installed_runtime_payloads_unchanged", "master_and_backup_files_unchanged"]}))


if __name__ == "__main__":
    main()
