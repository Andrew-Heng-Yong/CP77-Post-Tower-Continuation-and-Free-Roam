"""Verify the exact Cuckoo's Nest findings against read-only captures."""

import argparse
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
sys.path.insert(0, str(WORKSPACE / "tools" / "parity_audit"))
from common import read, sha, value, walk
from model import Resource, reachable

DISTRICT = r"base\open_world\street_stories\santo_domingo\rancho_corronado"
GIG = DISTRICT + r"\sts_std_rcr_02"
NATIVE = GIG + r"\phases\sts_std_rcr_02_phase.questphase"
LEGACY = GIG + r"\scenes\sts_std_rcr_02_scene.scene"
DIXON = GIG + r"\scenes\sts_std_rcr_02_dixon.scene"
EXPECTED_NULLS = {
    ("2", "In"): ("2464", "2463"),
    ("11", "In"): ("2405", "2404"),
    ("13", "In"): ("2425", "2424"),
    ("15", "In"): ("2444", "2443"),
}
EMBEDDED_NULLS = {
    ("2", "In"): ("7189", "7188"),
    ("11", "In"): ("7130", "7129"),
    ("13", "In"): ("7150", "7149"),
    ("15", "In"): ("7169", "7168"),
}
KEY = "118782818377"
UNKNOWN = "114327022403"
GUARD = "Character.rcr_02_enemy_security_keycard"


def null_sources(resource, graph):
    result = {}
    for handle in graph["nodes"]:
        node = resource.d(handle)
        for socket_handle in node.get("sockets", ()):
            socket = resource.d(socket_handle)
            for connection_handle in socket.get("connections", ()):
                connection = resource.d(connection_handle)
                if connection["source"] is None:
                    assert resource.hid(connection["destination"]) == resource.hid(socket_handle)
                    result[str(node["id"]), value(socket["name"])] = (
                        resource.hid(connection_handle), resource.hid(socket_handle)
                    )
    return result


def condition_payload(node, embedded=False):
    payload = node["payload"]
    if embedded:
        payload = payload["questNode"]
    return payload["condition"]["type"]


def player_has_one(predicate, item):
    return (
        predicate["$type"] == "questInventory_ConditionType"
        and predicate["isPlayer"] == 1
        and predicate["comparisonType"] == "GreaterOrEqual"
        and predicate["quantity"] == 1
        and value(predicate["itemID"]) == item
    )


