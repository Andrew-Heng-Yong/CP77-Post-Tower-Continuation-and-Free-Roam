"""Independent data/source contract and conservative S2 admission model checks.

This is not REDscript runtime proof. Compilation and native graph tests are separate.
Print-only by default; an optional new output path is written exclusively.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def method(source: str, name: str) -> str:
    pattern = r"\b(?:public|private)\s+(?:static\s+)?func\s+" + re.escape(name) + r"\([^)]*\)[^{]*\{"
    match = re.search(pattern, source)
    assert match, name
    depth = 1
    start = match.end()
    for pos in range(start, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos]
    raise AssertionError(f"Unbalanced method: {name}")


def branch_array(source: str, name: str, index: int) -> list[str]:
    match = re.search(r"if i == " + str(index) + r"\s*\{\s*return\s*\[(.*?)\];", method(source, name), re.S)
    if match is None:
        return []
    return re.findall(r'"([^"\n]*)"', match.group(1))


def capture_journals(job: dict) -> list:
    return job.get("capture_journals", job["journals"])


def fresh_indices(job: dict) -> list[int]:
    return [capture_journals(job).index(row) for row in job["journals"]]


def sample(job: dict) -> dict:
    return {"states": [1] * len(capture_journals(job)), "facts": [0] * len(job["zero_facts"]), "setup": [0] * len(job["allowed_passive_fields"])}


def fresh(job: dict, row: dict) -> bool:
    return (
        len(row["states"]) == len(capture_journals(job)) > 0
        and len(row["facts"]) == len(job["zero_facts"])
        and len(row["setup"]) == len(job["allowed_passive_fields"])
        and all(row["states"][k] == 1 for k in fresh_indices(job))
        and all(v == 0 for v in row["facts"])
        and all(field["min"] <= v <= field["max"] for v, field in zip(row["setup"], job["allowed_passive_fields"]))
    )


def certificate(*, native_boundary=True, teardown=False, ready=True, shape=True,
                age=0.0, journal_available=True, delayed=False) -> bool:
    return native_boundary and not teardown and ready and shape and 0 <= age <= 6 and journal_available and not delayed


def permit(job: dict, current: dict, *, running=True, warmup=0, faulted=False,
           common=True, owner_ready=1, issued=0, finished=0, owner_fault=0,
           certified=False, development=False, player_safe=True, stable=True) -> bool:
    return running and warmup == 0 and not faulted and common and owner_ready == 1 and issued == 0 and finished == 0 and owner_fault == 0 and (certified or development) and player_safe and stable and fresh(job, current)


def enable_development(state: dict, confirmation: str) -> dict:
    """Independent opt-in model: no native state or certificate mutation."""
    result = copy.deepcopy(state)
    if confirmation == "DISPOSABLE_SAVE" and not result["faulted"] and result["common"]:
        result["explicitDevelopment"] = True
    return result


def development_armed(state: dict, prior=False) -> bool:
    return not state["faulted"] and (state["explicitDevelopment"] or prior)


def authorized_route(*, certified: bool, development: bool) -> int:
    return 1 if certified else (2 if development else 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg_path = ROOT / "prealpha/sidejobs_s2/admission.json"
    src_path = HERE / "SideJobsS2.reds"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    source = src_path.read_text(encoding="utf-8")
    definition_path = ROOT / "research/activity_state_r3/definition.json"
    definition = json.loads(definition_path.read_text(encoding="utf-8-sig"))
    inventory_path = ROOT / "research/sidejobs_s21_failed/inventory_01.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
    whitelist_path = ROOT / "research/gig_restoration/lore_whitelists_v4_cast.json"
    whitelist = json.loads(whitelist_path.read_text(encoding="utf-8-sig"))
    data_source = source[source.index("public abstract class SideJobDataS2 {"):]
    failure_source = source[source.index("public abstract class SideJobFailureDataS21 {"):source.index("public abstract class SideJobDataS2 {")]
    checks = 0
    cases = 0

    def check(value: bool, label: str) -> None:
        nonlocal checks
        assert value, label
        checks += 1

    def find_job(value, identifier):
        if isinstance(value, dict):
            if value.get("id") == identifier and "journal_entries" in value:
                return value
            for child in value.values():
                found = find_job(child, identifier)
                if found:
                    return found
        if isinstance(value, list):
            for child in value:
                found = find_job(child, identifier)
                if found:
                    return found
        return None

    check([j["key"] for j in cfg["jobs"]] == ["mq032_sacrum", "mq008_party"], "exact selected job order")
    check([j["tag"] for j in cfg["jobs"]] == ["MQ032", "MQ008"], "exact selected tags")
    check(f'n"{cfg["catalogue"]}"' in method(source, "Catalogue"), "schema catalogue binding")
    for i, job in enumerate(cfg["jobs"]):
        prior = find_job(definition, job["key"])
        check(prior is not None, "whitelisted existing journal job")
        expected = [{"path": r["path"], "class": r["className"]} for r in prior["journal_entries"]]
        if i == 0:
            expected.append({"path": "quests/minor_quest/mq032_sacrum/mq032_alternative_title", "class": "gameJournalQuestTitleModifier"})
        check(capture_journals(job) == expected, "source capture journal paths/classes")
        check(branch_array(data_source, "Paths", i) == [v["path"] for v in capture_journals(job)], "compiled source path table")
        check(branch_array(data_source, "Classes", i) == [v["class"] for v in capture_journals(job)], "compiled source class table")
        match = re.search(r"if i == " + str(i) + r"\s*\{\s*return\s*\[(.*?)\];", method(source, "FreshIndices"), re.S)
        check(match is not None and [int(v) for v in re.findall(r"\d+", match.group(1))] == fresh_indices(job), "exact source-backed required freshness indexes")
        check(branch_array(data_source, "ZeroFacts", i) == job["zero_facts"], "compiled source zero table")
        check(branch_array(data_source, "SetupFacts", i) == [v["name"] for v in job["allowed_passive_fields"]], "compiled source passive table")
        check(len(set(job["zero_facts"])) == len(job["zero_facts"]), "unique facts")
        check(not (set(job["zero_facts"]) & {v["name"] for v in job["allowed_passive_fields"]}), "passive fields not zero gates")
        base = sample(job)
        check(fresh(job, base), "fresh baseline")
        check(not permit(job, base), "no historical or development authorization")
        check(permit(job, base, certified=True), "certified admission")
        check(permit(job, base, development=True), "explicit development admission")
        for field, bad_values in (("states", [-1, 0, 2, 3, 4, 5]), ("facts", [-1, 1, 2]), ("setup", [-1, 2])):
            for pos in range(len(base[field])):
                for value in bad_values:
                    altered = copy.deepcopy(base)
                    altered[field][pos] = value
                    if field == "states" and pos not in fresh_indices(job):
                        check(fresh(job, altered), "cosmetic journal not treated as gameplay freshness")
                        cases += 1
                        continue
                    check(not fresh(job, altered), f"reject {job['key']} {field}[{pos}]={value}")
                    check(not permit(job, altered, certified=True), "certificate does not bypass changed current state")
                    check(not permit(job, altered, development=True), "development does not bypass changed current state")
                    cases += 1
            malformed = copy.deepcopy(base)
            malformed[field].append(0)
            check(not fresh(job, malformed), "extra value rejected")
            if base[field]:
                malformed = copy.deepcopy(base)
                malformed[field].pop()
                check(not fresh(job, malformed), "missing value rejected")
        for setup in itertools.product((0, 1), repeat=len(base["setup"])):
            row = copy.deepcopy(base)
            row["setup"] = list(setup)
            check(fresh(job, row), "passive native initialization accepted")
            check(permit(job, row, development=True), "passive native initialization admission")
            cases += 1
        for field, values in {"running": [False], "warmup": [1, 3], "faulted": [True], "common": [False], "owner_ready": [-1, 0, 2], "issued": [-1, 1, 2], "finished": [-1, 1, 2], "owner_fault": [-1, 1, 2], "player_safe": [False], "stable": [False]}.items():
            for value in values:
                check(not permit(job, base, development=True, **{field: value}), f"deny owner/session field {field}")
                cases += 1
    for values in itertools.product((False, True), repeat=6):
        native, teardown, ready, shape, available, delayed = values
        for age in (-1, 0, 1, 6, 6.01, 99):
            expected = native and not teardown and ready and shape and available and not delayed and 0 <= age <= 6
            check(certificate(native_boundary=native, teardown=teardown, ready=ready, shape=shape, journal_available=available, delayed=delayed, age=age) == expected, "freeze boundary/age matrix")
            cases += 1
    # Capture before and at cutoff must match; a changed job cannot be promoted.
    for job in cfg["jobs"]:
        before = sample(job)
        after = copy.deepcopy(before)
        after["states"][0] = 2
        check(not (certificate() and fresh(job, before) and before == after), "changed-at-cutoff individually rejected")
        check(not certificate(native_boundary=False), "poll fallback does not certify")
        check(not certificate(teardown=True), "late teardown does not certify")
        check(not permit(job, before, development=True, issued=1), "issued owner never restarted")
    for name, value in cfg["common_guards"].items():
        check(re.search(r'this\.Fact\("' + re.escape(name) + r'"\)\s*==\s*' + str(value), method(source, "Common")) is not None, "common fact binding: " + name)
    for token in ["profile.PTFRPAComplete()", "!profile.PTFRPAFaulted()"]:
        check(token in method(source, "Common"), "profile binding")
    for token in ["BodyPolicy.Safe(player)", "before.fresh && after.fresh", "this.Same(before, after)", "this.DevelopmentArmed()", "this.Certified("]:
        check(token in method(source, "CanPermit"), "live admission binding")
    check("prior.DevelopmentArmed()" in method(source, "DevelopmentArmed"), "existing dev authorization preserved")
    check(source.count(".SetFactStr(") == 2 and '"_Permit", value' in method(source, "SetPermit") and '"_AuthorizedRoute", route' in method(source, "SetRoute"), "only owned admission writes")
    check('this.SetRoute(i, this.Certified(SideJobDataS2.ID(i)) ? 1 : 2)' in method(source, "Poll"), "persisted route has actual authorization")
    check('this.SetPermit(i, false); this.SetRoute(i, 0)' in method(source, "Restored"), "permit revoked before saved route cleared")
    check("this.SetPermit(i, false)" in method(source, "Restored"), "restore clears unissued permits")
    check('this.Own(i, "Issued") == 0' in method(source, "Restored") and 'this.Own(i, "Issued") == 0' in method(source, "Poll"), "never reset issued owner")
    check("epoch != this.epoch" in method(source, "Poll"), "stale tick rejected")
    check("this.certified = false" in method(source, "Restored"), "loaded-after-cutoff uncertified")
    check("this.baseline[i].fresh && this.Same(this.baseline[i], this.Read(i))" in method(source, "Freeze"), "cutoff downgrade only")
    for forbidden in ("ModLog(", "ChangeEntryState(", "SetFact(", "ForceReset", "QueueRequest(", "GiveItem(", "GetTransactionSystem("):
        check(forbidden not in source, "no runtime/native/reward/log mutation: " + forbidden)
    check("mq008_active" not in cfg["jobs"][1]["zero_facts"], "Stadium passive native count is not zero")
    # S2.1 surgical source proof: the installed/pinned class schema, catalogue,
    # native guard, history capture, save lifecycle, ownership and all tables stay
    # byte-equivalent after removing only the declared additive delta.
    old_source_path = ROOT / "prealpha/sidejobs_s2/SideJobsS2.reds"
    old_source = old_source_path.read_text(encoding="utf-8").rstrip() + "\n"
    old_development = method(old_source, "DevelopmentArmed")
    candidate = source
    candidate = candidate.replace(
        "  // S2.1: explicit disposable-save authorization, saved only with this batch.\n"
        "  private persistent let explicitDevelopment: Bool;\n", "", 1)
    api_start = candidate.index("  // Does not certify history, reset native state, or issue any owner directly.")
    api_end = candidate.index("  private func DevelopmentArmed()", api_start)
    candidate = candidate[:api_start] + candidate[api_end:]
    candidate = candidate.replace(method(candidate, "DevelopmentArmed"), old_development, 1)
    report_start = candidate.index("  // Manual read-only inventory. A Failed root is a candidate, not a restored job.")
    report_end = candidate.index("  public func Status()", report_start)
    candidate = candidate[:report_start] + candidate[report_end:]
    data_start = candidate.index("public abstract class SideJobFailureDataS21 {")
    data_end = candidate.index("public abstract class SideJobDataS2 {", data_start)
    candidate = candidate[:data_start] + candidate[data_end:]
    candidate = candidate.replace(' + " explicitFreshFixture=" + ToString(this.explicitDevelopment)', "")
    candidate = candidate.replace('" explicitFreshFixture=" + ToString(this.explicitDevelopment) + " currentFresh="', '" currentFresh="')
    check(candidate.rstrip() + "\n" == old_source, "entire previous source preserved except exact S2.1 delta")
    check("private persistent let explicitDevelopment: Bool;" in source, "explicit authorization saved within S2 class")
    check(source.count("this.explicitDevelopment = true;") == 1, "one scoped opt-in setter")
    check(source.count("this.explicitDevelopment =") == 1, "not silently enabled or cleared by lifecycle")
    body = method(source, "EnableFreshFixture")
    check('NotEquals(confirmation, "DISPOSABLE_SAVE")' in body, "case-sensitive exact disposable confirmation")
    check("this.faulted || !this.Common()" in body, "opt-in retains fault and full post-Tower admission")
    check("BodyPolicy.Safe" not in body, "CET menu does not block opt-in request")
    check("this.explicitDevelopment = true;" in body, "opt-in stores local permission")
    for name in ("baseline", "eligible", "certified", "captures", "ready", "frozen", "schema", "catalogue"):
        check("this." + name + " =" not in body, "opt-in cannot modify captured history: " + name)
    for forbidden in ("SetPermit(", "SetRoute(", ".SetFact", "ChangeEntryState", "Poll(", "Restored(", "CaptureBeforeEnding("):
        check(forbidden not in body, "opt-in does not issue/reset/recapture: " + forbidden)
    dev = method(source, "DevelopmentArmed")
    check("if this.faulted { return false; }" in dev, "fault refuses both development paths")
    check("this.explicitDevelopment || (IsDefined(prior) && prior.DevelopmentArmed())" in dev, "new OR old explicit development")
    for name in ("Status", "Inspect"):
        check('" explicitFreshFixture=" + ToString(this.explicitDevelopment)' in method(source, name), "manual diagnostic identifies explicit opt-in: " + name)
    # Exhaustive confirmation/fault/common/prior/initial-state combinations.
    base_state = {"explicitDevelopment": False, "faulted": False, "common": True,
                  "certified": False, "ready": False, "frozen": True, "captures": 0,
                  "baseline": [], "eligible": [], "native": {"issued": 0, "finished": 0, "reward": 0}}
    for confirmation, fault, common, prior, already in itertools.product(
            ("", "disposable_save", "DISPOSABLE_SAVE ", " DISPOSABLE_SAVE", "DISPOSABLE_SAVE"),
            (False, True), (False, True), (False, True), (False, True)):
        state = copy.deepcopy(base_state)
        state.update(faulted=fault, common=common, explicitDevelopment=already)
        result_state = enable_development(state, confirmation)
        accepted = confirmation == "DISPOSABLE_SAVE" and not fault and common
        check(result_state["explicitDevelopment"] == (already or accepted), "opt-in acceptance matrix")
        check(development_armed(result_state, prior) == (not fault and (already or accepted or prior)), "development OR/fault matrix")
        result_without_flag = {k: v for k, v in result_state.items() if k != "explicitDevelopment"}
        original_without_flag = {k: v for k, v in state.items() if k != "explicitDevelopment"}
        check(result_without_flag == original_without_flag, "all capture/native state unchanged")
        check(state["explicitDevelopment"] == already, "model request does not mutate prior snapshot")
        cases += 1
    accepted_state = enable_development(base_state, "DISPOSABLE_SAVE")
    check(not development_armed(base_state), "saved post-Tower default remains unauthorized")
    check(development_armed(accepted_state), "saved post-Tower explicitly authorized")
    check(accepted_state == enable_development(accepted_state, "DISPOSABLE_SAVE"), "opt-in is idempotent")
    check(development_armed(copy.deepcopy(accepted_state)), "opt-in persists through modeled reload")
    for job in cfg["jobs"]:
        current = sample(job)
        check(not permit(job, current, development=development_armed(base_state)), "reported fresh-but-unauthorized bug reproduced")
        check(permit(job, current, development=development_armed(accepted_state)), "same fresh save admitted after opt-in")
        check(not permit(job, current, development=development_armed(accepted_state), player_safe=False), "CET-menu opt-in still waits for safe gameplay")
        for root_state in (2, 3, 4):  # Active, Succeeded, Failed.
            terminal = copy.deepcopy(current)
            terminal["states"][0] = root_state
            check(not permit(job, terminal, development=development_armed(accepted_state)), "active/succeeded/failed roots not replayed")
            cases += 1
        for issued in (1, 2, -1):
            check(not permit(job, current, development=development_armed(copy.deepcopy(accepted_state)), issued=issued), "persistent opt-in never reissues saved owner")
            cases += 1
    for certified, prior_dev, explicit in itertools.product((False, True), repeat=3):
        state = copy.deepcopy(accepted_state)
        state["explicitDevelopment"] = explicit
        route = authorized_route(certified=certified, development=development_armed(state, prior_dev))
        check(route == (1 if certified else (2 if prior_dev or explicit else 0)), "route1 reserved for actual certificate")
        cases += 1
    production = copy.deepcopy(base_state)
    production.update(certified=True, ready=True, captures=9, baseline=[{"fresh": True}], eligible=[True])
    check({k: v for k, v in enable_development(production, "DISPOSABLE_SAVE").items() if k != "explicitDevelopment"} ==
          {k: v for k, v in production.items() if k != "explicitDevelopment"}, "genuine production captures and certificate preserved")
    # Exact 58-root R4 inventory and 55 source-bound detail catalogues. A failed
    # state is observed, not interpreted as safe-to-replay or as owner history.
    roster = inventory["jobs"]
    check(len(roster) == 58, "exact R4 inventory size")
    check(len({j["id"] for j in roster}) == 58, "unique root IDs")
    check(len({j["journal_path"] for j in roster}) == 58, "unique root paths")
    check(all(j["className"] == "gameJournalQuest" for j in roster), "root native class contract")
    allowed_titles = set(whitelist["two_year_aware"]["side_and_minor_jobs"]) | set(whitelist["ignore_two_year_gap"]["side_and_minor_jobs"])
    check({j["title"] for j in roster} == allowed_titles, "inventory exactly matches R4 selected side/minor titles")
    check("return 58;" in method(failure_source, "Count"), "native data count")
    for name, field in (("IDs", "id"), ("Titles", "title"), ("Paths", "journal_path")):
        values = re.findall(r'"([^"\n]*)"', method(failure_source, name))
        check(values == [j[field] for j in roster], "exact ordered root table: " + name)
    covered = 0
    gaps = []
    for i, job in enumerate(roster):
        detail = find_job(definition, job["id"])
        journals = detail["journal_entries"] if detail else []
        facts = detail["fact_names"] if detail else []
        check(branch_array(failure_source, "DetailPaths", i) == [row["path"] for row in journals], "exact detail path bindings: " + job["id"])
        check(branch_array(failure_source, "DetailClasses", i) == [row["className"] for row in journals], "exact detail class bindings: " + job["id"])
        dispatch = method(failure_source, "FactNames")
        if detail:
            check(f"if i == {i} {{ return SideJobFailureDataS21.FactNames{i}(); }}" in dispatch, "exact fact helper dispatch: " + job["id"])
            helper = method(failure_source, "FactNames" + str(i))
            check(re.findall(r'"([^"\n]*)"', helper) == facts, "exact helper fact bindings: " + job["id"])
            check(("return [" in helper) == bool(facts), "nonempty helper is literal bound data")
            if not facts:
                check("let empty: array<String>; return empty;" in helper, "covered job with no catalogued facts stays empty")
        else:
            check(f"if i == {i} " not in dispatch and f"func FactNames{i}(" not in failure_source, "uncovered job has no fabricated fact helper")
        check(len({row["path"] for row in journals}) == len(journals), "unique per-job journal paths")
        check(len(set(facts)) == len(facts), "unique per-job facts")
        if detail:
            covered += 1
            check(detail["journal_path"] == job["journal_path"], "root/detail canonical binding")
        else:
            gaps.append(job["id"])
        cases += 1
    check(covered == 55 and gaps == ["mq306_dumpster", "mq015_wizardbook", "mq026_conspiracy"], "exact three explicitly uncovered jobs")
    check(len(re.findall(r"public static func FactNames\d+\(", failure_source)) == 55, "exact 55 bounded fact helpers")
    check(re.findall(r"if i == (\d+) \{ return SideJobFailureDataS21\.FactNames(\d+)\(\); \}", method(failure_source, "FactNames")) == [(str(i), str(i)) for i, job in enumerate(roster) if find_job(definition, job["id"])], "no swapped or extra fact dispatcher branches")
    check("let empty: array<String>; return empty;" in method(failure_source, "FactNames"), "invalid and uncovered indices return empty")
    report = method(source, "FailedReport")
    details = method(source, "FailedDetails")
    for name, body in (("FailedReport", report), ("FailedDetails", details)):
        check("GameInstance.GetJournalManager" in body, "native journal manager: " + name)
        check("!IsDefined(jm)" in body, "missing manager rejected: " + name)
        check(body.count("jm.HasAnyDelayedStateChanges()") == 2, "settled journal checked before and after: " + name)
        check('GetEntryByString(' in body and '"gameJournalQuest"' in body and "jm.GetEntryState(" in body, "native actual root state only: " + name)
        check('state == 4' in body, "Failed-only candidate classification: " + name)
        check("candidate, adapter pending" in body, "candidate not restoration label: " + name)
        check("UNKNOWN " in body, "unknown per-ID exposed: " + name)
        for forbidden in ("SetFact", "SetPermit", "SetRoute", "ChangeEntry", "EnableFreshFixture", "CaptureBeforeEnding", "Schedule(", "ModLog(", "QueueRequest", "GiveItem"):
            check(forbidden not in body, "read-only inventory: " + name + " lacks " + forbidden)
        check(re.search(r"this\.\w+\s*=", body) is None, "no persistent/local owner writes: " + name)
        check(source.count("func " + name + "(") == 1 and source.count("this." + name + "(") == (1 if name == "FailedReport" else 0), "only manual details calls summary: " + name)
        check("this." + name + "(" not in method(source, "Poll") and "this." + name + "(" not in method(source, "Restored"), "never autoscheduled: " + name)
    for token in ("inactive += 1", "active += 1", "succeeded += 1", "failed += 1", "unknown += 1"):
        check(token in report, "all native root categories: " + token)
    check('IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1' in report, "missing root not assumed inactive")
    check('IsDefined(root) ? EnumInt(jm.GetEntryState(root)) : -1' in details, "missing details root not assumed failed")
    check("noDetailCoverage" in details, "gap remains explicit")
    check("NOT full scene/item/execution history" in details, "bounded detail limitations disclosed")
    check("qs.GetFactStr(facts[k])" in details and "!IsDefined(qs)" in details, "native facts only with available fact system")
    check('if EnumInt(jm.GetEntryState(root)) != 4' in details, "failed root rechecked after collecting details")
    check('if state < 1 || state > 4' in details, "unrecognized enum states reported unknown")
    check('this.FailedReport()' in details, "one manual command includes root counts and detail evidence")
    check('ToString(this.Common())' in report and '(context only, NOT admission)' in report, "genuine post-Tower readiness reported only as context")
    check('fresh-fixture authorization only; not failed-job restoration' in method(source, "EnableFreshFixture"), "fresh fixture purpose explicit")
    check("func EnableDevelopment(" not in source, "misleading public API removed")
    # Model diagnostics as pure observations; false/unknown/missing cannot admit an owner.
    def diagnostic_counts(states):
        labels = {1: "inactive", 2: "active", 3: "succeeded", 4: "failed"}
        counts = {name: 0 for name in (*labels.values(), "unknown")}
        selected = []
        for i, state in enumerate(states):
            counts[labels.get(state, "unknown")] += 1
            if state == 4:
                selected.append(i)
        return counts, selected
    for root_state in (None, -1, 0, 1, 2, 3, 4, 5, 99):
        states = [root_state] * 58
        before = copy.deepcopy(states)
        counts, selected = diagnostic_counts(states)
        label = {1: "inactive", 2: "active", 3: "succeeded", 4: "failed"}.get(root_state, "unknown")
        check(counts[label] == 58 and sum(counts.values()) == 58, "complete state categorization")
        check(selected == (list(range(58)) if root_state == 4 else []), "only actual Failed roots receive details")
        check(states == before, "diagnostic does not mutate observed state")
        cases += 1
    counts, selected = diagnostic_counts([1, 2, 3, 4, None, -1, 5] + [1] * 51)
    check(counts == {"inactive": 52, "active": 1, "succeeded": 1, "failed": 1, "unknown": 3} and selected == [3], "mixed unknown/terminal roster")
    check(data_source == old_source[old_source.index("public abstract class SideJobDataS2 {"):], "original SideJobDataS2 suffix remains byte-exact")
    for relative in ("research/activity_state_r3/definition.json", "research/gig_restoration/lore_whitelists_v4_cast.json"):
        check(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper() == inventory["source_hashes"][relative], "pinned inventory source: " + relative)
    result = {"status": "PASS", "checks": checks, "modeled_cases": cases,
              "limitations": ["Independent model and bound source/data tests; not live API or native-graph execution proof.", "Actual REDscript compilation and packed native graph verification required separately.", "Saved-permit/native-loader ordering still requires reload playtest; local-state guard must be repeated in native graph."],
              "sha256": {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in (src_path, cfg_path, inventory_path, definition_path, whitelist_path, Path(__file__))}}
    rendered = json.dumps(result, indent=2)
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
