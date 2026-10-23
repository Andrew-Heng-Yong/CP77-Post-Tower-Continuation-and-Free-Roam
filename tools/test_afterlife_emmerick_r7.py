"""Exact two-payload delta, authored workspot compatibility and installed baseline."""
import copy
import json
from pathlib import Path
from test_afterlife_booth_r6 import clean, sha, read, walk, differences
from test_radio_memorial import canonical, handles

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/afterlife_world'
OUT = BASE / 'emmerick_r7'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')

def main():
    m = read(OUT/'manifest.json')
    r2 = read(BASE/'population_r2/manifest.json')
    assert m['packed_readback'] and m['resources'] == r2['resources'] and sha(m['archive']) == m['sha256']
    for p, h in m['source_hashes'].items():
        assert sha(p) == h, p
    changed = [r for r in m['resources'] if sha(Path(m['source_root'])/r) != sha(Path(r2['source_root'])/r)]
    assert set(changed) == set(m['changed_payloads']) and len(changed) == 2
    before = clean(BASE/'patrons_spots.streamingsector.json')
    after = clean(OUT/'patrons_spots.streamingsector.json')
    vanilla = clean(OUT/'vanilla_entrance.streamingsector.json')
    vn = copy.deepcopy(vanilla['nodes'][97])
    vn['debugName'] = before['nodes'][78]['debugName']
    vn['sourcePrefabHash'] = before['nodes'][78]['sourcePrefabHash']
    before['nodes'][78] = vn
    vd = next(d for d in vanilla['nodeData']['Data'] if d['NodeIndex'] == 97)
    target = next(d for d in before['nodeData']['Data'] if d['NodeIndex'] == 78)
    for k in ('Position', 'Orientation', 'Scale', 'Bounds'):
        target[k] = copy.deepcopy(vd[k])
    assert before == after, differences(before, after)[:10]
    assert vn['isWorkspotInfinite'] == 1 and vn['isWorkspotStatic'] == 0
    assert vn['spot']['masterNodeRef']['$value'] == vn['lookAtTarget']['$value'] == '0'
    assert vn['spot']['resource']['DepotPath']['$value'] == m['animation']
    observed = [-1457.196, 1026.172, 16.793]
    assert all(abs(vd['Position'][k] - n) < .001 for k, n in zip(('X', 'Y', 'Z'), observed))

    before = clean(BASE/'patrons_registry.streamingsector.json')
    after = clean(OUT/'patrons_registry.streamingsector.json')
    pd = read(OUT/'vanilla_persistent.json')
    matches = [p for p in before['nodes'][0]['workspotsPersistentData'] if p['globalNodeId']['hash'] == '10404772310209767793']
    assert len(matches) == 1
    matches[0]['worldPosition'] = pd['worldPosition']
    matches[0]['yaw'] = pd['yaw']
    target = next(d for d in before['nodeData']['Data'] if d['NodeIndex'] == 2)
    for k in ('Position', 'Orientation', 'Scale', 'Bounds'):
        target[k] = copy.deepcopy(vd[k])
    assert before == after, differences(before, after)[:10]
    assert len(after['nodes'][0]['communitiesData']) == 2
    # No saved phase, entry, actor, appearance, alias or graph identity changes.
    source_registry = read(BASE/'baseline_r7/emmerick_vanilla.json')[0]['community']
    phases = next(n for n in walk(source_registry) if n.get('$type') == 'communitySpawnEntry')['phases']
    q005, q103 = [canonical(p, handles(source_registry)) for p in phases[:2]]
    for phase in (q005, q103):
        phase.pop('phaseName')
        for period in phase['timePeriods']:
            assert period['quantity'] == 1
            period.pop('spotNodeRefs')
    assert q005 == q103, 'Non-spot phase rules differ'
    workspot = clean(BASE/'baseline_r7/source/json'/(m['animation']+'.json'))
    idle = next(n for n in walk(workspot) if n.get('$type') == 'workSequence' and n['id']['id'] == 2)
    assert idle['loopInfinitely'] == 1
    random_lists = [n for n in walk(idle) if n.get('$type') == 'workRandomList']
    assert len(random_lists) == 1 and random_lists[0]['dontRepeatLastAnims'] == 4
    assert len(random_lists[0]['weights']) == len(random_lists[0]['list']) == 12
    assert abs(sum(random_lists[0]['weights']) - 1) < 1e-5
    assert random_lists[0]['minClips'] == 3 and random_lists[0]['maxClips'] == 5
    # Old single-pose resource lacks this random gesture list.
    old = clean(BASE/'baseline_r7/source/json/base/workspots/common/ground/bodyguard__stand_ground__2h_front__01.workspot.json')
    assert not any(n.get('$type') == 'workRandomList' for n in walk(old))

    expected = {}
    for p in ('install_receipt.json', 'population_r2/install_receipt.json', 'idles_r3/install_receipt.json', 'faces_r5/install_receipt.json', 'booth_r6/install_receipt.json'):
        for f in read(BASE/p)['files']:
            expected[f['relative'].replace('\\', '/')] = f['sha256']
    for p, h in expected.items():
        assert sha(GAME/p) == h, p
    relative = 'archive/pc/mod/TowerContinued_AfterlifeR1.archive'
    report = {'status': 'PASS_R7_OFFLINE_NOT_INSTALLED_NOT_LIVE', 'packed_readback': True,
              'exact_changed_payloads': changed, 'unchanged_r2_payloads': 8, 'private_workspots_changed': 1,
              'vanilla_gesture_weight_count': 12, 'vanilla_recent_clip_exclusion': 4,
              'preserved_community_phase_identity': True, 'preserved_population_and_appearance': True,
              'protected_afterlife_files': len(expected), 'manifest_sha256': sha(OUT/'manifest.json'),
              'builder_sha256': sha(ROOT/'tools/build_afterlife_emmerick_r7.ps1'), 'validator_sha256': sha(__file__),
              'files': [{'relative': relative, 'source': str(Path(m['archive']).relative_to(ROOT)), 'sha256': m['sha256'], 'before_sha256': expected[relative]}],
              'game_writes': 0, 'live_tested': False,
              'limitations': ['Rendered animation/placement and streamed return/reload require live test', 'Same private identity may retain serialized AI state until fresh streaming', 'No dialogue or Rogue eye-glow repair in this bounded patch']}
    (OUT/'tests.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