def run(capture):
    checks = []

    def check(name, passed, evidence=None):
        if not passed:
            raise ValueError(f"{name}: {evidence}")
        checks.append({"check": name, "evidence": evidence})

    index = read(capture / "providers.json")
    providers = defaultdict(list)
    for row in index["providers"]:
        check("extracted byte and export hashes", (
            sha(capture / row["raw"]) == row["sha256"]
            and sha(capture / row["json"]) == row["json_sha256"]
        ), row["depot"])
        providers[row["depot"]].append(row)
    check("unique providers for each live target; none for the orphan scene", (
        set(index["targets"]) == providers.keys() | {LEGACY}
        and all(len(rows) == 1 for rows in providers.values())
        and all(
            Path(rows[0]["provider"]).name == (
                "zzzz_PTFR_Combined.archive" if depot.startswith("towercontinued") else "basegame_4_gamedata.archive"
            )
            for depot, rows in providers.items()
        )
    ), {"archives": len(index["archives"]), "missing_depot": LEGACY})
    installed = Path(index["installed_manifest"])
    check("QR19 manifest and archive hashes", (
        sha(installed) == index["installed_manifest_sha256"]
        and all(sha(row["path"]) == row["sha256"] for row in index["core"])
    ), index["core"])

    def resource(depot):
        return Resource(read(capture / providers[depot][0]["json"]))

    historical_dir = WORKSPACE / "research" / "gig_restoration" / "batch_b4" / "sources"
    historical = {row["resource"]: row for row in read(historical_dir / "inventory.json")}
    older = {}
    for depot in (NATIVE, DIXON):
        row = historical[depot]
        relative = Path(*depot.split("\\"))
        raw = historical_dir / "raw" / relative
        decoded = historical_dir / "json" / (str(relative) + ".json")
        check("historical byte and export hashes", (
            sha(raw) == row["raw_sha256"] and sha(decoded) == row["json_sha256"]
        ), depot)
        older[depot] = Resource(read(decoded))
    check("Dixon scene is byte-identical to historical vanilla", (
        historical[DIXON]["raw_sha256"] == providers[DIXON][0]["sha256"]
    ), providers[DIXON][0]["sha256"])

    native = resource(NATIVE)
    district = resource(DISTRICT + r"\sts_std_rancho_corronado.questphase")
    embedded = next(row["Content"] for row in district.obj["Data"]["EmbeddedFiles"] if value(row["FileName"]) == NATIVE)
    graphs = native.normalize()["graphs"]
    district_graphs = district.normalize()["graphs"]
    check("all native story graphs agree across three captures", (
        older[NATIVE].normalize()["graphs"] == graphs
        and all(district_graphs[f"embedded/{NATIVE}/{name}"] == graph for name, graph in graphs.items())
    ), {"graphs": len(graphs)})
    for label, source, root, expected in (
        ("older vanilla", older[NATIVE], older[NATIVE].root, EXPECTED_NULLS),
        ("installed standalone vanilla", native, native.root, EXPECTED_NULLS),
        ("installed district embedded vanilla", district, embedded, EMBEDDED_NULLS),
    ):
        actual = null_sources(source, source.d(root["graph"]))
        check("literal null sources in " + label, actual == expected, [
            {"node": node, "input": socket, "connection": handles[0], "destination": handles[1]}
            for (node, socket), handles in sorted(actual.items(), key=lambda row: int(row[0][0]))
        ])
    root = graphs["root"]
    check("none of the orphan paths are reachable from the native input", (
        set(root["reachable"]) == {"0", "17", "8", "9", "1"}
        and {node for node, row in root["nodes"].items() if LEGACY in row["refs"]} == {"3", "12", "14", "16"}
    ), root["edges"])

    u9 = r"towercontinued\native_gigs_u9\sts_std_rcr_02"
    origin = read(WORKSPACE / "research" / "gig_restoration" / "native_gigs_u9" / "manifest.json")["resources"]
    for suffix in ("entry", "credit", "map0", "map1"):
        depot = u9 + f"_{suffix}.questphase"
        check("private payload matches U9 pin", providers[depot][0]["sha256"] == origin[depot], depot)
    wrapper = resource(u9 + "_entry.questphase").normalize()["graphs"]["root"]
    check("installed wrapper calls the exact native In1", (
        ["65004", "Out", "7", "In1"] in wrapper["edges"]
        and wrapper["nodes"]["7"]["refs"] == [NATIVE]
        and root["entries"]["In1"] == "0"
    ), NATIVE)
    callers = graphs["root/9/5/22"]
    check("active nested phase calls the native Dixon entry", (
        ["38", "Out", "52", "dixon"] in callers["edges"]
        and "52" in callers["reachable"]
        and callers["nodes"]["52"]["refs"] == [DIXON]
    ), "root/9/5/22:52.dixon")

    community = resource(GIG + r"\communities\sts_std_rcr_02_enemies.community")
    guards = [node for node in walk(community.root) if node.get("$type") == "communitySpawnEntry"
              and value(node.get("entryName")) == "enemy_005"]
    check("original community binds the exact guard record", (
        len(guards) == 1 and value(guards[0]["characterRecordId"]) == GUARD
    ), GUARD)
    capture_rows = read(capture / "tweakdb.json")
    check("both current and historical base and expansion databases were read", (
        sorted(Path(row["path"]).name for row in capture_rows) == ["tweakdb.bin"] * 2 + ["tweakdb_ep1.bin"] * 2
        and len({row["sha256"] for row in capture_rows}) == 4
    ))
    for database in capture_rows:
        records = {row["id"]: row for row in database["records"]}
        guard = next(row for row in records.values() if row["name"] == GUARD)
        table = records[guard["fields"]["lootDrop"]["id"]]
        item = records[table["fields"]["lootItems"][0]["id"]]
        check("guard loot yields the named key; the scene's raw ID has no definition", (
            sha(database["path"]) == database["sha256"]
            and table["type"] == "gamedataLootTable_Record"
            and len(table["fields"]["lootItems"]) == 1
            and item["type"] == "gamedataLootItem_Record"
            and item["fields"]["itemID"]["id"] == KEY
            and item["fields"]["dropCountMin"] == item["fields"]["dropCountMax"] == item["fields"]["dropChance"] == "1"
            and item["fields"]["playerPrereqID"]["id"] == "0"
            and records[KEY]["name"] == "Keycards.rcr_02_keycard_doc"
            and records[KEY]["type"] == "gamedataItem_Record"
            and records[UNKNOWN]["type"] is None
            and records[UNKNOWN]["name"] is None
        ), {"database": database["path"], "sha256": database["sha256"], "loot_table": table["name"], "loot_item": item["name"]})
    objectives = graphs["root/9/3"]
    check("authored key objective consumes the guard's keycard identity", (
        player_has_one(condition_payload(objectives["nodes"]["49"]), "Keycards.rcr_02_keycard_doc")
        and ["49", "Out", "13", "Succeeded"] in objectives["edges"]
        and objectives["nodes"]["13"]["journal_paths"][0].endswith("/key")
    ), "root/9/3:49.Out to 13.Succeeded")

    scene = resource(DIXON).normalize()["graphs"]["scene"]
    nodes = scene["nodes"]
    edges = scene["edges"]
    check("Dixon's inventory condition remains a different exact ID", (
        player_has_one(condition_payload(nodes["86"], embedded=True), UNKNOWN)
        and UNKNOWN != KEY
        and ["84", "0:0", "86", "0:1"] in edges
    ), "scene:86")
    guard = condition_payload(nodes["152"], embedded=True)
    check("both scene branches converge with the native guard, distance and dialogue preserved", (
        guard["$type"] == "questCharacterKilled_ConditionType"
        and guard["defeated"] == guard["killed"] == guard["unconscious"] == 1
        and [value(name) for name in guard["objectRef"]["names"]] == ["enemy_005"]
        and value(guard["objectRef"]["reference"]) == "#rcr_02_com_enemies"
        and ["86", "0:0", "158", "0:0"] in edges
        and ["86", "0:1", "152", "0:1"] in edges
        and ["158", "0:0", "6", "0:0"] in edges
        and ["152", "0:0", "88", "0:0"] in edges
        and ["88", "0:0", "244", "0:1"] in edges
        and ["244", "0:0", "192", "0:0"] in edges
        and ["192", "0:0", "249", "0:0"] in edges
        and ["249", "0:0", "6", "0:0"] in edges
        and condition_payload(nodes["244"], embedded=True)["distanceDefinition2"]["distanceValue"] == 4
        and sum(event["$type"] == "scnDialogLineEvent" for event in nodes["192"]["payload"]["events"]) == 2
        and "82" in reachable(nodes, edges, ["6"])
        and any(write["factName"] == "rcr_02_jason_ready" and write["value"] == 1 for write in nodes["82"]["writes"])
    ), {"choice": "6", "guard": "152", "distance": "244", "dialogue": "192", "ready_writer": "82"})

    altered = Resource(deepcopy(native.obj))
    altered_root = altered.d(altered.root["graph"])
    source_node = next(altered.d(handle) for handle in altered_root["nodes"] if altered.d(handle)["id"] == 17)
    source_handle = next(handle for handle in source_node["sockets"] if value(altered.d(handle)["name"]) == "False")
    connection_handle = EXPECTED_NULLS[("11", "In")][0]
    altered.handles[connection_handle]["source"] = {"HandleRefId": altered.hid(source_handle)}
    altered.d(source_handle)["connections"].append({"HandleRefId": connection_handle})
    check("control detects speculative rewiring of an orphan to a live socket", (
        null_sources(altered, altered_root) != EXPECTED_NULLS
        and {"11", "12"} <= set(altered.normalize()["graphs"]["root"]["reachable"])
    ), "17.False to 11.In would activate a scene with no provider")
    altered_item = deepcopy(condition_payload(nodes["86"], embedded=True))
    altered_item["itemID"]["$value"] = KEY
    check("control detects silently substituting the guard's key for the unknown ID", (
        not player_has_one(altered_item, UNKNOWN) and player_has_one(altered_item, KEY)
    ), "would take 86.True and skip the existing guard and dialogue path")

    return {
        "assessment": "INHERITED_ORPHANS_AND_UNRESOLVED_STOCK_ID",
        "runtime_changes": [],
        "checks": checks,
        "limits": [
            "Historical author intent and the raw item's original name or producer are unresolved.",
            "The known loot route targets the same guard as the native fallback and supplies a distinct ID.",
            "Graph reachability and stock record lookup do not establish live guard or scene behavior.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = run(args.capture)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{len(report['checks'])} checks passed")
