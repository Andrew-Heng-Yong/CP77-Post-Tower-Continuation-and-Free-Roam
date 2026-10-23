"""Independent R7 exact-preservation, supplemental payload and opt-in checks."""
import hashlib
import json
import sys
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_street_r3 import quest_normalized
from test_misty_viktor_optin import evaluate
from test_misty_viktor_repair_r6 import evaluate_loading

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/misty_viktor_world'
OLD = ROOT / 'build/MistyViktorRepairR6/source'
NEW = ROOT / 'build/MistyViktorDetailsR7/source'
PHASE = r'towercontinued\misty_viktor_world\shell_optin.questphase'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_probe(facts):
    sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    path = ROOT / 'diagnostics/PTFR_MistyViktor_World/init.lua'
    code = path.read_text()
    assert code.count('SetFactStr("PTFRMV_Enabled",') == 2
    assert not any(x in code for x in ('NewObject', 'Teleport(', 'ExecuteQuest', 'TogglePrefab'))
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};writes={};f={};pos={x=-1658.9,y=997.4,z=23.7}
    function IsDefined(x)return x~=nil end
    function registerForEvent(n,cb)events[n]=cb end
    function print(...)end
    json={encode=function()return 'row' end}
    io={open=function(n,m)if m=='r' then return nil end;return {write=function(self)return self end,flush=function()return true end,close=function()return true end}end}
    local q={GetFactStr=function(self,k)return f[k] or 0 end,SetFactStr=function(self,k,v)f[k]=v;writes[#writes+1]={k,v}end}
    Game={GetQuestsSystem=function()return q end,GetPlayer=function()return {GetWorldPosition=function()return pos end}end}''')
    mod = lua.execute(code)
    facts_lua = lua.globals().f
    for key, value in facts.items():
        facts_lua[key] = value
    facts_lua.PTFRMV_Registered, facts_lua.PTFRMV_Enabled = 1, 0
    for stale in (0, 4, 5, 6):
        facts_lua.PTFRMV_Revision = stale
        mod.Start()
        assert len(lua.globals().writes) == 0
    facts_lua.PTFRMV_Revision = 7
    mod.Start(); mod.Start()
    assert len(lua.globals().writes) == 1
    lua.execute('pos={x=-1542,y=1210,z=16}')
    mod.Stop()
    assert facts_lua.PTFRMV_Enabled == 1
    lua.execute('pos={x=-1658.9,y=997.4,z=23.7}')
    mod.Stop(); mod.Finish()
    assert facts_lua.PTFRMV_Enabled == 0
    facts_lua.q307_active = 1
    mod.Start()
    assert len(lua.globals().writes) == 2
    return sha(path)


def main():
    from test_misty_construction_r7 import main as check_construction
    check_construction()
    m = read(BASE / 'details_r7_manifest.json')
    oldm = read(BASE / 'repair_r6_manifest.json')
    assert m['status'] == 'BUILT_R7_DETAILS_NOT_INSTALLED_OR_LIVE'
    assert m['guards'] == oldm['guards'] and m['edges'] == oldm['edges']
    assert m['original_lighting_changes'] == m['original_world_resource_overrides'] == 0
    assert m['native_scene_starts'] == m['story_fact_writes'] == 0
    assert m['construction_mesh_instances'] == 18 and m['truck_spawners'] in (0, 2)
    if m['truck_spawners']:
        from test_misty_trucks_r7 import main as check_trucks
        check_trucks()
    expected_supplements = ['r7_construction_manifest.json'] + (['r7_trucks_manifest.json'] if m['truck_spawners'] else [])
    assert [s['manifest'] for s in m['supplements']] == expected_supplements
    additions, blocks = [], []
    for entry in m['supplements']:
        path = BASE / entry['manifest']
        assert sha(path) == entry['sha256']
        supplement = read(path)
        assert entry['resources'] == supplement['resources'] and len(entry['resources']) == 2
        for depot in entry['resources']:
            assert depot.startswith('towercontinued\\misty_viktor_world\\') and '..' not in depot
            assert (NEW / depot).read_bytes() == (Path(supplement['source_root']) / depot).read_bytes()
        additions.extend(entry['resources'])
        blocks.append(supplement['block_depot'])
    assert len(additions) == len(set(additions))
    assert len(m['resources']) == len(set(m['resources'])) == 19 + len(additions)
    assert set(m['resources']) == set(oldm['resources']) | set(additions)
    changed = {d for d in oldm['resources'] if (OLD / d).read_bytes() != (NEW / d).read_bytes()}
    assert changed == {PHASE}
    assert sha(Path(m['archive'])) == m['sha256']
    assert sha(Path(m['archive']+'.xl')) == m['xl_sha256']
    oldxl = Path(oldm['archive']+'.xl').read_text(encoding='utf-8-sig').splitlines()
    newxl = Path(m['archive']+'.xl').read_text(encoding='utf-8-sig').splitlines()
    anchor = '    - towercontinued\\misty_viktor_world\\crowd_alley_r6.streamingblock'
    index = oldxl.index(anchor) + 1
    assert newxl == oldxl[:index] + ['    - '+b for b in blocks] + oldxl[index:]
    old = read(BASE / 'repair_r6_phase.json')['Data']['RootChunk']
    new = read(BASE / 'details_r7_phase.json')['Data']['RootChunk']
    oh, nh = handles(old), handles(new)
    on, nn = nodes(old), nodes(new)
    assert set(on) == set(nn) == set(range(30))
    assert old['phasePrefabs'] == new['phasePrefabs'] == []
    for obj in walk(new):
        if 'HandleRefId' in obj:
            assert str(obj['HandleRefId']) in nh
    for index in range(30):
        before = quest_normalized(canonical(on[index], oh))
        after = quest_normalized(canonical(nn[index], nh))
        if index == 18:
            assert before['type']['factName'] == after['type']['factName'] == 'PTFRMV_Revision'
            assert before['type']['value'] == 6 and after['type']['value'] == 7
            before['type']['value'] = 7
        assert before == after, ('Unexpected R6 node change', index)
    assert quest_edges(old)[0] == quest_edges(new)[0]
    entry, stop, restore = (canonical(nn[i]['condition'], nh) for i in (2, 5, 13))
    wait, ready, unload, rearm = (canonical(nn[i]['condition'], nh) for i in (25, 26, 27, 28))
    facts = m['guards']
    assert evaluate(entry, facts) and not evaluate(stop, facts)
    assert evaluate(restore, facts | {'PTFRMV_Enabled': 0})
    negatives = 0
    for fact, value in facts.items():
        for bad in (-1, 0, 1, 2):
            if bad == value:
                continue
            state = facts | {fact: bad}
            assert not evaluate(entry, state) and evaluate(stop, state)
            if fact != 'PTFRMV_Enabled':
                assert not evaluate(restore, state)
            for resident in (False, True):
                assert evaluate_loading(wait, state, resident) and evaluate_loading(unload, state, resident)
                assert not evaluate_loading(ready, state, resident) and not evaluate_loading(rearm, state, resident)
            negatives += 1
    assert negatives == 45
    for resident in (False, True):
        assert evaluate_loading(wait, facts, resident) == resident
        assert evaluate_loading(ready, facts, resident) == resident
        assert evaluate_loading(unload, facts, resident) != resident
        assert evaluate_loading(rearm, facts, resident)
    result = {
        'status': 'PASS_R7_OFFLINE_NOT_LIVE', 'archive_sha256': m['sha256'],
        'xl_sha256': m['xl_sha256'], 'probe_sha256': test_probe(facts),
        'unchanged_prior_resources': 18, 'changed_prior_resources': [PHASE],
        'new_resources': additions, 'native_nodes': 30, 'controller_only_change': 'Revision6->7',
        'negative_guards': negatives, 'loading_guard_cases': 92,
        'original_world_resources_changed': 0, 'original_lighting_changes': 0,
        'construction_mesh_instances': 18, 'truck_spawners': m['truck_spawners'],
        'story_writes': 0, 'scene_starts': 0, 'live_tested': False,
    }
    (BASE / 'details_r7_tests.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
