"""PA1 entry contract and adversarial lifecycle models; not an engine playtest.

Run with Python 3 from any directory. Does not write game files or evidence.
The parent performs full redscript compilation with the final consolidated set.
"""
from copy import deepcopy
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent / "scripts"
ENTRY = (STAGE / "PreAlphaEntry.reds").read_text(encoding="utf-8")
GIG = (STAGE / "NativeGigsU9.reds").read_text(encoding="utf-8")
BRIDGE = (STAGE / "ProfileEntryPA1.reds").read_text(encoding="utf-8")
PROFILE = (STAGE / "ProfilePolicy.reds").read_text(encoding="utf-8")
DATA_PATH = ROOT / "redscript/PTFR_NativeGigsU9/NativeGigDataU9.generated.reds"
DATA = DATA_PATH.read_text(encoding="utf-8")


def classify(states, facts, terminal):
    if not states:
        return 4
    if states[0] in (3, 4) or any(terminal):
        return 3
    if any(s not in (1, 2, 3, 4) for s in states):
        return 4
    if any(s != 1 for s in states):
        return 2
    if any(facts):
        return 4
    return 1


class EntryModel:
    """Independent specification: persisted facts, not timers, own admission."""
    def __init__(self):
        self.baseline = None
        self.certificate = None
        self.frozen = False
        self.late = False
        self.observed = False
        self.requested = set()
        self.profile_refunds = 0
        self.profile_stage = 0

    def sample(self, snapshot, before_cutoff=True):
        if before_cutoff and not self.frozen:
            self.baseline = deepcopy(snapshot)

    def cutoff(self, current, native=True, before_cleanup=True, timely=True):
        if self.frozen:
            return
        self.observed = True
        self.frozen = True
        if native and before_cleanup and timely and self.baseline is not None:
            self.certificate = [old == new and classify(*old) == 1
                                for old, new in zip(self.baseline, current)]

    def load_after_cutoff(self):
        self.frozen = True
        # A read from a post-ending save is not an observed boundary.

    def arm_late(self, active, y2079, base_killed, ep1_killed, done,
                 finished, free_roam, direct_return, root):
        self.late |= (active == y2079 == base_killed == ep1_killed == 1
                      and done == finished == free_roam == direct_return == 0
                      and root == 2)

    def tick(self, complete, safe, eligible, terminal, available):
        if not complete or not safe or not (self.observed or self.certificate or self.late):
            return
        if self.profile_stage == 0:
            self.profile_refunds += 1
            self.profile_stage = 1
            return
        if self.profile_stage != 4:
            return
        for gig in eligible:
            if gig not in terminal and gig in available:
                self.requested.add(gig)


