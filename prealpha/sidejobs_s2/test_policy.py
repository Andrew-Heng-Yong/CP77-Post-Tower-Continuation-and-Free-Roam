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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg_path = HERE / "admission.json"
    src_path = HERE / "SideJobsS2.reds"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    source = src_path.read_text(encoding="utf-8")
    definition = json.loads((ROOT / "research/activity_state_r3/definition.json").read_text(encoding="utf-8-sig"))
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
        check(branch_array(source, "Paths", i) == [v["path"] for v in capture_journals(job)], "compiled source path table")
        check(branch_array(source, "Classes", i) == [v["class"] for v in capture_journals(job)], "compiled source class table")
        match = re.search(r"if i == " + str(i) + r"\s*\{\s*return\s*\[(.*?)\];", method(source, "FreshIndices"), re.S)
        check(match is not None and [int(v) for v in re.findall(r"\d+", match.group(1))] == fresh_indices(job), "exact source-backed required freshness indexes")
        check(branch_array(source, "ZeroFacts", i) == job["zero_facts"], "compiled source zero table")
        check(branch_array(source, "SetupFacts", i) == [v["name"] for v in job["allowed_passive_fields"]], "compiled source passive table")
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
    check("prior.DevelopmentArmed()" in method(source, "DevelopmentArmed"), "existing dev authorization only")
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
    result = {"status": "PASS", "checks": checks, "modeled_cases": cases,
              "limitations": ["Independent model and bound source/data tests; not live API or native-graph execution proof.", "Actual REDscript compilation and packed native graph verification required separately.", "Saved-permit/native-loader ordering still requires reload playtest; local-state guard must be repeated in native graph."],
              "sha256": {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in (src_path, cfg_path, Path(__file__))}}
    rendered = json.dumps(result, indent=2)
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
