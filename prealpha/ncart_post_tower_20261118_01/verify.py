"""Validate native and serialized boarding routes, then stage the full successor Core."""
import binascii
import copy
import gzip
import json
import re
import shutil
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
TOUR = ROOT.parent / "welcome_to_paradise_cut_20261118_01"
PARENT = TOUR / "candidate_01"
PARENT_SHA = "FF043272463E7CEE53E367495DA589F18158F049A3F970455C56BD1FDAB111E0"
sys.path.insert(0, str(ROOT.parent / "phone_support_ph1"))
sys.path.insert(0, str(ROOT.parent / "misty_rooftop_seat_20261117_01"))
import model
from build import ARCHIVE, GAME, XL, plain, read, row, safe, sha, verify_rows, write
from validate import crc16

PREFIX = "towercontinued\\ncart\\"
BASE = "base\\open_world\\metro\\ue_metro\\"
RIDE = BASE + r"scenes\ue_metro_01_train_ride.scene"
MAIN = BASE + "ue_metro_main.questphase"
TRAIN = BASE + r"phases\ue_metro_train_handler.questphase"
LIP = r"towercontinued\sidejob_repair_sr1\en-us.lipmap"


def chunk(path):
    p = Path(path)
    data = gzip.open(p, "rb").read() if p.suffix == ".gz" else p.read_bytes()
    return json.loads(data)["Data"]["RootChunk"]


def dependency_paths(root):
    return {v["$value"] for v in model.walk(root) if v.get("$type") == "ResourcePath"
            and v["$value"].endswith((".questphase", ".scene"))}


def check_registration(package, parent_graph, addition):
    previous = (PARENT / "package" / XL).read_bytes()
    actual = (package / XL).read_bytes()
    assert actual.count(addition) == 1 and actual.replace(addition, b"", 1) == previous
    ids = {h["Data"]["id"] for h in parent_graph["graph"]["Data"]["nodes"]}
    registered = {}
    for folder in (GAME / "archive/pc", GAME / "mods"):
        for path in folder.rglob("*.xl"):
            plain(path)
            content = (package / XL if path == GAME / XL else path).read_text(encoding="utf-8-sig")
            section = re.search(r"(?ms)^quest:\s*\n(.*?)(?=^\w|\Z)", content)
            if not section:
                assert not re.search(r"(?m)^quest\s*:", content)
                continue
            for block in re.split(r"(?m)^    - path:\s*", section[1])[1:]:
                parent = re.search(r"(?m)^      parent: (.+)$", block)
                if not parent or parent[1].strip() != r"ep1\quest\ep1.quest":
                    continue
                depot = block.splitlines()[0].strip()
                assert re.search(r"(?m)^        node: \[1\]\s*$", block)
                assert re.search(r"(?m)^        socket: Out\s*$", block)
                key = depot + ":1"
                i = binascii.crc_hqx(key.encode(), 65535)
                assert i == crc16(key) and i not in ids and i not in registered, (depot, i)
                registered[i] = depot
    return next(i for i, d in registered.items() if d == PREFIX + "entry.questphase")


def check_scene(stock, actual):
    expected = copy.deepcopy(stock)
    # Cooked TweakDBIDs in the stock export carry resolved names in this registry.
    for w in model.walk(expected):
        if w.get("$type") == "TweakDBID" and w["$storage"] == "string":
            data = w["$value"].encode()
            w.update({"$storage": "uint64", "$value": str(len(data) << 32 | zlib.crc32(data))})
    defs = {w["HandleId"]: w["Data"] for w in model.walk(expected) if "HandleId" in w}
    def resolve(h):
        return defs[h.get("HandleId", h.get("HandleRefId"))]
    nodes = {n["nodeId"]["id"]: n for h in resolve(expected["sceneGraph"])["graph"] if (n := resolve(h))}
    johnny, = [a for a in expected["actors"] if a["actorName"] == "Johnny"]
    for k in ("isEnabled", "spawnOnStart", "alwaysSpawned"):
        assert johnny["spawnDespawnParams"][k] == 1
        johnny["spawnDespawnParams"][k] = 0
    for start, ordinal, end, target, stamp in ((2199,1,2203,860,4),(2923,0,2203,860,4),(3368,1,3377,640,7)):
        dest, = [d for s in nodes[start]["outputSockets"] if (s["stamp"]["name"],s["stamp"]["ordinal"]) == (0,ordinal)
                 for d in s["destinations"]]
        assert (dest["nodeId"]["id"], dest["isockStamp"]["ordinal"]) == (end,0)
        dest["nodeId"]["id"], dest["isockStamp"]["ordinal"] = target, stamp
    assert expected == actual
    stack = [p["nodeId"]["id"] for p in actual["entryPoints"]]
    live = set()
    while stack:
        i = stack.pop()
        if i in live:
            continue
        live.add(i)
        stack.extend(d["nodeId"]["id"] for s in nodes[i]["outputSockets"] for d in s["destinations"])
    assert {2203,3377,2287,3440}.isdisjoint(live)
    actor = johnny["actorId"]["id"]
    for i in live:
        for h in nodes[i].get("events", []):
            for w in model.walk(resolve(h)):
                assert (w.get("$type"),w.get("id")) not in (("scnActorId",actor),("scnPerformerId",actor << 8 | 1))
    assert {e["nodeId"]["id"] for e in actual["exitPoints"]} <= live


