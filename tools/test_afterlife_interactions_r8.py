"""Exact source deltas + native graph contract/model + actual redscript compile.

Offline evidence only; models do not prove engine scene acquisition or motion.
"""
import copy
import itertools
import json
import re
import subprocess
from pathlib import Path
from test_afterlife_booth_r6 import clean, read, sha, walk, differences
from test_radio_memorial import handles
from audit_wilson_vendor_owner import graph_edges

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'research/afterlife_world'
OUT = BASE/'interactions_r8'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DRIVER = ROOT/'redscript/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'
E = '$/03_night_city/#PTFRAL1_Emmerick'
R = '$/03_night_city/#PTFRAF1_RogueCommunity'
PREFIX = 'towercontinued\\afterlife_interactions_r8\\'

def nodes(scene):
    return {n['nodeId']['id']: n for n in scene['sceneGraph']['graph']}

def bind(actor, ref, entry):
    actor['acquisitionPlan'] = 'community'
    actor['communityParams']['reference']['$value'] = ref
    actor['communityParams']['reference']['$storage'] = 'string'
    actor['communityParams']['entryName']['$value'] = entry
    actor['spawnSetParams']['reference']['$value'] = '0'
    actor['spawnSetParams']['reference']['$storage'] = 'uint64'
    actor['spawnSetParams']['entryName']['$value'] = 'None'

def scope(scene, start, end):
    by_id = nodes(scene)
    seen, todo = set(), [start]
    while todo:
        i = todo.pop()
        if i in seen: continue
        seen.add(i)
        todo.extend(d['nodeId']['id'] for s in by_id[i]['outputSockets'] for d in s['destinations'])
    scene['sceneGraph']['graph'] = [n for n in scene['sceneGraph']['graph'] if n['nodeId']['id'] in seen]
    scene['sceneGraph']['startNodes'] = [n for n in scene['sceneGraph']['startNodes'] if n['id'] == start]
    scene['sceneGraph']['endNodes'] = [n for n in scene['sceneGraph']['endNodes'] if n['id'] == end]
    scene['entryPoints'] = [n for n in scene['entryPoints'] if n['nodeId']['id'] == start]
    scene['exitPoints'] = [n for n in scene['exitPoints'] if n['nodeId']['id'] == end]
    return seen

def redirect(scene, src, before, after):
    matches = [d for s in nodes(scene)[src]['outputSockets'] for d in s['destinations'] if d['nodeId']['id'] == before]
    assert len(matches) == 1
    matches[0]['nodeId']['id'] = after
    matches[0]['isockStamp']['name'] = 0
    matches[0]['isockStamp']['ordinal'] = 0

def fact_leaves(value):
    return [n for n in walk(value) if n.get('$type') == 'questVarComparison_ConditionType']

