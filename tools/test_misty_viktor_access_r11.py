"""Independent R11 graph, state-transition, world-scope and packed-byte checks.

These checks model native dispatch; they do not prove live node registration,
door prompts, actor visibility, navigation or engine save compatibility.
"""
import itertools
import json
import subprocess
import zlib
from collections import Counter, defaultdict
from pathlib import Path

from audit_world_interactions import walk
from test_misty_viktor_access_r10 import eval_stream, read, sha
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/misty_viktor_world"
SOURCE = ROOT / "build/MistyViktorAccessR11/source"
PHASE = r"towercontinued\misty_viktor_world\shell_optin.questphase"
ACCESS = r"towercontinued\misty_viktor_world\access_r11.questphase"
STREET_NAMES = {f"q307_alley_extra_{n}" for n in range(12, 16)}
PRIVATE_STREET = "$/03_night_city/#PTFRMV_StreetCommunity"


def graph(path):
    root = read(path)["Data"]["RootChunk"]
    table = handles(root)
    for obj in walk(root):
        if "HandleRefId" in obj:
            assert str(obj["HandleRefId"]) in table, "unresolved graph handle"
    normalized = {i: canonical(n, table) for i, n in nodes(root).items()}
    # WK emits the original door's second alias after loading sector strings.
    # packed_and_yaml verifies both spellings and R2/R11 binaries have exactly
    # the same UInt64 hash before the report can pass.
    for obj in walk(normalized):
        if obj.get("$type") == "NodeRef" and obj.get("$value", "").endswith("/#q115_misty_door_back;#q307_zetatech_doors_02"):
            obj["$value"] = obj["$value"].removesuffix(";#q307_zetatech_doors_02")
    return root, normalized, quest_edges(root)[0]


def reachable(edges, initial=0):
    adjacent = defaultdict(set)
    for source, _, target, _ in edges:
        adjacent[source].add(target)
    found, pending = set(), [initial]
    while pending:
        current = pending.pop()
        if current not in found:
            found.add(current)
            pending.extend(adjacent[current])
    return found


class NativeDispatchModel:
    """Execute the exported graph with parked waits and mutable load/fact state."""

    def __init__(self, graph_nodes, edges, facts, loaded, initial=0):
        self.nodes, self.facts, self.loaded = graph_nodes, dict(facts), dict(loaded)
        self.pending, self.actions = {initial}, []
        self.edges = defaultdict(list)
        for a, socket, b, _ in edges:
            self.edges[a, socket].append(b)

    def settle(self, before=None):
        for _ in range(500):
            progressed = False
            for index in sorted(self.pending):
                node = self.nodes[index]
                kind, socket = node["$type"], "Out"
                if before is not None and index == before:
                    return
                if kind == "questPauseConditionNodeDefinition":
                    if not eval_stream(node["condition"], self.facts, self.loaded):
                        continue
                elif kind == "questConditionNodeDefinition":
                    socket = "True" if eval_stream(node["condition"], self.facts, self.loaded) else "False"
                elif kind == "questFactsDBManagerNodeDefinition":
                    payload = node["type"]
                    assert payload["$type"] == "questSetVar_NodeType"
                    name, value = payload["factName"], payload["value"]
                    self.facts[name] = value if payload["setExactValue"] else self.facts.get(name, 0) + value
                elif kind == "questInteractiveObjectManagerNodeDefinition":
                    for param in node["type"]["params"]:
                        self.actions.append((index, "door", param["objectRef"]["$value"], param["deviceAction"]["$value"]))
                elif kind == "questSpawnManagerNodeDefinition":
                    for action in node["actions"]:
                        payload = action["type"]
                        self.actions.append((index, "community", payload["communityEntryName"]["$value"], payload["action"]))
                else:
                    assert kind == "questInputNodeDefinition", ("unexpected simulator node", kind)
                self.pending.remove(index)
                self.pending.update(self.edges[index, socket])
                progressed = True
            if not progressed:
                return
        raise AssertionError("graph did not settle: immediate loop or unhandled wait")


