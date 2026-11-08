"""Verify the owner and stage the additive HH1 delta on installed QR19."""

import argparse
import binascii
import re
from pathlib import Path
from shutil import copyfile

from prepare import BLOCK, COMMON, HERE, NATIVE, OWNER, read, sha, write
from model import model, walk

QR19 = HERE.parent / "quest_restoration_qr19"
PRIOR = QR19 / "candidate_01"
BUILT = HERE / "built_04"
CANDIDATE = HERE / "candidate_01"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
XL = ARCHIVE + ".xl"
PARENT = r"ep1\quest\ep1.quest"


def checked(path, digest):
    path = Path(path)
    assert sha(path) == digest, f"Hash mismatch: {path}"
    return path


def baseline():
    installed = read(checked(
        QR19 / "deployment_01/installed_manifest_01.json",
        "B926963B5BA85B95E8F371DBB00720A37793E5BC3E9904F770A220B8AED89784",
    ))
    package = read(checked(
        PRIOR / "package_manifest.json",
        "7259E12EABB61A8253F50A22BE6198DA7CFECA65692D99C37AE7283F2ADE942D",
    ))
    assert installed["core_epoch"] == "QR19" and installed["core_files"] == package["files"]
    game = Path(installed["game_root"])
    rows = installed["core_files"] + installed["required_files"]
    assert len(rows) == 77
    for row in rows:
        checked(game / row["path"], row["sha256"])
    return game, package


def facts_and_spawns(condition):
    assert condition["$type"] == "questLogicalCondition" and condition["operation"] == "AND"
    facts, spawns = {}, []
    for clause in condition["conditions"]:
        if clause["$type"] == "questFactsDBCondition":
            fact = clause["type"]
            assert fact["$type"] == "questVarComparison_ConditionType"
            assert fact["comparisonType"] == "Equal" and fact["factName"] not in facts
            facts[fact["factName"]] = fact["value"]
            continue
        assert not spawns and clause["$type"] == "questLogicalCondition" and clause["operation"] == "OR"
        for item in clause["conditions"]:
            assert item["$type"] == "questCharacterCondition"
            spawned = item["type"]
            assert spawned["$type"] == "questCharacterSpawned_ConditionType"
            assert spawned["comparisonParams"] == {
                "$type": "questComparisonParam", "comparisonType": "GreaterOrEqual", "count": 1, "entireCommunity": 1,
            }
            entity = spawned["objectRef"]
            assert entity["type"] == "EntityRef" and entity["names"] == []
            spawns.append(entity["reference"]["$value"])
    return facts, spawns


def verify_owner(plan, build):
    data = read(BUILT / "owner.json")["Data"]["RootChunk"]
    assert not data.get("phasePrefabs")
    graph = model(BUILT / "owner.json")
    outer = graph["root"]
    assert set(graph) == {"root", "root/13", "root/23"}
    assert set(outer["nodes"]) == {0, 10, 11, 12, 13, 20, 21, 22, 23}
    assert outer["nodes"][0]["$type"] == "questInputNodeDefinition"
    edges, allowed_writes = [], set()
    native = read(NATIVE / "club.questphase.json")["Data"]["RootChunk"]["phasePrefabs"]
    fixtures = 0
    for spec, row in zip(plan["sectors"], build["sectors"], strict=True):
        i = row["node"]
        name = row["name"]
        assert name == spec["name"] and row["private_ref"] == spec["private_ref"]
        wait, recheck, claim, phase = (outer["nodes"][n] for n in range(i, i + 4))
        assert [n["$type"] for n in (wait, recheck, claim, phase)] == [
            "questPauseConditionNodeDefinition", "questConditionNodeDefinition",
            "questFactsDBManagerNodeDefinition", "questPhaseNodeDefinition",
        ]
        assert wait["condition"] == recheck["condition"]
        prefix = f"PTFRHH1_{name}_"
        facts, spawns = facts_and_spawns(wait["condition"])
        assert facts == COMMON | {prefix + s: 0 for s in ("Claimed", "Entered", "Hold")}
        assert spawns == spec["communities"]
        assert claim["type"]["factName"] == prefix + "Claimed"
        original, = [p for p in native if row["native_ref"].endswith("/" + p["prefabNodeRef"]["$value"])]
        assert phase["phaseInstancePrefabs"] == [
            original | {"prefabNodeRef": original["prefabNodeRef"] | {"$value": spec["private_ref"]}},
        ]
        inner = graph[f"root/{i+3}"]
        assert inner["edges"] == [(0, "Out", 1, "In"), (1, "Out", 2, "In")]
        assert set(inner["nodes"]) == {0, 1, 2}
        assert inner["nodes"][0]["$type"] == "questInputNodeDefinition"
        assert inner["nodes"][1]["$type"] == "questFactsDBManagerNodeDefinition"
        assert inner["nodes"][1]["type"]["factName"] == prefix + "Entered"
        assert inner["nodes"][2]["$type"] == "questPauseConditionNodeDefinition"
        hold = inner["nodes"][2]["condition"]["type"]
        assert (hold["factName"], hold["value"], hold["comparisonType"]) == (prefix + "Hold", 1, "Equal")
        allowed_writes.update((prefix + "Claimed", prefix + "Entered"))
        edges.extend([(0, "Out", i, "In"), (i, "Out", i+1, "In"), (i+1, "False", i, "In"),
                      (i+1, "True", i+2, "In"), (i+2, "Out", i+3, "In1")])

        def admitted(state, existing):
            return all(state.get(k) == v for k, v in facts.items()) and any(ref in existing for ref in spawns)

        assert admitted(facts | {"sts_ep1_06_active": 1, "sts_ep1_06_start": 0}, {spawns[0]})
        assert not admitted(facts, set())
        assert not admitted(facts, {"unrelated"})
        assert all(not admitted(facts | {k: 1-v}, {spawns[0]}) for k, v in facts.items())
        fixtures += 3 + len(facts)
    assert outer["edges"] == sorted(edges)
    writes = [n for g in graph.values() for node in g["nodes"].values()
              for n in walk({k: v for k, v in node.items() if k != "phaseGraph"})
              if n.get("$type") == "questSetVar_NodeType"]
    assert len(writes) == len(allowed_writes) == 4
    assert {n["factName"] for n in writes} == allowed_writes and all(n["value"] == n["setExactValue"] == 1 for n in writes)
    return fixtures