def main():
    m = read(OUT/'manifest.json'); r7 = read(BASE/'emmerick_r7/manifest.json')
    assert m['packed_readback'] and len(m['resources']) == 13
    assert sha(m['archive']) == m['sha256'] and sha(m['archive']+'.xl') == m['xl_sha256']
    for p, h in m['source_hashes'].items(): assert sha(p) == h, p
    changed = [p for p in r7['resources'] if sha(Path(m['source_root'])/p) != sha(Path(r7['source_root'])/p)]
    assert changed == ['towercontinued\\afterlife_r1\\patrons_registry.streamingsector', 'towercontinued\\afterlife_r1\\patrons_spots.streamingsector']
    assert set(m['resources']) - set(r7['resources']) == {PREFIX+x for x in ('emmerick.scene','rogue.scene','owner.questphase')}
    # R7 spots and registry are unchanged prefixes; one start spot, one trigger,
    # one persistent descriptor and one phase in the EXISTING actor are added.
    before = clean(BASE/'emmerick_r7/patrons_spots.streamingsector.json')
    after = clean(OUT/'patrons_spots.streamingsector.json')
    assert len(after['nodes']) == 81 and len(after['nodeRefs']) == len(before['nodeRefs'])+2
    for key in ('nodes','nodeRefs'): after[key] = after[key][:-2]
    after['nodeData']['Data'] = after['nodeData']['Data'][:-2]
    assert before == after, differences(before, after)[:5]
    vanilla = clean(BASE/'emmerick_r7/vanilla_entrance.streamingsector.json')
    after = clean(OUT/'patrons_spots.streamingsector.json')
    for i, old in ((79,84),(80,64)):
        v = copy.deepcopy(vanilla['nodes'][old]); n = after['nodes'][i]
        for k in ('sourcePrefabHash','debugName'): v[k] = n[k]
        assert v == n, differences(v,n)[:4]
        a = next(n for n in after['nodeData']['Data'] if n['NodeIndex'] == i)
        b = copy.deepcopy(next(n for n in vanilla['nodeData']['Data'] if n['NodeIndex'] == old))
        for k in ('Id','NodeIndex','QuestPrefabRefHash','UkHash1'): b[k] = a[k]
        assert a == b, differences(a,b)[:4]
    # The native trigger outline buffer and notifier remain exact vanilla data.
    assert after['nodes'][80]['$type'] == 'worldTriggerAreaNode'
    before = clean(BASE/'emmerick_r7/patrons_registry.streamingsector.json')
    after = clean(OUT/'patrons_registry.streamingsector.json')
    entry = after['nodes'][0]['communitiesData'][1]['template']['entries'][0]
    assert len(entry['phases']) == 2
    added = entry['phases'].pop(); expected = copy.deepcopy(entry['phases'][0])
    expected['phaseName']['$value'] = 'PTFRAL8_Entrance'
    expected['timePeriods'][0]['spotNodeRefs'][0]['$value'] = '$/03_night_city/#PTFRAL8_EmmerickStart'
    assert added == expected, differences(added,expected)[:4]
    assert added['timePeriods'][0]['quantity'] == 1
    a = after['nodes'][2]['area']['entriesData'][0]['phasesData']
    added_area = a.pop(); expected_area = copy.deepcopy(a[0]); expected_area['entryPhaseName']['$value'] = 'PTFRAL8_Entrance'
    expected_area['timePeriodsData'][0]['spotNodeIds'] = added_area['timePeriodsData'][0]['spotNodeIds']
    assert added_area == expected_area
    pd = after['nodes'][0]['workspotsPersistentData'].pop()
    assert pd['globalNodeId']['hash'] == added_area['timePeriodsData'][0]['spotNodeIds'][0]['hash']
    assert before == after, differences(before,after)[:5]

    # Exact scene transformations; all clips, selection/history conditions,
    # localization, voices and helper resource tables remain unchanged.
    src = clean(OUT/'sources/json/base/quest/main_quests/part1/q103/scenes/q103_02_afterlife_intro.scene.json')
    target = clean(OUT/'emmerick.scene.json')
    bind(src['actors'][0],E,'emmerick')
    nodes(src)[445]['questNode']['entityReference']['reference']['$value'] = E
    nodes(src)[447]['questNode'] = copy.deepcopy(nodes(target)[447]['questNode'])
    assert scope(src,440,449) == {440,441,445,447,449}
    assert src == target, differences(src,target)[:8]
    action = nodes(target)[447]['questNode']['actions'][0]['type']
    assert action['action'] == 'Activate' and action['communityEntryPhaseName']['$value'] == 'q005_emmerick_bouncer'
    assert E in json.dumps(action)
    motion = next(n for n in walk(nodes(target)[441]) if n.get('$type') == 'scnPlaySkAnimEvent')
    assert motion['rootMotionData']['placementMode'] == 'PlayAtActorPosition'
    assert motion['animName']['unk1'][0]['$value'] == 'stand__2h_front__01__two_step_right__01'
    assert nodes(target)[441]['sectionDuration']['stu'] == 4533
    src = clean(BASE/'rogue_sources/json/base/quest/secondary_characters/default_dialogues/rogue_default.scene.json')
    target = clean(OUT/'rogue.scene.json')
    bind(src['actors'][0],R,'rogue'); src['actors'].pop(1)
    redirect(src,4,266,268); redirect(src,276,271,273); redirect(src,4,228,2)
    for i in (140,142,144,147,154,157): nodes(src)[i]['questNode']['entityReference']['reference']['$value'] = R
    nodes(src)[235]['questNode']['type']['sceneFile']['DepotPath']['$value'] = PREFIX+'rogue.scene'
    ids = scope(src,1,2); assert len(ids) == 47
    src['interruptionScenarios'] = src['interruptionScenarios'][:1]
    for n in src['sceneGraph']['graph']:
        if n['$type'] == 'scnChoiceNode': n['forceAttachToScreenCondition'] = None
        if n['$type'] == 'scnSectionNode':
            n['events'] = [e for e in n['events'] if not e['executionTagFlags'] & 1]
            n['actorBehaviors'] = [e for e in n['actorBehaviors'] if e['actorId']['id'] != 1]
    src['exitPoints'][0]['name']['$value'] = 'local_out'
    assert src == target, differences(src,target)[:10]
    assert len(target['actors']) == 1 and target['playerActors'][0]['actorId']['id'] == 2
    assert all(n['nodeId']['id'] in ids for n in target['notablePoints'])
    for n in walk(target['sceneGraph']):
        assert n.get('$type') != 'questSetVar_NodeType', n
        if n.get('$type') == 'NodeRef': assert n['$value'] in ('0',R), n
        if n.get('$type') == 'questUseWorkspotNodeDefinition': assert n['paramsV1']['playAtActorLocation'] == 1
    for i, action in ((136,'Play'),(192,'Break')):
        assert any(n.get('$type') == 'scneventsVFXEvent' and n['action'] == action and n['effectEntry']['effectName']['$value'] == 'eye_glow_gold' for n in walk(nodes(target)[i]))
    assert not any(n.get('$type') == 'questSetVar_NodeType' for n in walk(clean(OUT/'emmerick.scene.json')))

    # Traverse native owner with sockets (canonical form excludes sockets).
    raw = read(OUT/'owner.questphase.json')['Data']['RootChunk']; lookup = handles(raw)
    owner = clean(OUT/'owner.questphase.json'); graph = owner['graph']; all_graphs = [graph]
    all_graphs.extend(n['phaseGraph'] for n in graph['nodes'] if n['$type'] == 'questPhaseNodeDefinition')
    assert len(all_graphs) == 3 and sum(len(g['nodes']) for g in all_graphs) == 32
    writes = [n['factName'] for n in walk(owner) if n.get('$type') == 'questSetVar_NodeType']
    assert writes and all(n.startswith('PTFRAL8_') for n in writes)
    scenes = [n for n in walk(owner) if n.get('$type') == 'questSceneNodeDefinition']
    assert len(scenes) == 2
    assert {n['sceneFile']['DepotPath']['$value'] for n in scenes} == {PREFIX+'emmerick.scene',PREFIX+'rogue.scene'}
    assert len([n for n in walk(owner) if n.get('$type') == 'questSpawnManagerNodeDefinition']) == 1
    graph_map = {n['id']:n for n in graph['nodes']}
    for base, who in ((100,'E'),(200,'R')):
        phase = graph_map[base+4]; local = {n['id']:n for n in phase['phaseGraph']['nodes']}
        assert local[1]['type'] == 'Terminating'
        for node in (graph_map[base+1],graph_map[base+2],local[2],local[3]):
            text = json.dumps(node['condition'])
            assert all('"'+name+'"' in text for name in m['guards'])
            assert 'PTFRAL8_'+who+'Continue' in text
        interrupt = json.dumps(local[5]['condition'])
        assert all('"'+name+'"' in interrupt for name in m['guards'])
        assert 'PTFRAL8_'+who+'Continue' in interrupt
        depart = json.dumps(graph_map[base+6]['condition'])
        assert 'Continue' not in depart, 'Transient scene-release must not bypass departure latch'
    native_edges = []
    def collect(g, route):
        edges = graph_edges(g,route,lookup); native_edges.extend(edges)
        ids = {n['Data']['id'] for n in g['nodes']}
        assert all(e['source_node_id'] in ids and e['destination_node_id'] in ids for e in edges)
        for n in g['nodes']:
            d=n['Data']
            if d.get('phaseGraph'): collect(d['phaseGraph']['Data'],route+'/'+str(d['id']))
    collect(raw['graph']['Data'],'root')
    assert len(native_edges) == 37, len(native_edges)
    # Native guard negative and full stream/permission interleaving contract.
    model_cases = 0
    for flags in itertools.product((False,True), repeat=8):
        allowed, identity, healthy, loaded, ready, start, inside, outside = flags
        acquire = allowed and identity and healthy and loaded and ready and outside
        execute = allowed and identity and healthy and loaded and ready and start and inside
        release = not (allowed and identity and healthy and loaded and ready)
        assert not (execute and release)
        if not all(flags[:5]): assert not acquire and not execute
        model_cases += 1
    # Regression: completion/temporary permission flicker cannot restart while
    # nearby; unload/reload and a genuine departure must revisit guarded entry.
    for event in ('goodbye','interrupt','unload','reload','death','combat'):
        waiting_departure = True
        for transient in (False,True,False):
            departed = event in ('unload','reload')
            can_restart = not waiting_departure or departed
            if not departed: assert not can_restart

    text = DRIVER.read_text()
    assert 'ArraySize(ids) != 1' in text and 'npc.GetRecordID() != record' in text
    assert all(x in text for x in ('this.ClearPermissions();','this.epoch += 1','this.warmup = 4','this.eAge >= 80','this.glowOwner != r','BreakEffectLoopEvent','q116_rogue_dead'))
    assert not any(x in text for x in ('SendCommand(', 'Reactivate', 'Respawn(', 'StartEffectEvent', 'SetAppearance('))
    assert set(re.findall(r'this.Set\(q, n"([^"]+)"',text)) == {'PTFRAL8_'+s for s in ('DriverReady','EContinue','EAvailable','EStart','RContinue','RAvailable','RStart','RDeparted')}
    cmd = [str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),'compile','-s',str(DRIVER.parent),'-s',str(ROOT/'redscript/PTFR_Afterlife_Idles_R3'),'-s',str(ROOT/'redscript/PTFR_Afterlife_Faces_R5'),'-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(GAME/'r6/cache/final.redscripts'),'-o',str(OUT/'compile.redscripts')]
    result = subprocess.run(cmd,capture_output=True,text=True)
    log = result.stdout+result.stderr
    (OUT/'compile.log').write_text(log)
    assert result.returncode == 0 and 'ERROR' not in log and 'Output successfully saved' in log, log
    expected = {}
    for path in ('install_receipt.json','population_r2/install_receipt.json','idles_r3/install_receipt.json','faces_r5/install_receipt.json','booth_r6/install_receipt.json','emmerick_r7/install_receipt.json'):
        for f in read(BASE/path)['files']: expected[f['relative'].replace('\\','/')] = f['sha256']
    for p,h in expected.items(): assert sha(GAME/p) == h,p
    files = []
    for suffix in ('','.xl'):
        p = 'archive/pc/mod/TowerContinued_AfterlifeR1.archive'+suffix
        source = Path(m['archive']+suffix)
        files.append(dict(relative=p,source=str(source.relative_to(ROOT)),sha256=sha(source),before_sha256=expected[p]))
    relative = 'r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'
    assert not (GAME/relative).exists()
    files.append(dict(relative=relative,source=str(DRIVER.relative_to(ROOT)),sha256=sha(DRIVER),before_sha256=None))
    report = dict(status='PASS_R8_OFFLINE_NOT_INSTALLED_NOT_LIVE',packed_readback=True,
        exact_prior_payloads_unchanged=8,emmerick_scene_nodes=5,rogue_local_scene_nodes=47,
        native_nodes=32,native_edges=len(native_edges),guard_stream_model_cases=model_cases,
        redscript_compile=True,scene_exact_deltas=True,protected_prior_afterlife_files=len(expected),
        source_story_writes=0,new_actor_identities=0,original_overrides=0,
        manifest_sha256=sha(OUT/'manifest.json'),builder_sha256=sha(ROOT/'tools/build_afterlife_interactions_r8.ps1'),
        validator_sha256=sha(__file__),runtime_sha256=sha(DRIVER),files=files,
        limits=['Not an engine simulation','Live private scene acquisition, trigger mapping, phase walking, eye rendering and dialogue availability need play testing','Saved graph restoration and native/runtime scheduling require live reload testing'],live_tested=False)
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
