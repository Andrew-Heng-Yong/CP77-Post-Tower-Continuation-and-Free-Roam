"""Validate packed scene routes, retained speech and caller closure, then stage all 51 Core paths."""
import copy
import json
import shutil
from pathlib import Path
from edit import CUT, DIR, EDITS, LIP, PACKAGE, PARENT, PARENT_SHA, ROOT, WORK, resources, scene_nodes, src
from verify import normalized
from check_gates import fnv
from build import ARCHIVE, XL, row, safe, verify_rows


def ends(n, port=(0,0)):
    return [(d["nodeId"]["id"],d["isockStamp"]["ordinal"]) for s in n["outputSockets"]
            if (s["stamp"]["name"],s["stamp"]["ordinal"])==port for d in s["destinations"]]


def reachable(nodes, starts):
    seen=set()
    stack=list(starts)
    while stack:
        i=stack.pop()
        if i in seen:
            continue
        seen.add(i)
        stack.extend(d["nodeId"]["id"] for s in nodes[i]["outputSockets"] for d in s["destinations"])
    return seen


def onscreen_options(nodes):
    return {i:[o["screenplayOptionId"]["id"] for o in n["options"]] for i,n in nodes.items() if n["$type"]=="scnChoiceNode"}


def dialogue(nodes, resolve):
    return {(i,e["id"]["id"]):e for i,n in nodes.items() for h in n.get("events",[])
            if (e:=resolve(h))["$type"]=="scnDialogLineEvent"}


def review_scene(original, edited, name):
    root, n, de=scene_nodes(edited)
    oldroot, old, unpack=scene_nodes(original)
    targets=CUT.get(name,{})
    # Lookup-table IDs encode index and type. All retained dialogue and the
    # compacted Kabuki menu must still resolve to the exact original text.
    assert root["screenplayStore"]==oldroot["screenplayStore"] and root["locStore"]==oldroot["locStore"]
    assert root["entryPoints"]==oldroot["entryPoints"] and root["exitPoints"]==oldroot["exitPoints"]
    assert n.keys()==old.keys()
    before, after=dialogue(old,unpack),dialogue(n,de)
    expected={k:e for k,e in before.items() if e["screenplayLineId"]["id"] not in targets.get(k[0],[])}
    assert after==expected, name
    for (i,_),e in after.items():
        item=e["screenplayLineId"]["id"]
        assert root["screenplayStore"]["lines"][item>>8]["itemId"]["id"]==item
        assert n[i]["sectionDuration"]==old[i]["sectionDuration"]
    opts=onscreen_options(old)
    if name=="12_kabuki_scene":
        opts[710]=[2050,2306]
        assert ends(n[710])==[(125,0)] and ends(n[710],(0,1))==[(129,0)]
        assert ends(n[129])==ends(old[129]) and ends(n[125])==ends(old[125])
        assert ends(n[484],(0,0))==ends(old[484],(0,0))==[(487,0)]
        assert ends(n[484],(0,1))==ends(old[172])==[(487,1)]
        assert ends(n[143])==ends(n[146])==[(572,0)] and (591,3) in ends(n[572],(0,1))
        assert (307,1) not in ends(n[244])
    elif name=="12_kabuki_scene_haze_body":
        assert ends(n[64])==[(72,1)] and ends(n[72])==[(68,0)] and ends(n[72],(0,1))==[(70,0)]
        assert ends(n[68])==ends(n[70])==[(90,0)] and (92,3) in ends(n[90],(0,1))
        assert 66 in reachable(n,[92])
    elif name=="01_nc_tower_scene":
        assert ends(n[518])==[(1160,1),(328,0),(882,1)]
        for i in (328,882,1160):
            assert ends(n[i])==ends(old[i])
    elif name=="03_arasaka_memorial_scene":
        assert (588,1) in ends(n[581]) and ends(n[588])==ends(old[588])+[(582,0)]
        assert ends(n[582])==[(235,0)] and (696,2) in ends(n[215])
    elif name=="07_rancho_scene":
        assert [p["nodeId"]["id"] for p in root["entryPoints"] if src.value(p["name"])=="johnny"]==[294]
        assert [p["nodeId"]["id"] for p in root["exitPoints"] if src.value(p["name"])=="End johnny"]==[306]
        assert reachable(n,[294])=={294,300,301,302,306}
        assert ends(n[294])==[(300,3)] and ends(n[300])==[(301,1)] and ends(n[301])==[(302,1),(306,0)]
        for i in (300,301,302):
            assert normalized(src.canonical(de(n[i]["questNode"]),src.definitions(edited),set()))==normalized(
                src.canonical(unpack(old[i]["questNode"]),src.definitions(original),set()))
    elif name=="13_end_scene":
        assert ends(n[188])==[(193,0)] and 293 not in reachable(n,[188])
    assert opts==onscreen_options(n)
    for items in opts.values():
        for item in items:
            assert root["screenplayStore"]["options"][item>>8]["itemId"]["id"]==item
    live=reachable(n,[p["nodeId"]["id"] for p in root["entryPoints"]])
    for node in targets:
        assert node not in live and n[node]["sectionDuration"]["stu"]==0 and not n[node]["events"], (name,node)
    if targets:
        actor,=[a for a in root["actors"] if a["actorName"]=="Johnny"]
        assert actor["spawnDespawnParams"]["isEnabled"]==0
        who=actor["actorId"]["id"]
        for e in after.values():
            line=root["screenplayStore"]["lines"][e["screenplayLineId"]["id"]>>8]
            assert who not in (line["speaker"]["id"],line["addressee"]["id"])
        for i in live:
            for h in n[i].get("events",[]):
                assert all(not ((v.get("$type")=="scnActorId" and v["id"]==who) or
                               (v.get("$type")=="scnPerformerId" and v["id"]==((who<<8)|1))) for v in src.walk(de(h)))
    return len(before)-len(after),len(after),sum(map(len,opts.values()))


