"""Offline parser fixtures only: passing these tests is not a game runtime test."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import analyze_phase2b_p2 as analyzer


def state(objective=2, phase=2, quest=2, locked=True):
    labels = {0: "Inactive", 1: "Undefined", 2: "Active", 3: "Succeeded", 4: "Failed"}
    def entry(name, value):
        return {"present": True, "id": name, "hash": 123, "state": labels.get(value, "UNKNOWN"),
                "state_value": value, "tracked": name == "05_take_walk"}
    return {"facts": dict(analyzer.GUARD_FACTS), "player_exists": True, "player_id": "1", "in_scene": False,
            "journal": {"objective": entry("05_take_walk", objective),
                        "phase": entry("02_mistys_alley", phase),
                        "quest": entry("q307_tomorrow", quest),
                        "tracked": entry("05_take_walk", objective), "hierarchy_verified": True},
            "door": {"id": analyzer.DOOR_ID, "expected_id": analyzer.DOOR_ID,
                     "full_noderef": analyzer.DOOR_REF, "identity_verified": True,
                     "controller_class": "DoorControllerPS", "controller_verified": True, "position": {"x": -1548, "y": 1221, "z": 12},
                     "device": {"IsLocked": locked, "IsSealed": False, "IsOpen": False,
                                "IsInteractive": True, "IsDisabled": False,
                                "type_interactive": True, "IsUnpowered": False,
                                "IsOFF": False, "IsBusy": False}},
            "guard": {"passed": True, "failures": []}}


def row(event, snapshot=None, stage="SYSTEM", seq=1, session="1", run="sample", detail=None):
    return {"schema": 1, "probe": analyzer.PROBE, "run_id": run, "session_id": session,
            "seq": seq, "utc": "2026-09-22T05:00:00Z", "elapsed_s": seq * 0.1,
            "frame": seq, "event": event, "stage": stage, "detail": detail or {},
            "state": copy.deepcopy(snapshot if snapshot is not None else state()), "read_errors": {}}


def ready_rows(session="1", run="sample"):
    return [row("INIT", session=session, run=run,
                detail={"mode": "WRITABLE_REPAIR_PROBE_MANUAL_TRIGGERS_ONLY", "hooks_registered": True}),
            row("SESSION_ATTACHED", session=session, run=run, seq=2),
            row("BASELINE", session=session, run=run, stage="INSPECT", seq=3),
            row("HEARTBEAT", session=session, run=run, seq=4)]


def stage_rows(stage="J", after=None):
    after = after if after is not None else state(objective=3, phase=3, quest=3)
    return [row("STAGE_BEFORE", stage=stage, seq=5),
            row("OPERATION_REQUESTED", stage=stage, seq=6, detail={"operation": "Succeeded" if stage == "J" else "ForceUnlock"}),
            row("OPERATION_RETURNED", stage=stage, seq=7, detail={"ok": True, "result": "UNKNOWN"}),
            row("STAGE_AFTER", after, stage=stage, seq=8),
            row("STABILITY_CHECK", after, stage=stage, seq=9, detail={"delay_s": 2}),
            row("STABILITY_CHECK", after, stage=stage, seq=10, detail={"delay_s": 10})]


class ParserTests(unittest.TestCase):
    def test_ready_before_repairs(self):
        self.assertEqual(analyzer.readiness_failures(ready_rows()), [])

    def test_invalid_needed_door_repair_gates_rejected(self):
        for gate in ("IsSealed", "IsOFF", "IsBusy", "IsDisabled", "IsUnpowered", "IsOpen"):
            rows = ready_rows()
            rows[-1]["state"]["door"]["device"][gate] = True
            self.assertTrue(analyzer.readiness_failures(rows), gate)
        for gate in ("IsInteractive", "type_interactive"):
            rows = ready_rows()
            rows[-1]["state"]["door"]["device"][gate] = False
            self.assertTrue(analyzer.readiness_failures(rows), gate)

    def test_journal_failed_or_unknown_not_ready(self):
        for value in (0, 4, "UNKNOWN"):
            rows = ready_rows()
            rows[-1]["state"]["journal"]["objective"]["state_value"] = value
            self.assertTrue(analyzer.readiness_failures(rows))

    def test_already_target_no_op_readiness(self):
        rows = ready_rows()
        for item in rows:
            item["state"] = state(objective=3, locked=False)
            item["state"]["door"]["device"]["IsSealed"] = True
        self.assertEqual(analyzer.readiness_failures(rows), [])
        stages = analyzer.stage_readiness(rows[-1]["state"])
        self.assertEqual(stages["J"]["mode"], "ALREADY_TARGET_NO_OP")
        self.assertEqual(stages["D"]["mode"], "ALREADY_TARGET_NO_OP")

    def test_scene_and_registration_verified_independently(self):
        rows = ready_rows()
        rows[0]["detail"]["hooks_registered"] = False
        self.assertTrue(analyzer.readiness_failures(rows))
        for value in (True, "UNKNOWN"):
            rows = ready_rows()
            rows[-1]["state"]["in_scene"] = value
            self.assertTrue(analyzer.readiness_failures(rows))

    def test_journal_success_is_observed_separately_from_request(self):
        report = analyzer.summarize(ready_rows() + stage_rows())
        attempt = report["journal_repair"]["attempts"][0]
        self.assertEqual(attempt["operation_requests"], 1)
        self.assertTrue(attempt["target_change_observed_after_request"])
        self.assertTrue(attempt["stable_at_10s"])
        self.assertFalse(attempt["other_issue_deltas"]["IsLocked"]["changed"])
        self.assertEqual(attempt["hud_updated"], "UNKNOWN")

    def test_parent_active_is_not_overclaimed(self):
        attempt = analyzer.summarize(ready_rows() + stage_rows(after=state(objective=3)))["journal_repair"]["attempts"][0]
        self.assertEqual(attempt["journal_after"]["quest"]["state_value"], 2)
        self.assertTrue(attempt["target_change_observed_after_request"])

    def test_return_ok_without_changed_state_is_not_success(self):
        attempt = analyzer.summarize(ready_rows() + stage_rows(after=state()))["journal_repair"]["attempts"][0]
        self.assertFalse(attempt["target_change_observed_after_request"])
        self.assertEqual(attempt["interpretation"], "TARGET_NOT_REACHED_IN_IMMEDIATE_SNAPSHOT")

    def test_no_request_cannot_label_operation_success(self):
        rows = ready_rows() + [row("STAGE_BEFORE", stage="J"), row("STAGE_AFTER", state(objective=3), stage="J")]
        attempt = analyzer.summarize(rows)["journal_repair"]["attempts"][0]
        self.assertEqual(attempt["interpretation"], "NO_OPERATION_REQUESTED")
        self.assertFalse(attempt["target_change_observed_after_request"])

    def test_already_target_is_not_new_repair(self):
        rows = ready_rows() + [row("STAGE_BEFORE", state(objective=3), stage="J"),
                               row("ALREADY_TARGET", state(objective=3), stage="J")]
        attempt = analyzer.summarize(rows)["journal_repair"]["attempts"][0]
        self.assertEqual(attempt["already_target_events"], 1)
        self.assertEqual(attempt["operation_requests"], 0)

    def test_door_unlock_is_not_human_exit(self):
        attempt = analyzer.summarize(ready_rows() + stage_rows("D", state(locked=False)))["door_repair"]["attempts"][0]
        self.assertTrue(attempt["target_change_observed_after_request"])
        for key in ("interaction_prompt_available", "normal_player_opening", "player_left_clinic"):
            self.assertEqual(attempt[key], "UNKNOWN")
        self.assertFalse(attempt["other_issue_deltas"]["objective"]["changed"])

    def test_exact_large_entity_id_required(self):
        rows = ready_rows()
        rows[-1]["state"]["door"]["id"] = 13806931541592989805
        self.assertTrue(analyzer.readiness_failures(rows))
        rows[-1]["state"]["door"]["id"] = "13806931541592989805ULL"
        self.assertTrue(analyzer.readiness_failures(rows))
        rows[-1]["state"]["door"]["id"] = "6805700156449448318"
        self.assertTrue(analyzer.readiness_failures(rows))

    def test_unknown_is_not_false_or_zero(self):
        after = state()
        after["door"]["device"]["IsLocked"] = "UNKNOWN"
        attempt = analyzer.summarize(ready_rows() + stage_rows("D", after))["door_repair"]["attempts"][0]
        self.assertEqual(attempt["target_after"], "UNKNOWN")
        self.assertFalse(attempt["target_change_observed_after_request"])

    def test_arrays_do_not_crash(self):
        rows = ready_rows() + stage_rows()
        for key in ("detail", "state", "read_errors"):
            rows[-1][key] = []
        result = analyzer.summarize(rows)
        self.assertEqual(result["journal_repair"]["attempts"][0]["delayed_checks"][-1]["target_reached"], "UNKNOWN")
        self.assertTrue(analyzer.readiness_failures(rows))

    def test_nested_arrays_do_not_crash(self):
        rows = ready_rows()
        rows[-1]["state"].update({"journal": [], "facts": [], "door": [], "guard": []})
        self.assertTrue(analyzer.readiness_failures(rows))
        analyzer.summarize(rows)

    def test_noncritical_read_errors_do_not_fail_ready(self):
        rows = ready_rows()
        rows[-1]["read_errors"] = {"optional_gate": "API unavailable"}
        self.assertEqual(analyzer.readiness_failures(rows), [])

    def test_stale_trace_not_ready(self):
        self.assertTrue(analyzer.readiness_failures(ready_rows(), 31))

    def test_detached_or_shutdown_not_ready(self):
        self.assertTrue(analyzer.readiness_failures(ready_rows() + [row("SESSION_DETACHED")]))
        self.assertTrue(analyzer.readiness_failures(ready_rows() + [row("SHUTDOWN")]))

    def test_new_session_cannot_reuse_old_baseline(self):
        rows = ready_rows() + stage_rows() + [row("SESSION_ATTACHED", session="2"), row("HEARTBEAT", session="2")]
        self.assertTrue(analyzer.readiness_failures(rows))
        report = analyzer.summarize(rows)
        self.assertEqual(report["session_id"], "1")
        self.assertFalse(report["selected_session_is_latest_record_session"])

    def test_cross_session_before_after_not_compared(self):
        rows = ready_rows() + stage_rows() + [row("BASELINE", session="2", stage="INSPECT"),
                                              row("STAGE_AFTER", state(objective=3), stage="J", session="2")]
        report = analyzer.summarize(rows)
        self.assertEqual(report["session_id"], "2")
        attempt = report["journal_repair"]["attempts"][0]
        self.assertEqual(attempt["operation_requests"], 0)
        self.assertFalse(attempt["target_change_observed_after_request"])

    def test_reload_baseline_preserves_original_j_and_d_reports(self):
        rows = ready_rows() + stage_rows() + stage_rows("D", state(locked=False))
        rows.extend([row("SESSION_DETACHED", session="1"),
                     row("SESSION_ATTACHED", state(objective=3, locked=False), session="2"),
                     row("BASELINE", state(objective=3, locked=False), stage="INSPECT", session="2")])
        report = analyzer.summarize(rows)
        self.assertEqual(report["session_id"], "2")
        self.assertEqual(report["journal_repair"]["attempts"], [])
        self.assertEqual(len(report["loaded_sessions"]), 2)
        original, reloaded = report["loaded_sessions"]
        self.assertEqual(original["session_id"], "1")
        self.assertTrue(original["journal_repair"]["attempts"][0]["target_change_observed_after_request"])
        self.assertTrue(original["door_repair"]["attempts"][0]["target_change_observed_after_request"])
        self.assertEqual(reloaded["session_id"], "2")
        self.assertEqual(reloaded["door_repair"]["attempts"], [])
        self.assertEqual(reloaded["baseline"]["journal"]["objective"]["state_value"], 3)
        self.assertNotIn("loaded_sessions", original)  # No recursive copies.

    def test_new_run_requires_own_init_and_baseline(self):
        rows = ready_rows() + stage_rows() + [row("SESSION_ATTACHED", run="new"), row("HEARTBEAT", run="new")]
        self.assertTrue(analyzer.readiness_failures(rows))

    def test_guard_failure_and_boolean_fact_rejected(self):
        for value in (0, "UNKNOWN", True):
            rows = ready_rows()
            rows[-1]["state"]["facts"]["q307_done"] = value
            self.assertTrue(analyzer.readiness_failures(rows))

    def test_fact_changes_and_other_issue_changes_reported(self):
        after = state(objective=3, locked=False)
        after["facts"]["q307_2079"] = 0
        report = analyzer.summarize(ready_rows() + stage_rows(after=after))
        attempt = report["journal_repair"]["attempts"][0]
        self.assertTrue(attempt["fact_deltas"]["q307_2079"]["changed"])
        self.assertTrue(attempt["other_issue_deltas"]["IsLocked"]["changed"])
        self.assertEqual(len(report["fact_history"]["q307_2079"]["changes"]), 1)

    def test_stability_failure_visible(self):
        rows = ready_rows() + stage_rows()
        rows[-1]["state"] = state()
        attempt = analyzer.summarize(rows)["journal_repair"]["attempts"][0]
        self.assertTrue(attempt["target_change_observed_after_request"])
        self.assertFalse(attempt["stable_at_10s"])

    def test_asynchronous_target_change_at_delayed_check(self):
        rows = ready_rows() + stage_rows("D", state(locked=False))
        rows[-3]["state"] = state()  # Queue returned before native operation applied.
        attempt = analyzer.summarize(rows)["door_repair"]["attempts"][0]
        self.assertFalse(attempt["target_after"])
        self.assertTrue(attempt["target_change_observed_after_request"])
        self.assertEqual(attempt["first_observed_target_seq"], 9)

    def test_reactivation_between_successful_samples_is_not_stable(self):
        rows = ready_rows() + stage_rows()
        rows[-2]["state"] = state()  # Active at 2 seconds, succeeded again at 10.
        attempt = analyzer.summarize(rows)["journal_repair"]["attempts"][0]
        self.assertTrue(attempt["stable_at_10s"])
        self.assertFalse(attempt["target_remained_true_in_later_samples"])

    def test_malformed_truncated_and_foreign_trace_lines(self):
        with tempfile.TemporaryDirectory(prefix="ptfr_p2_parser_") as tmp:
            path = Path(tmp) / "trace.jsonl"
            payload = "\n".join(json.dumps(r) for r in ready_rows())
            path.write_text(payload + '\n[]\n{\"probe\":\"Phase2B-P1-readonly\"}\n{\"truncated\":\n', encoding="utf-8")
            rows, diagnostics = analyzer.load_trace(path)
        self.assertEqual(len(rows), 4)
        self.assertEqual(diagnostics["malformed_lines"], 2)
        self.assertEqual(diagnostics["other_probe_lines"], 1)

    def test_empty_records_and_missing_fields(self):
        self.assertTrue(analyzer.readiness_failures([]))
        with self.assertRaises(ValueError):
            analyzer.summarize([])
        report = analyzer.summarize([{"probe": analyzer.PROBE}])
        self.assertEqual(report["run_id"], "UNKNOWN")


if __name__ == "__main__":
    print("OFFLINE SAMPLE-TRACE TESTS ONLY; not runtime or API validation.")
    unittest.main(verbosity=2)
