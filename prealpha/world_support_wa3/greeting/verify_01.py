"""Validate the bounded native receptionist greeting without community activation."""
import copy
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks = []
pins = []
def check(name, result):
    checks.append({"check": name, "pass": bool(result)})
    assert result, name
def pin(p):
    p = p.resolve()
    pins.append({"path": str(p), "sha256": sha(p)})
def expand(x):
    if isinstance(x, dict):
        if "HandleId" in x:
            return expand(x["Data"])
        return {k: expand(v) for k, v in x.items() if k != "sockets"}
    if isinstance(x, list):
        return [expand(v) for v in x]
    return x
def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)

proof = read(H / "build_proof_01.json")
source = read(Path(proof["native"] + ".json"))["Data"]["RootChunk"]
native = next(n for n in expand(source)["graph"]["nodes"] if n["id"] == 3)["phaseGraph"]["nodes"]
native = {n["id"]: n for n in native}
back = read(H / "readback_01.json")["Data"]["RootChunk"]
nodes = {n["id"]: n for n in expand(back)["graph"]["nodes"]}
bindings = {"#pac_wwd_ripper_com": proof["community"], "#pac_wwd_ripdoc_01_tr_rec": proof["trigger"]}
for n in native.values():
    for d in walk(n):
        if d.get("$type") == "NodeRef" and d.get("$value") in bindings:
            d["$value"] = bindings[d["$value"]]

def validate(ns, edges):
    assert set(ns) == {0, 100, 101, 102, 3, 4, 7, 8, 9}
    for ident in [4, 7, 8, 9]:
        assert ns[ident] == native[ident], f"Native payload {ident} changed"
    for ident in [100, 3]:
        guard = ns[ident]["condition"]
        assert guard["$type"] == "questLogicalCondition" and guard["operation"] == "AND"
        conditions = guard["conditions"]
        assert len(conditions) == 14
        facts = {d["type"]["factName"]: d["type"]["value"] for d in conditions if d["$type"] == "questFactsDBCondition"}
        expected = dict(proof["facts"])
        if ident == 100:
            expected["PTFRWA3GREETING_WWD_Claimed"] = 0
        assert facts == expected
        ready = [d["type"] for d in conditions if d["$type"] == "questSpawnerCondition"]
        assert len(ready) == 1
        assert ready[0]["$type"] == "questSpawnerReady_ConditionType"
        assert ready[0]["spawnerReference"]["$value"] == proof["community"]
        assert ready[0]["communityEntryNames"] == [{"$type": "CName", "$storage": "string", "$value": "ripdoc_rec"}]
        if ident == 3:
            assert native[3]["condition"] in conditions
    assert ns[101]["type"]["factName"] == "PTFRWA3GREETING_WWD_Claimed" and ns[101]["type"]["value"] == 1
    assert ns[102]["type"]["factName"] == "PTFRWA3GREETING_WWD_Entered" and ns[102]["type"]["value"] == 1
    assert set(edges) == {"0.Out -> 100.In", "100.Out -> 101.In", "101.Out -> 102.In", "102.Out -> 3.In",
                          "3.Out -> 9.In", "9.True -> 4.In", "4.Out -> 8.In", "8.Out -> 7.In", "7.Out -> 3.In"}

validate(nodes, proof["edges"])
check("native payloads, all guards and cooldown-only loop", True)
check("cooked owner hash", sha(Path(proof["path"])) == proof["sha256"])
check("pinned source graph", sha(Path(proof["native"])) == proof["native_sha256"])
current = read(H / "../native_review/greeting_current_native_01/report_01.json")
check("fresh128 archive scan", current["archives"] == 128 and len(current["hits"]) == 3 and not any(h["is_mod"] for h in current["hits"]))
for hit in current["hits"]:
    check("native current bytes " + Path(hit["raw"]).parent.name + "/" + Path(hit["raw"]).name,
          sha(Path(hit["raw"])) == hit["sha256"])
    pin(Path(hit["raw"]))
    if hit["resource"].endswith("pac_wwd_phase.questphase"):
        check("current native greeting donor", hit["sha256"] == proof["native_sha256"])