def main():
    assets=WORK/"assets_02"
    manifest=src.read(assets/"readback.json")
    docs,old_private=resources()
    plan=src.read(EDITS/"plan.json")
    assert manifest["parent_sha256"]==PARENT_SHA and (manifest["private_keys_checked"],manifest["packed_members"],manifest["preserved"])==(17,1768,1758)
    changed={r["depot"]:r for r in manifest["resources"]}
    assert set(changed)=={src.PREFIX+d for d in plan["changed"]}|{LIP}
    readback={}
    for depot,r in changed.items():
        assert r["sha256"]==src.sha(r["raw"]) and r["json_sha256"]==src.sha(r["json"])
        if depot!=LIP:
            readback[depot]=src.read(r["json"])
            assert normalized(readback[depot]["Data"])==normalized(src.read(EDITS/(depot+".json"))["Data"]),depot
    # Resolve the full graph using actual serialized paths from the entry owner.
    registered=src.read(old_private[src.ENTRY]["json"])
    assert any(src.value(v)==src.PREFIX+src.QUEST for v in src.walk(registered))
    all_private=set(old_private)|set(changed)
    todo=[src.PREFIX+src.QUEST];visited=set();totals=[0,0,0];phase_count=0;scene_count=0
    while todo:
        ref=todo.pop()
        if ref in visited:
            continue
        visited.add(ref)
        d=ref.removeprefix(src.PREFIX)
        assert d in docs and (ref.startswith(src.PREFIX)==(src.PREFIX+d in all_private)),ref
        actual=readback.get(ref,docs[d])
        if d.endswith(".questphase"):
            expected=copy.deepcopy(docs[d])
            for v in src.walk(expected):
                if v.get("$type")=="ResourcePath" and src.value(v) in plan["added"]:
                    v["$value"]=src.PREFIX+v["$value"]
            assert normalized(expected["Data"])==normalized(actual["Data"]),d
            phase_count+=1
        else:
            counts=review_scene(docs[d],actual,Path(d).stem.removeprefix("mq061_"))
            totals=[a+b for a,b in zip(totals,counts)]
            scene_count+=1
        for v in src.walk(actual):
            if v.get("$type")=="ResourcePath":
                dest=src.value(v)
                if isinstance(dest,str) and dest.removeprefix(src.PREFIX) in docs:
                    todo.append(dest)
    assert (scene_count,phase_count,totals[0],totals[2])==(14,19,15,68)
    oldlip=src.read(old_private[LIP]["json"])["Data"]["RootChunk"]
    lip=src.read(changed[LIP]["json"])["Data"]["RootChunk"]
    vanilla=src.read(PARENT/"work/lipmap_comparison/original.json")["Data"]["RootChunk"]
    assert {k:(v[:len(oldlip[k])] if k in ("sceneEntries","scenePaths") else v) for k,v in lip.items()}==oldlip
    assert len(lip["scenePaths"])==len(lip["sceneEntries"])==len(oldlip["scenePaths"])+2
    for d in (s for s in plan["added"] if s.endswith(".scene")):
        i=vanilla["scenePaths"].index(fnv(d)); j=lip["scenePaths"].index(fnv(src.PREFIX+d))
        assert vanilla["sceneEntries"][i]==lip["sceneEntries"][j]

    old=src.read(PACKAGE/"core_manifest.json")
    verify_rows(PACKAGE/"package",old["core_files"])
    installed=src.read(src.BASE)
    verify_rows(Path(installed["game_root"]),installed["core_files"]+installed["required_files"])
    assert src.sha(assets/"package"/ARCHIVE)==manifest["archive_sha256"]
    out=ROOT/"candidate_01";pkg=out/"package"
    assert not out.exists()
    for f in old["core_files"]:
        name=f["path"]
        source=safe(assets/"package" if name==ARCHIVE else PACKAGE/"package",name)
        target=safe(pkg,name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    files=[row(pkg,f["path"]) for f in old["core_files"]]
    assert len(files)==51 and [a["path"] for a,b in zip(files,old["core_files"]) if a!=b]==[ARCHIVE]
    # ArchiveXL phase/node registration and sibling script bytes have not changed.
    assert src.sha(pkg/XL)==src.sha(PACKAGE/"package"/XL)
    compile_proof=PARENT/"work/compile_01/assessment.json"
    assert src.sha(compile_proof)==old["compile_assessment_sha256"] and src.read(compile_proof)["source_after"][src.S29]==src.sha(pkg/src.S29)
    verify_rows(pkg,files)
    core={"status":"STAGED_OFFLINE","baseline_sha256":old["baseline_sha256"],"predecessor_candidate_sha256":PARENT_SHA,
          "changed_paths":old["changed_paths"],"core_files":files,"asset_assessment_sha256":src.sha(assets/"readback.json"),
          "compile_assessment_sha256":old["compile_assessment_sha256"]}
    src.write(out/"core_manifest.json",core)
    proof={"status":"PASS_OFFLINE","candidate_sha256":src.sha(out/"core_manifest.json"),"core_files":len(files),
           "changed_from_staged":[ARCHIVE],"native_quest_phases":phase_count,"quest_scenes":scene_count,
           "removed_dialogue_events":totals[0],"retained_dialogue_events":totals[1],"remaining_choices":totals[2],
           "private_lipmaps_appended":2,"archives_checked":manifest["archives_checked"],"packed_members":manifest["packed_members"],
           "game_writes":0,"save_writes":0,"gameplay":"pending"}
    src.write(out/"verification.json",proof)
    print(json.dumps(proof))


if __name__=="__main__":
    main()
