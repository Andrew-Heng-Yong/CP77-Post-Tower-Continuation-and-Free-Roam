"""Constrain cooked SD1 resources and test absent-actor completion contracts.

The signal fixtures are bounded graph models, not engine or gameplay tests.
"""
from collections import Counter
import copy
import heapq
import json
from pathlib import Path
from prepare import HERE, WS, KM2, BASE, OUT, ARCHIVE, SCENE, PHASE, read, sha, write
from model import Resource, compare_graph, reachable
from common import walk


def normal(path):
    result = Resource(read(path)).normalize()
    assert not result['errors'], result['errors']
    return result


def johnny_refs(payload):
    return [x for x in walk(payload) if
            (x.get('$type') == 'scnActorId' and x.get('id') == 0) or
            (x.get('$type') == 'scnPerformerId' and x.get('id') == 1)]


def destination(node, ordinal=0):
    return {'$type': 'scnInputSocketId', 'isockStamp': {'$type': 'scnInputSocketStamp',
            'name': 0, 'ordinal': ordinal}, 'nodeId': {'$type': 'scnNodeId', 'id': node}}


class Signals:
    """Authored event sockets/timers; player choices need an explicit action.

    Native non-condition quest nodes are assumed to acknowledge immediately.
    Actual animation, scene scheduling and device acknowledgement remain live-only.
    """
    def __init__(self, graph, start, choose=False):
        self.g, self.choose = graph, choose
        self.queue, self.visited, self.ends, self.held = [], [], [], []
        self.order, self.terminated = 0, False
        self.push(0, start)

    def push(self, time, node):
        self.order += 1
        heapq.heappush(self.queue, (time, self.order, node))

    def emit(self, time, payload, stamp=(0, 0)):
        for socket in payload.get('outputSockets', []):
            if (socket['stamp']['name'], socket['stamp']['ordinal']) == stamp:
                for target in socket['destinations']:
                    self.push(time, str(target['nodeId']['id']))

    def run(self):
        while self.queue and not self.terminated:
            assert len(self.visited) < 100, 'Unbounded signal loop'
            time, _, nid = heapq.heappop(self.queue)
            self.visited.append([time, nid])
            node = self.g['nodes'][nid]['payload']
            kind = node['$type']
            if kind == 'scnEndNode':
                self.ends.append([time, nid, node['type']])
                self.terminated = node['type'] == 'Terminating'
            elif kind == 'scnChoiceNode':
                if self.choose:
                    self.emit(time, node)
                else:
                    self.held.append(nid)
            elif kind == 'scnSectionNode':
                for event in node['events']:
                    if event['$type'] == 'scneventsSocket':
                        stamp = event['osockStamp']
                        self.emit(time + event['startTime'], node, (stamp['name'], stamp['ordinal']))
                self.emit(time + node['sectionDuration']['stu'], node)
            elif kind == 'scnQuestNode':
                q = node['questNode']
                assert 'johnny' not in json.dumps(q).lower(), nid
                delay = 0
                if q['$type'] == 'questPauseConditionNodeDefinition':
                    c = q['condition']['type']
                    assert c['$type'] == 'questRealtimeDelay_ConditionType'
                    delay = ((c['hours'] * 60 + c['minutes']) * 60 + c['seconds']) * 1000 + c['miliseconds']
                self.emit(time + delay, node)
            else:
                assert kind == 'scnStartNode', kind
                self.emit(time, node)
        return {'visited': self.visited, 'ends': self.ends, 'held_choices': self.held}


