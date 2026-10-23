"""Offline, filesystem-free regressions for the read-only P4 trace analyzer.

Synthetic records are not game observations. No installed logs, game files,
saves, package artifacts or Git state are accessed or modified by these tests.
"""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import analyze_phase2b_p4_explore as analyzer


FACTS = {
    "PostTowerFreeRoamActive": 1,
    "q307_active": 0,
    "q307_done": 1,
    "q307_finished": 1,
    "q307_2079": 1,
}


def row(seq, event="HEARTBEAT", *, run="run-A", load=1, elapsed=None,
        detail=None, state=None, errors=None):
    return {
        "schema": 1,
        "probe": "Phase2B-P4-explore",
        "run_id": run,
        "session_id": run + (f"/load-{load}" if load is not None else "/not-loaded"),
        "seq": seq,
        "elapsed_s": seq if elapsed is None else elapsed,
        "event": event,
        "detail": {} if detail is None else copy.deepcopy(detail),
        "state": {} if state is None else copy.deepcopy(state),
        "read_errors": {} if errors is None else copy.deepcopy(errors),
    }


def state(facts=None, rich=False):
    value = {"player_exists": True, "facts": dict(FACTS if facts is None else facts),
             "guard": {"passed": True}}
    if rich:
        value["systems"] = {"weather": {"preset": "UNKNOWN"}, "base_root_instances": "UNKNOWN"}
    return value


def ready_rows(run="run-A", load=1):
    return [
        row(1, "INIT", run=run, load=None,
            detail={"manual_only": True, "hooks_registered": True}),
        row(2, "PLAYER_ATTACHED", run=run, load=load),
        row(3, "BASELINE", run=run, load=load, state=state()),
        row(4, "PREFLIGHT", run=run, load=load, state=state(),
            detail={"baseline_ready": True, "target_check": {"passed": True, "failures": []}}),
        row(5, run=run, load=load, state=state()),
    ]


def parse_text(text):
    with patch.object(Path, "read_text", return_value=text):
        return analyzer.read_rows(Path("synthetic-p4-trace.jsonl"))


class TraceNormalizationTests(unittest.TestCase):
    def test_empty_lua_maps_are_normalized(self):
        record = row(1, detail=[], state=[], errors=[])
        rows, warnings = parse_text(json.dumps(record) + "\n")
        self.assertEqual(warnings, [])
        for key in ("detail", "state", "read_errors"):
            self.assertEqual(rows[0][key], {})
        self.assertEqual(analyzer.summarize(rows)["read_errors"], {})

    def test_empty_errors_do_not_break_readiness(self):
        records = ready_rows()
        for record in records:
            record["read_errors"] = []
        rows, _ = parse_text("\n".join(json.dumps(r) for r in records) + "\n")
        self.assertEqual(analyzer.readiness(rows, 1), [])

    def test_nonempty_maps_with_wrong_shape_are_rejected(self):
        for field, value in (("read_errors", ["not a map"]), ("state", "UNKNOWN"), ("detail", 4)):
            with self.subTest(field=field):
                record = row(1)
                record[field] = value
                with self.assertRaises(ValueError):
                    parse_text(json.dumps(record) + "\n")

    def test_unterminated_partial_final_line_is_ignored_with_warning(self):
        first = row(1, "INIT")
        rows, warnings = parse_text(json.dumps(first) + '\n{"schema":1,"probe":')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event"], "INIT")
        self.assertEqual(len(warnings), 1)
        self.assertIn("incomplete final line", warnings[0])
        report = analyzer.summarize(rows, warnings)
        self.assertEqual(report["warnings"], warnings)

    def test_completed_or_middle_invalid_json_is_not_silently_ignored(self):
        valid = json.dumps(row(1))
        for content in (valid + '\n{"broken":\n', '{"broken":\n' + valid + "\n"):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    parse_text(content)

    def test_no_complete_records_and_wrong_schema_are_rejected(self):
        for content in ('{"unfinished":', "\n", json.dumps({"schema": 1, "probe": "P0"}) + "\n"):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    parse_text(content)