def registrations(text):
    target = re.compile(r"(?im)^\s+parent:\s*[\"']?ep1[\\/]quest[\\/]ep1\.quest[\"']?\s*$")
    expected = len(target.findall(text))
    quest = re.search(r"(?ms)^quest:\s*\n(.*?)(?=^\S|\Z)", text)
    found = []
    if quest:
        for item in re.split(r"(?m)^    - path: +", quest[1])[1:]:
            if not target.search(item):
                continue
            path = item.splitlines()[0].strip().strip("\"'")
            assert re.search(r"(?m)^        node: \[1\]\s*$", item)
            assert re.search(r"(?m)^        socket: Out\s*$", item)
            found.append((path, binascii.crc_hqx((path + ":1").encode(), 65535)))
    assert len(found) == expected, "Unsupported ep1.quest injection form"
    return found


def stage_xl(game, old_path, new_path):
    source = old_path.read_bytes()
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    phase = newline.join(f"    - path: {OWNER}\n      parent: {PARENT}\n      input:\n        node: [1]\n        socket: Out\n".encode().split(b"\n"))
    stream = f"    - {BLOCK}".encode() + newline
    assert source.count(b"streaming:" + newline) == source.count(b"localization:" + newline) == 1
    assert OWNER.encode() not in source and BLOCK.encode() not in source
    candidate = source.replace(b"streaming:" + newline, phase + b"streaming:" + newline)
    candidate = candidate.replace(b"localization:" + newline, stream + b"localization:" + newline)
    assert candidate.replace(phase, b"").replace(stream, b"") == source
    new_path.write_bytes(candidate)
    installs = sorted((game / "archive/pc").rglob("*.xl"))
    pins = {str(p): sha(p) for p in installs}
    before, after = [], []
    for f in installs:
        data = f.read_text(encoding="utf-8-sig")
        before.extend(registrations(data))
        after.extend(registrations(candidate.decode("utf-8-sig").replace("\r\n", "\n") if f == game / XL else data))
    native = model(NATIVE / "root.quest.json")["root"]
    assert any(a == 1 and socket == "Out" for a, socket, _, _ in native["edges"])
    new_id = binascii.crc_hqx((OWNER + ":1").encode(), 65535)
    remaining = [r for r in after if r[0] != OWNER]
    assert before == remaining and len(after) == len(before) + 1
    ids = {i for _, i in after}
    assert len(ids) == len(after) and not ids.intersection(native["nodes"])
    assert all(sha(Path(p)) == digest for p, digest in pins.items())
    return {"new_phase_id": new_id, "target_registrations": len(after), "xl_scanned": len(installs), "sources": pins}


