"""R2 packaged graph/source contract and lifecycle model, NOT an engine proof."""
import copy
import binascii
import itertools
import json
import re
from collections import defaultdict
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_access_r10 import read, sha
from test_afterlife_population import action

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/afterlife_world'
OUT = BASE / 'population_r2'


def graph(path):
    root = read(path)['Data']['RootChunk']
    hh = handles(root)
    return root, {i: canonical(n, hh) for i, n in nodes(root).items()}, quest_edges(root)[0]


class Model:
    """Native requests/condition scheduling only; no fake rendered-actor census."""
    def __init__(self, nn, edges, facts, loaded, inside, distance=100):
        self.nn = nn
        self.f = dict(facts)
        self.loaded = dict(loaded)
        self.inside = dict(inside)
        self.distance = distance
        self.pending = {0}
        self.edges = defaultdict(list)
        self.now = 0
        self.due = {}
        self.log = []
        self.active = set()  # Community-entry request state, NOT entities.
        for a, s, b, _ in edges:
            self.edges[a, s].append(b)

    def condition(self, c):
        kind = c['$type']
        if kind == 'questLogicalCondition':
            values = [self.condition(x) for x in c['conditions']]
            return all(values) if c['operation'] == 'AND' else any(values)
        if kind == 'questFactsDBCondition':
            p = c['type']; a = self.f.get(p['factName'], 0); b = p['value']
            return {'Equal': a == b, 'NotEqual': a != b,
                    'Greater': a > b, 'LessOrEqual': a <= b}[p['comparisonType']]
        if kind == 'questNodeLoadingCondition':
            value = self.loaded[c['objectRef']['$value']]
            return not value if c['inverted'] else value
        if kind == 'questTriggerCondition':
            assert c['isPlayerActivator'] == 1
            value = self.inside[c['triggerAreaRef']['$value']]
            assert c['type'] in ('IsInside', 'IsOutside')
            return value if c['type'] == 'IsInside' else not value
        if kind == 'questDistanceCondition':
            p = c['type']; b = p['distanceDefinition2']['distanceValue']
            assert b == 45
            return self.distance < b if p['comparisonType'] == 'Less' else self.distance >= b
        raise AssertionError(kind)

    def settle(self, before=None):
        for _ in range(1500):
            progress = False
            for i in sorted(self.pending):
                if i == before:
                    return
                n = self.nn[i]; kind = n['$type']; socket = 'Out'
                if kind == 'questPauseConditionNodeDefinition':
                    if n['condition']['$type'] == 'questTimeCondition':
                        seconds = n['condition']['type']['seconds']
                        self.due.setdefault(i, self.now + seconds)
                        if self.now < self.due[i]:
                            continue
                        del self.due[i]
                    elif not self.condition(n['condition']):
                        continue
                elif kind == 'questConditionNodeDefinition':
                    socket = 'True' if self.condition(n['condition']) else 'False'
                elif kind == 'questFactsDBManagerNodeDefinition':
                    p = n['type']; name = p['factName']
                    self.f[name] = p['value'] if p['setExactValue'] else self.f.get(name, 0) + p['value']
                elif kind == 'questSpawnManagerNodeDefinition':
                    for a in n['actions']:
                        a = action(a['type']); self.log.append((i, a))
                        key = a[:-1]
                        if a[-1] in ('Activate', 'Reactivate'):
                            self.active.add(key)
                        else:
                            assert a[-1] == 'Deactivate'; self.active.discard(key)
                else:
                    assert kind == 'questInputNodeDefinition', kind
                self.pending.remove(i)
                self.pending.update(self.edges[i, socket])
                progress = True
            if not progress:
                return
        raise AssertionError('Non-quiescent loop')

    def acquired(self):
        return [(i, a) for i, a in self.log if a[-1] in ('Activate', 'Reactivate')]