class SourceContracts(unittest.TestCase):
    def test_redscript_persistence_and_array_reference_contracts(self):
        self.assertNotRegex(ENTRY, r"persistent let \w+: String")
        self.assertNotRegex(ENTRY, r"ArraySize\(NativeGigDataU9\.")
        self.assertNotIn("@addMethod(", BRIDGE)
        original = (ROOT / "redscript/PTFR_Restrictions_R3/ProfilePolicy.reds").read_text(encoding="utf-8")
        before, remainder = PROFILE.split("  // PA1 read-only entry getters.", 1)
        getters, after = remainder.split("  private func Fail(message: String) -> Void", 1)
        self.assertEqual((before + "  private func Fail(message: String) -> Void" + after).rstrip(), original.rstrip())
        self.assertEqual(getters.count("public func PTFRPA"), 3)
        self.assertNotRegex(getters, r"this\.stage\s*=(?!=)")
        self.assertNotRegex(getters, r"this\.enabled\s*=(?!=)")

    def test_balanced_redscript_delimiters(self):
        for path in sorted(STAGE.glob("*.reds")):
            source = path.read_text(encoding="utf-8")
            scrubbed = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', "", source, flags=re.S)
            stack = []
            for offset, char in enumerate(scrubbed):
                if char in "({[":
                    stack.append(char)
                elif char in ")}]":
                    self.assertTrue(stack, (path, offset, char))
                    self.assertEqual(stack.pop(), {")": "(", "}": "{", "]": "["}[char], (path, offset))
            self.assertFalse(stack, path)

    def test_current_72_catalogue_pinned(self):
        self.assertIn(sha256(DATA_PATH.read_bytes()).hexdigest().upper(), ENTRY)
        ids = re.search(r"IDs\(\).*?return \[(.*?)\];", DATA).group(1)
        ids = re.findall(r'"([^"]+)"', ids)
        self.assertEqual(len(ids), 72)
        self.assertEqual(len(set(ids)), 72)

    def test_no_native_writers_or_old_pilot_dispatch(self):
        for source in (ENTRY, BRIDGE):
            for forbidden in ("SetFact", "SetEntryState", "GiveReward", "AddItem", "SetStat",
                              "RestoreSelected", "PTFR.GigPilotR1", "PTFR.SideJobPilotS1"):
                self.assertNotIn(forbidden, source)
        self.assertIn("profile.FullNerf()", ENTRY)
        self.assertIn("profile.PTFRPAComplete()", ENTRY)
        self.assertNotIn("FullNerfWithoutVitals", ENTRY)

    def test_no_claim_that_late_is_certified(self):
        arm = ENTRY.split("private func ArmLateTest()", 1)[1].split("private func Register", 1)[0]
        self.assertNotIn("this.certified = true", arm)
        self.assertIn("this.lateEndingTestArmed = true", arm)
        self.assertIn("!this.certified", ENTRY.split("public func DevelopmentArmed", 1)[1].split("\n", 1)[0])

    def test_credits_cleanup_and_arrival_precede_profile_dispatch(self):
        policy = (ROOT / "redscript/PTFR_Restrictions_R1/CyberwarePolicy.reds").read_text(encoding="utf-8")
        completed = policy.split("public static func Completed(", 1)[1].split("public static func Active", 1)[0]
        self.assertIn('q.GetFact(n"PTFRP0_DR13") == 1', completed)
        self.assertIn('q.GetFact(n"PostTowerFreeRoamActive") == 1', completed)
        driver = ENTRY.split("public func Poll(", 1)[1].split("private func Dispatch", 1)[0]
        self.assertLess(driver.index("arrival.Completed()"), driver.index("profile.FullNerf()"))
        self.assertLess(driver.index("profile.PTFRPAComplete()"), driver.index("this.Dispatch()"))
        self.assertIn("!BodyPolicy.Safe(player)", driver)
        source = (ROOT / "tools/build_phase2b_p0.ps1").read_text(encoding="utf-8-sig")
        self.assertLess(source.index("Rolling false rechecked"), source.index("'DR13'"))
        self.assertLess(source.index("::Unblock"), source.index("'DR13'"))

    def test_certified_adapter_checks_own_history(self):
        self.assertIn("history.Certified(id)", GIG)
        self.assertIn('this.Request(id,"DISPOSABLE_SAVE",true)', GIG)
        self.assertIn('this.Request(id,confirmation,false)', GIG)
        for guard in ("this.Terminal(i)", "this.EntrySafe(i)", "this.OldUnused(i)",
                      "this.LegacyIdle()", 'this.Own(id,"Request")!=0'):
            self.assertIn(guard, GIG)

    def test_original_native_semantics_and_fact_writes_preserved(self):
        original = (ROOT / "redscript/PTFR_NativeGigsU9/NativeGigsU9.reds").read_text(encoding="utf-8")
        # The entire poll, tier and retaliation handling is byte-for-byte source equivalent.
        self.assertEqual(original.split("  public func TierStatus()", 1)[1].rstrip(),
                         GIG.split("  public func TierStatus()", 1)[1].rstrip())
        for name in ("Terminal", "EntrySafe", "OldUnused", "LegacyIdle", "TierUntouched"):
            pattern = rf"  private func {name}\(.*?(?=\n  (?:public|private) func)"
            self.assertEqual(re.search(pattern, original, re.S).group(),
                             re.search(pattern, GIG, re.S).group())


