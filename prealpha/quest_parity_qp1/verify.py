"""Check the edited graph contracts and seal the complete local candidate."""

from binascii import crc_hqx
from collections import Counter
from pathlib import Path
import re
import struct
import sys
import zipfile
import zlib

from stage import (
    ARCHIVE, AUDIT, HERE, INSTALLED_SHA, LIPMAP, OUT, PRE, PRIVATE_TRUCK, SCRIPT,
    baseline, inventory, pinned, plain, read, sha, write,
)

sys.path.insert(0, str(AUDIT / "scene_audit"))
from scene_routes import Resource, active_nodes, scene

sys.path.insert(0, str(PRE / "voodoo_treasure_20261106_01"))
from bind_sector import Sector, node_hash, vlq

XL = ARCHIVE + ".xl"
AMBIENT = r"towercontinued\quest_parity_qp1\heavy_hearts_ambient.questphase"
ENTRY = r"towercontinued\native_gigs_u9\sts_ep1_06_entry.questphase"
BLOCK = r"towercontinued\heavy_hearts_hh1\workspots.streamingblock"
PARENT = r"ep1\quest\ep1.quest"
HH = OUT / "heavy_hearts"
TRUCK = OUT / "truck"


def garage():
    evidence = read(TRUCK / "area_inputs.json")
    pin = evidence["sector"]
    sector = Sector(pinned(pin["raw"], pin["sha256"]).read_bytes())
    setups = pinned(pin["buffer"], pin["buffer_sha256"]).read_bytes()
    handles, refs, tail = sector.root()
    count, pos = vlq(tail, 0)
    ranges = struct.unpack_from(f"<{count}I", tail, pos)
    assert ranges[0] == 0 and len(ranges) == 2
    _, _, offset, disk, size, _ = sector.buffers[0]
    assert (offset, disk, size) == (pin["offset"], pin["disk_size"], pin["size"])
    assert len(setups) == size and size % 144 == 0
    ref, = (r for r in refs if r.endswith("/#mq017_garage_area"))
    assert all(ref.startswith(b["prefab"] + "/") for b in evidence["blocks"])
    idx, = (struct.unpack_from("<Q", setups, i + 112)[0] & 0x7FFFF
            for i in range(0, size, 144) if struct.unpack_from("<Q", setups, i + 88)[0] == node_hash(ref))
    assert idx < ranges[1]
    node = sector.bind(handles[idx])
    assert node["node_type"] == "worldTriggerAreaNode"
    count, notifier = struct.unpack("<II", bytes.fromhex(node["properties"]["notifiers"]["hex"]))
    assert count == 1 and sector.chunk(notifier)[0] == "questTriggerNotifier_Quest"
    return {"ref": ref, "node": idx, "depot": evidence["depot"], "typed_limit": evidence["typed_decode_limit"]}


