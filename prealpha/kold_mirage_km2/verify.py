"""Independently constrain cooked KM2 changes and exercise their interaction order."""
from pathlib import Path
from collections import Counter, defaultdict, deque
import copy
import json
import sys
from prepare import HERE, WS, PREDECESSOR, BASE, OUT, INSTALLED, ARCHIVE, FREEZER, AFTERLIFE, PHASE, read, sha, write
sys.path.insert(0, str(WS/'tools/parity_audit'))
from model import Resource, compare_graph
from common import walk


def normal(path):
    result = Resource(read(path)).normalize()
    assert not result['errors'], result['errors']
    return result


class Flow:
    """Bounded signal model of the actual cooked scene, not an engine simulator.

    Manual choices, scan/focus waits and leaving the trigger stay explicit.
    Timed V barks are recorded without supplying any progression signal.
    """
    def __init__(self, model, recognized=0, restored_open=False):
        self.g = model['graphs']['scene']
        self.choices, self.waits, self.xors, self.and_inputs = set(), set(), set(), defaultdict(set)
        self.facts = {'mq016_recognized_bartmoss': recognized, 'mq016_cryofreezer_opened': 0}
        self.journals, self.visited, self.barks = {}, [], []
        self.grants, self.openings, self.closings = 0, 0, 0
        self.queue = deque([('331' if restored_open else '1', '0:0')])
        self.drain()

    def outputs(self, node, stamp='0:0'):
        self.queue.extend((b, inp) for a, out, b, inp in self.g['edges'] if a == node and out == stamp)

    def choose(self, node):
        if node not in self.choices:
            return False
        self.choices.remove(node)
        self.outputs(node)
        self.drain()
        return True

    def signal_wait(self, node):
        if node not in self.waits:
            return False
        self.waits.remove(node)
        self.outputs(node)
        self.drain()
        return True

    def drain(self):
        count = 0
        while self.queue:
            count += 1
            assert count < 500, 'Unexpected signal loop'
            node, inp = self.queue.popleft()
            n = self.g['nodes'][node]['payload']
            kind = n['$type']
            self.visited.append((node, inp))
            if kind == 'scnChoiceNode':
                self.choices.add(node)
            elif kind == 'scnSectionNode':
                assert not any(e['$type'] != 'scnDialogLineEvent' for e in n['events'])
                self.barks.append(node)
                assert not [e for e in self.g['edges'] if e[0] == node], 'Bark unexpectedly gates progress'
            elif kind == 'scnXorNode':
                if node not in self.xors:
                    self.xors.add(node)
                    self.outputs(node)
            elif kind == 'scnAndNode':
                self.and_inputs[node].add(inp)
                if len(self.and_inputs[node]) == n['numInSockets']:
                    self.outputs(node)
            elif kind in ['scnStartNode', 'scnDeletionMarkerNode', 'scnInterruptManagerNode']:
                self.outputs(node, '666:0' if kind == 'scnDeletionMarkerNode' else '0:0')
            elif kind == 'scnEndNode':
                pass
            else:
                assert kind == 'scnQuestNode', kind
                q = n['questNode']
                qt = q['$type']
                if qt == 'questPauseConditionNodeDefinition':
                    assert node in ['68', '581', '404'], node
                    self.waits.add(node)
                    continue
                if qt == 'questConditionNodeDefinition':
                    assert node == '542'
                    predicate = q['condition']['type']
                    assert predicate['factName'] == 'mq016_recognized_bartmoss' and predicate['comparisonType'] == 'GreaterOrEqual'
                    self.outputs(node, '0:0' if self.facts['mq016_recognized_bartmoss'] >= predicate['value'] else '0:1')
                    continue
                if qt == 'questJournalNodeDefinition':
                    slot = int(inp.split(':')[1])
                    state = n['isockMappings'][slot]['$value']
                    self.journals[q['type']['path']['realPath']] = state
                if qt == 'questFactsDBManagerNodeDefinition':
                    t = q['type']
                    assert t['setExactValue'] == 1
                    self.facts[t['factName']] = t['value']
                if qt == 'questItemManagerNodeDefinition':
                    p, = q['type']['params']
                    assert p['nodeType'] == 'AddItem' and p['itemID']['$value'] == 'Items.mq016_bartmoss_cyberdeck_encrypted' and p['quantity'] == 1
                    self.grants += 1
                if qt == 'questTransformAnimatorNodeDefinition':
                    if q['action']['reverse']:
                        self.closings += 1
                    else:
                        self.openings += 1
                self.outputs(node)