def stage():
    assert not CANDIDATE.exists()
    game, base = baseline()
    plan = read(HERE / "plan.json")
    build = read(BUILT / "build.json")
    world = read(BUILT / "world_verification.json")
    assert build["plan_sha256"] == sha(HERE / "plan.json")
    assert world["status"] == "PASS_TYPED_FILTERED_WORKSPOTS"
    assert world["sectors"] and sum(s["workspots"] for s in world["sectors"]) == 101
    fixtures = verify_owner(plan, build)
    new = {r["depot"]: r["sha256"] for r in build["resources"]}
    assert len(new) == 4 and set(new) == {OWNER, BLOCK, *(r["depot"] for r in build["sectors"])}
    assert not set(new).intersection(base["source_resources"])
    old_source = PRIOR / "archive_source"
    old_package = PRIOR / "package"
    assert {str(p.relative_to(old_source)) for p in old_source.rglob("*") if p.is_file()} == set(base["source_resources"])
    leaves = {r["path"]: r["sha256"] for r in base["files"]}
    assert {p.relative_to(old_package).as_posix() for p in old_package.rglob("*") if p.is_file()} == set(leaves)
    package = CANDIDATE / "package"
    (package / XL).parent.mkdir(parents=True)
    registration = stage_xl(game, checked(old_package / XL, leaves[XL]), package / XL)
    for relative, digest in leaves.items():
        p = checked(old_package / relative, digest)
        if relative not in (ARCHIVE, XL):
            dest = package / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            copyfile(p, dest)
    resources = base["source_resources"] | new
    for depot, digest in resources.items():
        source = (BUILT / "source" if depot in new else old_source) / depot
        dest = CANDIDATE / "archive_source" / depot
        dest.parent.mkdir(parents=True, exist_ok=True)
        copyfile(checked(source, digest), dest)
    leaves.pop(ARCHIVE)
    leaves[XL] = sha(package / XL)
    write(HERE / "pack_inputs.json", {"source_resources": resources, "package_without_archive": leaves})
    write(HERE / "owner_verification.json", {
        "status": "PASS_TYPED_OWNER_AND_REGISTRATIONS", "fixtures": fixtures,
        "registration": registration, "owner_sha256": new[OWNER],
    })
    copyfile(checked(QR19 / "pack.ps1", "7768A9C08234D5840403993A880A8A824A230300D35E41658076F0988491968E"),
             HERE / "pack.ps1")


def seal():
    _, base = baseline()
    packed = read(HERE / "archive_readback.json")
    inputs = read(HERE / "pack_inputs.json")
    assert packed["status"] == "PASS_ALL_ARCHIVE_MEMBERS"
    resources = {r["depot"]: r["sha256"] for r in packed["resources"]}
    keys = {r["depot"]: r["key"] for r in packed["resources"]}
    assert len(resources) == len(packed["resources"]) == len(set(keys.values())) == 1581
    assert resources == inputs["source_resources"]
    old = read(checked(QR19 / "archive_readback.json", "871B30C20EAD08CBEE3CAB9A43DA86FC80D2D80815671E67EEA6E160839B0315"))
    assert all(resources[r["depot"]] == r["sha256"] and keys[r["depot"]] == r["key"] for r in old["resources"])
    assert set(resources) - set(base["source_resources"]) == {r["depot"] for r in read(BUILT / "build.json")["resources"]}
    leaves = inputs["package_without_archive"] | {ARCHIVE: packed["archive_sha256"]}
    previous = {r["path"]: r["sha256"] for r in base["files"]}
    assert set(leaves) == set(previous) and {p for p in leaves if leaves[p] != previous[p]} == {ARCHIVE, XL}
    package = CANDIDATE / "package"
    assert len(leaves) == 51 and set(leaves) == {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    files = [{"path": p, "sha256": h, "bytes": checked(package / p, h).stat().st_size}
             for p, h in sorted(leaves.items())]
    write(CANDIDATE / "package_manifest.json", {
        "status": "STAGED_HH1_READBACK_VERIFIED", "predecessor": "QR19", "files": files,
        "source_resources": resources, "changed_paths": [ARCHIVE, XL],
        "added_depots": sorted(set(resources) - set(base["source_resources"])),
        "retained_archive_members": 1577, "installed_paths_verified": 77,
        "installed": False, "gameplay_validation": "UNTESTED",
    })
    print(f"Verified {len(files)} staged paths and {len(resources)} archive payloads")


if __name__ == "__main__":
    assert __debug__
    cli = argparse.ArgumentParser()
    cli.add_argument("phase", choices=("stage", "seal"))
    {"stage": stage, "seal": seal}[cli.parse_args().phase]()
