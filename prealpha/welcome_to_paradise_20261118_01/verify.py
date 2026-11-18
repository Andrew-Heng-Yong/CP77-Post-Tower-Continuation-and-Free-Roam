"""Stage the complete Core and verify the tour against the current game and genuine saves."""
import copy
import json
import shutil
import sys
import zlib
from pathlib import Path

import prepare as m

ROOT, WORK = m.ROOT, m.WORK
sys.path.insert(0, str(ROOT.parent / "phone_support_ph1"))
sys.path.insert(0, str(ROOT.parent / "misty_rooftop_seat_20261117_01"))
import build
import model
import validate as seat


def normalized(value):
    # The serializer compacts handle numbers after deleting an event. Bind both ends of each reference.
    found = [x["HandleId"] for x in m.walk(value) if "HandleId" in x]
    table = {v: i for i, v in enumerate(found)}
    assert len(found) == len(table)
    result = copy.deepcopy(value)
    for x in m.walk(result):
        for k in ("HandleId", "HandleRefId"):
            if k in x and x[k] != "-1":
                x[k] = table[x[k]]
    return result


def graph_check(records, lookup, contract):
    original = lookup(r"base\quest\bugfixing\quest_bugfixing.questphase")
    orig = model.model(original)["root/3"]
    built = model.model(records[m.ENTRY]["json"])["root"]
    edges = set(built["edges"])
    run = set(range(126,136)) | {142}
    for i in run - {126}:
        original_node=copy.deepcopy(orig["nodes"][i])
        for v in m.walk(original_node):
            if v.get("$type")=="TweakDBID" and v.get("$storage")=="string":
                name=v["$value"].encode()
                v["$storage"],v["$value"]="uint64",str(len(name)<<32 | zlib.crc32(name))
        assert built["nodes"][i] == original_node
    original_edges = {e for e in orig["edges"] if e[0] in run and e[2] in run}
    timer = (128, "Out", 126, "In1")
    assert timer in original_edges and original_edges - {timer} == {e for e in edges if e[0] in run and e[2] in run}
    assert (128,"Out",65006,"In") in edges and (65010,"Out",126,"In1") in edges and (126,"Out1",65011,"In") in edges
    assert [e for e in edges if e[2]==126] == [(65010,"Out",126,"In1")]
    assert built["nodes"][126]["phaseResource"]["DepotPath"]["$value"] == m.PREFIX+m.QUEST
    facts = lambda n: {v["factName"]:v["value"] for v in m.walk(built["nodes"][n]) if v.get("$type")=="questVarComparison_ConditionType"}
    for gate in (65003,65007,65008):
        required = facts(gate)
        assert all(required[n]==0 for n in contract["facts"])
        assert required["q307_main_game_killed"] == required["q307_ep1_killed"] == required[m.TAG+"_Permit"] == 1
        assert required[m.TAG+"_Issued"] == required[m.TAG+"_Entered"] == required[m.TAG+"_Finished"] == 0
        assert any(v.get("realPath")==m.JOURNAL for v in m.walk(built["nodes"][gate]))
    assert (65008,"False",65007,"In") in edges and (65008,"True",65009,"In") in edges
    assert all(v["factName"].startswith(m.TAG+"_") for n in built["nodes"].values() for v in m.walk(n)
               if v.get("$type")=="questSetVar_NodeType")
    return len(run), len(edges)


