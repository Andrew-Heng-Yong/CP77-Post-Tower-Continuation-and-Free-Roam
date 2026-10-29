"""Review passive support in the CE families outside the original477-reference census."""
import json
import hashlib
from collections import Counter
from pathlib import Path

H = Path(__file__).resolve().parent
N = H.parent / "native_review"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks = []
pins = []
def check(name, value):
    checks.append({"check": name, "pass": bool(value)})
    assert value, name
def pin(p):
    p = Path(p).resolve()
    pins.append({"path": str(p), "sha256": sha(p)})
def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)

identity = read(H / "identity_cohort_01.json")
check("94exact current owner identities", len(identity["groups"]) == 94)
convo = read(N / "combat_conversations_native_01/report_01.json")
known = read(N / "conversation_assessment_01.json")
party = read(N / "party_assessment_01.json")
check("fresh128native conversation dependencies", convo["archives"] == 128 and len(convo["hits"]) == 6)
check("previous generic scenes reviewed current128", known["status"] == "PASS_NATIVE_AMBIENT_CONVERSATIONS" and
      known["archives"] == {"groups": 128, "scenes": 128})
approved_speech = set()
for hit in convo["hits"]:
    p = Path(hit["copy"])
    check("native sole dependency " + p.name, "\\mod\\" not in hit["archive"] and sha(p) == hit["sha256"])
    if p.suffix == ".conversations":
        prior = [g for g in known["groups"] if g["depot"] == hit["depot"]]
        check("reviewed exact generic group " + p.name, len(prior) == 1 and prior[0]["sha256"] == hit["sha256"])
    elif p.name.startswith("dancefloor"):
        check("reviewed exact native party scene", party["scene"]["binary_sha256"] == hit["sha256"])
    else:
        d = read(Path(str(p) + ".json"))
        types = Counter(x["$type"] for x in walk(d) if "$type" in x)
        nodes = d["Data"]["RootChunk"]["sceneGraph"]["Data"]["graph"]
        check("chat dialogue graph only " + p.name, all(x["Data"]["$type"] in ["scnStartNode", "scnSectionNode", "scnEndNode"] for x in nodes))
        check("chat dialogue events only " + p.name, {t for t in types if t.endswith("Event")} == {"scnDialogLineEvent"})
        check("chat no native progress operations " + p.name, not any(t.startswith("quest") for t in types))
    approved_speech.add(hit["depot"])
    pin(p); pin(Path(str(p) + ".json"))

allowed = {"worldAISpotNode", "worldCrowdNullAreaNode", "worldSmartObjectNode", "worldTriggerAreaNode",
           "worldDeviceNode", "worldGuardAreaNode", "worldPopulationSpawnerNode", "worldInterestingConversationsAreaNode",
           "worldSpeedSplineNode", "worldAudioSignpostTriggerNode", "worldSplineNode", "worldPatrolSplineNode"}
device_templates = {"base\\gameplay\\devices\\security_systems\\security_area\\security_area_1.ent",
                    "base\\gameplay\\devices\\security_systems\\security_system.ent"}