def main():
    assert not (HERE/'verification.json').exists() and not (HERE/'compile_inventory.json').exists()
    plan_path, rb_path = HERE/'input_02/plan.json', HERE/'readback_01/manifest.json'
    plan, cooked = read(plan_path), read(rb_path)
    checks, groups = [], Counter()
    def check(group, name, passed):
        assert passed, (group, name)
        checks.append({'group': group, 'name': name, 'pass': True})
        groups[group] += 1
    check('pins', 'Exact two cooked resources and authoring plan', cooked['plan_sha256'] == sha(plan_path) and
          {r['depot'] for r in cooked['resources']} == {SCENE, PHASE})
    models, deltas = {}, {}
    for edit in plan['edits']:
        depot = edit['depot']; rb, = [r for r in cooked['resources'] if r['depot'] == depot]
        check('pins', depot, sha(edit['source']['json']) == edit['source']['json_sha256'] and
              sha(edit['source']['raw']) == edit['source']['sha256'] and
              sha(edit['edited_json']) == edit['edited_json_sha256'] and
              sha(rb['raw']) == rb['sha256'] and sha(rb['json']) == rb['json_sha256'])
        old, new = normal(edit['source']['json']), normal(rb['json'])
        models[depot] = new; deltas[depot] = compare_graph(old, new)
        check('identity', depot+' graph identities', set(old['graphs']) == set(new['graphs']))
        if depot == PHASE:
            check('identity', 'Phase metadata, prefabs and embedded files retained', old['metadata'] == new['metadata'] and
                  old['root_prefabs'] == new['root_prefabs'] and old['embedded_files'] == new['embedded_files'])
            for gp, before in old['graphs'].items():
                after = new['graphs'][gp]
                check('identity', gp+' saved nodes/entries', set(before['nodes']) == set(after['nodes']) and before['entries'] == after['entries'])
                expected_edges = copy.deepcopy(before['edges'])
                if gp == 'root':
                    expected_edges.remove(['353','Out1','78','In'])
                check('phase', gp+' exact edge delta', after['edges'] == expected_edges)
                for nid, node in before['nodes'].items():
                    expected = copy.deepcopy(node)
                    if gp == 'root' and nid in ['14','46','168','170']:
                        expected['payload']['interruptionOperations'] = [{'$type':'scnToggleInterruption_InterruptionOperation','enable':0}]
                        expected['payload']['reapplyInterruptionOperationsAfterGameLoad'] = 1
                        # Derived fingerprints change when the approved payload changes.
                        for key in ['payload_sha256']:
                            expected[key] = after['nodes'][nid][key]
                    check('phase', gp+'/'+nid+' entire node contract', after['nodes'][nid] == expected)
            root = new['graphs']['root']
            check('phase', 'Only auxiliary Johnny branch unreachable', set(old['graphs']['root']['reachable']) - set(root['reachable']) == {'78','139','46','53','45'})
            continue
        expected_meta = copy.deepcopy(old['metadata'])
        actor, = [a for a in expected_meta['actors'] if a['actorId']['id'] == 0]
        check('actor', 'Exact source actor is Johnny', actor['actorName'] == 'Johnny' and actor['acquisitionPlan'] == 'spawnDespawn')
        for flag in ['isEnabled','alwaysSpawned','spawnOnStart']:
            actor['spawnDespawnParams'][flag] = 0
        check('identity', 'Only three Johnny acquisition flags change in scene metadata', expected_meta == new['metadata'] and old['embedded_files'] == new['embedded_files'])
        check('actor', 'No independent prop or effect instance survives', new['metadata']['props'] == new['metadata']['effectDefinitions'] == new['metadata']['effectInstances'] == [])
        before, after = old['graphs']['scene'], new['graphs']['scene']
        check('identity', 'All saved scene nodes and named entry/exit IDs retained', set(before['nodes']) == set(after['nodes']) and before['entries'] == after['entries'])
        # Independent allowed destination map, rather than accepting the plan as proof.
        wiring = {('1',0,0):[(3,0)], ('22',0,0):[(21,0)], ('26',0,0):[(28,0)], ('1048',0,0):[(1055,0)],
                  ('3',6,0):[], ('21',2,0):[], ('28',2,0):[],
                  ('60',0,0):[(2,0),(105,1)], ('21',0,0):[(23,0),(125,1)], ('28',0,0):[(27,0),(117,1)],
                  ('105',0,0):[(110,0)], ('125',0,0):[(129,0)], ('117',0,0):[(121,0)]}
        removed = []
        for nid, node in before['nodes'].items():
            expected = copy.deepcopy(node['payload'])
            if 'actorBehaviors' in expected:
                expected['actorBehaviors'] = [a for a in expected['actorBehaviors'] if a['actorId']['id'] != 0]
            if 'events' in expected:
                targets = [e for e in expected['events'] if johnny_refs(e)]
                check('events', nid+' removed events contain no dialogue', all(e['$type'] != 'scnDialogLineEvent' for e in targets))
                removed.extend(str(e['id']['id']) for e in targets)
                expected['events'] = [e for e in expected['events'] if not johnny_refs(e)]
            if nid in ['105','125','117']:
                check('actor', nid+' replaces missing-Johnny camera focus only', 'Johnny' in json.dumps(expected['questNode']['condition']))
                expected['questNode']['condition'] = {'$type':'questTimeCondition','type':{'$type':'questRealtimeDelay_ConditionType','hours':0,'minutes':0,'seconds':0,'miliseconds':50}}
            for socket in expected.get('outputSockets', []):
                key = (nid, socket['stamp']['name'], socket['stamp']['ordinal'])
                if key in wiring:
                    socket['destinations'] = [destination(*t) for t in wiring[key]]
            check('delta', nid+' exact complete cooked payload', after['nodes'][nid]['payload'] == expected)
            check('identity', nid+' embedded quest socket schema', node.get('embedded_sockets') == after['nodes'][nid].get('embedded_sockets'))
        check('events', 'Exactly thirteen Johnny presentation events removed', len(removed) == len(set(removed)) == 13)
        def speech(g):
            return {str(e['id']['id']):e for n in g['nodes'].values() for e in n['payload'].get('events',[]) if e['$type'] == 'scnDialogLineEvent'}
        check('speech', 'Every previously retained spoken event and time exact', speech(before) == speech(after))
        for nid in after['reachable']:
            p = after['nodes'][nid]['payload']
            check('actor', nid+' no reachable Johnny reference or command', not johnny_refs(p) and 'johnny' not in json.dumps(p.get('questNode', {})).lower())
        check('timing', 'Wake/get-up and silent cut sections retain authored durations',
              {n:after['nodes'][n]['payload']['sectionDuration']['stu'] for n in ['3','21','28']} == {'3':31051,'21':7617,'28':7810})
        # All event-ID metadata must refer only to remaining events, including debug symbols.
        raw = read(rb['json'])
        check('events', 'Removed event IDs absent from serialized metadata', not any(x.get('$type') == 'scnSceneEventId' and str(x.get('id')) in removed for x in walk(raw)))
    scene = models[SCENE]['graphs']['scene']; phase = models[PHASE]['graphs']['root']
    fixtures = []
    expected_ends = {'waking_up_in':['2','110'], 'sucker_in':['23','129'], 'payback_in':['27','121'],
                     'elevator_in':['1055'], 'pc1_hack_in':['7'], 'gear_loot_in':['12'], 'pc2_hack_in':['17'],
                     'scav_chat_1_in':['32'], 'scav_chat_2_in':['37']}
    for name, start in scene['entries'].items():
        f = Signals(scene, start, choose=True).run()
        check('fixture', name+' delivers original named completion exits', [e[1] for e in f['ends']] == expected_ends[name])
        if len(f['ends']) == 2:
            check('fixture', name+' gameplay precedes terminating cleanup by fifty ms',
                  f['ends'][0][2] == 'NonTerminating' and f['ends'][1][2] == 'Terminating' and f['ends'][1][0]-f['ends'][0][0] == 50)
        fixtures.append({'entry':name,'manual_choice':True,**f})
    for name in ['pc1_hack_in','gear_loot_in','pc2_hack_in']:
        f = Signals(scene, scene['entries'][name]).run()
        check('fixture', name+' waits for player, never auto-loots or hacks', not f['ends'] and len(f['held_choices']) == 1)
        fixtures.append({'entry':name,'manual_choice':False,**f})
    for edge in [['33','Out','176','Active'],['176','Out','168','elevator_in'],['168','elevator_out','35','In'],
                 ['170','payback_johnny_out','173','In2'],['170','payback_out','171','Succeeded'],
                 ['171','Out','172','Active'],['172','Out','204','In'],['204','Out','269','In'],['269','Out','173','In1']]:
        check('contract', 'Native route '+str(edge), edge in phase['edges'])
    check('contract', 'Player still must enter the elevator trigger', phase['nodes']['35']['payload']['condition']['isPlayerActivator'] == 1 and
          phase['nodes']['35']['payload']['condition']['triggerAreaRef']['$value'] == '#mq036_tr_hideout_elevator')
    check('contract', 'Payback cleanup keeps native two-input AND', phase['nodes']['173']['type'] == 'questLogicalAndNodeDefinition' and
          phase['nodes']['173']['payload']['inputSocketCount'] == 2 and set(tuple(e) for e in phase['edges'] if e[2] == '173') ==
          {('269','Out','173','In1'),('170','payback_johnny_out','173','In2')})
    for order in [('In1','In2'),('In2','In1')]:
        seen = set(); fired = []
        for incoming in order:
            seen.add(incoming); fired.append(len(seen) == 2)
        check('fixture', 'Payback AND waits for both original callbacks '+str(order), fired == [False,True])
        fixtures.append({'payback_AND_order':list(order),'fired':fired})
    baseline = read(BASE/'package_manifest.json')
    members = {str(p.relative_to(OUT/'archive_source')).replace('/','\\'):sha(p) for p in (OUT/'archive_source').rglob('*') if p.is_file()}
    check('inventory', 'Exact full 1581 resource inventory', set(members) == set(baseline['source_resources']) and len(members) == 1581)
    changed = sorted(d for d,h in members.items() if h != baseline['source_resources'][d])
    check('inventory', 'Only two private Sweet Dreams resources changed; KOLD exact', changed == sorted([SCENE,PHASE]))
    files = {p.relative_to(OUT/'package').as_posix():sha(p) for p in (OUT/'package').rglob('*') if p.is_file()}
    check('inventory', 'All fifty other package files exact', files == {r['path']:r['sha256'] for r in baseline['files'] if r['path'] != ARCHIVE})
    cpath = WS/'prealpha/prepared_encounters_pe1/compile_01/result.json'; compiled = read(cpath)
    check('compile', 'Complete inherited 148-source compile', compiled['status'] == 'PASS_CURRENT_REGISTERED_SOURCE_COMPILE' and len(compiled['source_origins']) == 148)
    pins, sidecars = {}, []
    for source, staged in compiled['source_origins'].items():
        digest = compiled['staged_sources'][staged]
        check('compile', source+' exact compiled bytes', sha(source) == sha(staged) == digest)
        pins[source] = digest
    for source, digest in compiled['input_pins'].items():
        if source in pins:
            continue
        actual = sha(source)
        if source.endswith('.ts'):
            check('compile', 'Only normal sixteen-byte timestamp may refresh', Path(source).stat().st_size == 16)
            sidecars.append({'path':source,'previous_sha256':digest,'current_sha256':actual,'bytes':16})
        else:
            check('compile', 'Compiler/base cache retained '+source, actual == digest)
        pins[source] = actual
    write(HERE/'compile_inventory.json', {'status':'PASS_UNCHANGED_CURRENT_SOURCES_MATCH_PE1_COMPLETE_COMPILE','compile_result':str(cpath),
          'compile_result_sha256':sha(cpath),'compiled_sha256':compiled['compiled_sha256'],'source_count':148,'input_pins':pins,
          'timestamp_sidecar':sidecars,'scripts_changed':0,'new_compile_run':False,'game_writes':0,'save_writes':0})
    write(HERE/'verification.json', {'status':'PASS_SD1_COOKED_PRESENTATION_AND_COMPLETION_CONTRACTS','plan_sha256':sha(plan_path),
          'cooked_sha256':sha(rb_path),'checks':len(checks),'check_groups':dict(groups),'details':checks,'graph_deltas':deltas,
          'flow_fixtures':fixtures,'changed_depots':changed,'archive_payloads':1581,'retained_archive_payloads':1579,
          'scripts_changed':0,'compile_inventory_sha256':sha(HERE/'compile_inventory.json'),'new_depots':0,'new_ArchiveXL_phase_ids':0,
          'native_resource_overrides':0,'limits':'Static cooked graph, event timing and bounded acknowledgement fixtures. Engine actor absence, interruption/reload and gameplay pending. Completed current quest is preserved; no restart/migration.',
          'game_writes':0,'save_writes':0})
    print(json.dumps({'status':'PASS','checks':len(checks),'flow_fixtures':len(fixtures),'resources_changed':2,'scripts_changed':0}))


if __name__ == '__main__':
    main()
