"""Check the selected wait's original ownership and current resource providers."""

from contextlib import closing
import json
import sqlite3
import subprocess

from qualify_saved_wait import (CANDIDATE, CONTRACTS, HERE, INSTALLED, ORIGINAL, PREALPHA,
                                PRIVATE, REGISTRY, WAIT_OBJECTIVE, pin, read, sha, write)


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def journal_path(parameters):
    return parameters["type"]["path"]["realPath"]


def main():
    out = HERE / "run_sources_01"
    out.mkdir()
    registry = pin(REGISTRY, "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9")
    contracts = read(pin(CONTRACTS / "analysis_07/contracts.json",
                         "02A19F25EC7478DEB667F308FF876428D78D8E91DC6ADB9732ED5B2E060FC31F"))
    scopes = read(pin(CONTRACTS / "analysis_05/owner_map.json",
                      "B64B9010580CFFE9B5B642EAC8ACB17FFCF437DC16A6B84CCCBD8C7234F9907E"))["scopes"]
    quest, = [row for row in contracts["quests"] if row["id"] == CANDIDATE]
    require(not quest["whole_quest_exception"] and not quest["scoped_exception"], "Falco is outside the resume scope")
    by_address = {}
    for index in quest["scope_selectors"]["body_scope_ids"]:
        row = scopes[index]
        if row["kind"] == "quest" and row["address"]:
            prev = by_address.setdefault(tuple(row["address"]), row)
            require(row["sha256"] == prev["sha256"], "Competing Falco source")
    falco = by_address[ORIGINAL + (12,)]
    reyes = by_address[ORIGINAL + (11,)]
    parent = by_address[ORIGINAL]
    require(by_address[PRIVATE + (12,)]["rid"] == falco["rid"], "Private route changed donor")
    ancestry = [falco]
    while ancestry[-1]["parent"] is not None:
        ancestry.append(scopes[ancestry[-1]["parent"]])
    require([tuple(p["address"]) for p in ancestry] ==
            [ORIGINAL + (12,), ORIGINAL, ORIGINAL[:6], ORIGINAL[:5], ORIGINAL[:4],
             ORIGINAL[:3], ORIGINAL[:2], ORIGINAL[:1]], "Original ancestry changed")
    selected = {scope["rid"] for scope in [*ancestry, reyes]}

    with closing(sqlite3.connect(registry.as_uri() + "?mode=ro", uri=True)) as db:
        messages = {
            parent["rid"]: {(11, "StartFalco", 13, "Succeeded"), (13, "Out", 14, "Active"),
                            (14, "Out", 20, "In"), (20, "Out", 12, "In1"), (11, "Out1", 15, "In1"),
                            (12, "Out1", 15, "In2"), (15, "Out1", 17, "In")},
            falco["rid"]: {(0, "Out", 28, "In"), (28, "Out", 2, "In"), (2, "Out", 29, "In")},
            reyes["rid"]: {(22, "Out", 23, "In"), (22, "Out", 26, "In"), (23, "Out", 24, "In")},
            ancestry[-2]["rid"]: {(106, "Out", 109, "In"), (109, "Out", 107, "In")},
        }
        def node(rid, key):
            data, = db.execute("SELECT parameters_json FROM nodes WHERE rid=? AND graph='root' AND id=?",
                               (rid, key)).fetchone()
            return json.loads(data)

        for rid, required in messages.items():
            edges = set(db.execute("SELECT source,source_socket,destination,destination_socket FROM edges "
                                   "WHERE rid=? AND graph='root'", (rid,)))
            require(required <= edges, f"Required native branch changed in resource {rid}")
        pause = node(falco["rid"], 28)["condition"]["type"]
        require(pause["$type"] == "questGameTimeDelay_ConditionType" and
                [pause[k] for k in ("days", "hours", "minutes", "seconds")] == [1, 0, 0, 0],
                "Falco's authored wait changed")
        gate = node(falco["rid"], 2)["condition"]
        require(gate["operation"] == "AND" and len(gate["conditions"]) == 2 and
                gate["conditions"][0]["type"]["type"] == "SideQuest_MainPath" and
                gate["conditions"][1]["type"] == "IsOutside" and
                gate["conditions"][1]["triggerAreaRef"]["$value"] == "#mq049_tr_reyes_place",
                "Falco's follow-up conditions changed")
        require(journal_path(node(parent["rid"], 14)) == journal_path(node(falco["rid"], 16)) == WAIT_OBJECTIVE and
                node(reyes["rid"], 23)["condition"]["type"]["factName"] == "mq049_falco_done",
                "Native objective or parallel reply changed")
        ending = ancestry[-2]["rid"]
        require(node(ending, 109)["type"]["factName"] == "q307_main_game_killed" and
                node(ending, 107)["type"] == "Terminating", "The native ending cutoff changed")
        resources = []
        for rid in sorted(selected):
            depot, key, digest, support = db.execute(
                "SELECT depot,key,sha256,support_json FROM resources WHERE rid=?", (rid,)).fetchone()
            resources.append({"rid": rid, "depot": depot, "key": str(key), "sha256": digest,
                              "root_support": json.loads(support) if support else {}})
    source = out / "source_inventory_01.json"
    write(source, resources)

    template = PREALPHA / "universal_resume_owner_20261114_01/check_providers.ps1"
    scanner = pin(template, "12F1013F56CBDAFD98100FE0C409462FAC516BD80757808E1592EDEEB1F2B0D2")
    code = scanner.read_text(encoding="utf-8")
    code = code.replace("Split-Path (Split-Path $PSScriptRoot -Parent) -Parent",
                        "Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent")
    code = code.replace("prealpha/resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json",
                        INSTALLED.relative_to(PREALPHA.parent).as_posix())
    code = code.replace("AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8",
                        "57A78D066D6B7465572FB5F61AA0644AC6D247308C00E4AD1A7E07F59A4AB5C4")
    run = out / "ReadProviders.ps1"
    run.write_text(code, encoding="utf-8")
    subprocess.run(["pwsh", "-NoProfile", "-File", str(run)], check=True, timeout=150)
    report_path = out / "providers_01.json"
    providers = read(report_path)
    require(providers["source_inventory_sha256"] == sha(source), "Provider plan drift")
    for entry in resources:
        actual = {row["sha256"] for row in providers["providers"] if row["depot"] == entry["depot"]}
        require(actual == {entry["sha256"]}, f"Missing or conflicting provider {entry['depot']}")
    write(out / "source_assessment.json", {
        "status": "SOURCE_AND_PROVIDERS_VERIFIED",
        "native_ancestry": [scope["address"] for scope in ancestry],
        "native_sibling": reyes["address"], "resources": resources,
        "edges": {rid: sorted(edges) for rid, edges in messages.items()},
        "provider_scan_sha256": sha(report_path), "archives": len(providers["archives"]),
    })
    print(f"Verified {len(resources)} current provider identities and the original wait, join and ending cutoff.")


if __name__ == "__main__":
    main()