def check_entry(path, station_scene):
    g = model.model(path)["root"]
    assert g["edges"] == [(0,"Out",1,"In"),(1,"Out",2,"In"),(2,"Out",3,"In"),
                          (3,"False",1,"In"),(3,"True",4,"In"),(4,"Out",6,"In1")]
    n = g["nodes"]
    assert n[4]["type"]["factName"] == "PTFRNCART_Issued" and n[4]["type"]["value"] == 1
    assert n[6]["phaseResource"]["DepotPath"]["$value"] == PREFIX + "service.questphase"
    assert not chunk(path)["phasePrefabs"] and not n[6]["phaseInstancePrefabs"]
    gate = n[3]["condition"]
    assert gate["conditions"] == n[1]["condition"]["conditions"] + [n[2]["condition"]]
    facts = {w["factName"]: w["value"] for w in model.walk(gate) if w.get("$type") == "questVarComparison_ConditionType"}
    assert {k for k,v in facts.items() if v == 1} == {"PostTowerFreeRoamActive","PTFRPA2_Finished","q307_done",
        "q307_finished","q307_2079","q307_main_game_killed","q307_ep1_killed"}
    assert {k for k,v in facts.items() if v == 0} == {"PTFRPA2_Fault","q307_active","q307_debug_reset",
        "q115_point_of_no_return","PTFRNCART_Issued","ue_metro_ride_started","ue_metro_player_in_train_transition","watson_prolog_lock"}
    for w in model.walk(gate):
        if w.get("$type") == "questLogicalCondition":
            assert w["operation"] == "AND"
        elif w.get("$type") == "questVarComparison_ConditionType":
            assert w["comparisonType"] == "Equal"
    predicate, = [w for w in model.walk(gate) if w.get("$type") == "questInventory_ConditionType"]
    assert any(w == predicate for w in model.walk(station_scene))
    assert predicate["itemID"]["$value"] == "Items.ue_metro_ncart_city_pass"
    def accepts(state, quantity):
        return all(state[k] == v for k,v in facts.items()) and quantity >= predicate["quantity"]
    assert accepts(facts,1) and not accepts(facts,0)
    assert all(not accepts(facts | {k:1-v},1) for k,v in facts.items())


def check_graphs(paths, cooked):
    original = model.model(paths[MAIN])
    service = model.model(cooked[PREFIX+"service.questphase"])
    assert original.keys() - service.keys() == {"root/102"}
    assert original["root/8"] == service["root/8"]
    old = original["root"]
    assert old["nodes"].keys() - service["root"]["nodes"].keys() == {7,102}
    assert set(service["root"]["edges"]) == {e for e in old["edges"] if e[0] not in (7,102) and e[2] not in (7,102)}
    stock_support = chunk(paths[MAIN])["phasePrefabs"]
    assert stock_support == chunk(cooked[PREFIX+"service.questphase"])["phasePrefabs"]
    assert [v["prefabNodeRef"]["$value"] for v in stock_support] == ["#ue_metro_pr_main"]
    old["nodes"][16]["phaseResource"]["DepotPath"]["$value"] = PREFIX+"train_handler.questphase"
    assert service["root"]["nodes"] == {i:n for i,n in old["nodes"].items() if i not in (7,102)}
    train = model.model(paths[TRAIN])
    for i in (4,10):
        train["root"]["nodes"][i]["sceneFile"]["DepotPath"]["$value"] = PREFIX+"train_ride.scene"
    assert train == model.model(cooked[PREFIX+"train_handler.questphase"])
    loader = model.model(paths[BASE+r"phases\ue_metro_station_loader.questphase"])["root"]
    stations = {v["triggerAreaRef"]["$value"] for n in loader["nodes"].values() for v in model.walk(n)
                if v.get("type") == "IsInside" and "_tr_station_" in v["triggerAreaRef"]["$value"]}
    assert len(stations) == 19
    stack, visited = [PREFIX+"entry.questphase"], set()
    while stack:
        d = stack.pop()
        if d in visited:
            continue
        visited.add(d)
        if d.endswith(".questphase"):
            stack.extend(dependency_paths(chunk((cooked | paths)[d])))
    assert len(visited) == 22 and BASE+r"phases\ue_metro_cleanup.questphase" in visited
    assert MAIN not in visited and TRAIN not in visited and RIDE not in visited
    return len(visited)


