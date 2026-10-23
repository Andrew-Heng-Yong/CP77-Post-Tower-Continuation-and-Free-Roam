"""B1 offline review regressions. No gameplay, installation or old test reruns."""
import json
import unittest
from pathlib import Path

from audit_activity_batches_b1 import OUT, family, references, stable_write
from audit_activity_lifecycles_b1 import build, condition_value
from catalog_gig_rollout_r2 import ROOT, read, sha


def fact(name="tier", op="Greater", target=0):
    return {"$type": "questFactsDBCondition", "type": {"$type": "questVarComparison_ConditionType",
            "factName": name, "comparisonType": op, "value": target}}


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.structural = read(OUT / "structural_review.json")
        cls.review = build()

    def test_selected_set_and_adapter_claims(self):
        rows = self.structural["jobs"]
        self.assertEqual((len(rows), len({r["id"] for r in rows})), (128, 128))
        self.assertEqual(sum(r["category"] == "gig" for r in rows), 71)
        self.assertEqual(sum(r["category"] == "side_job" for r in rows), 57)
        self.assertEqual([(r["id"], r["adapter"]) for r in rows if r["adapter"]],
                         [("sts_wat_nid_02", "G1_resume"), ("mq005_alley", "S1_fresh")])
        self.assertFalse(any(r["completed_replay"] for r in rows))

    def test_families_cover_entire_set(self):
        self.assertEqual(sum(self.structural["family_counts"].values()), 128)
        self.assertEqual(self.structural["family_counts"]["base_fixer_gig"], 62)
        self.assertEqual(self.structural["family_counts"]["dogtown_gig"], 9)
        for row in self.structural["jobs"]:
            self.assertIn(row["family"], self.structural["family_counts"])

    def test_catalogue_coverage_does_not_admit_jobs(self):
        self.assertEqual(self.review["newly_restored"], 0)
        self.assertEqual(self.review["installed_changes"], 0)
        self.assertEqual(self.review["game_writes"], 0)
        self.assertEqual(self.review["save_writes"], 0)
        self.assertFalse(self.review["completed_replay_implemented"])
        self.assertEqual(self.structural["remaining_adapters"], 126)

    def test_source_hashes(self):
        for name, expected in (self.structural["source_inputs"] | self.review["source_inputs"]).items():
            self.assertEqual(sha(ROOT / name), expected, name)

    def test_recorded_output_matches_tested_builder(self):
        self.assertEqual(json.loads(json.dumps(self.review)), read(OUT / "lifecycle_review_r3.json"))

    def test_owner_not_catalogue_order_regression(self):
        rite = next(j for j in self.review["gigs"] if j["id"] == "sts_wat_nid_05")
        self.assertEqual(len(rite["resources"]), 3)
        self.assertEqual(len(rite["scenes"]), 3)
        self.assertEqual(rite["resources"][0]["binding"]["embedded_index"], 26)
        self.assertTrue(rite["resources"][0]["phase_prefabs"])
        self.assertTrue(any(s["source"].endswith("sts_wat_nid_05_scene.scene.json") for s in rite["scenes"]))
        self.assertFalse(any(s["johnny_cast"] for s in rite["scenes"]))

    def test_scene_cast_not_substring_guess(self):
        sides = {j["id"]: j for j in self.review["side_jobs"]}
        self.assertFalse(any(s["johnny_cast"] for s in sides["mq011_wilson"]["scenes"]))
        self.assertFalse(any(s["johnny_cast"] for s in sides["mq013_punks"]["scenes"]))
        self.assertTrue(any(s["johnny_cast"] for s in sides["mq030_melisa"]["scenes"]))
        self.assertEqual(len(sides["mq030_melisa"]["scenes"]), 2)
        self.assertTrue(all("/versions/" not in s["source"] for j in sides.values() for s in j["scenes"]))

    def test_native_graph_edges_resolve(self):
        for job in self.review["side_jobs"] + self.review["gigs"]:
            self.assertEqual(job["unresolved"], [])
            for resource in job["resources"]:
                for graph in resource["graphs"]:
                    nodes = {n["id"] for n in graph["nodes"]}
                    self.assertEqual(len(nodes), len(graph["nodes"]))
                    for a, _, b, _ in graph["edges"]:
                        self.assertIn(a, nodes); self.assertIn(b, nodes)

    def test_exact_saved_rite_stage(self):
        rite = next(j for j in self.review["gigs"] if j["id"] == "sts_wat_nid_05")
        pre, post = rite["captures"]
        self.assertEqual((pre["world"], post["world"]), ("PRE_TOWER", "POST_TOWER"))
        self.assertEqual([v["state"] for v in pre["journal"].values()], [2, 2, 1, 1, 2, 1, 2])
        self.assertEqual([v["state"] for v in post["journal"].values()], [4, 4, 1, 1, 4, 1, 2])
        for row in (pre, post):
            self.assertEqual(row["local_facts"]["nid_05_start"], 1)
            self.assertEqual(row["local_facts"]["nid_05_finished"], 0)
            self.assertEqual(row["local_facts"]["sts_wat_kab_nid_05_combat"], 0)
        self.assertEqual(self.review["next_adapter"]["mode"], "resume")

    def test_fact_evaluator_unknown_is_not_zero(self):
        self.assertIsNone(condition_value(fact(), {}))
        self.assertIsNone(condition_value(fact(), {"tier": True}))
        self.assertIsNone(condition_value(fact(), {"tier": "1"}))
        self.assertIsNone(condition_value(fact(op="Unknown"), {"tier": 1}))
        self.assertIsNone(condition_value({"$type": "questTriggerCondition"}, {"tier": 1}))

    def test_fact_evaluator_truth_tables(self):
        ops = {"Equal": lambda a,b:a == b, "NotEqual":lambda a,b:a != b, "Greater":lambda a,b:a > b,
               "GreaterOrEqual":lambda a,b:a >= b, "Less":lambda a,b:a < b, "LessOrEqual":lambda a,b:a <= b}
        for op, expected in ops.items():
            for a in range(-2, 4):
                for b in range(-2, 4):
                    self.assertIs(condition_value(fact(op=op, target=b), {"tier": a}), expected(a,b))
        for operation in ("AND", "OR"):
            for a in (-1, 0, 1):
                for b in (-1, 0, 1):
                    for missing in (False, True):
                        node = {"$type": "questLogicalCondition", "operation": operation,
                                "conditions": [fact("a"), fact("b")]}
                        values = {"a": a} if missing else {"a": a, "b": b}
                        x, y = a > 0, None if missing else b > 0
                        expected = (False if x is False or y is False else None if y is None else True) if operation == "AND" else (True if x is True or y is True else None if y is None else False)
                        self.assertIs(condition_value(node, values), expected)

    def test_kabuki_not_invented_unlocks(self):
        self.assertEqual(len(self.review["kabuki_gate_review"]), 3)
        for row in self.review["kabuki_gate_review"]:
            for evaluation in row["evaluations"]:
                self.assertTrue(all(n["fact_only_value"] is False for n in evaluation["nodes"]))

    def test_decode_gap_not_empty_community(self):
        self.assertEqual(len(self.review["community_decode_gaps"]), 1)
        gap = self.review["community_decode_gaps"][0]
        self.assertIn("kab_102_crowd_community", gap["resource"])
        self.assertIsNone(gap["json_sha256"])
        self.assertTrue(gap["decode_error"])

    def test_resource_reference_unwrapping(self):
        obj = {"sceneFile": {"DepotPath": {"$value": "a.scene"}}, "child": [
            {"sceneFile": {"DepotPath": {"$value": "0"}}}, {"sceneFile": {"DepotPath": {"$value": "a.scene"}}}]}
        self.assertEqual(references(obj, "sceneFile"), ["a.scene"])


