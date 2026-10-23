"""Check the Wilson opt-in package's narrow executable and native owner paths."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from audit_wilson_vendor_owner import graph_edges, walk  # noqa: E402

VAL = ROOT / "research/b0_wilson_vendor/validation"
PREFIX = "PTFRB0WV_"


def read(name):
    return json.loads((VAL / name).read_text(encoding="utf-8-sig"))


def nodes(graph):
    return {n["Data"]["id"]: n["Data"] for n in graph["nodes"]}


def value(obj):
    return obj.get("$value") if isinstance(obj, dict) else obj


def edges(graph):
    handles = {str(v["HandleId"]): v["Data"] for v in walk(graph) if "HandleId" in v and "Data" in v}
    return {(e["source_node_id"],e["source_socket"],e["destination_node_id"],e["destination_socket"])
            for e in graph_edges(graph,"test",handles)}


def main():
    manifest=read("build_manifest.json")
    assert manifest["status"] == "OPT_IN_DISPOSABLE_BUILD_NOT_INSTALLED"
    assert manifest["vanilla_replacements"] == []
    assert len(manifest["resources"]) == 3
    archive = ROOT / "build/B0_Wilson_Vendor" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    registration = (ROOT / "archive/b0_wilson_vendor/TowerContinued_B0_Wilson_Vendor.archive.xl").read_text(encoding="utf-8")
    assert registration.count("- path:") == 1
    assert "parent: ep1\\quest\\ep1.quest" in registration
    assert "towercontinued\\b0_wilson_vendor\\owner.questphase" in registration

    scene = read("shop.scene.json")["Data"]["RootChunk"]
    assert [value(x["name"]) for x in scene["entryPoints"]] == ["wilson_default_in"]
    assert [x["id"] for x in scene["sceneGraph"]["Data"]["startNodes"]] == [0]
    assert scene["props"] == []
    assert len(scene["actors"]) == 1
    assert value(scene["actors"][0]["spawnSetParams"]["reference"]) == "#wilson"
    assert value(scene["actors"][0]["spawnSetParams"]["entryName"]) == "wilson"
    scene_nodes = {n["Data"]["nodeId"]["id"]:n["Data"] for n in scene["sceneGraph"]["Data"]["graph"]}
    assert set(scene_nodes) == {0,678,224,177,215}
    assert [value(x["caption"]) for x in scene_nodes[177]["options"]] == ["Shop"]
    assert value(scene_nodes[224]["questNode"]["Data"]["condition"]["Data"]["triggerAreaRef"]).endswith("/#wat_lch_gunsmith_01_tr_met")
    vendor=scene_nodes[215]["questNode"]["Data"]["type"]["Data"]
    assert vendor["$type"] == "questVendorPanel_NodeType"
    assert vendor["vendorId"] == "Vendors.wat_lch_gunsmith_01"
    expected={0:(678,0),678:(224,1),224:(177,0),177:(215,1),215:(177,0)}
    for node_id,(target,ordinal) in expected.items():
        destinations=[d for s in scene_nodes[node_id]["outputSockets"] for d in s["destinations"]]
        assert len(destinations)==1,(node_id,destinations)
        assert destinations[0]["nodeId"]["id"]==target
        assert destinations[0]["isockStamp"]["ordinal"]==ordinal
    assert not any(k in scene_nodes[215]["questNode"]["Data"]["type"]["Data"] for k in ("factName","questPath"))

    owner=read("owner.questphase.json")["Data"]["RootChunk"]["graph"]["Data"]
    body=read("body.questphase.json")["Data"]["RootChunk"]["graph"]["Data"]
    own=nodes(owner);bod=nodes(body)
    assert set(own)==set(range(6))
    assert set(bod)==set(range(14))
    assert (4,"Out1",5,"In") in edges(owner)
    assert (5,"Out",3,"In") in edges(owner)
    be=edges(body)
    assert (1,"Out",2,"In") in be
    assert (4,"Out",5,"wilson_default_in") in be
    assert (12,"CutSource",5,"CutDestination") in be
    assert (6,"Out",7,"In") in be and (9,"Out",10,"In") in be
    for nid,action in ((1,"Activate"),(7,"Deactivate")):
        s=bod[nid]["actions"][0]["type"]["Data"]
        assert (s["action"],value(s["reference"]),value(s["entryName"]),value(s["phaseName"])) == (
            action,"#wilson","wilson","q001_give_weapon")
    body_scene=bod[5]
    assert value(body_scene["sceneFile"]["DepotPath"]) == "towercontinued\\b0_wilson_vendor\\shop.scene"
    assert value(body_scene["sceneLocation"]["nodeRef"]).endswith("/#wat_sm_lch_gunsmith_01")
    for graph in (owner,body):
        for node in nodes(graph).values():
            if node["$type"]=="questFactsDBManagerNodeDefinition":
                assert node["type"]["Data"]["factName"].startswith(PREFIX)
            assert node["$type"]!="questJournalNodeDefinition"
    guard_facts={x["Data"]["type"]["Data"]["factName"] for x in own[2]["condition"]["Data"]["conditions"]}
    assert guard_facts==set(manifest["guard_facts"])

    lua_source=(ROOT/"diagnostics/PTFR_B0_Wilson_Vendor/init.lua").read_text(encoding="utf-8")
    assert all(f"function M.{key}(" in lua_source for key in ("Inspect","Start","Mark","Stop"))
    assert "registerForEvent(\"onUpdate\"" in lua_source
    assert "io.open(name,\"a\")" in lua_source
    try:
        from lupa.luajit21 import LuaRuntime
    except (ImportError,PermissionError):
        print("Lua parser unavailable in sandbox; CET execution/syntax remains a game-load check.")
    else:
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute("registerForEvent=function() end")
        diagnostic=lua.execute(lua_source)
        assert all(diagnostic[key] is not None for key in ("Inspect","Start","Mark","Stop"))
    print("Wilson static package PASS: 3 owned resources, 5 executable Shop nodes, native spawn/cut/exit, guarded opt-in")
    print("Live actor/trigger/trade/reload behavior still requires the disposable in-game test.")


if __name__ == "__main__":
    main()
