"""Offline independent collection fixtures. All synthetic game/save trees stay in QR9."""
from pathlib import Path
import copy
import importlib.util
import json
import unittest
import datetime

H = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("collector", H / "collect_observation.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
LOG = "QR9_capture_20261031T230000Z_0001.jsonl"
SUITE = H / "collector_fixtures" / datetime.datetime.now(datetime.timezone.utc).strftime("suite_%Y%m%dT%H%M%S_%f")


def capture(events=None):
    events = events or ["CAPTURE_START", "ATTACHED_BASELINE", "LISTENER_CALLS_COMPLETED", "FACT_DELIVERY", "STOP", "LISTENER_CLEANUP_CALLS"]
    rows = []
    for i, e in enumerate(events, 1):
        rows.append({"schema": 1, "module": c.MODULE, "run_id": LOG, "seq": i,
                     "utc": "2026-10-31T23:00:00Z", "profile": "S00", "event": e,
                     "data": {"failures": 0, "fact": "plugin_receipt", "value": 1}})
    return ("\n".join(json.dumps(r) for r in rows) + "\n").encode()


class CollectionTests(unittest.TestCase):
    def test_valid_never_implies_gameplay_or_execution(self):
        r = c.analyze_capture(capture(), LOG, "S00")
        self.assertEqual(r["capture_integrity"], "VALID_CAPTURE")
        self.assertEqual(r["gameplay_result"], "NOT_TESTED")
        self.assertEqual(set(r["unsupported"].values()), {"NOT_OBSERVED"})

    def test_missing_cleanup_mutant(self):
        r = c.analyze_capture(capture(["CAPTURE_START", "ATTACHED_BASELINE", "LISTENER_CALLS_COMPLETED", "STOP"]), LOG, "S00")
        self.assertNotEqual(r["capture_integrity"], "VALID_CAPTURE")

    def test_each_independent_corruption(self):
        base = [json.loads(line) for line in capture().splitlines()]
        for mutation in ["seq", "schema", "identity", "profile", "cleanup", "data", "cleanup_data", "event", "bool_schema", "bool_seq", "nan"]:
            with self.subTest(mutation=mutation):
                rows = copy.deepcopy(base)
                if mutation == "seq": rows[2]["seq"] = 5
                if mutation == "schema": rows[2]["schema"] = 2
                if mutation == "identity": rows[2]["run_id"] = "other"
                if mutation == "profile": rows[2]["profile"] = "S02"
                if mutation == "cleanup": rows[-1]["data"]["failures"] = 1
                if mutation == "data": rows[1]["data"] = []
                if mutation == "cleanup_data": rows[-1]["data"] = []
                if mutation == "event": rows[1]["event"] = []
                if mutation == "bool_schema": rows[0]["schema"] = True
                if mutation == "bool_seq": rows[0]["seq"] = True
                if mutation == "nan": rows[0]["wall_elapsed_s"] = float("nan")
                data = ("\n".join(json.dumps(r) for r in rows) + "\n").encode()
                self.assertNotEqual(c.analyze_capture(data, LOG, "S00")["capture_integrity"], "VALID_CAPTURE")

    def test_truncated_duplicate_and_large_rows(self):
        for blob in [capture()[:-8], b'{"schema":1,"schema":2}\n', b"x" * 131073 + b"\n", capture() * 350]:
            self.assertNotEqual(c.analyze_capture(blob, LOG, "S00")["capture_integrity"], "VALID_CAPTURE")

    def test_late_error_or_missing_attach(self):
        for events in [["CAPTURE_START", "STOP", "LISTENER_CLEANUP_CALLS"],
                       ["CAPTURE_START", "ATTACHED_BASELINE", "LISTENER_CALLS_COMPLETED", "API_UNAVAILABLE", "STOP", "LISTENER_CLEANUP_CALLS"],
                       ["CAPTURE_START", "ATTACHED_BASELINE", "LISTENER_CALLS_COMPLETED", "STOP", "LISTENER_CLEANUP_CALLS", "FACT_DELIVERY"]]:
            self.assertNotEqual(c.analyze_capture(capture(events), LOG, "S00")["capture_integrity"], "VALID_CAPTURE")

    def test_stale_declared_observer_version(self):
        r = c.analyze_capture(capture(), LOG, "S00", {"version": "QR9B04", "source_lua_sha256": "pinned"})
        self.assertEqual(r["declared_addon_metadata"], "STALE_OR_MISSING_DECLARATION")
        self.assertNotEqual(r["capture_integrity"], "VALID_CAPTURE")

    def test_real_file_collection_is_read_only_and_exact(self):
        root = SUITE / self._testMethodName
        self.assertFalse(root.exists(), "fresh fixture required")
        game, saves = root / "game", root / "saves"
        folder = game / "bin/x64/plugins/cyber_engine_tweaks/mods" / c.MODULE
        folder.mkdir(parents=True)
        (folder / LOG).write_bytes(capture())
        (folder / "init.lua").write_bytes(b"read-only observer")
        master = saves / "ManualSave-23"
        master.mkdir(parents=True)
        (master / "sav.dat").write_bytes(b"opaque synthetic save bytes")
        (game / "core.archive").write_bytes(b"current core")
        logs = game / "red4ext/plugins/ArchiveXL"
        logs.mkdir(parents=True)
        (logs / "ArchiveXL-test.log").write_bytes(b"[old] Patching phase receipt1\n[error] historical candidate\n")
        m = root / "master.json"
        c.save(m, {"path": str(master), "files": {"sav.dat": {"sha256": c.sha_bytes((master / "sav.dat").read_bytes())}}})
        baseline = {"game_root": str(game), "core_files": [{"path": "core.archive", "after": c.sha_bytes(b"current core")}],
                    "external_dependencies": [], "selected_master": {"path": str(m)}}
        addon = [{"path": str((folder / "init.lua").relative_to(game)), "after": c.sha_bytes(b"read-only observer")}]
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
        out = root / "output"
        r = c.collect(baseline, addon, out, "S00")
        self.assertEqual(r["capture_integrity"], "VALID_CAPTURE")
        self.assertEqual(r["runtime_results"], "NOT_TESTED_PENDING_HUMAN_REPORT")
        self.assertEqual((out / "logs" / LOG).read_bytes(), capture())
        for p, state in before.items():
            self.assertEqual((p.read_bytes(), p.stat().st_mtime_ns), state)
        self.assertEqual(c.load(out / "resource_observations.json")["core"][0]["status"], "MATCH")
        self.assertEqual(c.load(out / "human_result.json")["result"], "NOT_TESTED")
        self.assertIn("NOT_VERIFIED", c.load(out / "support_log_candidates.json")[0]["run_alignment"])
        with self.assertRaises(ValueError): c.collect(baseline, addon, out, "S00")
        with self.assertRaises(ValueError): c.collect(baseline, addon, root / "escape", "S00", "../bad.jsonl")
        self.assertFalse((root / "escape").exists())
        (game / "core.archive").write_bytes(b"different core")
        self.assertEqual(c.hash_observation(game / "core.archive", baseline["core_files"][0]["after"])["status"], "MISMATCH_OR_GROWING")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CollectionTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    c.save(H / "collector_test_result.json", {"status": "PASS" if result.wasSuccessful() else "FAIL", "tests": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "fixtures": str(SUITE), "scope": "Synthetic capture mutations and actual read-only file-copy fixture; no installed game/save/API access"})
    raise SystemExit(0 if result.wasSuccessful() else 1)