registry = read(H / "registry_01/report_01.json")
for row in registry["rows"]:
    actual = next(h for h in current["hits"] if Path(h["archive"]).name == row["archive"])
    check(row["archive"] + " registry current raw identity", row["raw_sha256"] == actual["sha256"])
    found = row["found"]
    check(row["archive"] + " exact community", len(found) == 1 and found[0]["ref"] == proof["community"] and found[0]["hash"] == proof["community_hash"])
    data = read(Path(found[0]["json"]))
    check(row["archive"] + " exact native receptionist entry", len([e for e in data["template"]["Data"]["entries"] if e["Data"]["entryName"]["$value"] == "ripdoc_rec"]) == 1)
    pin(Path(found[0]["json"]))

env = H / "../environment_variants"
placements = read(env / "decode_01/ep1_1_nightcity_9155791958214798761.streamingsector.placements.json")
triggers = [p for p in placements["placements"] if p["quest_ref"] == proof["trigger"]]
check("current exact exterior trigger", len(triggers) == 1 and triggers[0]["node"] == 233 and triggers[0]["type"] == "worldTriggerAreaNode")
definitions = read(env / "decode_01/ep1_1_nightcity_9155791958214798761.streamingsector.nodes.json")
trigger = next(n["definition"] for n in definitions["nodes"] if n["node"] == 233)
check("native player trigger enabled", trigger["notifiers"][0]["Data"]["includeChannels"] == "TC_Player" and trigger["notifiers"][0]["Data"]["isEnabled"] == 1)
oldraw = env / "extract_01/ep1_1_nightcity_9155791958214798761.streamingsector"
newraw = env / "extract_02/ep1_1_nightcity_9155791958214798761.streamingsector"
check("decoded trigger equals fresh current128 native bytes", sha(oldraw) == sha(newraw))

negative = []
for name in ["cooldown removed", "community alias drift", "Activate inserted", "cooldown bypass"]:
    altered = copy.deepcopy(nodes)
    edges = list(proof["edges"])
    if name == "cooldown removed": altered[7]["condition"]["type"]["days"] = 0
    elif name == "community alias drift": altered[4]["type"]["params"][0]["puppetRef"]["reference"]["$value"] = "#pac_wwd_ripper_com"
    elif name == "Activate inserted": altered[2] = native[2]
    else: edges.append("4.Out -> 3.In")
    try:
        validate(altered, edges)
    except AssertionError:
        negative.append(name)
    else:
        raise AssertionError("Negative control accepted: " + name)
check("four negative controls rejected", len(negative) == 4)
for p in [H / "build_01.ps1", H / "build_proof_01.json", H / "readback_01.json", Path(proof["native"]),
          Path(proof["native"] + ".json"), H / "registry_01/report_01.json",
          H / "../native_review/greeting_current_native_01/report_01.json", env / "extract_02/report_01.json",
          env / "decode_01/ep1_1_nightcity_9155791958214798761.streamingsector.placements.json",
          env / "decode_01/ep1_1_nightcity_9155791958214798761.streamingsector.nodes.json", newraw]:
    pin(p)
result = {"status": "PASS", "check_count": len(checks), "checks": checks, "negative_controls": negative,
          "resources": [{"depot": proof["resource"].replace("/", "\\"), "sha256": proof["sha256"]}], "pins": pins,
          "scope": "Native WestWind receptionist greeting with exact alive check, player trigger and one-game-day cooldown; native Activate omitted, no NPC spawning or native facts written.",
          "limits": "Requires already-active native ripdoc_rec. Does not activate inactive communities. No runtime proof.",
          "game_writes": 0, "save_writes": 0}
(H / "assessment_01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": result["status"], "checks": len(checks), "negative_controls": len(negative)}))