def current_install_check():
    receipts = ["research/gig_restoration/pilot_r1/install_receipt.json",
                "research/restriction_profiles/profile_implant_r3_2/install_receipt.json",
                "research/activity_state_r3/install_receipt.json",
                "research/side_job_pilot_s1/install_receipt.json",
                "research/journal_label_j1/install_receipt.json",
                "research/side_job_cleanup_s1_1/install_receipt.json"]
    files = {}
    for name in receipts:
        for row in read(ROOT / name)["files"]:
            files[row["relative"]] = row  # Newer scoped replacements supersede older receipts.
    game = Path("C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077")
    checks = []
    for rel, row in sorted(files.items()):
        actual = sha(game / rel)
        assert actual == row["sha256"], (rel, "installed file changed")
        checks.append({"relative": rel, "sha256": actual})
    return checks


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReviewTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    checked = current_install_check()
    report = {"status": "OFFLINE_REVIEW_REGRESSIONS_PASS_NOT_RUNTIME_PROOF", "test_methods": result.testsRun,
              "fact_truth_table_cases": 252, "installed_files_checked": checked,
              "game_writes": 0, "save_writes": 0, "new_adapters": 0,
              "structural_sha256": sha(OUT / "structural_review.json"),
              "lifecycle_sha256": sha(OUT / "lifecycle_review_r3.json"),
              "superseded_initial_review_sha256": sha(OUT / "lifecycle_review.json")}
    stable_write(OUT / "tests_r2.json", report)
    print(json.dumps({"tests": result.testsRun, "current_installed_files_unchanged": len(checked), "new_adapters": 0}))


if __name__ == "__main__":
    main()