def tweakdb_ids(obj):
    if isinstance(obj, list):
        return [tweakdb_ids(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    if obj.get("$type") == "TweakDBID" and obj.get("$storage") == "string":
        name = obj["$value"].encode()
        return {"$type": "TweakDBID", "$storage": "uint64", "$value": str(zlib.crc32(name) | len(name) << 32)}
    return {k: tweakdb_ids(v) for k, v in obj.items()}


def normalized(doc):
    data = Resource(doc).normalize()
    assert not data["errors"], data["errors"]
    return data


def truck_scene(plan):
    pinned(plan["truck"]["before"]["json"], plan["truck"]["before"]["json_sha256"])
    pinned(plan["truck"]["stock"]["json"], plan["truck"]["stock"]["json_sha256"])
    old = tweakdb_ids(read(plan["truck"]["before"]["json"]))
    new = tweakdb_ids(read(TRUCK / "scene.json"))
    stock = read(plan["truck"]["stock"]["json"])
    prev, candidate, vanilla = map(scene, (old, new, stock))
    old_active, old_inputs = active_nodes(prev, "Start 0")
    new_active, new_inputs = active_nodes(candidate, "Start 0")
    stock_active, _ = active_nodes(vanilla, "Start 0")
    assert old_inputs[241] == {0} and 2 not in old_active
    assert new_inputs[241] == {0, 1, 2} and new_inputs[1891] == {0, 1}
    assert old_active <= new_active and {184, 198, 618, 925, 977, 1786, 1796, 2093, 2194, 1311, 2} <= new_active
    assert not new_active.intersection({507, 995, 1024})
    assert candidate["exits"]["End 0"] == 2
    retained_events = {e["id"] for i in (new_active - old_active) & stock_active
                       for e in candidate["events"][i] if e["type"] != "scneventsSocket"}
    assert len(retained_events) == 123
    assert {"2066502182111158272", "1996941528546693164", "2817412227776409600"} <= retained_events
    assert candidate["nodes"][241]["numInSockets"] == 3
    assert candidate["graph"][618] == [(0, 0, 210, 0, 1)]
    assert candidate["graph"][618] == vanilla["graph"][507] and prev["graph"][618] == []
    candidate["nodes"][618]["outputSockets"][0]["destinations"].clear()
    assert normalized(old) == normalized(new), "Unexpected Small Man semantic change"
    parents = read(AUDIT / "scene_audit/scene_route_results.json")
    return {
        "added_edge": ["618", "0:0", "210", "0:1"],
        "and_241_before": sorted(old_inputs[241]), "and_241_after": sorted(new_inputs[241]),
        "and_1891_after": sorted(new_inputs[1891]), "restored_event_payloads": len(retained_events),
        "connected_end": "End 0", "scope": parents.get("scope", "AND-aware named entry reachability"),
        "garage": garage(),
    }


def edges(graph, expected):
    assert Counter(map(tuple, graph["edges"])) == Counter(expected), graph["edges"]


def condition_parts(node, operation):
    root = node["payload"]["condition"]
    assert root["$type"] == "questLogicalCondition" and root["operation"] == operation
    return root["conditions"]


def var_checks(clauses):
    facts = {}
    for c in clauses:
        if c["$type"] == "questFactsDBCondition":
            t = c["type"]
            assert t["factName"] not in facts
            facts[t["factName"]] = (t["comparisonType"], t["value"])
    return facts


def heavy_hearts():
    providers = AUDIT / "encounter_audit/capture_01"
    cap = read(providers / "providers.json")

    def stock(tag):
        row, = (r for r in cap["providers"] if r["tag"] == tag and r["json"])
        pinned(providers / row["raw"], row["sha256"])
        return normalized(read(pinned(providers / row["json"], row["json_sha256"])))

    before, after = stock("sts_ep1_06_current_entry"), normalized(read(HH / "gig_entry.json"))
    ambient = normalized(read(HH / "ambient.json"))
    cooked = read(HH / "resources.json")
    gig, chatter = cooked["areas"]
    assert gig["name"] == "gig" and chatter["name"] == "ambient"
    assert {p["ref"].rsplit("/", 1)[-1] for p in gig["placements"]} == {
        "#sts_ep1_06_tr_cleanup", "#sts_ep1_06_tr_init", "#sts_ep1_06_tr_client",
        "#sts_ep1_06_tr_drug_dealer_interrupt", "#sts_ep1_06_tr_bouncer", "#sts_ep1_06_dealer_enter",
    }
    assert {p["ref"].rsplit("/", 1)[-1] for p in chatter["placements"]} == {
        "#sts_ep1_06_tr_chat_kurtz_001", "#sts_ep1_06_tr_chat_kurtz_002",
    }
    n50 = after["graphs"]["root"]["nodes"]["50"]
    assert n50["prefabs"] == [gig["ref"]] and before["graphs"]["root"]["nodes"]["50"]["prefabs"] == []
    after["graphs"]["root"]["nodes"]["50"] = before["graphs"]["root"]["nodes"]["50"]
    assert before == after, "Unexpected U9 entry change"
    assert ("9", "Out1", "2", "In") in map(tuple, after["graphs"]["root/50"]["edges"])
    assert after["graphs"]["root/50"]["nodes"]["2"]["node_refs"] == ["#sts_ep1_06_tr_init"]

    g = ambient["graphs"]
    assert g["root"]["nodes"]["3"]["prefabs"] == [chatter["ref"]]
    assert not ambient["root_prefabs"]
    edges(g["root"], [
        ("0", "Out", "1", "In"), ("1", "Out", "2", "In"), ("2", "False", "1", "In"),
        ("2", "True", "3", "In1"), ("3", "Out1", "4", "In"), ("4", "CutSource", "3", "CutDestination"),
    ])
    base = condition_parts(g["root"]["nodes"]["1"], "AND")
    assert base == condition_parts(g["root"]["nodes"]["2"], "AND")
    base_facts = var_checks(base)
    assert base_facts["q307_ep1_killed"] == ("Equal", 1)
    assert base_facts["PostTowerFreeRoamActive"] == ("Equal", 1)
    assert base_facts["q307_active"] == ("Equal", 0)
    holder = g["root/3"]
    assert var_checks(condition_parts(holder["nodes"]["1"], "OR")) == {
        k: ("NotEqual", v) for k, (_, v) in base_facts.items()
    }
    assert all(not n["writes"] and not n["reward"] for graph in g.values() for n in graph["nodes"].values())
    assert {n["type"] for graph in g.values() for n in graph["nodes"].values()} == {
        "questInputNodeDefinition", "questPauseConditionNodeDefinition", "questConditionNodeDefinition",
        "questPhaseNodeDefinition", "questSceneNodeDefinition", "questOutputNodeDefinition", "questCutControlNodeDefinition",
    }
    donor = stock("heavy_hearts")["graphs"]
    hub = donor["root/1"]["nodes"]
    vendor = donor["root/1/341"]["nodes"]
    fixture_rows = []
    for id, caller, approach, start, end, actors in (
        (10, hub["370"], hub["369"], "Start 0", "End 0", {"chat_kurtz_001a", "chat_kurtz_001b"}),
        (20, hub["371"], hub["372"], "Start1", "End1", {"chat_kurtz_002a", "chat_kurtz_002b"}),
        (30, vendor["2"], hub["342"], "dealing", "", {"drug_dealer"}),
    ):
        inner = g[f"root/3/{id + 2}"]
        call = inner["nodes"]["1"]
        expected = dict(caller["payload"], id=1)
        assert call["payload"] == expected
        ready = condition_parts(holder["nodes"][str(id)], "AND")
        assert ready == condition_parts(holder["nodes"][str(id + 1)], "AND")
        stop = condition_parts(inner["nodes"]["2"], "OR")
        assert approach["payload"]["condition"] in ready
        now = var_checks(ready)
        assert now["sts_ep1_06_active"] == ("Equal", 0)
        assert now["sts_ep1_06_close_club"] == ("Equal", 0)
        assert now["sts_ep1_06_alarm_raised"] == ("Equal", 0)
        assert var_checks(stop) == {
            k: ("NotEqual" if op == "Equal" else "Less", v) for k, (op, v) in now.items()
        }
        for conditions, op in ((ready, "Equal"), (stop, "NotEqual")):
            actor_conditions = [c["type"] for c in conditions if c["$type"] == "questCharacterCondition"]
            assert all(c["$type"] == "questCharacterSpawned_ConditionType" for c in actor_conditions)
            assert {c["objectRef"]["names"][0]["$value"] for c in actor_conditions} == actors
            assert all(c["objectRef"]["reference"]["$value"] == "#sts_ep1_06_com_civilians"
                       and c["comparisonParams"]["count"] == 1
                       and c["comparisonParams"]["comparisonType"] == op for c in actor_conditions)
        route = [("0", "Out", "1", start), ("0", "Out", "2", "In"), ("2", "Out", "3", "In")]
        if end:
            route.append(("1", end, "3", "In"))
            assert now["q304_kurt_dead"] == ("GreaterOrEqual", 1) and now["mq304_active"] == ("Equal", 0)
        else:
            assert now["sts_ep1_06_drug_dealer_default_on"] == ("Equal", 1)
            assert now["sts_ep1_06_drug_dealer_info"] == ("GreaterOrEqual", 1)
            assert now["sts_ep1_06_dealer_scared"] == ("Equal", 0)
            assert vendor["3"]["payload"]["condition"] in stop
        edges(inner, route)
        branch_edges = [("0", "Out", str(id), "In"), (str(id), "Out", str(id + 1), "In"),
                        (str(id + 1), "False", str(id), "In"), (str(id + 1), "True", str(id + 2), "In1"),
                        (str(id + 2), "Out1", str(id + 3), "In"), (str(id + 3), "CutSource", str(id + 2), "CutDestination")]
        if not end:
            branch_edges.append((str(id + 3), "Out", str(id), "In"))
        assert set(branch_edges) <= set(map(tuple, holder["edges"]))
        assert len([r for r in holder["edges"] if r[0] == str(id + 3)]) == (1 if end else 2)
        fixture_rows.append({"input": start, "scene": call["refs"][0], "actors": sorted(actors), "rearms": not end})
    return {"markers": cooked["markers"], "gig_areas": gig["placements"], "ambient_areas": chatter["placements"],
            "ambient_callers": fixture_rows, "archives_scanned": cooked["archives_scanned"]}


def registrations(text):
    targets = re.findall(r"(?im)^\s+parent:\s*[\"']?ep1[\\/]quest[\\/]ep1\.quest[\"']?\s*$", text)
    result = []
    for section in re.split(r"(?m)^    - path: +", text)[1:]:
        if not re.search(r"(?im)^\s+parent:\s*[\"']?ep1[\\/]quest[\\/]ep1\.quest[\"']?\s*$", section):
            continue
        assert re.search(r"(?m)^        node: \[1\]\s*$", section)
        assert re.search(r"(?m)^        socket: Out\s*$", section)
        result.append(section.splitlines()[0].strip().strip("\"'"))
    assert len(result) == len(targets), "Unsupported registration to ep1.quest"
    return result


def stage_xl(game):
    package = OUT / "package" / XL
    source = (game / XL).read_bytes()
    assert package.read_bytes() == source
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    reg = newline.join(s.encode() for s in (
        f"    - path: {AMBIENT}", f"      parent: {PARENT}", "      input:", "        node: [1]", "        socket: Out", "",
    ))
    anchor = b"streaming:" + newline
    assert source.count(anchor) == 1 and AMBIENT.encode() not in source
    update = source.replace(anchor, reg + anchor)
    assert update.replace(reg, b"") == source
    native = read(AUDIT / "audit_controls.json")["native_parent_ids"]
    paths = sorted((game / "archive/pc").rglob("*.xl"))
    prior, successor = [], []
    for p in paths:
        plain(p)
        s = p.read_text(encoding="utf-8-sig")
        prior += registrations(s)
        successor += registrations(update.decode("utf-8-sig")) if p == game / XL else registrations(s)
    assert [p for p in successor if p != AMBIENT] == prior and successor.count(AMBIENT) == 1
    phase_ids = {crc_hqx((p + ":1").encode(), 65535) for p in successor}
    assert len(phase_ids) == len(successor) and phase_ids.isdisjoint(native)
    package.write_bytes(update)
    return {"phase_node_id": crc_hqx((AMBIENT + ":1").encode(), 65535), "phase_bindings": len(successor),
            "xl_files_checked": len(paths), "xl_sha256": sha(package)}


def prepare_pack():
    pack_inputs = OUT / "pack_inputs.json"
    assert not pack_inputs.exists()
    installed, _, base = baseline()
    plan = read(OUT / "inputs.json")
    proof = {"small_man": truck_scene(plan), "heavy_hearts": heavy_hearts()}
    hh = read(HH / "resources.json")
    before = base["source_resources"]
    resources = inventory(OUT / "archive_source", depots=True)
    new = set(resources) - set(before)
    assert new == set(hh["new_depots"]) and len(new) == 3 and not set(before) - set(resources)
    changed = {d for d in before if resources[d] != before[d]}
    assert changed == {PRIVATE_TRUCK, LIPMAP, BLOCK, ENTRY}
    for row in hh["areas"] + hh["edited"]:
        assert resources[row["depot"]] == row["sha256"]
    assert resources[LIPMAP] == plan["lipmap_sha256"]
    compiled = read(HERE / "compile_01/result.json")
    assert compiled["status"] == "PASS_CURRENT_INPUT_OFFLINE_COMPILE"
    assert compiled["candidate_script_sha256"] == sha(OUT / "package" / SCRIPT) == plan["script_sha256"]
    proof["compile_sources"] = compiled["source_count"]
    proof["registration"] = stage_xl(Path(installed["game_root"]))
    write(OUT / "verification.json", proof)
    write(pack_inputs, {"before_archive": installed["archive_sha256"], "resources": resources,
                        "changed": sorted(changed), "new": sorted(new)})
    print(f"Verified the graph edits and prepared {len(resources)} archive members.")


def seal():
    installed, _, _ = baseline()
    inputs = read(OUT / "pack_inputs.json")
    archive = read(OUT / "archive_readback.json")
    assert archive["status"] == "PASS_QP1_ARCHIVE_READBACK"
    assert archive["inputs_sha256"] == sha(OUT / "pack_inputs.json") and archive["members"] == inputs["resources"]
    path = OUT / "package"
    actual = inventory(path)
    assert actual[ARCHIVE] == archive["archive_sha256"]
    assert actual[XL] == read(OUT / "verification.json")["registration"]["xl_sha256"]
    assert actual[SCRIPT] == read(HERE / "compile_01/result.json")["candidate_script_sha256"]
    fixtures = read(TRUCK / "fixtures.json")
    assert fixtures["status"] == "PASS_BOUNDED_TRUCK_SIGNALS"
    assert fixtures["cooked_scene_json_sha256"] == sha(TRUCK / "scene.json") and len(fixtures["cases"]) == 5
    before = {r["path"]: r["sha256"] for r in installed["core_files"]}
    assert actual.keys() == before.keys() and len(actual) == 51
    assert {p for p in actual if actual[p] != before[p]} == {ARCHIVE, XL, SCRIPT}
    target = HERE / "QP1_Core51_01.zip"
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for p in before:
            z.write(path / p, p)
    with zipfile.ZipFile(target) as z:
        assert len(z.namelist()) == 51 and set(z.namelist()) == set(before) and z.testzip() is None
        assert all(z.read(p) == (path / p).read_bytes() for p in actual)
    write(OUT / "package_manifest.json", {
        "status": "STAGED_QP1_READBACK_VERIFIED", "predecessor": "JB3", "installed_manifest_sha256": INSTALLED_SHA,
        "archive_sha256": actual[ARCHIVE], "archive_payloads": len(archive["members"]),
        "changed_depots": inputs["changed"], "new_depots": inputs["new"],
        "changed_paths": sorted((ARCHIVE, XL, SCRIPT)),
        "files": [{"path": p, "sha256": actual[p], "bytes": (path / p).stat().st_size} for p in before],
        "verification_sha256": sha(OUT / "verification.json"),
        "truck_fixtures_sha256": sha(TRUCK / "fixtures.json"),
        "compile_sha256": sha(HERE / "compile_01/result.json"),
        "archive_readback_sha256": sha(OUT / "archive_readback.json"),
        "zip": str(target), "zip_sha256": sha(target), "gameplay": "PENDING", "game_writes": 0, "save_writes": 0,
    })
    print(f"Verified all 51 ZIP files. SHA256 {sha(target)}")


if __name__ == "__main__":
    {"prepare-pack": prepare_pack, "seal": seal}[sys.argv[1]]()