def packed_and_yaml():
    # Reopen every payload in memory; use a real YAML parser for XL nesting.
    # Re-export the two phase binaries in memory and compare their Data to the
    # JSON readback used by this test, so stale exports cannot masquerade as PASS.
    code = r'''
    $ErrorActionPreference='Stop'
    . ./tools/build_phase2a.ps1 -HelpersOnly
    $m=Get-Content ./research/misty_viktor_world/access_r11_manifest.json -Raw|ConvertFrom-Json
    $source=Join-Path (Get-Location) 'build\MistyViktorAccessR11\source'
    $hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
    if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($m.archive,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Archive cannot reopen'}
    $actual=@($ar.Files.Values|ForEach-Object {$_.Name}|Sort-Object)
    if(@(Compare-Object @($m.resources|Sort-Object) $actual).Count){throw 'Packed payload set mismatch'}
    foreach($entry in $ar.Files.Values){
      $ms=[IO.MemoryStream]::new()
      try{$entry.Extract($ms);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()}
      if($digest -ne (Get-FileHash -LiteralPath (Join-Path $source $entry.Name)).Hash){throw ('Packed payload differs '+$entry.Name)}
    }
    foreach($pair in @(@('shell_optin.questphase','access_r11_shell_phase.json'),@('access_r11.questphase','access_r11_phase.json'),
      @('doors_r11_front.streamingsector','r11_doors_front_sector.json'),@('doors_r11_inner.streamingsector','r11_doors_inner_sector.json'),
      @('doors_r11.streamingblock','r11_doors_block.json'),@('street_people_r11_registry.streamingsector','r11_street_registry_sector.json'),
      @('street_people_r11_spots.streamingsector','r11_street_spots_sector.json'),@('street_people_r11.streamingblock','r11_street_block.json'))){
      $file=Read-Cr2wFile (Join-Path $source ('towercontinued\misty_viktor_world\'+$pair[0]))
      $dto=[WolvenKit.Common.Conversion.RedFileDto]::new($file,$false)
      $opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
      $freshObject=([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,$opt)|ConvertFrom-Json).Data
      $priorObject=(Get-Content -LiteralPath ('research\misty_viktor_world\'+$pair[1]) -Raw|ConvertFrom-Json).Data
      if($pair[0] -eq 'street_people_r11_registry.streamingsector'){
        $freshEntries=$freshObject.RootChunk.nodes[0].Data.communitiesData[0].template.Data.entries
        $priorEntries=$priorObject.RootChunk.nodes[0].Data.communitiesData[0].template.Data.entries
        if($freshEntries.Count -ne 4 -or $priorEntries.Count -ne 4){throw 'Registry template count changed'}
        $cast=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
        for($i=0;$i -lt 4;$i++){
          $a=$freshEntries[$i].Data.characterRecordId;$b=$priorEntries[$i].Data.characterRecordId
          if($a.'$storage' -eq 'string'){
            $record=[WolvenKit.RED4.Types.TweakDBID]::op_Implicit($a.'$value')
            $hash=$cast.Invoke($null,[object[]]@($record.PSObject.BaseObject)).ToString()
          }else{$hash=$a.'$value'}
          if($b.'$storage' -ne 'uint64' -or $hash -ne $b.'$value'){throw 'Registry record identity changed'}
          $freshEntries[$i].Data.characterRecordId=$b
        }
      }
      $fresh=$freshObject|ConvertTo-Json -Depth 100 -Compress
      $prior=$priorObject|ConvertTo-Json -Depth 100 -Compress
      if($fresh -ne $prior){throw ('Export differs from binary '+$pair[0])}
    }
    $access=Read-Cr2wFile (Join-Path $source 'towercontinued\misty_viktor_world\access_r11.questphase')
    $rear=(Get-QuestNode $access.RootChunk.Graph.Chunk 53).Type.Chunk.Params[0].Chunk.ObjectRef
    $rearText=($m.door_specs|Where-Object {$_.name -eq 'Rear'}).ref
    $single=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($rearText)
    $combined=[WolvenKit.RED4.Types.NodeRef]::op_Implicit(($rearText+';#q307_zetatech_doors_02'))
    $r2=Read-Cr2wFile './build/MistyViktorAccessR2/source/towercontinued/misty_viktor_world/shell_optin.questphase'
    $r2Rear=(Get-QuestNode $r2.RootChunk.Graph.Chunk 11).Type.Chunk.Params[0].Chunk.ObjectRef
    foreach($ref in @($rear,$single,$combined,$r2Rear)){
      if($ref.GetRedHash().ToString() -ne '3600113115862639549'){throw 'Outer rear identity differs from R2 proven target'}
    }
    [void][Reflection.Assembly]::LoadFrom('C:\Users\Ayong\Documents\WolvenKit-8.20.0\YamlDotNet.dll')
    $yaml=[YamlDotNet.RepresentationModel.YamlStream]::new()
    $reader=[IO.StringReader]::new([IO.File]::ReadAllText($m.archive+'.xl'))
    try{$yaml.Load($reader)}finally{$reader.Dispose()}
    if($yaml.Documents.Count -ne 1){throw 'Unexpected XL documents'}
    function Field($node,[string]$key){return ,$node.Children[[YamlDotNet.RepresentationModel.YamlScalarNode]::new($key)]}
    $root=$yaml.Documents[0].RootNode
    $blocks=@((Field (Field $root 'streaming') 'blocks').Children|ForEach-Object {$_.Value})
    $phases=@((Field (Field $root 'quest') 'phases').Children|ForEach-Object {
      $inputNode=Field $_ 'input'
      @{path=(Field $_ 'path').Value;parent=(Field $_ 'parent').Value;nodes=@((Field $inputNode 'node').Children|ForEach-Object {[int]$_.Value});socket=(Field $inputNode 'socket').Value}
    })
    Write-Output ('R11_PACKAGE_JSON:'+(@{payloads=$ar.Files.Count;blocks=$blocks;phases=$phases;binary_exports_match=$true;rear_alias_hash=$rear.GetRedHash().ToString()}|ConvertTo-Json -Depth 8 -Compress))
    '''
    result = subprocess.run(["pwsh", "-NoProfile", "-Command", code], cwd=ROOT, text=True,
                            capture_output=True, timeout=120)
    assert result.returncode == 0, (result.stdout, result.stderr)
    output = next(line.split(":", 1)[1] for line in result.stdout.splitlines() if line.startswith("R11_PACKAGE_JSON:"))
    return json.loads(output)