class ReadinessTests(unittest.TestCase):
    def test_fresh_eligible_current_fixture_is_ready(self):
        self.assertEqual(analyzer.readiness(ready_rows(), 0), [])
        self.assertEqual(analyzer.readiness(ready_rows(), 30), [])

    def test_required_readiness_failures(self):
        variants = []
        records = ready_rows(); records[0]["detail"]["manual_only"] = False
        variants.append(("manual-only", records))
        records = ready_rows(); records[0]["detail"]["hooks_registered"] = False
        variants.append(("hooks", records))
        records = ready_rows(); records.pop(0)
        variants.append(("missing INIT", records))
        records = ready_rows(); records[3]["detail"]["baseline_ready"] = False
        variants.append(("baseline", records))
        records = ready_rows(); records[3]["state"]["guard"]["passed"] = False
        variants.append(("guard", records))
        records = ready_rows(); records[3]["detail"]["target_check"] = {"passed": False, "failures": ["floor unavailable"]}
        variants.append(("target floor", records))
        records = ready_rows(); records.pop(3)
        variants.append(("missing Inspect", records))
        records = ready_rows(); records[-1]["elapsed_s"] = 35
        variants.append(("old preflight", records))
        records = ready_rows(); records.append(row(6, "PLAYER_DETACH"))
        variants.append(("detach", records))
        records = ready_rows(); records.append(row(6, "SHUTDOWN"))
        variants.append(("shutdown", records))
        for label, records in variants:
            with self.subTest(label=label):
                self.assertTrue(analyzer.readiness(records, 1))
        self.assertTrue(analyzer.readiness(ready_rows(), 30.1))

    def test_previous_load_preflight_does_not_arm_new_load(self):
        records = ready_rows()
        records.extend([row(6, "PLAYER_DETACH"), row(7, "PLAYER_ATTACHED", load=2),
                        row(8, load=2, state=state())])
        failures = analyzer.readiness(records, 1)
        self.assertTrue(any("Inspect" in failure for failure in failures))

    def test_request_in_previous_load_blocks_retry_for_same_run(self):
        records = ready_rows()
        records.extend([row(6, "RELOCATION_REQUEST"), row(7, "PLAYER_DETACH"),
                        row(8, "PLAYER_ATTACHED", load=2),
                        row(9, "PREFLIGHT", load=2, state=state(),
                            detail={"baseline_ready": True, "target_check": {"passed": True}})])
        self.assertTrue(any("already requested" in failure for failure in analyzer.readiness(records, 1)))

    def test_old_process_shutdown_or_request_does_not_poison_latest_run(self):
        previous = ready_rows()
        previous.extend([row(6, "RELOCATION_REQUEST"), row(7, "SHUTDOWN")])
        newest = ready_rows("run-B")
        self.assertEqual(analyzer.current_run(previous + newest), newest)
        self.assertEqual(analyzer.readiness(previous + newest, 1), [])

    def test_duplicate_out_of_order_or_noninteger_sequence_is_rejected(self):
        for last in (4, 2, "5", None):
            records = ready_rows()
            records[-1]["seq"] = last
            with self.subTest(last=last):
                with self.assertRaises(ValueError):
                    analyzer.current_run(records)


