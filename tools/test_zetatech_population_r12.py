"""Source/graph/runtime/packed-readback checks, not a live animation claim."""
import copy
import hashlib
import itertools
import json
import re
import subprocess
import zlib
from pathlib import Path

from audit_world_interactions import walk
from test_misty_viktor_access_r11 import NativeDispatchModel, graph, reachable
from test_radio_memorial import handles

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'research/misty_viktor_world'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def normalize(obj):
    if isinstance(obj, list):
        return [normalize(v) for v in obj]
    if not isinstance(obj, dict):
        return obj
    obj = {k: normalize(v) for k, v in obj.items() if k != 'HandleId'}
    if obj.get('$type') == 'TweakDBID':
        value = str(obj['$value'])
        if not value.isdigit():
            value = str((len(value.encode()) << 32) | zlib.crc32(value.encode()))
        obj['$value'], obj['$storage'] = value, 'uint64'
    return obj


def inflate(obj, table):
    if isinstance(obj, list):
        return [inflate(x, table) for x in obj]
    if not isinstance(obj, dict):
        return obj
    if 'HandleRefId' in obj:
        if str(obj['HandleRefId']) == '-1':
            return None
        return {'Data': inflate(table[str(obj['HandleRefId'])], table)}
    return {k: inflate(v, table) for k, v in obj.items() if k != 'HandleId'}