def main():
    assert sha(PARENT/"core_manifest.json") == PARENT_SHA
    parent = read(PARENT/"core_manifest.json")
    verify_rows(PARENT/"package", parent["core_files"])
    providers = read(WORK/"sources_01/providers.json")
    registry = ROOT.parent/"quest_resume_registry_20261112_01/evidence_02/resources.jsonl"
    registered = {r["sha256"]:r for line in registry.open(encoding="utf-8") if (r:=json.loads(line)).get("json")}
    paths = {}
    for h in providers["hits"]:
        assert sha(Path(h["raw"])) == h["sha256"] and h["depot"] not in paths
        if h["depot"].endswith(".lipmap"):
            continue
        r = registered[h["sha256"]]
        assert r["depot"] == h["depot"] and sha(Path(r["json"])) == r["json_sha256"]
        paths[h["depot"]] = Path(r["json"])
    assert len(paths) == 25
    cooked = {r["depot"]:Path(r["json"]) for r in read(WORK/"cook_01/manifest.json")["resources"]
              if sha(Path(r["json"])) == r["json_sha256"] and sha(Path(r["raw"])) == r["sha256"]}
    assert len(cooked) == 5
    check_entry(cooked[PREFIX+"entry.questphase"],chunk(paths[BASE+r"scenes\ue_metro_02_station_v3.scene"]))
    check_scene(chunk(paths[RIDE]),chunk(cooked[PREFIX+"train_ride.scene"]))
    closure = check_graphs(paths,cooked)
    prev = chunk(TOUR/"work/assets_02/readback"/(LIP+".json"))
    lips = chunk(cooked[LIP])
    assert all(lips[k][:-1] == prev[k] if k in ("scenePaths","sceneEntries") else lips[k] == prev[k] for k in prev)
    def fnv(s):
        key = 14695981039346656037
        for c in s.encode():
            key = (key ^ c)*1099511628211 & ((1<<64)-1)
        return str(key)
    ref = chunk(ROOT.parent/"welcome_to_paradise_20261118_01/work/lipmap_comparison/original.json")
    assert lips["scenePaths"][-1] == fnv(PREFIX+"train_ride.scene")
    assert lips["sceneEntries"][-1] == ref["sceneEntries"][ref["scenePaths"].index(fnv(RIDE))]
    saved = read(WORK/"owners.json")["saves"]
    before, after = saved[:2]
    full = "0/2/82/3/19/156/6/9"
    assert len([h for h in before["handlers"] if h["route"] == full]) == 20 and not after["handlers"]
    for state, inventory, owner in zip(read(WORK/"facts.json")["saves"], read(WORK/"pass.json")["saves"],saved,strict=True):
        assert state["save_sha256"] == inventory["sha256"] == owner["save_sha256"]
        assert any(h["inventory"]=="1" and h["quantity"]==1 for h in inventory["matching_items"])
    pack = read(WORK/"pack_01/readback.json")
    assert pack["unchanged_members"] == 1767 and pack["packed_members"] == 1772
    packed = WORK/"pack_01/package"
    assert sha(packed/ARCHIVE) == pack["archive_sha256"]
    node = check_registration(packed,chunk(paths[r"ep1\quest\ep1.quest"]),pack["xl_addition"].encode())
    candidate = ROOT/"candidate_01"
    assert not candidate.exists()
    pkg = candidate/"package"
    for f in parent["core_files"]:
        name = f["path"]
        target = safe(pkg,name)
        target.parent.mkdir(exist_ok=True,parents=True)
        shutil.copyfile(safe(packed if name in (XL,ARCHIVE) else PARENT/"package",name),target)
    files = [row(pkg,f["path"]) for f in parent["core_files"]]
    assert {a["path"] for a,b in zip(files,parent["core_files"]) if a != b} == {ARCHIVE,XL}
    verify_rows(pkg,files)
    write(candidate/"core_manifest.json",dict(parent,predecessor_candidate_sha256=PARENT_SHA,
          core_files=files,asset_assessment_sha256=sha(WORK/"pack_01/readback.json")))
    proof = dict(status="STAGED_OFFLINE",core_sha256=sha(candidate/"core_manifest.json"),core_files=len(files),
                 archive_members=1772,private_resources=4,phase_and_scene_closure=closure,
                 providers=len(providers["archives"]),station_areas=19,archive_xl_node=node,
                 game_writes=0,save_writes=0,gameplay="pending")
    write(candidate/"verification.json",proof)
    print(json.dumps(proof))


if __name__ == "__main__":
    main()