class SummaryEvidenceTests(unittest.TestCase):
    def test_prior_observed_results_survive_optional_unknown_errors(self):
        records = ready_rows()
        records[0]["detail"]["prior_observed"] = {"pedestrians": "WORKING", "police": "WORKING", "weapons": "WORKING"}
        records.append(row(6, state=state(rich=True), errors={"weather.preset": "getter absent", "police.heat": "getter unavailable"}))
        report = analyzer.summarize(records)
        for system in ("pedestrians", "police", "weapons"):
            self.assertEqual(report["systems"][system]["status"], "WORKING")
            self.assertIn("Prior tester-observed", report["systems"][system]["basis"])
            self.assertIn("not a new current-run test", report["systems"][system]["basis"])
        for system in ("traffic", "phone", "vendors", "dogtown"):
            self.assertEqual(report["systems"][system]["status"], "UNKNOWN / NOT TESTED")
        self.assertEqual(report["read_errors"]["police.heat"]["count"], 1)
        self.assertEqual(report["current_active_quest_graph_instances"], "UNKNOWN")
        self.assertEqual(report["complete_world_streaming"], "UNKNOWN")

    def test_explicit_human_outcomes_and_errors_remain_distinct(self):
        records = ready_rows()
        records.extend([
            row(6, "HUMAN_REPORT", detail={"system": "vehicles", "status": "BROKEN", "note": "summon failed"}),
            row(7, "HUMAN_REPORT", detail={"system": "phone", "status": "UNKNOWN", "note": "not tried"}),
            row(8, "HUMAN_REPORT", detail={"system": "movement", "status": "WORKING", "note": "walked outside"}),
            row(9, errors={"phone.available": "unavailable"}),
        ])
        report = analyzer.summarize(records)
        self.assertEqual(report["systems"]["vehicles"]["status"], "BROKEN")
        self.assertEqual(report["systems"]["phone"]["status"], "UNKNOWN / NOT TESTED")
        self.assertEqual(report["systems"]["movement"]["status"], "WORKING")
        self.assertEqual(len(report["human_reports"]), 3)

    def test_request_and_void_native_return_are_not_arrival(self):
        records = ready_rows()
        records.extend([
            row(6, "RELOCATION_REQUEST", detail={"operation": "TeleportationFacility.Teleport ONLY"}),
            row(7, "RELOCATION_RETURNED", detail={"call_returned": True, "arrival_confirmed": False}),
            row(8, "ARRIVAL_SAMPLE", detail={"seconds_after_request": 2, "near_target": False}),
        ])
        report = analyzer.summarize(records)
        self.assertEqual(len(report["requests"]), 1)
        self.assertEqual(report["loaded_sessions"][0]["initial_arrival_evidence"], [])
        self.assertEqual(report["systems"]["ground"]["status"], "UNKNOWN / NOT TESTED")
        self.assertEqual(report["systems"]["movement"]["status"], "UNKNOWN / NOT TESTED")

    def test_local_support_evidence_does_not_certify_free_roam(self):
        records = ready_rows()
        records.append(row(6, "ARRIVAL_SAMPLE", detail={"milestone": 10, "near_target": True,
                           "initial_arrival_evidence": "SUPPORTED_TARGET_SAMPLES"}))
        report = analyzer.summarize(records)
        self.assertEqual(len(report["loaded_sessions"][0]["initial_arrival_evidence"]), 1)
        self.assertEqual(report["systems"]["vendors"]["status"], "UNKNOWN / NOT TESTED")
        self.assertEqual(report["systems"]["movement"]["status"], "UNKNOWN / NOT TESTED")

    def test_run_and_load_grouping_prevent_cross_fixture_fact_differences(self):
        old = [row(1, "RELOCATION_REQUEST", run="old", state=state({"q307_2079": 0}))]
        records = [row(1, "INIT", load=None), row(2, "BASELINE", load=1, state=state({"q307_2079": 1})),
                   row(3, "PLAYER_DETACH", load=1), row(4, "PLAYER_ATTACHED", load=2),
                   row(5, "BASELINE", load=2, state=state({"q307_2079": 0}))]
        report = analyzer.summarize(old + records)
        self.assertEqual(report["run_id"], "run-A")
        self.assertEqual(report["requests"], [])
        self.assertEqual([s["session"] for s in report["loaded_sessions"]], ["run-A/load-1", "run-A/load-2"])
        self.assertTrue(all(not s["fact_differences"] for s in report["loaded_sessions"]))

    def test_rich_to_cheap_snapshot_does_not_invent_missing_fact_changes(self):
        records = [row(1, "BASELINE", state=state({**FACTS, "radio_on": 0}, rich=True)),
                   row(2, state=state(FACTS))]
        summary = analyzer.summarize(records)["loaded_sessions"][0]
        self.assertEqual(summary["fact_differences"], {})
        self.assertEqual(summary["first_facts"]["radio_on"], 0)
        self.assertEqual(summary["last_facts"]["radio_on"], 0)
        self.assertTrue(summary.get("fact_comparison_scope"), "Per-fact, non-simultaneous comparison scope must be explicit")

    def test_actual_numeric_fact_change_is_reported_despite_sparse_snapshots(self):
        records = [row(1, "BASELINE", state=state({**FACTS, "radio_on": 0})),
                   row(2, state=state(FACTS)), row(3, state=state({**FACTS, "radio_on": 1})),
                   row(4, state=state({**FACTS, "radio_on": "UNKNOWN"}))]
        summary = analyzer.summarize(records)["loaded_sessions"][0]
        self.assertEqual(summary["first_facts"]["radio_on"], 0)
        self.assertEqual(summary["last_facts"]["radio_on"], 1)
        self.assertEqual(set(summary["fact_differences"]), {"radio_on"})
        self.assertEqual(summary["fact_differences"]["radio_on"]["before"], 0)
        self.assertEqual(summary["fact_differences"]["radio_on"]["after"], 1)
        self.assertIn("Not established", summary["fact_differences"]["radio_on"]["cause"])

    def test_each_fact_uses_first_and_last_readable_finite_number(self):
        records = [row(1, state=state({"a": "UNKNOWN", "b": False, "c": float("nan"), "d": float("inf")})),
                   row(2, state=state({"a": 0, "b": 1, "c": 3.0, "new_later": 9})),
                   row(3, state=state({"a": "bad", "b": True, "c": float("-inf"), "new_later": None})),
                   row(4, state=state({"a": 2})),
                   row(5, state=state({}))]
        summary = analyzer.summarize(records)["loaded_sessions"][0]
        self.assertEqual(summary["first_facts"], {"a": 0, "b": 1, "c": 3.0, "new_later": 9})
        self.assertEqual(summary["last_facts"], {"a": 2, "b": 1, "c": 3.0, "new_later": 9})
        self.assertEqual(set(summary["fact_differences"]), {"a"})

    def test_rich_snapshot_retention_is_bounded_without_discarding_comparison(self):
        records = [row(i, state=state({**FACTS, "extra": i}, rich=(i % 2 == 1))) for i in range(1, 8)]
        summary = analyzer.summarize(records)["loaded_sessions"][0]
        self.assertEqual([s["seq"] for s in summary["readable_system_snapshots"]], [1, 7])
        self.assertEqual(summary["first_facts"]["extra"], 1)
        self.assertEqual(summary["last_facts"]["extra"], 7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