def main_controller(m):
    root, new, edges = graph(BASE / "access_r11_shell_phase.json")
    _, old, old_edges = graph(BASE / "access_r10_phase.json")
    assert set(new) == set(old) == set(range(50)) and root["phasePrefabs"] == []
    assert edges == {(a, socket, b, "In") for a, socket, b in m["main_edges"]}
    retired = set(range(31, 44))
    assert retired == set(m["retired_r10_nodes"])
    assert not any(a in retired or b in retired for a, _, b, _ in edges)
    assert not (retired | {11, 14, 15}) & reachable(edges)
    assert not any(new[i]["$type"] == "questInteractiveObjectManagerNodeDefinition"
                   and new[i].get("type", {}).get("$type") == "questDeviceManager_NodeType"
                   for i in reachable(edges)), "legacy door action remains live in main controller"
    for index in new:
        if index not in {5, 30, 44, 45}:
            assert new[index] == old[index], ("unexpected R10 payload delta", index)
    assert new[18]["type"]["factName"] == "PTFRMV_Revision" and new[18]["type"]["value"] == 7
    assert new[30]["type"]["factName"] == "PTFRMV_AccessRevision" and new[30]["type"]["value"] == 11
    assert new[45]["type"]["factName"] == "PTFRMV_InteriorNPCRequests"
    expected = {("#q307_com_main", "q307_zetatech_clerk", "q307_ws_zetatech_clerk_return"),
                ("#q307_com_alley", "q307_alley_extra_01", "return")}
    activate, deactivate = set(), set()
    for index in reachable(edges):
        for action in new[index].get("actions", []):
            p = action["type"]
            assert p["$type"] == "questCommunityTemplate_NodeType"
            target = (p["spawnerReference"]["$value"], p["communityEntryName"]["$value"], p["communityEntryPhaseName"]["$value"])
            assert p["action"] in {"Reactivate", "Deactivate"}
            (activate if p["action"] == "Reactivate" else deactivate).add(target)
    assert activate == deactivate == expected
    facts = dict(m["guards"])
    stop, entry = new[5]["condition"], new[2]["condition"]
    assert eval_stream(entry, facts, {}) and not eval_stream(stop, facts, {})
    for revision in (0, 7, 9, 10):
        assert eval_stream(stop, facts | {"PTFRMV_AccessRevision": revision}, {})
    negatives = 0
    for name, value in read(BASE / "access_r10_manifest.json")["guards"].items():
        for bad in {-1, 0, 1, 2} - {value}:
            wrong = facts | {name: bad}
            assert not eval_stream(entry, wrong, {}) and eval_stream(stop, wrong, {})
            negatives += 1
    return {"main_native_nodes": len(new), "main_negative_guards": negatives,
            "r10_branch_disconnected": True, "revision_migration_checked": [0, 7, 9, 10]}