def main():
    baseline = m.read(m.BASE)
    assert m.sha(m.BASE) == "CED6C03DE5B242E5B3F934BCE79160FE60DEDBACADF673951F4258D2A113B404"
    game = Path(baseline["game_root"])
    build.verify_rows(game, baseline["core_files"]+baseline["required_files"]+baseline["archivexl_files"]+baseline["ifp_files"])
    source = m.read(WORK/"sources_01/providers.json")
    registry = {e["sha256"]:e for line in m.REGISTRY.open(encoding="utf-8") if (e:=json.loads(line)).get("json")}
    def lookup(depot):
        h, = [h for h in source["hits"] if h["depot"]==depot]
        e=registry[h["sha256"]]
        assert m.sha(h["raw"])==h["sha256"] and m.sha(e["json"])==e["json_sha256"]
        return e["json"]
    c=m.read(WORK/"contract_02.json")
    records={e["depot"]:e for e in m.read(WORK/"cook_02/manifest.json")["resources"]}
    for e in records.values():
        assert m.sha(e["raw"])==e["sha256"] and m.sha(e["json"])==e["json_sha256"]
    private=set(c["private"])
    dialog_count=0
    for depot in private:
        old=m.read(lookup(depot))
        expected=copy.deepcopy(old)
        if depot.endswith(".scene"):
            assert m.visual_changes(expected)==c["presentation"][depot]
        for v in m.walk(expected):
            if v.get("$type")=="ResourcePath" and m.value(v) in private:
                v["$value"]=m.PREFIX+m.value(v)
        handles=m.definitions(old) | m.definitions(expected)
        desired=m.canonical(expected,handles,set())["Data"]
        actual=m.read(records[m.PREFIX+depot]["json"])["Data"]
        assert normalized(actual)==normalized(desired), depot
        if depot.endswith(".scene"):
            for key in ("actors","locStore","entryPoints","exitPoints"):
                assert actual["RootChunk"][key]==old["Data"]["RootChunk"][key], (depot,key)
            dialogs=lambda doc: sorted([str(v) for v in m.walk(doc) if v.get("$type")=="scnDialogLineEvent"])
            assert dialogs(actual)==dialogs(old), depot
            dialog_count+=len(dialogs(actual))
        else:
            assert actual["RootChunk"]["phasePrefabs"]==old["Data"]["RootChunk"]["phasePrefabs"]
    assert len(m.read(records[m.PREFIX+m.QUEST]["json"])["Data"]["RootChunk"]["phasePrefabs"])==15
    for spot in c["workspots"]:
        actual=m.read(records[m.PREFIX+spot]["json"])["Data"]
        assert normalized(actual)==normalized(m.read(WORK/"cook_02"/(Path(spot).name+".json.private.json"))["Data"])
        assert all(x["eventFilterType"]=="Mute" for x in m.walk(actual) if x.get("$type")=="animAnimNode_WorkspotHub")
    nodes, edges=graph_check(records,lookup,c)
    pack=m.read(WORK/"pack_01/readback.json")
    assert pack["packed_members"]==1764 and pack["private_additions"]==13 and pack["unchanged_members"]==1750
    assert m.sha(WORK/"pack_01/package"/build.ARCHIVE)==pack["archive_sha256"]
    ep=r"ep1\quest\ep1.quest"
    current=next(x for x in source["hits"] if x["depot"]==ep)
    cached=m.read(ROOT.parent/"misty_rooftop_seat_20261117_01/work/native_01/providers.json")
    parent=next(x for x in cached["hits"] if x["depot"]==ep)
    assert parent["sha256"]==current["sha256"]==m.sha(current["raw"])
    seat.WORK=WORK;seat.DEPOT=m.ENTRY
    xls, registrations, node_id=seat.xl_check(WORK/"pack_01/package",cached)
    assert not m.read(WORK/"private_01/providers.json")["hits"]
    registered=m.read(WORK/"compile_01/assessment.json")
    runtime=WORK/"runtime"/Path(m.S29).name
    assert registered["status"]=="PASS" and registered["changed_sources"]==[m.S29]
    assert registered["source_after"][m.S29]==m.sha(runtime)
    compiled=(WORK/"compile_01/compiled.script").read_text(encoding="utf-8-sig")
    for name in ('history','content'):
        assert name in compiled
    for token in ('SnapshotDataHS3.FactName(10489)', 'FactValue(10489)', 'FactValue(10488)', 'mq061_BlockToken_Temp', 'PTFRParadise', 'An existing tour item'):
        assert token in compiled,token
    fixture=m.read(ROOT/"quest_evidence_02.json")["saves"]
    owners=m.read(ROOT/"owner_evidence.json")["saves"]
    assert [s["save_sha256"] for s in owners]==[s["save_sha256"] for s in fixture]
    assert all(not s["journals"] and all(s["facts"][k] in (None,0) for k in c["facts"]) for s in fixture)
    assert any(e["node"]==128 and e["route"]=="0/2/82/4/9/3" for e in owners[0]["handlers"])
    assert all(not s["handlers"] for s in owners[1:])
    proof=Path(baseline["game_root"])/"bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/snapshot_hs3_20261115T203348Z_5_3.json"
    capture=m.read(proof)
    captured=[r for r in capture["rows"] if r["definition"].get("name") in {"mq061_start","mq061_07_rancho_done"}]
    assert len(captured)==2 and capture["origin"]=="pre_native_cleanup" and all(r["stable"] and r["value"]==0 for r in captured)
    candidate=ROOT/"candidate_01"; package=candidate/"package"
    changed={build.ARCHIVE,build.XL,m.S29}
    assert not candidate.exists()
    for row in baseline["core_files"]:
        rel=row["path"]
        src=runtime if rel==m.S29 else (WORK/"pack_01/package" if rel in changed else game)/rel
        target=build.safe(package,rel);target.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(src,target)
    rows=[build.row(package,e["path"]) for e in baseline["core_files"]]
    assert {a["path"] for a,b in zip(rows,baseline["core_files"],strict=True) if a!=b}==changed
    build.verify_rows(package,rows)
    m.write(candidate/"core_manifest.json",{"status":"STAGED_OFFLINE","baseline_sha256":m.sha(m.BASE),"core_files":rows,"changed_paths":sorted(changed),
            "asset_assessment_sha256":m.sha(WORK/"pack_01/readback.json"),"compile_assessment_sha256":m.sha(WORK/"compile_01/assessment.json")})
    result={"status":"PASS_OFFLINE","core_files":len(rows),"registered_scripts":registered["registered_sources"],"packed_resources":pack["packed_members"],
            "private_resources":13,"scene_dialogue_events_compared":dialog_count,"tour_prefabs_preserved":15,"native_entry_nodes":nodes,"wrapper_edges":edges,
            "xl_files":xls,"ep1_registrations":registrations,"private_phase_node":node_id,"journals_checked":len(c["journals"]),"progress_facts":len(c["facts"]),
            "items_checked":len(c["items"]),"snapshot_evidence_sha256":m.sha(proof),"save_fixture_sha256":m.sha(ROOT/"quest_evidence_02.json"),
            "owner_fixture_sha256":m.sha(ROOT/"owner_evidence.json"),"candidate_sha256":m.sha(candidate/"core_manifest.json"),"game_writes":0,"save_writes":0,"gameplay":"pending"}
    m.write(candidate/"verification.json",result)
    print(json.dumps(result))


if __name__=="__main__":
    main()
