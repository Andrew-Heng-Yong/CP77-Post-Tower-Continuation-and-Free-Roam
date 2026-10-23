"""Offline definition tests, not game runtime tests; preserves installed sources."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import validate_restriction_profile as profile


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, cls.inputs = profile.load_bundle()
        cls.before = profile.verify_installed()

    def refused(self, mutate):
        candidate = copy.deepcopy(self.bundle)
        mutate(candidate)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            profile.validate_bundle(candidate)

    def test_exact_approved_profile(self):
        result = profile.validate_bundle(self.bundle)
        self.assertEqual(result["perk_counts"], {"catalogue": 188, "allowed": 93, "blocked": 95})
        self.assertEqual(result["max_hp"], 150)
        self.assertEqual(result["cyberware_allowed_records"], 13)
        self.assertEqual(result["stamina"], "unchanged")
        actual = set(result["blocked_perks"])
        other = {p for p in actual if not p.startswith(("NewPerks.Body_", "NewPerks.Espionage_"))}
        audit = profile.read_json(profile.ROOT / "research/restriction_profiles/body_stats_design/other_perk_policy.json")
        self.assertEqual(other, {p["record"] for p in audit["perks"] if p["classification"] in
                                ("proposed_core", "dependency_core", "decision_smart")})
        self.assertTrue(profile.SMART <= actual)
        self.assertFalse(result["runtime_ready"])
        self.assertEqual(result["game_writes"], 0)
        self.assertEqual(result["unresolved_level_bindings"], {"NewPerks.Tech_Central_Perk_3_3": ["91068214685"]})

    def test_retained_optional_sustain_and_personal_link_perks(self):
        allowed = self.bundle["perks"]["allowed_records"]
        for perk in ("Intelligence_Left_Milestone_1", "Intelligence_Left_Perk_1_2",
                     "Cool_Central_Perk_3_2", "Cool_Right_Perk_2_4", "Cool_Right_Perk_3_2", "Cool_Inbetween_Right_3"):
            self.assertIn("NewPerks." + perk, allowed)

    def test_whole_branch_dependency_closure(self):
        rows = profile.catalogue_records(self.bundle["catalogue"])
        allowed = set(self.bundle["perks"]["allowed_records"])
        for record in allowed:
            self.assertTrue(set(rows[record]["requires"]) <= allowed)
        self.refused(lambda b: b["perks"]["allowed_records"].remove("NewPerks.Intelligence_Left_Milestone_1"))

    def test_health_invalid_values(self):
        for value in (0, -1, True, False, float("nan"), float("inf"), 100001, "100", None, []):
            with self.subTest(value=value):
                self.refused(lambda b: b["vitals"]["health"].update(value=value))

    def test_health_modularity_without_runtime_claim(self):
        candidate = copy.deepcopy(self.bundle)
        candidate["vitals"]["health"]["value"] = 125
        result = profile.validate_bundle(candidate)
        self.assertEqual(result["max_hp"], 125)
        self.assertFalse(result["runtime_ready"])
        self.assertEqual(result["perk_counts"]["blocked"], 95)

    def test_strict_profile_preserved(self):
        strict, _ = profile.load_bundle(profile.PROFILES / "tower_strict/profile.json")
        result = profile.validate_bundle(strict)
        self.assertEqual(result["perk_counts"], {"catalogue": 188, "allowed": 72, "blocked": 116})
        for module in ("vitals", "nerf_rules", "cyberware", "catalogue"):
            self.assertEqual(strict[module], self.bundle[module])
        self.assertTrue(set(strict["perks"]["allowed_records"]) < set(self.bundle["perks"]["allowed_records"]))
        self.assertEqual(result["max_hp"], 150)

    def test_implant_only_reflexes_and_cool_selection(self):
        result = profile.validate_bundle(self.bundle)
        self.assertEqual(result["perks_by_category"]["Reflexes"], {"allowed": 36, "blocked": 1})
        self.assertEqual(result["perks_by_category"]["Cool"], {"allowed": 35, "blocked": 2})
        for p in ("Reflexes_Right_Milestone_2", "Reflexes_Right_Perk_2_1", "Reflexes_Right_Perk_2_3",
                  "Reflexes_Right_Milestone_3", "Reflexes_Central_Milestone_2", "Reflexes_Central_Milestone_3",
                  "Cool_Inbetween_Left_2", "Cool_Left_Perk_3_2"):
            self.assertIn("NewPerks." + p, self.bundle["perks"]["allowed_records"])

    def test_unsafe_policy_mutations(self):
        mutations = [
            lambda b: b["vitals"]["health"].update(current_policy="refill"),
            lambda b: b["vitals"].update(stamina={"mode": "fixed", "value": 50}),
            lambda b: b["vitals"].update(modifier_ownership="all_modifiers"),
            lambda b: b["nerf_rules"]["body"].update(target=4),
            lambda b: b["nerf_rules"]["body"].update(refund_attribute_points=1),
            lambda b: b["nerf_rules"]["smart_targeting"].update(allowed=True),
            lambda b: b["nerf_rules"]["smart_targeting"].update(allowed=0),
            lambda b: b["nerf_rules"]["smart_targeting"].update(tattoo_exception="all_functions"),
            lambda b: b["nerf_rules"]["relic"].update(refund_points=False),
            lambda b: b["nerf_rules"]["refunds"].update(method="force_sale"),
            lambda b: b["nerf_rules"]["refunds"].update(reversal="restore_build"),
            lambda b: b["nerf_rules"]["preserve"].remove("story_facts"),
            lambda b: b["nerf_rules"].update(allowed_implant_in_removed_slot="delete_item"),
            lambda b: b["cyberware"].update(vendor_purchase="auto_install"),
            lambda b: b["cyberware"].update(function_denials_override_item_permission=False),
            lambda b: b["perks"].update(unknown_or_changed_catalogue="refund_unknowns"),
            lambda b: b["perks"].update(selection="blacklist"),
            lambda b: b["vitals"].update(schema_version=True),
            lambda b: b["nerf_rules"].update(unrecognized_rule=True),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.refused(mutate)

    def test_invalid_perk_whitelist(self):
        for record in ("NewPerks.Unknown", "NewPerks.Cool_Right_Perk_3_3",
                       "NewPerks.Body_Central_Milestone_1", "NewPerks.Espionage_Central_Milestone_1",
                       "NewPerks.Intelligence_Right_Milestone_2", "NewPerks.Intelligence_Left_Milestone_1"):
            with self.subTest(record=record):
                self.refused(lambda b: b["perks"]["allowed_records"].append(record))

    def test_invalid_cyberware_whitelist(self):
        for item in ("Items.SmartLink", "Items.AdvancedYakuzaTattoo", "Items.MaskCW", "Items.*"):
            with self.subTest(item=item):
                self.refused(lambda b: b["cyberware"]["categories"]["HandsCW"].append(item))
        self.refused(lambda b: b["cyberware"]["categories"].pop("LegsCW"))
        self.refused(lambda b: b["cyberware"]["categories"]["EyesCW"].append("Items.CasiusTattoo"))
        self.refused(lambda b: b["cyberware"]["categories"]["HandsCW"].append("Items.CasiusTattoo"))

    def test_catalogue_drift(self):
        self.refused(lambda b: b["catalogue"]["perks"].pop())
        self.refused(lambda b: b["catalogue"]["perks"][0].update(ranks=5))
        self.refused(lambda b: b["catalogue"]["perks"][0]["requires"].append("NewPerks.Unknown"))
        self.refused(lambda b: b["catalogue"]["sources"][0].update(sha256="0" * 64))
        self.refused(lambda b: b["catalogue"]["approved_other_bans"].pop())
        self.refused(lambda b: b["catalogue"]["perks"][-1].update(category="Body"))
        def hide_binding(b):
            for row in b["catalogue"]["perks"]:
                row["unresolved_levels"] = []
        self.refused(hide_binding)

    def test_duplicate_and_nonfinite_json_rejected(self):
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with patch.object(Path, "read_text", return_value=text):
                with self.assertRaises(ValueError):
                    profile.read_json(Path("not_opened.json"))

    def test_reference_boundary(self):
        for ref in ("../../AGENTS.md", "C:/Windows/test.json", "https://example.com/a.json", "..\\test.json"):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                profile.local_file(profile.DEFAULT.parent, ref, profile.PROFILES)

    def test_runtime_check_matches_build_evidence(self):
        result = subprocess.run([sys.executable, str(profile.ROOT / "tools/validate_restriction_profile.py"),
                                 "--require-runtime"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["definition_valid"])
        self.assertTrue(data["runtime_ready"])
        self.assertFalse(data["live_verified"])

    def test_sources_unchanged(self):
        self.assertEqual(profile.verify_installed(), self.before)
        _, after = profile.load_bundle()
        self.assertEqual(after, self.inputs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