def access_controller(m):
    root, ns, edges = graph(BASE / "access_r11_phase.json")
    assert root["phasePrefabs"] == []
    assert edges == {(a, socket, b, "In") for a, socket, b in m["access_edges"]}
    live = reachable(edges)
    specs = {d["name"]: d for d in m["door_specs"]}
    assert set(specs) == {"Front", "Inner", "Rear"}
    for name in ("Front", "Inner"):
        assert specs[name]["ref"] == "$/03_night_city/#PTFRMV_Zetatech" + name + "Door"
    assert "/#q115_misty_door_back" in specs["Rear"]["ref"]
    observed = Counter()
    for index in live:
        for p in ns[index].get("type", {}).get("params", []):
            assert p["$type"] == "questDeviceManager_NodeTypeParams"
            assert p["deviceControllerClass"]["$value"] == "DoorControllerPS" and p["actionProperties"] == []
            observed[p["objectRef"]["$value"], p["deviceAction"]["$value"]] += 1
    expected = Counter({(specs[n]["ref"], a): 1 for n in ("Front", "Inner")
                        for a in ("ForceCloseImmediate", "ForceUnlock")})
    expected[specs["Rear"]["ref"], "ForceUnlock"] = 1
    assert observed == expected, "door actions are not exactly two close/unlock plus outer-rear unlock"
    for index, action in ((72, "Reactivate"), (76, "Deactivate")):
        actions = ns[index]["actions"]
        assert len(actions) == 4
        assert {p["type"]["communityEntryName"]["$value"] for p in actions} == STREET_NAMES
        for p in actions:
            payload = p["type"]
            assert payload["action"] == action
            assert payload["communityEntryPhaseName"] == payload["communityEntryName"]
            assert payload["spawnerReference"]["$value"] == PRIVATE_STREET, "original post-cleanup workspots cannot service new population"
    load_refs = {o["objectRef"]["$value"] for o in walk(ns[70]["condition"]) if o.get("$type") == "questNodeLoadingCondition"}
    assert load_refs == set(m["private_street_spots"]) and len(load_refs) == 4
    assert m["private_street_spawner"] == PRIVATE_STREET
    door_refs = [specs[n]["ref"] for n in ("Front", "Inner", "Rear")]
    all_refs = door_refs + sorted(load_refs)
    valid, all_loaded = m["guards"], dict.fromkeys(all_refs, True)
    cases = 0
    for combination in itertools.product((False, True), repeat=len(all_refs)):
        loaded = dict(zip(all_refs, combination))
        sim = NativeDispatchModel(ns, edges, valid, loaded); sim.settle()
        for name, spec in specs.items():
            expected_count = int(loaded[spec["ref"]])
            assert sim.facts.get("PTFRMV11_" + name + "Requests", 0) == expected_count
            assert sim.facts.get("PTFRMV11_" + name + "Ready", 0) == expected_count
        street = int(all(loaded[ref] for ref in load_refs))
        assert sim.facts.get("PTFRMV11_StreetRequests", 0) == street
        assert sum(a[1] == "community" for a in sim.actions) == street * 4
        count = len(sim.actions); sim.settle(); assert len(sim.actions) == count
        cases += 1
    negative = 0
    for fact, value in valid.items():
        for bad in {-1, 0, 1, 2} - {value}:
            sim = NativeDispatchModel(ns, edges, valid | {fact: bad}, all_loaded); sim.settle()
            assert sim.actions == [], ("unguarded initial action", fact, bad)
            negative += 1
    # Starting with everything loaded, each unload/reload only rearms its owner.
    for ref in all_refs:
        sim = NativeDispatchModel(ns, edges, valid, all_loaded); sim.settle()
        first = len(sim.actions); sim.loaded[ref] = False; sim.settle()
        if ref in load_refs:
            assert len(sim.actions) == first + 4 and all(a[3] == "Deactivate" for a in sim.actions[first:])
            assert sim.facts["PTFRMV11_StreetReady"] == 0
        else:
            assert len(sim.actions) == first
        sim.loaded[ref] = True; sim.settle()
        for name, spec in specs.items():
            assert sim.facts["PTFRMV11_" + name + "Requests"] == (2 if spec["ref"] == ref else 1)
        assert sim.facts["PTFRMV11_StreetRequests"] == (2 if ref in load_refs else 1)
    # Guard loss releases owned street entries; doors issue no new device write.
    for fact, value in valid.items():
        sim = NativeDispatchModel(ns, edges, valid, all_loaded); sim.settle()
        first = len(sim.actions); sim.facts[fact] = value + 1; sim.settle()
        assert len(sim.actions) == first + 4 and all(a[3] == "Deactivate" for a in sim.actions[first:])
        assert all(sim.facts["PTFRMV11_" + n + "Ready"] == 0 for n in (*specs, "Street"))
        sim.facts[fact] = value; sim.settle()
        assert all(sim.facts["PTFRMV11_" + n + "Requests"] == 2 for n in (*specs, "Street"))
    # A load/guard change after a wait wakes but before its condition is checked
    # must return to waiting without a device/community action.
    for start in (10, 30, 50, 70):
        sim = NativeDispatchModel(ns, edges, valid, all_loaded, initial=start)
        sim.settle(before=start + 1); sim.facts["q307_active"] = 1; sim.settle()
        assert sim.actions == []
    return {"access_native_nodes": len(ns), "independent_stream_combinations": cases,
            "access_negative_guards": negative, "unload_reload_cases": len(all_refs),
            "guard_loss_rearm_cases": len(valid), "wait_check_race_cases": 4,
            "reachable_door_actions": 5, "street_entries": 4}