def main():
    m = read(OUT/'manifest.json'); r1 = read(BASE/'manifest.json')
    source = Path(m['source_root'])
    assert sha(Path(m['archive'])) == m['sha256']
    assert sha(Path(m['archive']+'.xl')) == m['xl_sha256']
    assert len(m['resources']) == 10 and m['packed_readback_pass']
    for p in m['payloads']:
        assert sha(source/p['depot']) == p['sha256']
    for p, h in m['source_hashes'].items():
        assert sha(ROOT/p) == h
    assert set(m['resources']) == set(r1['resources']) | {m['gate'], m['owner']}
    unchanged = [p for p in r1['payloads'] if p['depot'] != r1['population_phase']]
    assert len(unchanged) == 7
    assert all(sha(source/p['depot']) == p['sha256'] for p in unchanged)
    assert not any(p.startswith(('base\\', 'ep1\\')) for p in m['resources'])
    # Same registration-ID construction used by the project's reviewed native
    # owner builders. Old registrations remain byte-for-byte in the XL prefix.
    xl = Path(m['archive']+'.xl').read_text()
    oldxl = Path(r1['archive']+'.xl').read_text()
    assert xl.startswith(oldxl.rstrip()+'\n')
    registration_id = binascii.crc_hqx((m['gate']+':1').encode(), 65535)
    parent = read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')['Data']['RootChunk']
    assert registration_id not in nodes(parent)
    game = Path(read(BASE/'install_receipt.json')['game_root'])
    peer_registrations = []
    for config in (game/'archive/pc/mod').glob('*.archive.xl'):
        text = config.read_text(encoding='utf-8-sig')
        for match in re.finditer(r'- path: ([^\r\n]+)\s+parent: ep1\\quest\\ep1.quest\s+input:\s+node: \[1\]', text):
            depot = match[1].strip()
            peer_registrations.append(depot)
            assert depot != m['gate']
            assert binascii.crc_hqx((depot+':1').encode(),65535) != registration_id

    oldroot, old, oldedges = graph(BASE/'population_phase.json')
    newroot, new, newedges = graph(OUT/'legacy_population.json')
    assert oldedges == newedges and set(old) == set(new)
    expected = copy.deepcopy(old)
    legacy = [b for b in r1['population_branches'] if b['role'] == 'patron']
    for b in legacy:
        start = b['start']
        a = expected[start+2]['actions'][1]
        a['type']['action'] = 'Deactivate'
        expected[start+2]['actions'] = [a]
        expected[start+4]['type']['value'] = 0
    assert new == expected, 'Legacy delta escaped 26 retire actions/ready clears'
    assert newroot['phasePrefabs'] == oldroot['phasePrefabs'] == []
    # Every saved node position in each retired branch remains compatible and
    # cannot dispatch a positive spawn request, including the old acquire node.
    retired_positions = 0
    for b in legacy:
        for offset in range(9):
            pending = [b['start']+offset]; seen = set()
            while pending:
                i = pending.pop()
                if i in seen:
                    continue
                seen.add(i)
                for a in new[i].get('actions', []):
                    a = action(a['type'])
                    assert a[1] == '$/03_night_city/#PTFRAL1_Crowd' and a[-1] == 'Deactivate'
                pending.extend(e[2] for e in newedges if e[0] == i)
            assert seen == set(range(b['start'], b['start']+9))
            retired_positions += 1

    root, nn, edges = graph(OUT/'owner.json')
    gate, gn, ge = graph(OUT/'gate.json')
    assert not gate['phasePrefabs'] and len(gn) == 4
    assert root['phasePrefabs'] == [{'$type':'questQuestPrefabEntry', 'prefabNodeRef':{
        '$type':'NodeRef', '$storage':'string', '$value':m['controller_prefab']}}]
    assert len(nn) == m['owner_nodes'] and len(nn) == 244
    assert ge == {(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'False',1,'In'),(2,'True',3,'In1')}
    assert gn[1]['condition'] == gn[2]['condition']
    trigger_json = ROOT/'research/afterlife_world/population_r2_sources/json/base/worlds/03_night_city/_compiled/default/quest_01e5ca81919708f1.streamingsector.json'
    ts = read(trigger_json)['Data']['RootChunk']
    assert len(ts['nodes']) == 4
    assert all(n['Data']['$type']=='worldTriggerAreaNode' for n in ts['nodes'])
    assert all([x['Data']['$type'] for x in n['Data']['notifiers']] == ['questTriggerNotifier_Quest'] for n in ts['nodes'])
    writes = {v['factName'] for v in walk(root) if v.get('$type') == 'questSetVar_NodeType'}
    assert all(f.startswith('PTFRAL2_') for f in writes)
    assert not any(v.get('$type') in ('questSceneNodeDefinition','questTeleportPuppets_NodeType', 'questWorldDataManagerNodeDefinition') for v in walk(root))

    registry = {r['community_index']: r for r in read(BASE/'patron_vanilla_registry.json')}
    entries = m['entries']; slots = m['slots']
    assert len(entries) == 25 and len(slots) == 71
    background = [r for r in entries if r['community_id']=='16642022925330812742']
    extras = [r for r in entries if r['community_id']=='12548627742725757564']
    assert len(background) == 20 and sum(r['quantity'] for r in background) == 66
    assert {r['entry'] for r in extras} == {'cleaner','mercenary_big','valentino_01','valentino_02','valentino_03'}
    assert len({(s['community_id'],s['entry'],s['phase'],s['slot']) for s in slots}) == 71
    # Vanilla itself shares one workspot between two background entries. Keep
    # native reservation/budget arbitration; do not manufacture another spot.
    assert len({s['spot_id'] for s in slots}) == 70
    shared = [s for s in slots if sum(t['spot_id']==s['spot_id'] for t in slots)>1]
    assert {s['entry'] for s in shared} == {'crowd_female','mercenary_woman'}
    assert all(s['ref'].endswith('/#q005_ws_mercenary_female_outside') for s in shared)
    for r in entries:
        original = registry[1070 if r in background else 8665]
        e = next(e['data'] for e in original['entries'] if e['name'] == r['entry'])
        ph = next(p['Data'] for p in e['phases'] if p['Data']['phaseName']['$value']=='q005')
        assert len(ph['timePeriods'])==1 and ph['timePeriods'][0]['quantity']==r['quantity']
        assert len(r['refs'])==r['quantity'] and r['phase']=='q005'
        start = r['start']
        assert action(nn[start+2]['actions'][0]['type']) == ('community',r['spawner'],r['entry'],'q005','Activate')
        assert action(nn[start+6]['actions'][0]['type']) == ('community',r['spawner'],r['entry'],'q005','Deactivate')
        assert nn[start]['condition'] == nn[start+1]['condition']
    cached = {}
    for s in slots:
        path = ROOT/s['source'].replace('\\raw\\','\\json\\')
        path = Path(str(path)+'.json')
        if path not in cached:
            cached[path]=read(path)['Data']['RootChunk']
        w = cached[path]; d=w['nodeData']['Data'][s['source_placement']]
        assert d['NodeIndex']==s['source_node'] and d['QuestPrefabRefHash']['$value']==s['ref']
        assert s['source_placement'] < w['variantIndices'][1]
        assert w['nodes'][s['source_node']]['Data']['$type']=='worldAISpotNode'
    facts = m['guards'] | m['policy']
    all_refs = {v['objectRef']['$value'] for v in walk(root) if v.get('$type')=='questNodeLoadingCondition'}
    legacy_refs = {s for b in legacy for s in b['refs']}
    inside = {s: False for s in m['controller_triggers']}
    loaded = {s: s not in legacy_refs for s in all_refs}
    def fresh():
        return Model(nn,edges,facts,loaded,inside)
    def migrated():
        x=fresh(); x.settle(); assert x.f['PTFRAL2_Migration']==0
        x.now=1; x.settle(); assert x.f['PTFRAL2_Migration']==2
        assert not x.acquired(); return x
    def inside_bar(x):
        x.inside[m['controller_prefab']+'/#afterlife_tr_inside_area']=True
        x.distance=70  # Inside overrides distance from door, as authored.
    def outside_all(x):
        x.inside={s:False for s in x.inside}; x.distance=100
    def enter():
        x=migrated(); inside_bar(x); x.settle()
        assert len(x.acquired())==25 and len(x.active)==25
        return x

    negatives=0
    for f, value in m['guards'].items():
        for bad in (value-1, value+1):
            x=fresh(); x.f[f]=bad; inside_bar(x); x.settle(); x.now=10; x.settle()
            assert not x.log, (f,bad)
            gx=Model(gn,ge,x.f,loaded,inside)
            assert not gx.condition(gn[1]['condition'])
            negatives+=1
    for f,value in m['policy'].items():
        for bad in (value-1,value+1):
            x=migrated(); x.f[f]=bad; inside_bar(x); x.settle(); assert not x.acquired()
            negatives+=1
    # Crossing/stream barrier cannot be replaced by an active flag or empty IDs.
    for ref in legacy_refs:
        x=fresh(); x.loaded[ref]=True; x.settle(); x.now=20; x.settle()
        assert x.f['PTFRAL2_Migration']==0
    for ref in inside:
        if ref.endswith('fast_travel'):
            continue
        x=fresh(); x.inside[ref]=True; x.settle(); x.now=20; x.settle()
        assert x.f['PTFRAL2_Migration']==0
    for ref in inside:
        x=fresh(); x.loaded[ref]=False; x.settle(); x.now=20; x.settle()
        assert x.f['PTFRAL2_Migration']==0
    # Migration recheck catches re-stream/re-entry during its stabilization wait.
    x=fresh(); x.settle(); inside_bar(x); x.now=1; x.settle()
    assert x.f['PTFRAL2_Migration']==0

    combinations=0
    # Every occupancy combination and threshold boundary settles (no exit/entry
    # busy loop). A streamable door alone is never local occupancy.
    for flags in itertools.product((False,True),repeat=4):
        for distance in (0,44.99,45,45.01,100):
            x=migrated(); x.inside=dict(zip(inside,flags)); x.distance=distance
            entry=x.condition(nn[20]['condition']); exit_=x.condition(nn[24]['condition'])
            assert not (entry and exit_)
            x.settle(); assert bool(x.acquired())==entry
            combinations+=1
    cycles=0
    x=enter()
    for _ in range(10):
        before=len(x.acquired()); x.settle(); assert len(x.acquired())==before
        # Native save/restore model carries pending tokens, fact state and request
        # identity, not a second initialization/Reactivate of every entry.
        x=copy.deepcopy(x); x.settle(); assert len(x.acquired())==before
        outside_all(x); x.settle(); assert not x.active
        inside_bar(x); x.settle(); assert len(x.active)==25
        cycles+=1
    stream_cases=0
    for ref in {r for e in entries for r in e['refs']} | set(inside) | {m['door']}:
        x=enter(); x.loaded[ref]=False; x.settle()
        affected={('community',e['spawner'],e['entry'],'q005') for e in entries if ref in e['refs']}
        if ref in inside or ref==m['door']:
            assert not x.active
        else:
            assert len(x.active)==25-len(affected) and not (x.active & affected)
        x.loaded[ref]=True; x.settle(); assert len(x.active)==25
        stream_cases+=1
    for f,value in facts.items():
        x=enter(); x.f[f]=value+1; x.settle(); assert not x.active
        x.f[f]=value; x.settle(); assert len(x.active)==25
    # Per-entry wait -> recheck race; fail every constituent workspot independently.
    races=0
    for e in entries:
        for ref in e['refs']:
            x=migrated(); inside_bar(x); x.settle(before=e['start']+1)
            assert e['start']+1 in x.pending
            x.loaded[ref]=False; x.settle()
            assert not any(a[2]==e['entry'] and a[1]==e['spawner'] for _,a in x.acquired())
            races+=1
    # Simulated surviving originals are the same keys; activation does not create
    # a private second cohort. This tests action identity, not engine realization.
    x=migrated(); original_keys={('community',e['spawner'],e['entry'],'q005') for e in entries}
    x.active=original_keys.copy(); inside_bar(x); x.settle(); assert x.active==original_keys
    x=enter(); x.inside[m['controller_prefab']+'/#afterlife_tr_fast_travel']=True; x.settle()
    assert not x.active
    result={
        'status':'PASS_R2_OFFLINE_NOT_INSTALLED_NOT_LIVE',
        'archive_sha256':m['sha256'],'xl_sha256':m['xl_sha256'],
        'manifest_sha256':sha(OUT/'manifest.json'),
        'builder_sha256':sha(ROOT/'tools/build_afterlife_population_r2.ps1'),
        'validator_sha256':sha(Path(__file__)),
        'unchanged_r1_payloads':7,'legacy_saved_positions_retire_only':retired_positions,
        'new_registration_id':registration_id,'peer_ep1_root_registrations_checked':len(peer_registrations),
        'owner_nodes':len(nn),'gate_nodes':len(gn),'configured_original_slots':71,
        'distinct_original_workspots':70,'vanilla_shared_workspot_entries':['crowd_female','mercenary_woman'],
        'negative_guard_policy_cases':negatives,'occupancy_threshold_cases':combinations,
        'stream_loss_return_cases':stream_cases,'entry_recheck_races':races,
        'modeled_save_reload_leave_return_cycles':cycles,'new_actor_identities':0,
        'source_appearance_budget_changes':0,'forced_story_writes':0,
        'limitations':['No engine execution or rendered population census.',
                      'Streaming barrier is not an actor-removal acknowledgement.',
                      'ArchiveXL adoption of saved R1 tokens and native prefab reacquisition need live validation.',
                      'Unsupported early/q103-active states fail closed; no mission restoration.']}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