def main():
    output = HERE/'verification.json'
    assert not output.exists()
    plan_path, cooked_path = HERE/'input_02/plan.json', HERE/'readback_01/manifest.json'
    plan, cooked = read(plan_path), read(cooked_path)
    assert cooked['plan_sha256'] == sha(plan_path)
    checks, groups = [], Counter()
    def check(group, name, passed):
        assert passed, (group, name)
        checks.append({'group': group, 'name': name, 'pass': True})
        groups[group] += 1
    rows = {r['depot']: r for r in cooked['resources']}
    models, diffs = {}, {}
    for edit in plan['edits']:
        depot, rb = edit['depot'], rows[edit['depot']]
        check('pins', depot, sha(edit['source']['json']) == edit['source']['json_sha256'] and sha(edit['edited_json']) == edit['edited_json_sha256'] and sha(rb['raw']) == rb['sha256'] and sha(rb['json']) == rb['json_sha256'])
        old, new = normal(edit['source']['json']), normal(rb['json'])
        models[depot] = new
        diffs[depot] = compare_graph(old, new)
        check('identity', depot+' graph inventory', set(old['graphs']) == set(new['graphs']))
        if depot == PHASE:
            expected = copy.deepcopy(old['graphs']['root']['nodes']['4']['payload'])
            expected['interruptionOperations'][0]['enable'] = 0
            expected['reapplyInterruptionOperationsAfterGameLoad'] = 1
            check('phase', 'Only scoped interruption behavior changes', len(diffs[depot]) == 1 and diffs[depot][0]['node'] == '4' and new['graphs']['root']['nodes']['4']['payload'] == expected)
            continue
        actor = 0 if depot == FREEZER else 1
        performer = (actor << 8) | 1
        expected_meta = copy.deepcopy(old['metadata'])
        target, = [a for a in expected_meta['actors'] if a['actorId']['id'] == actor]
        for flag in ['isEnabled', 'alwaysSpawned', 'spawnOnStart']:
            target['spawnDespawnParams'][flag] = 0
        if depot == FREEZER:
            expected_meta['interruptionScenarios'][0]['enabled'] = 0
        check('identity', depot+' exact root metadata', new['metadata'] == expected_meta and old['embedded_files'] == new['embedded_files'])
        before, after = old['graphs']['scene'], new['graphs']['scene']
        check('identity', depot+' all saved node and entry IDs', set(before['nodes']) == set(after['nodes']) and before['entries'] == after['entries'])
        changes = edit['changes']
        removed = {r['id'] for r in changes['removed_events']}
        rewires = {(r['node'], tuple(r['output_stamp'])): r for r in changes['rewires']}
        durations = {r['node']: r for r in changes['duration_changes']}
        for nid, prior in before['nodes'].items():
            actual = after['nodes'][nid]['payload']
            expected = copy.deepcopy(prior['payload'])
            if 'actorBehaviors' in expected:
                expected['actorBehaviors'] = [a for a in expected['actorBehaviors'] if a['actorId']['id'] != actor]
            if 'events' in expected:
                for event in expected['events']:
                    if str(event['id']['id']) not in removed:
                        continue
                    refs = [r for r in walk(event) if (r.get('$type') == 'scnActorId' and r.get('id') == actor) or (r.get('$type') == 'scnPerformerId' and r.get('id') == performer)]
                    check('events', depot+'/'+str(event['id']['id'])+' presentation removal only', bool(refs) or (depot == FREEZER and nid == '28' and event['$type'] == 'scneventsSocket'))
                expected['events'] = [e for e in expected['events'] if str(e['id']['id']) not in removed]
            if nid in durations:
                expected['sectionDuration']['stu'] = durations[nid]['after']
                check('timing', depot+'/'+nid+' ends at retained speech', durations[nid]['after'] == max(e['startTime']+e['duration'] for e in expected['events']))
            for socket in expected.get('outputSockets', []):
                key = (nid, (socket['stamp']['name'], socket['stamp']['ordinal']))
                if key in rewires:
                    check('edges', depot+'/'+str(key)+' exact old destinations', socket['destinations'] == rewires[key]['before'])
                    socket['destinations'] = rewires[key]['after']
            check('delta', depot+'/'+nid+' complete payload', actual == expected)
        # Every retained spoken event is byte-equivalent at normalized field level.
        def spoken(graph):
            return {str(e['id']['id']): e for n in graph['nodes'].values() for e in n['payload'].get('events', []) if e['$type'] == 'scnDialogLineEvent'}
        check('speech', depot+' all prior kept speech unchanged', spoken(before) == spoken(after))
        for nid in after['reachable']:
            p = after['nodes'][nid]['payload']
            q = p.get('questNode')
            check('actor', depot+'/'+nid+' no reachable Johnny command or objective', not q or 'johnny' not in json.dumps(q).lower())
            for event in p.get('events', []):
                check('actor', depot+'/'+str(event['id']['id'])+' no Johnny performer', not any((r.get('$type') == 'scnActorId' and r.get('id') == actor) or (r.get('$type') == 'scnPerformerId' and r.get('id') == performer) for r in walk(event)))
        if depot == FREEZER:
            check('flow', 'Only first Open and native Take choices reachable', {i for i in after['reachable'] if after['nodes'][i]['type'] == 'scnChoiceNode'} == {'331', '470'})
            for nid in ['68', '581', '174', '490', '470', '331', '453', '657']:
                old_payload, new_payload = before['nodes'][nid]['payload'], after['nodes'][nid]['payload']
                check('native', nid+' logic unchanged outside reviewed destination wiring', {k:v for k,v in old_payload.items() if k != 'outputSockets'} == {k:v for k,v in new_payload.items() if k != 'outputSockets'})
        else:
            # Nix's entire crisis section and original callback time remain;
            # only Johnny's optional workspot branch and body animation disappear.
            check('native', 'Nix crisis timing and native rescue input callback retained', before['nodes']['64']['payload']['sectionDuration'] == after['nodes']['64']['payload']['sectionDuration'] and any(e['$type'] == 'scneventsSocket' and e['startTime'] == 32009 and e['osockStamp']['name'] == 2 for e in after['nodes']['64']['payload']['events']))
    simulations = []
    for restored in [False, True]:
        for recognized in [0, 1]:
            for scan in ['68', '581']:
                flow = Flow(models[FREEZER], recognized, restored)
                check('fixture', 'Pre-Open has no Take/grant', flow.choices == {'331'} and flow.grants == 0 and not flow.signal_wait(scan))
                check('fixture', 'Open chosen', flow.choose('331'))
                check('fixture', 'Scan armed without waiting for V bark', {'68','581'} <= flow.waits and '470' not in flow.choices and flow.facts['mq016_cryofreezer_opened'] == 1)
                check('fixture', 'Scan/focus signal reaches Take', flow.signal_wait(scan) and '470' in flow.choices and flow.grants == 0)
                check('fixture', 'Retained box observation respects recognition history', ('101' in flow.barks) == (recognized == 0))
                check('fixture', 'Native Take gives one encrypted deck', flow.choose('470') and flow.grants == 1)
                flow.signal_wait('581' if scan == '68' else '68')
                check('fixture', 'Repeated scan/Take does not expose another grant', not flow.choose('470') and flow.grants == 1)
                check('fixture', 'Open once and close automatically after pickup', flow.openings == 1 and flow.closings == 1 and flow.facts['mq016_cryofreezer_opened'] == 0)
                check('fixture', 'No Johnny journal activation', not any('johnny' in p for p in flow.journals))
                check('fixture', 'Native Nix objective after pickup', flow.journals.get('quests/minor_quest/mq016_bartmoss/02_afterlife/01_talk_with_nix') == 'Active')
                check('fixture', 'Leave reaches both native exits', flow.signal_wait('404') and {'2','426'} <= {n for n,_ in flow.visited})
                simulations.append({'restored_at_open_choice': restored, 'recognized_bartmoss': recognized, 'native_scan_source': scan, 'grants': flow.grants, 'openings': flow.openings, 'closings': flow.closings, 'journals': flow.journals, 'visited': flow.visited})
    baseline = read(BASE/'package_manifest.json')
    members = {str(p.relative_to(OUT/'archive_source')).replace('/', '\\'): sha(p) for p in (OUT/'archive_source').rglob('*') if p.is_file()}
    changed = sorted(d for d,h in members.items() if h != baseline['source_resources'][d])
    check('inventory', 'Same1581 depots, only three approved resources changed', len(members) == 1581 and set(members) == set(baseline['source_resources']) and changed == sorted([FREEZER,AFTERLIFE,PHASE]))
    files = {p.relative_to(OUT/'package').as_posix(): sha(p) for p in (OUT/'package').rglob('*') if p.is_file()}
    check('inventory', 'All fifty retained package files exact, archive pending', files == {r['path']:r['sha256'] for r in baseline['files'] if r['path'] != ARCHIVE})
    # Bind unchanged current sources to PE1's actual compiled staging inventory.
    cpath = PREDECESSOR/'compile_01/result.json'
    compiled = read(cpath)
    check('compile', 'Inherited successful complete148-source compile', compiled['status'] == 'PASS_CURRENT_REGISTERED_SOURCE_COMPILE' and len(compiled['source_origins']) == 148)
    pins = {}
    for source, staged in compiled['source_origins'].items():
        digest = compiled['staged_sources'][staged]
        check('compile', 'Exact compiled source '+source, sha(source) == sha(staged) == digest)
        pins[source] = digest
    sidecars = []
    for source, digest in compiled['input_pins'].items():
        if source in pins:
            continue
        actual = sha(source)
        if source.endswith('.ts'):
            check('compile', 'Only16-byte compiler timestamp sidecar may refresh', Path(source).stat().st_size == 16)
            sidecars.append({'path': source, 'previous_sha256': digest, 'current_sha256': actual, 'bytes': 16})
        else:
            check('compile', 'Compiler/base cache unchanged '+source, actual == digest)
        pins[source] = actual
    write(HERE/'compile_inventory.json', {'status': 'PASS_UNCHANGED_CURRENT_SOURCES_MATCH_PE1_COMPLETE_COMPILE', 'compile_result': str(cpath), 'compile_result_sha256': sha(cpath), 'compiled_sha256': compiled['compiled_sha256'], 'source_count': 148, 'input_pins': pins, 'timestamp_sidecar': sidecars, 'scripts_changed': 0, 'new_compile_run': False, 'game_writes': 0, 'save_writes': 0})
    write(output, {'status': 'PASS_KM2_COOKED_ACTOR_SUPPRESSION_FLOW_AND_COMPLETE_DELTA', 'plan_sha256': sha(plan_path), 'cooked_sha256': sha(cooked_path), 'checks': len(checks), 'check_groups': dict(groups), 'details': checks, 'graph_deltas': diffs, 'flow_fixtures': simulations, 'changed_depots': changed, 'archive_payloads': 1581, 'retained_archive_payloads': 1578, 'package_paths_unchanged_before_packing': 50, 'scripts_changed': 0, 'compile_inventory_sha256': sha(HERE/'compile_inventory.json'), 'new_depots': 0, 'new_ArchiveXL_phase_ids': 0, 'native_resource_overrides': 0, 'limits': 'Static cooked signal/event ordering, byte/source checks and inherited complete compile. No engine spawn/scan/animation/save-reload or gameplay qualification; transition scope is before first Open only.', 'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'status': 'PASS', 'checks': len(checks), 'flow_fixtures': len(simulations), 'resources_changed': 3, 'scripts_changed': 0}))


if __name__ == '__main__':
    main()