class AdversarialModels(unittest.TestCase):
    def test_completed_active_missing_and_failed_not_fresh(self):
        for root, child, fact, terminal in product(range(-1, 5), range(-1, 5), (0, 1), (0, 1)):
            fresh = classify([root, child], [fact], [terminal]) == 1
            self.assertEqual(fresh, root == child == 1 and fact == terminal == 0)

    def test_sample_changed_at_cutoff_never_recovers_freshness(self):
        initial = [([1, 1], [0], [0]), ([1, 1], [0], [0])]
        changed = deepcopy(initial); changed[1] = ([2, 1], [1], [0])
        model = EntryModel(); model.sample(initial); model.cutoff(changed)
        self.assertEqual(model.certificate, [True, False])
        model.sample(initial)
        model.cutoff(initial)
        self.assertEqual(model.certificate, [True, False])

    def test_loaded_postending_has_no_history_and_no_auto_entry(self):
        model = EntryModel(); model.load_after_cutoff()
        for _ in range(100):
            model.tick(True, True, {0, 1}, set(), {0, 1})
        self.assertIsNone(model.certificate)
        self.assertEqual(model.profile_refunds, 0)
        self.assertFalse(model.requested)

    def test_cutoff_must_be_native_early_and_current(self):
        for native, early, timely in product((False, True), repeat=3):
            model = EntryModel(); data = [([1], [0], [0])]
            model.sample(data); model.cutoff(data, native, early, timely)
            self.assertEqual(model.certificate == [True], native and early and timely)

    def test_late_fixture_exact_admission(self):
        expected = (1, 1, 1, 1, 0, 0, 0, 0, 2)
        for position in range(len(expected)):
            for replacement in range(-1, 4):
                values = list(expected); values[position] = replacement
                model = EntryModel(); model.arm_late(*values)
                self.assertEqual(model.late, tuple(values) == expected)
                self.assertIsNone(model.certificate)

    def test_late_route_waits_for_complete_and_safe_gameplay(self):
        for complete, safe in product((False, True), repeat=2):
            model = EntryModel(); model.arm_late(1, 1, 1, 1, 0, 0, 0, 0, 2)
            model.tick(complete, safe, {0}, set(), {0})
            self.assertEqual(model.profile_refunds, int(complete and safe))
            self.assertFalse(model.requested)

    def test_checkpoint_reload_no_double_refund_or_reward_request(self):
        model = EntryModel(); model.arm_late(1, 1, 1, 1, 0, 0, 0, 0, 2)
        model.tick(True, True, {0, 1, 2}, {2}, {0})
        model.profile_stage = 4
        model.tick(True, True, {0, 1, 2}, {2}, {0})
        self.assertEqual(model.requested, {0})
        loaded = deepcopy(model)
        for _ in range(50):
            loaded.tick(True, True, {0, 1, 2}, {2}, {0, 1, 2})
        self.assertEqual(loaded.requested, {0, 1})
        self.assertEqual(loaded.profile_refunds, 1)

    def test_faulted_profile_never_retried(self):
        model = EntryModel(); model.late = True; model.profile_stage = 5
        for _ in range(100):
            model.tick(True, True, {0}, set(), {0})
        self.assertFalse(model.requested)
        self.assertEqual(model.profile_refunds, 0)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "status": "PASS_SOURCE_CONTRACTS_AND_LIFECYCLE_MODELS_NOT_ENGINE_PROOF" if result.wasSuccessful() else "FAIL",
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "source_hashes": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest().upper()
                          for path in sorted(STAGE.glob("*.reds"))},
        "catalogue_sha256": sha256(DATA_PATH.read_bytes()).hexdigest().upper(),
        "no_game_or_save_writes": True,
    }
    output = ROOT / "research/pre_alpha_clean/entry"
    output.mkdir(parents=True, exist_ok=True)
    (output / "entry_tests.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
