"""Read printed CET snapshots for the Serial Suicide pilot; no game writes."""
import argparse
import hashlib
import json
import re
from pathlib import Path

TAG = "PTFR_CPZ01_AUDIT"
LINE = re.compile(r"^\[[^\]]+\] \[\d+\] (\{.*\})$")
ROOT = "quests/street_stories/city_center/corpo_plaza/sts_cct_cpz_01"
POI = "points_of_interest/street_stories/sts_cct_cpz_01"
TOWER = (
    "PostTowerFreeRoamActive", "q307_done", "q307_finished",
    "q307_2079", "q307_main_game_killed",
)


def classify(facts):
    values = [facts.get(name) for name in TOWER]
    if values == [0] * len(TOWER):
        return "PRE_TOWER_MARKERS"
    if values == [1] * len(TOWER):
        return "POST_TOWER_MARKERS"
    return "UNKNOWN_OR_MIXED_MARKERS"


def load(log):
    snapshots = []
    for number, line in enumerate(log.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
        match = LINE.match(line)
        if not match or TAG not in line:
            continue
        try:
            row = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if row.get("tag") != TAG:
            continue
        snapshots.append((number, row))
    return snapshots


def summarize(line, row):
    journal = row.get("journal", {})
    facts = row.get("facts", {})
    return {
        "line": line,
        "utc": row.get("utc"),
        "world": classify(facts),
        "revision": row.get("revision"),
        "journal_count": len(journal),
        "fact_count": len(facts),
        "error_count": len(row.get("errors", {})),
        "errors": row.get("errors", {}),
        "quest_state": journal.get(ROOT, {}).get("state"),
        "poi_state": journal.get(POI, {}).get("state"),
        "start": facts.get("cpz_01_start"),
        "finished": facts.get("cpz_01_finished"),
        "tier_1": facts.get("sts_cct_cpz_tier_1"),
        "player_present": row.get("player_before", {}).get("present") is True and
                          row.get("player_after", {}).get("present") is True,
        "journal_service": row.get("journal_service"),
        "quest_service": row.get("quest_service"),
        "same_player_during_read": row.get("player_before") == row.get("player_after"),
        "same_tracking_during_read": row.get("tracked_before") == row.get("tracked_after"),
        "delayed_before": row.get("delayed_before"),
        "delayed_after": row.get("delayed_after"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    snapshots = load(args.log)
    summary = [summarize(line, row) for line, row in snapshots]
    pre = next((row for row in reversed(summary) if row["world"] == "PRE_TOWER_MARKERS"), None)
    post = next((row for row in reversed(summary) if row["world"] == "POST_TOWER_MARKERS"), None)
    pair = [row for row in (pre, post) if row is not None]
    paired = (len(pair) == 2 and pre["line"] < post["line"] and
              all(row["revision"] == 1 and row["journal_count"] == 11 and
                  row["fact_count"] == 17 and row["error_count"] == 0 and
                  row["player_present"] and row["journal_service"] is True and
                  row["quest_service"] is True and row["delayed_before"] is False and
                  row["delayed_after"] is False and
                  row["same_player_during_read"] and row["same_tracking_during_read"]
                  for row in pair))
    report = {
        "status": "READ_ONLY_SNAPSHOTS_NOT_ACTIVATION_ADMISSION",
        "log_path": str(args.log.resolve()),
        "log_sha256_at_read": hashlib.sha256(args.log.read_bytes()).hexdigest().upper(),
        "snapshot_count": len(snapshots),
        "latest": summary[-2:],
        "selected_pair": pair,
        "clean_pre_post_pair": paired,
        "all_selected_journal_inactive": paired and all(
            all(entry.get("state") == 1 and entry.get("present") is True
                for entry in raw.get("journal", {}).values())
            for line, raw in snapshots if line in {pre["line"], post["line"]}
        ),
        "local_start_finish_zero": paired and all(
            row["start"] == 0 and row["finished"] == 0 for row in pair
        ),
        "normal_entry_eligibility": "UNTESTED_TIER_2_NOT_IN_PROBE",
        "note": "Tier 1 is not the Serial Suicide entry gate. The authored path requires Corpo Plaza tier 2 or a debug gate. Current facts and journal states do not prove unlock, pre-ending start history, device access, owner state, or reward safety."
    }
    if args.output:
        destination = args.output.resolve()
        research_root = (Path(__file__).resolve().parents[1] / "research/gig_restoration").resolve()
        destination.relative_to(research_root)
        if destination.exists() or destination.suffix.lower() != ".json":
            raise SystemExit("Choose a new JSON output under research/gig_restoration")
        report["selected_raw_snapshots"] = [raw for line, raw in snapshots
                                            if line in {row["line"] for row in pair}]
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "selected_raw_snapshots"}, indent=2))


if __name__ == "__main__":
    main()
