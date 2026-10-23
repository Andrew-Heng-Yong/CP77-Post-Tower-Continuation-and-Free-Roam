"""Aggregate identity/contract checks; native component cases remain separately bound."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main(revision):
    build = HERE / "build" / revision
    target = build / "tests.json"
    assert not target.exists(), "Proof already exists"
    m = read(build / "build.json")
    checks = []
    def check(value, label):
        assert value, label
        checks.append(label)
    check(m["status"] == "BUILT_DT1_LIVE_PENDING", "expected native package")
    check(m["official_overrides"] == [] and m["runtime_scripts_added"] == 0, "no official replacement or runtime scripts")
    check(m["game_writes"] == m["save_writes"] == 0, "build did not mutate live state")
    check(m["packed_readback"] and m["native_scenes_unchanged"], "packed source contract")
    check([f["relative"] for f in m["files"]] == ["archive/pc/mod/TowerContinued_Dogtown_DT1.archive", "archive/pc/mod/TowerContinued_Dogtown_DT1.archive.xl"], "exact two additions")
    for f in m["files"]:
        check(sha(build / Path(f["relative"]).name) == f["sha256"], "package " + f["relative"])
    for p, digest in m["source_pins"].items():
        check(sha(ROOT / p) == digest, "source " + p)
    resources, boots, cases = {}, [], 0
    for ref in m["components"]:
        cp = ROOT / ref["path"]
        check(sha(cp) == ref["sha256"], "component identity " + ref["path"])
        c = read(cp)
        proof = read(ROOT / ref["tests"])
        check(sha(ROOT / ref["tests"]) == ref["tests_sha256"], "bound component test receipt")
        check(proof["status"] == "PASS_OFFLINE_NOT_LIVE" and proof["component_sha256"] == ref["sha256"], "matching component tests")
        check(proof["test_source_sha256"] in c["source_pins"].values(), "component tester pinned")
        check(proof["native_writes_added"] == 0 and proof["admission_cases"] >= 55, "bounded guard cases")
        check(c["official_overrides"] == [] and c["runtime_scripts_added"] == 0, "native component scope")
        check(c["changed_native_edges"] == [] and c["changed_native_properties"] == [], "stock gate unchanged")
        for key, value in c["source_pins"].items():
            check(m["source_pins"].get(key) == value, "component source merged " + key)
        for key, value in c["resources"].items():
            check(key not in resources, "unique component resource " + key)
            resources[key] = value
        boots.extend(c["boots"])
        for w in ref["readbacks"]:
            check(sha(ROOT / w["path"]) == w["sha256"] == m["source_pins"].get(w["path"]), "bound raw witness")
        cases += proof["admission_cases"]
    check(resources == m["resources"] and boots == m["boots"], "aggregate exact component resources and boots")
    check(len(boots) == len(set(boots)) == len(set(m["injection_ids"])), "unique registrations")
    for p, value in resources.items():
        check(sha(build / "source" / p.replace("\\", "/")) == value, "raw output " + p)
    check(len(m["installed_xl"]) == len({x["name"] for x in m["installed_xl"]}), "all XL identities unique")
    result = {"status": "PASS_NOT_LIVE", "build_sha256": sha(build / "build.json"), "tester_sha256": sha(Path(__file__)), "checks": len(checks), "check_names": checks, "component_admission_cases": cases, "native_writes_added": 0, "live_gate_pass": False}
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "check_names"}))

if __name__ == "__main__":
    main(sys.argv[1])
