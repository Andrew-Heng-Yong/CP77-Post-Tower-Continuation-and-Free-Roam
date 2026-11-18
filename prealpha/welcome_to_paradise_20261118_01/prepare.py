"""Build the tour's fresh-entry contract and private presentation from verified game resources."""

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WS = ROOT.parents[1]
WORK = ROOT / "work"
BASE = ROOT.parent / "misty_roof_pickup_release_20261118_01/installed_manifest.json"
REGISTRY = ROOT.parent / "quest_resume_registry_20261112_01/evidence_02/resources.jsonl"
S29 = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
PREFIX = "towercontinued\\paradise\\"
QUEST = "base\\quest\\minor_quests\\mq061\\mq061.questphase"
ENTRY = PREFIX + "entry.questphase"
TAG = "PTFRParadise"
JOURNAL = "quests/minor_quest/mq061"


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def value(obj):
    return obj.get("$value") if isinstance(obj, dict) else obj


def definitions(doc):
    return {v["HandleId"]: v["Data"] for v in walk(doc) if "HandleId" in v}


def canonical(obj, handles, seen):
    if isinstance(obj, list):
        return [canonical(v, handles, seen) for v in obj]
    if not isinstance(obj, dict):
        return obj
    key = obj.get("HandleId", obj.get("HandleRefId"))
    if key in handles:
        if key in seen:
            return {"HandleRefId": key}
        seen.add(key)
        return {"HandleId": key, "Data": canonical(handles[key], handles, seen)}
    return {k: canonical(v, handles, seen) for k, v in obj.items()}


def visual_changes(doc):
    root = doc["Data"]["RootChunk"]
    actor = next((a for a in root["actors"] if a["actorName"].lower() == "johnny"), None)
    if not actor:
        return None
    pid = (actor["actorId"]["id"] << 8) | 1
    alias = value(actor["spawnDespawnParams"]["dynamicEntityUniqueName"])
    handles = definitions(doc)

    def resolve(wrapper):
        return wrapper.get("Data", handles.get(wrapper.get("HandleRefId"), wrapper))

    instances = {w["workspotInstanceId"]["id"]: w["dataId"]["id"] for w in root["workspotInstances"]}
    owned, other = set(), set()
    removed, muted = [], []
    for v in walk(root):
        if v.get("$type") == "questUseWorkspotNodeDefinition":
            params = resolve(v.get("paramsV1") or {})
            wid = params.get("workspotInstanceId", {}).get("id")
            ref = v["entityReference"]
            identifiers = [value(ref.get(k)) for k in ("sceneActorContextName", "dynamicEntityUniqueName", "reference")]
            identifiers.extend(value(n) for n in ref.get("names", []))
            mine = any(isinstance(n, str) and (n.lower() in ("johnny", "#johnny") or n == alias and n != "None") for n in identifiers)
        elif v.get("$type") == "scnPlaySkAnimEvent":
            wid = resolve(v.get("poseBlendOutWorkspot") or {}).get("workspotId", {}).get("id")
            mine = v.get("performer", {}).get("id") == pid
            if mine:
                muted.append(v["id"]["id"])
                v["muteAnimEvents"] = "STANDARD"
        else:
            continue
        if wid in instances:
            (owned if mine else other).add(instances[wid])
    assert owned.isdisjoint(other), "Shared workspot needs separate actor binding"
    spots = set()
    for wrapper in root["workspots"]:
        station = resolve(wrapper)
        if station["dataId"]["id"] in owned:
            ref = station["workspotResource"]["DepotPath"]
            spots.add(value(ref))
            ref["$value"] = PREFIX + value(ref)
    for wrapper in root["sceneGraph"]["Data"]["graph"]:
        node = resolve(wrapper)
        if "events" not in node:
            continue
        keep = []
        for handle in node["events"]:
            event = resolve(handle)
            if event.get("performerId", {}).get("id") == pid and event["$type"] in (
                "scneventsVFXEvent", "scneventsEquipItemToPerformer", "scneventsUnequipItemFromPerformer"
            ):
                removed.append(event["id"]["id"])
            else:
                keep.append(handle)
        node["events"] = keep
    symbols = root["debugSymbols"]["sceneEventsDebugSymbols"]
    kept = []
    for group in symbols:
        old_ids = group["sceneEventIds"]
        group["sceneEventIds"] = [e for e in old_ids if e["id"] not in removed]
        if not old_ids or group["sceneEventIds"]:
            kept.append(group)
    root["debugSymbols"]["sceneEventsDebugSymbols"] = kept
    if spots or removed or muted:
        return {"workspots": sorted(spots), "removed_visual_events": removed, "muted_anims": muted}
    return None