def world_scope(m):
    r7 = read(BASE / "details_r7_manifest.json")
    changed = [d for d in r7["resources"] if (ROOT / "build/MistyViktorDetailsR7/source" / d).read_bytes() != (SOURCE / d).read_bytes()]
    assert changed == [PHASE] or set(changed) == {PHASE}
    assert len(r7["resources"]) - len(changed) == 22
    assert all(d.startswith("towercontinued\\misty_viktor_world\\") for d in m["resources"])
    assert sorted(str(p.relative_to(SOURCE)) for p in SOURCE.rglob("*") if p.is_file()) == sorted(m["resources"])
    doors = read(BASE / "r11_doors_manifest.json")
    assert doors["door_entities"] == 2 and doors["exact_payload_transform_readback_pass"]
    assert doors["original_world_overrides"] == doors["original_templates_changed"] == 0
    assert doors["default_range_count"] == 0 and doors["fresh_aliases_and_identities"]
    t = doors["template"]
    assert (t["opened"], t["locked"], t["sealed"], t["interactive"], t["device_state"]) == (0, 0, 0, 1, "ON")
    assert t["door_properties"]["doorType"] == "INTERACTIVE" and t["door_properties"]["initialDoorState"] == "CLOSED"
    assert t["door_properties"]["automaticallyClosesItself"] == 1
    private_ids = set()
    for selection in doors["selections"]:
        assert sha(ROOT / selection["source"]) == selection["source_sha256"]
        assert sha(SOURCE / selection["depot"]) == selection["sha256"]
        sector = read(BASE / ("r11_doors_" + selection["name"] + "_sector.json"))["Data"]["RootChunk"]
        assert len(sector["nodes"]) == len(sector["nodeData"]["Data"]) == 1
        node, datum = sector["nodes"][0]["Data"], sector["nodeData"]["Data"][0]
        assert node["$type"] == "worldEntityNode" and node["instanceData"] is None
        assert node["entityTemplate"]["DepotPath"]["$value"] == t["depot"]
        assert node["appearanceName"]["$value"] == selection["appearance"]
        assert datum["Position"] == selection["position"]
        assert datum["Id"] == selection["private_id"]
        assert datum["QuestPrefabRefHash"]["$value"] == selection["private_ref"]
        assert [ref["$value"] for ref in sector["nodeRefs"]] == [selection["private_ref"]]
        private_ids.add(datum["Id"])
    assert len(private_ids) == 2
    block = read(BASE / "r11_doors_block.json")["Data"]["RootChunk"]
    assert sha(SOURCE / doors["block_depot"]) == doors["block_sha256"]
    for descriptor in block["descriptors"]:
        assert len(descriptor["variants"]) == 1
        v = descriptor["variants"][0]
        assert v["enabledByDefault"] == 0 and v["rangeIndex"] == 1
        assert v["name"]["$value"] == doors["variant_name"] and v["nodeRef"]["$value"] == doors["variant_owner"]
    return {"unchanged_r7_resources": 22, "new_private_doors": 2,
            "source_default_door_interactive_closed_unlocked": True}