rows = []
total = Counter()
for group in identity["groups"]:
    ident = group["id"]
    p = Path(group["support_sector_json"])
    d = read(p)
    check(f"{ident} current native bytes", sha(Path(group["support_sector_raw"])) == group["support_sector_sha256"] == d["raw_sha256"])
    check(f"{ident} exact decoded bytes", sha(p) == group["support_sector_json_sha256"])
    ns = {n["index"]: n["definition"] for n in d["nodes"]}
    check(f"{ident} no unknown node type", all(n["$type"] in allowed for n in ns.values()))
    check(f"{ident} no embedded quest operations", not any(x.get("$type", "").startswith("quest") and x.get("$type") != "questTriggerNotifier_Quest" for x in walk(list(ns.values()))))
    drop = [29, 34] if ident == 1246 else []
    kept = [n for i, n in ns.items() if i not in drop]
    for i, n in ns.items():
        t = n["$type"]
        if t == "worldPopulationSpawnerNode":
            if i in drop:
                check(f"{ident}/{i} exact auto vehicle preview excluded", n["spawnOnStart"] == 1 and n["alwaysSpawned"] == "default__false_")
            else:
                check(f"{ident}/{i} preview disabled", n["spawnOnStart"] == 0 and n["alwaysSpawned"] in ["false_", "default__false_"])
        elif t == "worldInterestingConversationsAreaNode":
            refs = {x["$value"] for x in walk(n) if x.get("$type") == "ResourcePath" and x.get("$value") != "0"}
            if refs:
                check(f"{ident}/{i} reviewed exact speech", refs <= approved_speech)
            else:
                check(f"{ident}/{i} native empty speech placeholder", not n.get("conversationResources") and not n.get("conversations") and all(x["DepotPath"]["$value"] == "0" for x in n.get("conversationGroups", [])))
        elif t == "worldDeviceNode":
            check(f"{ident}/{i} native security template", n["entityTemplate"]["DepotPath"]["$value"] in device_templates)
            check(f"{ident}/{i} NPC/area connections only", all(c["deviceClassName"]["$value"] in ["CommunityProxyPS", "SecurityAreaControllerPS"] for c in n.get("deviceConnections", [])))
            # These are retained native controller instances, not commands to reset
            # security or alter attitudes. The owner preserves their original IDs.
            for x in walk(n):
                if x.get("$type", "").endswith("ControllerPS"):
                    check(f"{ident}/{i} no scripted device operations", x.get("deviceOperationsSetup") is None and x.get("markAsQuest", 0) == 0)
        elif t == "worldTriggerAreaNode":
            check(f"{ident}/{i} passive quest notifier only", all(x["Data"]["$type"] == "questTriggerNotifier_Quest" for x in n.get("notifiers", [])))
    if drop:
        removed = [x for x in d["placements"] if x["node"] in drop]
        aliases = [x["quest_ref"].split("/")[-1] for x in removed]
        check("1246exact2vehicle placements", len(removed) == 2)
        check("1246retained support does not reference removed vehicle nodes", all(not any(a in json.dumps(n) for a in aliases) for n in kept))
        spec = {"id": ident, "native_prefab": group["native_prefab"], "sector_resource": group["support_sector_resource"],
                "sector_raw": group["support_sector_raw"], "sector_sha256": group["support_sector_sha256"], "sector_json": str(p),
                "drop_nodes": drop, "drop_types": [ns[i]["$type"] for i in drop], "drop_placements": [x["datum"] for x in removed],
                "preserve_ai_spots": sum(n["$type"] == "worldAISpotNode" for n in kept), "preserve_nodes": len(kept),
                "reason": "Omit two automatic vehicle preview spawners. Preserve native support for already-active exact NPC entries; do not replay the staged convoy, mounting, faction or fight controller."}
        sp = H / "filter1246_spec_01.json"
        sp.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8", newline="\n")
        pin(sp)
    counts = Counter(n["$type"] for n in kept)
    total.update(counts)
    rows.append({"id": ident, "prefab": group["prefab"], "sector": group["support_sector_resource"],
                 "drop_nodes": drop, "retained_types": dict(counts), "native_admission_facts": group["native_admission_facts"],
                 "disposition": "PASS_PRIVATE_FILTER_REQUIRED" if drop else "PASS_EXACT_NATIVE_PASSIVE_SUPPORT"})
    pin(p); pin(group["support_sector_raw"]); pin(group["native_binary"])

for p in [H / "identity_cohort_01.json", H / "closure_01.json", N / "combat_conversations_native_01/report_01.json",
          N / "conversation_assessment_01.json", N / "party_assessment_01.json"]:
    pin(p)
result = {"status": "PASS_ADDITIONAL94_PASSIVE_SUPPORT_PAYLOADS", "check_count": len(checks), "checks": checks,
          "approved_ids": [g["id"] for g in identity["groups"]], "rows": rows, "retained_node_types": dict(total),
          "pins": pins, "private_filter_ids": [1246],
          "scope": "Native passive support for exact already-active living community entries. No encounter graph, combat preset, loot enable, security reset, global attitude, vehicle mount, phase switch, native fact or kill-count reset is rehosted.",
          "limits": ["1246 needs selected private sector proof before owner promotion.",
                     "Existing combat and scripted fights are not restarted by these support owners.",
                     "Native guard/security metadata remains exact; it can affect ordinary native perception/area behavior and is not a claim that every member is out of combat.",
                     "Native quest triggers have no rehosted encounter consumer. They remain exact native node identities; no phase reset is issued."],
          "game_writes": 0, "save_writes": 0}
(H / "payload_assessment_01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": result["status"], "checks": len(checks), "workspots": total["worldAISpotNode"], "owners": len(rows)}))