def main():
    baseline = read(BASE)
    game = Path(baseline["game_root"])
    registry = {r["sha256"]: r for line in REGISTRY.open(encoding="utf-8") if (r := json.loads(line)).get("json")}
    source = read(WORK / "sources_01/providers.json")
    assert source["manifest_sha256"] == sha(BASE)
    docs, private, presentation, facts, items = {}, set(), {}, set(), set()
    for hit in source["hits"]:
        depot = hit["depot"]
        if "\\mq061\\" not in depot:
            continue
        assert depot not in docs and sha(hit["raw"]) == hit["sha256"] == registry[hit["sha256"]]["sha256"]
        export = registry[hit["sha256"]]
        assert sha(export["json"]) == export["json_sha256"]
        doc = read(export["json"])
        docs[depot] = doc
        for v in walk(doc):
            if isinstance(v.get("factName"), str) and v["factName"].lower().startswith("mq061_"):
                facts.add(v["factName"])
            if v.get("$type") == "questAddRemoveItem_NodeTypeParams":
                items.add(int(value(v["itemID"])))
        if depot.endswith(".scene"):
            scope = visual_changes(doc)
            if scope:
                private.add(depot)
                presentation[depot] = scope

    changed = True
    while changed:
        count = len(private)
        for depot, doc in docs.items():
            if any(v.get("$type") == "ResourcePath" and value(v) in private for v in walk(doc)):
                private.add(depot)
        changed = len(private) != count
    assert QUEST in private and len(presentation) == 4 and len(private) == 9
    for depot in sorted(private):
        doc = docs[depot]
        handles = definitions(read(registry[next(h["sha256"] for h in source["hits"] if h["depot"] == depot)]["json"]))
        handles.update(definitions(doc))
        for v in walk(doc):
            if v.get("$type") == "ResourcePath" and value(v) in private:
                v["$value"] = PREFIX + value(v)
        write(WORK / "edited_02" / (PREFIX + depot + ".json"), canonical(doc, handles, set()))

    jhit, = [h for h in source["hits"] if h["depot"] == r"base\journal\cooked_journal.journal" and "ep1_2_gamedata" in h["archive"]]
    jp = WS / "research/sidejobs_s28/journal_variants_05/ep1_2_gamedata/json/base/journal/cooked_journal.journal.json"
    raw_journal = Path(str(jp).replace("\\json\\", "\\raw\\" )[:-5])
    assert sha(raw_journal) == jhit["sha256"]
    journals = {}

    def visit(entry, path):
        if isinstance(entry, list):
            for child in entry:
                visit(child, path)
        elif isinstance(entry, dict):
            if isinstance(entry.get("id"), str) and entry["id"]:
                path = "/".join(filter(None, (path, entry["id"])))
                if (path == JOURNAL or path.startswith(JOURNAL + "/") or re.match(r"^contacts/aera/mq061(?:$|[/_])", path)):
                    if entry["$type"] in {"gameJournalQuest", "gameJournalQuestPhase", "gameJournalQuestObjective", "gameJournalQuestMapPin", "gameJournalPhoneConversation", "gameJournalPhoneMessage"}:
                        journals[path] = entry["$type"]
            for child in entry.values():
                visit(child, path)
    visit(read(jp), "")
    assert journals[JOURNAL] == "gameJournalQuest" and len(journals) > 65 and "mq061_done" in facts and 73020674584 in items
    write(WORK / "contract_02.json", {"private": sorted(private), "presentation": presentation, "journals": journals,
          "facts": sorted(facts), "items": sorted(items), "workspots": sorted({s for v in presentation.values() for s in v["workspots"]})})
    print(f"{len(private)} private phases/scenes, {len(facts)} progress facts, {len(journals)} journal entries, {len(items)} item guards")


if __name__ == "__main__":
    main()