def private_street_scope(m):
    sm = read(BASE / "r11_street_world_manifest.json")
    assert sm["private_spawner"] == m["private_street_spawner"] == PRIVATE_STREET
    assert sm["registry_entries"] == sm["compiled_area_entries"] == sm["workspots"] == sm["workspot_persistent_descriptors"] == 4
    assert sm["initial_active_entries"] == 0 and sm["no_spawn_before_native_activation"]
    assert sm["no_original_overrides"] and sm["no_original_record_or_template_resource_changes"]
    assert sha(ROOT / sm["source_registry"]) == sm["source_registry_sha256"]
    assert sha(ROOT / sm["source_spots"]) == sm["source_spots_sha256"]
    for resource in sm["hashes"]:
        assert sha(SOURCE / resource["depot"]) == resource["sha256"]
    registry = read(BASE / "r11_street_registry_sector.json")["Data"]["RootChunk"]
    spots = read(BASE / "r11_street_spots_sector.json")["Data"]["RootChunk"]
    original = read(BASE / "r6_wall_nav_sources/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/ep1/quest_bb3937b6e34a251c.streamingsector.json")["Data"]["RootChunk"]
    assert len(registry["nodes"]) == len(registry["nodeData"]["Data"]) == 2
    assert len(spots["nodes"]) == len(spots["nodeData"]["Data"]) == len(spots["nodeRefs"]) == 4
    rh, sh, oh = handles(registry), handles(spots), handles(original)
    reg, area = [canonical(n, rh) for n in registry["nodes"]]
    assert reg["$type"] == "worldCommunityRegistryNode" and area["$type"] == "worldCompiledCommunityAreaNode"
    assert reg["representsCrowd"] == 0 and reg["crowdCreationRegistry"] is None
    assert reg["spawnSetNameToCommunityID"]["entries"] == []
    assert len(reg["communitiesData"]) == 1
    community = reg["communitiesData"][0]
    assert community["communityId"]["entityId"]["hash"] == area["sourceObjectId"]["hash"] == sm["private_community_hash"]
    assert community["template"]["crowdEntries"] == []
    entry_map = {e["entryName"]["$value"]: e for e in community["template"]["entries"]}
    initial = {e["entryName"]["$value"]: e for e in community["entriesInitialState"]}
    compiled = {e["entryName"]["$value"]: e for e in area["area"]["entriesData"]}
    assert set(entry_map) == set(initial) == set(compiled) == STREET_NAMES
    assert all(e["entryActiveOnStart"] == 0 for e in initial.values())
    persistent = {p["globalNodeId"]["hash"]: p for p in reg["workspotsPersistentData"]}
    assert len(persistent) == 4
    mappings = {p["private_ref"]: p for p in sm["source_spot_mapping"]}
    records = {e["entry"]: e for e in m["street_entries"]}
    all_ids = set()
    for index, expected in enumerate(sm["entries"]):
        name, ref = expected["entry"], expected["private_workspot_ref"]
        mapping, entry = mappings[ref], entry_map[name]
        phase = entry["phases"][0]
        assert len(entry["phases"]) == 1 and entry["initializers"] == []
        assert initial[name]["initialPhaseName"]["$value"] == phase["phaseName"]["$value"] == name
        assert phase["alwaysSpawned"] == "default__false_"
        assert phase["appearances"][0]["$value"] == records[name]["appearance"]
        assert len(phase["appearances"]) == 1 and len(phase["timePeriods"]) == 1
        record = expected["record"]
        tdbid = zlib.crc32(record.encode()) | (len(record.encode()) << 32)
        assert entry["characterRecordId"]["$value"] == str(tdbid)
        period = phase["timePeriods"][0]
        assert period["quantity"] == 1 and period["hour"] == "Day" and period["isSequence"] == 0
        assert period["categories"] == period["markings"] == []
        assert [s["$value"] for s in period["spotNodeRefs"]] == [ref]
        data = compiled[name]["phasesData"]
        assert len(data) == 1 and data[0]["entryPhaseName"]["$value"] == name
        compiled_periods = data[0]["timePeriodsData"]
        assert len(compiled_periods) == 1
        assert [s["hash"] for s in compiled_periods[0]["spotNodeIds"]] == [mapping["private_hash"]]
        assert compiled_periods[0]["isSequence"] == 0 and compiled_periods[0]["periodName"]["$value"] == "Day"
        new_node = canonical(spots["nodes"][index], sh)
        original_node = canonical(original["nodes"][expected["source_node"]], oh)
        for field in ("debugName", "sourcePrefabHash"):
            new_node[field] = original_node[field]
        assert new_node == original_node, ("workspot payload changed", name)
        assert new_node["$type"] == "worldAISpotNode" and new_node["isWorkspotInfinite"] == 1
        assert new_node["spot"]["masterNodeRef"]["$value"] == "0" and new_node["lookAtTarget"]["$value"] == "0"
        assert new_node["spot"]["resource"]["DepotPath"]["$value"] == expected["workspot"]
        datum = dict(spots["nodeData"]["Data"][index])
        source_datum = original["nodeData"]["Data"][expected["source_datum"]]
        assert datum["QuestPrefabRefHash"]["$value"] == ref and datum["NodeIndex"] == index
        all_ids.add(datum["Id"])
        for field in ("Id", "NodeIndex", "QuestPrefabRefHash", "UkHash1"):
            datum[field] = source_datum[field]
        assert datum == source_datum, ("workspot transform changed", name)
        p = persistent[mapping["private_hash"]]
        assert p["isEnabled"] == 1
        for axis, poskey in (("x", "X"), ("y", "Y"), ("z", "Z")):
            assert abs(p["worldPosition"][axis]["Bits"] / 131072 - datum["Position"][poskey]) < 0.001
    assert len(all_ids) == 4
    assert {r["$value"] for r in spots["nodeRefs"]} == set(m["private_street_spots"])
    block = read(BASE / "r11_street_block.json")["Data"]["RootChunk"]
    assert len(block["descriptors"]) == 2
    by_path = {d["data"]["DepotPath"]["$value"]: d for d in block["descriptors"]}
    reg_descriptor = by_path[next(d for d in sm["resources"] if "registry.streamingsector" in d)]
    spot_descriptor = by_path[next(d for d in sm["resources"] if "spots.streamingsector" in d)]
    assert reg_descriptor["category"] == "AlwaysLoaded" and reg_descriptor["variants"] == []
    assert len(spot_descriptor["variants"]) == 1
    variant = spot_descriptor["variants"][0]
    assert variant["enabledByDefault"] == 0 and variant["rangeIndex"] == 1
    assert variant["name"]["$value"] == "PTFRMV_ZetatechShell"
    return {"private_street_registry_entries": 4, "private_street_compiled_entries": 4,
            "private_workspots_source_payloads_preserved": 4, "private_street_initially_active": 0}