def main():
    m = read(AUDIT / 'population_r12_manifest.json')
    w = read(AUDIT / 'population_r12_world_manifest.json')
    assert sha(m['archive']) == m['sha256']
    assert sha(m['archive'] + '.xl') == m['xl_sha256']
    root, ns, edges = graph(AUDIT / 'r12_population_phase.json')
    assert len(ns) == 212 and reachable(edges) == set(ns)
    assert {tuple(e[:3]) for e in edges} == {tuple(e) for e in m['edges']}
    refs = {r for b in m['branches'] for r in b['refs']} | {w['terry_spot']['ref']}
    ready = dict.fromkeys(refs, True)
    expected = {x['entry'] for x in w['entries']}
    assert len(expected) == 29
    assert not expected.intersection({f'q307_alley_extra_{n}' for n in range(12, 16)})
    assert {x['entry'] for x in w['entries'] if x['role'] == 'street'} == (
        {f'q307_alley_extra_{n:02}' for n in range(2, 32) if n not in range(12, 16)} | {'q307_alley_extra_04b'})
    facts = m['guards']

    def simulate(facts=facts, loaded=ready):
        s = NativeDispatchModel(ns, edges, facts, loaded)
        s.settle()
        return s

    s = simulate()
    assert {a[2] for a in s.actions if a[3] == 'Reactivate'} == expected
    assert {a[2] for a in s.actions if a[3] == 'Deactivate'} == {'q307_alley_extra_01', 'q307_zetatech_clerk'}
    assert s.facts['PTFRMV12_TerrySpotReady'] == 1
    negative = 0
    for name, value in facts.items():
        for invalid in {-1, 0, 1, 2} - {value}:
            bad = dict(facts, **{name: invalid})
            assert not simulate(bad).actions
            release = simulate()
            release.actions.clear()
            release.facts[name] = invalid
            release.settle()
            assert len(release.actions) == 29 and all(a[3] == 'Deactivate' for a in release.actions)
            assert release.facts['PTFRMV12_TerrySpotReady'] == 0
            release.facts[name] = value
            release.actions.clear()
            release.settle()
            assert sum(a[3] == 'Reactivate' for a in release.actions) == 29
            negative += 1
    for ref in refs:
        missing = dict(ready, **{ref: False})
        expected_blocked = {b['entry'] for b in m['branches'] if ref in b['refs']}
        assert {a[2] for a in simulate(loaded=missing).actions if a[3] == 'Reactivate'} == expected - expected_blocked
        cycle = simulate()
        cycle.actions.clear()
        cycle.loaded[ref] = False
        cycle.settle()
        assert {a[2] for a in cycle.actions} == expected_blocked
        assert all(a[3] == 'Deactivate' for a in cycle.actions)
        cycle.actions.clear()
        cycle.loaded[ref] = True
        cycle.settle()
        assert {a[2] for a in cycle.actions if a[3] == 'Reactivate'} == expected_blocked
    assert not simulate(loaded=dict.fromkeys(refs, False)).actions
    race_cases = 0
    for b in m['branches']:
        s = NativeDispatchModel(ns, edges, facts, ready)
        s.settle(before=b['start'] + 1)
        s.loaded[b['refs'][0]] = False
        s.settle()
        assert not any(a[2] == b['entry'] for a in s.actions)
        race_cases += 1
    for obj in walk(root):
        if obj.get('$type') == 'questSetVar_NodeType':
            assert obj['factName'].startswith('PTFRMV12_')
        assert obj.get('$type') not in {'questSceneNodeDefinition', 'questInteractiveObjectManagerNodeDefinition'}
        if obj.get('$type') == 'questCommunityTemplate_NodeType':
            assert obj['communityEntryName']['$value'] in expected
            if obj['spawnerReference']['$value'] != w['spawner']:
                assert obj['action'] == 'Deactivate'
                assert obj['communityEntryName']['$value'] in {'q307_alley_extra_01', 'q307_zetatech_clerk'}

    registry = read(AUDIT / 'r12_registry.streamingsector.json')['Data']['RootChunk']
    registry = inflate(registry, handles(registry))
    spots = read(AUDIT / 'r12_spots.streamingsector.json')['Data']['RootChunk']
    spots = inflate(spots, handles(spots))
    original = read(AUDIT / 'r6_wall_nav_sources/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/ep1/quest_bb3937b6e34a251c.streamingsector.json')['Data']['RootChunk']
    original = inflate(original, handles(original))
    reg = registry['nodes'][0]['Data']
    template = reg['communitiesData'][0]['template']['Data']
    compiled = registry['nodes'][1]['Data']['area']['Data']['entriesData']
    assert len(registry['nodes']) == 2 and len(spots['nodes']) == 31
    assert len(reg['communitiesData']) == 1 and len(reg['workspotsPersistentData']) == 30
    assert len(template['entries']) == len(compiled) == 29
    assert not template['crowdEntries']
    assert not any(x['entryActiveOnStart'] for x in reg['communitiesData'][0]['entriesInitialState'])
    communities = {}
    for kind in ['alley', 'main']:
        source = read(AUDIT / f'street_npc_sources/json/ep1/quest/main_quests/q307/communities/q307_com_{kind}.community.json')['Data']['RootChunk']
        source = inflate(source, handles(source))['communityTemplate']['Data']
        communities.update({e['Data']['entryName']['$value']: e['Data'] for e in source['entries']})
    replacements = {'q307_alley_extra_03': 40, 'q307_alley_extra_07': 20, 'q307_alley_extra_11': 40, 'q307_alley_extra_20': 2, 'q307_alley_extra_28': 44}
    for i, row in enumerate(w['entries']):
        actual = template['entries'][i]['Data']
        expect = copy.deepcopy(communities[row['entry']])
        expect['phases'] = [p for p in expect['phases'] if p is not None and p['Data']['phaseName']['$value'] == row['phase']]
        assert len(expect['phases']) == 1
        ref = expect['phases'][0]['Data']['timePeriods'][0]['spotNodeRefs'][0]
        ref['$value'], ref['$storage'] = row['spot']['ref'], 'string'
        assert normalize(actual) == normalize(expect), ('community delta', row['entry'])
        cp = compiled[i]
        assert cp['entryName']['$value'] == row['entry']
        assert len(cp['phasesData']) == 1 and cp['phasesData'][0]['entryPhaseName']['$value'] == row['phase']
        assert cp['phasesData'][0]['timePeriodsData'][0]['spotNodeIds'][0]['hash'] == str(row['spot']['hash'])
        assert reg['workspotsPersistentData'][i]['globalNodeId']['hash'] == str(row['spot']['hash'])
    for i, row in enumerate([x['spot'] for x in w['entries']] + [w['terry_spot']]):
        actual = spots['nodes'][i]['Data']
        expect = copy.deepcopy(original['nodes'][row['index']]['Data'])
        if i < 29 and w['entries'][i]['entry'] in replacements:
            expect['spot'] = copy.deepcopy(original['nodes'][replacements[w['entries'][i]['entry']]]['Data']['spot'])
        for key in ['debugName', 'sourcePrefabHash']:
            expect[key] = actual[key]
        expect['isWorkspotInfinite'] = 1
        assert normalize(actual) == normalize(expect), ('workspot delta', i)
        datum = spots['nodeData']['Data'][i]
        source_datum = next(x for x in original['nodeData']['Data'] if x['NodeIndex'] == row['index'])
        for field in ['Position', 'Orientation', 'Scale', 'Pivot', 'MaxStreamingDistance']:
            if field in source_datum:
                assert datum[field] == source_datum[field], (field, i)
        assert datum['QuestPrefabRefHash']['$value'] == row['ref']
        assert datum['NodeIndex'] == i
    chair = spots['nodes'][30]['Data']
    chair_source = copy.deepcopy(original['nodes'][203]['Data'])
    for key in ['debugName', 'sourcePrefabHash']:
        chair_source[key] = chair[key]
    assert normalize(chair) == normalize(chair_source)
    original_chair = next(x for x in original['nodeData']['Data'] if x['NodeIndex'] == 203)
    assert spots['nodeData']['Data'][30]['Position'] == original_chair['Position']
    block = read(AUDIT / 'r12_population.streamingblock.json')['Data']['RootChunk']
    assert len(block['descriptors']) == 2
    assert block['descriptors'][0]['category'] == 'AlwaysLoaded'
    assert not block['descriptors'][0]['variants']
    assert block['descriptors'][1]['variants'][0]['enabledByDefault'] == 0
    assert block['descriptors'][1]['variants'][0]['name']['$value'] == 'PTFRMV_ZetatechShell'

    driver = ROOT / 'redscript/PTFR_Zetatech_Idles_R12/TerryIdleR12.reds'
    text = driver.read_text()
    for name, value in facts.items():
        assert f'q.GetFact(n"{name}") == {value}' in text
    for required in ['NPCPuppet.IsInCombat(npc)', 'npc.IsDead()', 'scene.IsEntityInScene', 'this.requests >= 3', 'command.continueInCombat = false', 'ai.CancelCommand(this.command)', 'system.IsManaged(ids[0])', 'system.IsTagged(ids[0], n"PTFRMV11_Terry")', 'npc.GetRecordID() != t"Character.PTFRMV_Terry"']:
        assert required in text
    assert not re.search(r'CreateEntity|DeleteEntity|Teleport|SetGodMode|ForceKill|SaveGame|LoadGame', text)
    assert all(x.startswith('PTFRMV12_') for x in re.findall(r'this.Count\(n"([^"]+)"', text))
    lint = subprocess.run([str(ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'), 'lint', '-s', str(driver), '-b', str(GAME / 'r6/cache/final.redscripts.modded')], capture_output=True, text=True)
    output = lint.stdout + lint.stderr
    assert 'Lint successful' in output and 'ERROR' not in output, output
    (ROOT / 'build/ZetatechPopulationR12/redscript_lint.log').write_text(output)

    # Re-read binary archive resources, verifying the exported trees used above.
    code = r'''
    . ./tools/build_phase2a.ps1 -HelpersOnly
    $m=Get-Content research/misty_viktor_world/population_r12_manifest.json -Raw|ConvertFrom-Json
    $hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
    if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($m.archive,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Archive read error'}
    if($ar.Files.Count -ne 4){throw 'Extra payload'}
    foreach($entry in $ar.Files.Values){
      $ms=[IO.MemoryStream]::new();$entry.Extract($ms)
      $src=Join-Path 'build/ZetatechPopulationR12/source' $entry.Name
      $digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))
      if($digest -ne (Get-FileHash $src).Hash){throw 'Packed bytes differ'}
      $ms.Position=0;$r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($ms);$f=$null
      $r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
      if($r.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw 'Payload decode error'}
      $dto=[WolvenKit.Common.Conversion.RedFileDto]::new($f,$false)
      $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($dto,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
      [pscustomobject]@{name=[IO.Path]::GetFileName($entry.Name);data=($json|ConvertFrom-Json -Depth 100).Data}|ConvertTo-Json -Depth 100 -Compress
      $ms.Dispose()
    }
    '''
    result = subprocess.run(['pwsh', '-NoProfile', '-Command', code], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for line in result.stdout.splitlines():
        row = json.loads(line)
        name = 'r12_population_phase.json' if row['name'] == 'population.questphase' else 'r12_' + row['name'] + '.json'
        assert normalize(row['data']) == normalize(read(AUDIT / name)['Data']), ('stale export', name)
    # User-passed R11 archive/XL and Terry lifecycle/tweak must remain byte-exact.
    installed = read(AUDIT / 'access_r11_install_receipt.json')
    protected = 0
    for payload in installed['files']:
        if payload['relative'].endswith('PTFR_Zetatech_Access_Audit\\init.lua'):
            assert sha(GAME / payload['relative']) in {payload['sha256'], sha(ROOT / 'diagnostics/PTFR_Zetatech_Access_Audit/init.lua')}
        else:
            assert sha(GAME / payload['relative']) == payload['sha256']
            protected += 1
    report = dict(status='PASS_R12_OFFLINE_NOT_LIVE', archive_sha256=m['sha256'], xl_sha256=m['xl_sha256'],
                  driver_sha256=sha(driver), diagnostic_sha256=sha(ROOT / 'diagnostics/PTFR_Zetatech_Access_Audit/init.lua'),
                  native_nodes=len(ns), negative_guards_and_rearms=negative, single_node_unload_reload_cases=len(refs),
                  wait_check_races=race_cases, additional_street_npcs=27, private_indoor_entries=2,
                  exact_source_workspots=25, documented_animation_substitutions=5, exact_wheelchair=1,
                  initially_active_entries=0, packed_payloads=4, redscript_lint=True, protected_r11_files=protected,
                  story_writes=0, scene_starts=0, live_tested=False)
    (AUDIT / 'population_r12_tests.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
