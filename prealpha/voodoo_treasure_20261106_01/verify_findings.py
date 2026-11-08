"""Check the installed Voodoo Treasure routes and the new binding evidence."""

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from bind_sector import HERE, MASK, Sector, decode, node_hash, read_pinned

WORKSPACE = HERE.parents[1]
sys.path.insert(0, str(WORKSPACE / "prealpha/phone_support_ph1"))
from model import model


GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077")
CORE = WORKSPACE / "prealpha/quest_restoration_qr19/candidate_01"
ARCHIVE = GAME / "archive/pc/mod/zzzz_PTFR_Combined.archive"
SCRIPT = Path("r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds")
STASH = r"ep1\quest\main_quests\q304\phases\q304_slider_stash.questphase"
WRAPPER = r"towercontinued\sidejobs_s23\ep1\voodoo_boot.questphase"
BLOCK = r"base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock"
NATIVE_SHA = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def controller_key(entity):
    m = 0xC6A4A7935BD1E995
    t = (m * node_hash("controller")) & MASK
    return (m * (entity ^ ((m * (t ^ (t >> 47))) & MASK))) & MASK


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="verification.json")
    args = parser.parse_args()
    output = HERE / args.out
    assert output.parent == HERE and not output.exists()
    checks = []

    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)

    archive_sha = sha(ARCHIVE)
    check("installed QR19 combined archive", archive_sha == "2988A138B7AA529714BA1762A338C89D624C3C11D1C8F7449C6BF9571F216A2B")
    check("installed S23 equals pinned candidate", sha(GAME / SCRIPT) == sha(CORE / "package" / SCRIPT))
    check("installed engine matches native captures", sha(GAME / "bin/x64/Cyberpunk2077.exe") == NATIVE_SHA)
    assets = read(HERE / "assets_02/manifest.json")["providers"]
    providers = {}
    for row in assets:
        check(f"captured raw payload {Path(row['raw']).name}", sha(Path(row["raw"])) == row["sha256"])
        if "json_sha256" in row:
            check(f"typed export {Path(row['json']).name}", sha(Path(row["json"])) == row["json_sha256"])
        providers.setdefault(row["depot"], []).append(row)
    check("native and private phases each have one archive provider", len(providers[STASH]) == len(providers[WRAPPER]) == 1)
    vanilla, private = providers[STASH][0], providers[WRAPPER][0]
    check("installed private payload equals QR19 source", private["sha256"] == sha(CORE / "archive_source" / WRAPPER))
    check("EP1 block capture still matches scan authority", any(
        row["sha256"] == "4F17762B48D9F5019228B1BF930558A9CC1E7C365E7002725D670A23585215B9"
        and row["provider"].endswith("ep1_1_nightcity.archive") for row in providers[BLOCK]
    ))
    native_graph = model(vanilla["json"])["root"]
    graph = model(private["json"])
    n = native_graph["nodes"]
    p = graph["root"]["nodes"]
    check("original body called by root/100/4", graph["root/100"]["nodes"][4]["phaseResource"]["DepotPath"]["$value"] == STASH)
    for i in (2, 3, 90):
        terms = p[i]["condition"]["conditions"]
        load = [t for t in terms if t["$type"] == "questNodeLoadingCondition"]
        inverse = [t for t in terms if t["$type"] == "questLogicalCondition" and t["operation"] == "NOR"]
        check(f"loaded closed-door gate {i}", len(load) == len(inverse) == 1 and
              load[0] == n[2]["condition"] and inverse[0]["conditions"] == [n[3]["condition"]])
        check(f"four exact inactive journals at gate {i}", len([
            t for t in terms if t["$type"] == "questLogicalCondition" and t["operation"] == "OR" and
            len(t["conditions"]) == 1 and t["conditions"][0]["$type"] == "questJournalCondition" and
            t["conditions"][0]["type"]["state"] == "Inactive"
        ]) == 4)
    check("loaded-gate recheck, claim, late fault and entry edges", set([
        (2, "Out", 3, "In"), (3, "False", 2, "In"), (3, "True", 4, "In"), (4, "Out", 89, "In"),
        (89, "Out", 90, "In"), (90, "False", 91, "In"), (90, "True", 92, "In")
    ]).issubset(graph["root"]["edges"]))
    check("native false-journal branch still reaches Inject", (10, "False", 12, "In2") in native_graph["edges"] and
          (12, "Out1", 22, "In") in native_graph["edges"])
    check("all three native inject operations and exact shared target", {
        (operation["itemTDBID"]["$value"], operation["quantity"], operation["operationType"],
         param["objectRef"]["entityReference"]["reference"]["$value"])
        for param in n[22]["type"]["params"] for operation in param["lootOperations"]
    } == {(item, quantity, "Inject", "#q304_slider_stash_loot") for item, quantity in [
        ("Items.money", 8000), ("Items.q304_slider_stash_shard", 1), ("Items.Preset_Lexington_Rook", 1)
    ]})
    check("native empty-container termination route", set([
        (22, "Out", 5, "In"), (5, "Out", 13, "In"), (13, "Out", 6, "In"), (6, "Out", 1, "In")
    ]).issubset(native_graph["edges"]) and n[6]["condition"]["type"]["quantity"] == 0 and n[1]["type"] == "Terminating")
    check("native node 21 requests TerminalControllerPS on the door", all(
        a["deviceControllerClass"]["$value"] == "TerminalControllerPS" and
        a["objectRef"]["$value"] == "#q304_dvc_slider_stash_door" and
        a["deviceAction"]["$value"] == "ForceDisabled" for a in n[21]["type"]["params"]
    ))

    rows = read(HERE / "setups_01/manifest.json")
    bindings = [decode(row) for row in rows]
    check("reproduced placement evidence", json.dumps(bindings, sort_keys=True) ==
          json.dumps(read(HERE / "bindings_01.json"), sort_keys=True))
    placement = next(b for b in bindings if b["source"]["target"]["descriptor"] == 273)
    matches = {m["ref"].rsplit("/", 1)[-1]: m for m in placement["matches"]}
    check("always-loaded reference directory is not the placement", any(
        len(b["listed_refs_without_setups"]) == 5 and not b["matches"] for b in bindings
    ))
    sector = Sector(read_pinned(placement["source"]["captured"], placement["source"]["sha256"]))
    handles, refs, _ = sector.root()
    door = matches["#q304_dvc_slider_stash_door"]
    check("reject joining parallel reference/definition lists", refs.index(door["ref"]) != door["node_index"])
    check("reject treating node index as export index", door["node_index"] + 1 != door["export_index"] and
          sector.chunk(handles[door["node_index"]])[0] == "worldEntityNode")
    row = next(r for r in rows if r["source"]["sha256"] == placement["source"]["sha256"])
    setup = read_pinned(row["buffer_path"], row["sha256"])
    pos = door["setup_index"] * 0x90
    check("reject old packed node-index offset", struct.unpack_from("<Q", setup, pos + 0x78)[0] & 0xFFFFF != door["node_index"])
    instance = read(HERE / "instances_01/manifest.json")
    instances = {}
    for item in instance["instances"]:
        check(f"pinned instance override {item['chunk_type']}", sha(Path(item["raw"])) == item["raw_sha256"]
              and sha(Path(item["decoded"])) == item["decoded_sha256"])
        instances[item["chunk_type"]] = read(Path(item["decoded"]))
    door_ps = instances["DoorController"]["persistentState"]["Data"]
    keypad = instances["TerminalController"]["persistentState"]["Data"]
    loot = instances["LootContainerObjectAnimatedByTransform"]
    check("placed door is normally closed with auto-close off", door_ps["$type"] == "DoorControllerPS" and
          door_ps["doorProperties"]["initialDoorState"] == "CLOSED" and not door_ps["doorProperties"]["automaticallyClosesItself"])
    check("placed keypad's distinct terminal PS has an authored local code", keypad["$type"] == "TerminalControllerPS"
          and keypad["authorizationProperties"]["authorizationDataEntry"]["password"]["$value"] == "941229")
    check("placed container enables area loot with authored quest mark", loot["useAreaLoot"] == 1 and loot["lootTables"] == []
          and loot["persistentState"]["Data"]["markAsQuest"] == 1)
    saved = read(HERE / "saved_02.json")
    expected_ps = {
        str(controller_key(int(door["global_node_id"]))): "DoorControllerPS",
        str(controller_key(int(matches["#q304_dvc_slider_stash_terminal"]["global_node_id"]))): "TerminalControllerPS",
        str(controller_key(int(matches["#q304_dvc_slider_stash"]["global_node_id"]))): "GenericDeviceControllerPS",
        matches["#q304_slider_stash_loot"]["global_node_id"]: "LootContainerObjectAnimatedByTransformPS",
    }
    for i, sample in enumerate(saved["results"], 1):
        check(f"saved sample {i} binds all four placed identities and classes", {
            m["id"]: m["parsed_class"] for m in sample["ps2_matches"]
        } == expected_ps and sample["source_unchanged"])
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"status": "STATIC_AND_PINNED_SAVED_IDENTITY_CHECKS", "checks": checks, "ps2_keys": expected_ps,
                   "archive_sha256": archive_sha, "native_phase": vanilla, "wrapper": private,
                   "limits": ["No native callback execution", "No earlier-claim fixture", "No saved inventory or liveness inference"]},
                  stream, indent=2)
    print(f"{len(checks)} checks passed")


if __name__ == "__main__":
    main()
