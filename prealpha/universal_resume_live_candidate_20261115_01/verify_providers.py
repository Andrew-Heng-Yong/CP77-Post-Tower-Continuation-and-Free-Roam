"""Refresh the seven native provider identities used by the first handoff."""

import argparse
import shutil
import subprocess

from candidate_common import HERE, PREALPHA, digest, load, pin, require, write_json


SOURCE = PREALPHA / "universal_resume_first_live_wait_20261115_01/run_sources_01"
INVENTORY = SOURCE / "source_inventory_01.json"
INVENTORY_SHA = "5DDCA95C4C81BE4BE287BD78AA97E745E46D45EEBABF0885381E43C4A389DA40"
ASSESSMENT = SOURCE / "source_assessment.json"
ASSESSMENT_SHA = "5905BCE8AFCC83AFA58BA4868AD45B01E0999741BD50A64C31DE3631264DE009"
SCANNER = SOURCE / "ReadProviders.ps1"
SCANNER_SHA = "CA6DE5578335C94E4241A35A1B312E9001E382305FA763595BCC1B9A22250A0B"


def verify(out):
    template = load(ASSESSMENT, ASSESSMENT_SHA)
    source = load(INVENTORY, INVENTORY_SHA)
    require(template["status"] == "SOURCE_AND_PROVIDERS_VERIFIED" and source == template["resources"],
            "Provider scope differs from the reviewed native route")
    require(out.parent == HERE, "Scan directory must preserve the reviewed helper path depth")
    original = pin(SCANNER, SCANNER_SHA)
    current = out / SCANNER.name
    shutil.copyfile(original, current)
    pin(current, SCANNER_SHA)
    shutil.copyfile(INVENTORY, out / INVENTORY.name)
    pin(out / INVENTORY.name, INVENTORY_SHA)
    result = subprocess.run(["pwsh", "-NoProfile", "-File", str(current)], cwd=out, text=True,
                            capture_output=True, encoding="utf-8", errors="replace", timeout=150,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    log = result.stdout + result.stderr
    (out / "providers_stdout.txt").write_text(log, encoding="utf-8")
    print(log, end="")
    result.check_returncode()
    current_path = out / "providers_01.json"
    current_sha = digest(current_path)
    scan = load(current_path, current_sha)
    require(scan["source_inventory_sha256"] == INVENTORY_SHA and scan["archives"], "Incomplete provider scan")
    expected = {item["depot"]: item["sha256"] for item in source}
    actual = {}
    for row in scan["providers"]:
        actual.setdefault(row["depot"], set()).add(row["sha256"])
    require(actual == {depot: {sha} for depot, sha in expected.items()}, "Missing or conflicting native provider")
    assessment = out / "provider_result.json"
    write_json(assessment, {"status": "CURRENT_HANDOFF_PROVIDERS_VERIFIED", "verified_resources": len(expected),
                            "archives": len(scan["archives"]), "assessment_sha256": ASSESSMENT_SHA,
                            "inventory_sha256": INVENTORY_SHA, "scanner_sha256": SCANNER_SHA,
                            "provider_scan_sha256": current_sha})
    return {ASSESSMENT: ASSESSMENT_SHA, current_path: current_sha, assessment: digest(assessment)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100))
    out = HERE / f"provider_{parser.parse_args().attempt:02}"
    out.mkdir()
    verify(out)


if __name__ == "__main__":
    main()