def main():
    m = read(BASE / "access_r11_manifest.json")
    assert m["access_revision"] == 11 and m["compatibility_revision"] == 7
    assert m["original_world_overrides"] == m["story_writes"] == m["scene_starts"] == 0
    assert sha(Path(m["archive"])) == m["sha256"] and sha(Path(m["archive"] + ".xl")) == m["xl_sha256"]
    results = main_controller(m) | access_controller(m) | world_scope(m) | private_street_scope(m)
    for path in ("access_r11_shell_phase.json", "access_r11_phase.json"):
        root = read(BASE / path)
        assert not any(o.get("$type") in {"questSceneNodeDefinition", "questPhaseNodeDefinition"} for o in walk(root))
        writes = {o["factName"] for o in walk(root) if o.get("$type") == "questSetVar_NodeType"}
        assert all(name.startswith(("PTFRMV_", "PTFRMV11_")) for name in writes)
    package = packed_and_yaml()
    expected_blocks = {d for d in m["resources"] if d.endswith(".streamingblock")}
    assert set(package["blocks"]) == expected_blocks and len(package["blocks"]) == len(expected_blocks)
    assert len(package["phases"]) == 2 and {p["path"] for p in package["phases"]} == {PHASE, ACCESS}
    assert all(p["parent"] == r"ep1\quest\ep1.quest" and p["nodes"] == [1] and p["socket"] == "Out" for p in package["phases"])
    report = {"status": "PASS_R11_OFFLINE_NOT_LIVE", "archive_sha256": m["sha256"],
              "xl_sha256": m["xl_sha256"], **results, "packed_payloads_verified": package["payloads"],
              "binary_exports_match": package["binary_exports_match"], "rear_alias_hash": package["rear_alias_hash"], "parsed_xl_blocks": len(package["blocks"]),
              "parsed_xl_phases": 2, "story_writes": 0, "scene_starts": 0, "live_tested": False}
    (BASE / "access_r11_tests.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
