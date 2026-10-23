"""Check the next read-only CET gig probe against a mutation-trapping mock."""
from pathlib import Path

from test_serial_suicide_probe import run

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "research/gig_restoration/race_to_top_console.lua"


def main():
    assert len(PROBE.read_text(encoding="utf-8").splitlines()) == 1
    report, runtime = run(source_path=PROBE)
    assert report["tag"] == "PTFR_ARR03_AUDIT"
    assert len(report["facts"]) == 9
    assert len(report["journal"]) == 8
    assert report["errors"] == {}
    assert len(runtime.globals().mutations) == 0
    assert report["journal"]["quests/street_stories/santo_domingo/arroyo/sts_std_arr_03"]["state"] == 1
    print("Race to the Top CET probe: one-line, nine facts, eight journal paths, read-only mock PASS")


if __name__ == "__main__":
    main()
