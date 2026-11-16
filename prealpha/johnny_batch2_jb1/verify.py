"""Independent complete-payload constraints for the JB1 cooked resources.

The source node allowlists and manual wires below are intentionally separate
from the author's plan. Flow fixtures are a separate bounded signal assessment.
"""
import collections
import copy
import json
from pathlib import Path
from prepare import HERE, WS, BASE, OUT, ARCHIVE, read, sha, write
from model import Resource, compare_graph
from common import walk


ACTOR_NODES = {
    'mq029_01a_garage.scene': '28 31',
    'mq029_01b_josie_body.scene': '19 24 38',
    'mq017_streetkid_01a_johnny.scene': '65 119 152 189 213',
    'mq017_streetkid_03_confront_thugs.scene': '283 332 343 349 906 915 993 995 1268 1776 1856 1857 1858 1859 1860 1903 1917 2248 2257',
    'mq018_02_fortuneteller.scene': '665 785 789 799 1019 1023 1208 1250 1252 1287 1299 1301 1304 1312 1748 1938 1981 1990 1994 1996',
    'mq018_03_call02.scene': '85 133 173 176 305',
    'mq018_05_brooklyn.scene': '241 247 269 273 279 281 283 301 314 318 321 323 326 487 512 532',
    'mq018_06_solar.scene': '229 277 282 285 287 288 390 414',
    'mq018_07_protein.scene': '233 239 244 280 292 294 296 312 315 323 327 330 333 1475',
    'mq040_02_trail_wife.scene': '139 145 146 161 183 187 249 255 257 270 276 277 283 336 342 348 355 375 377 380 383 385 389 390 397 398 403 404 413 414 415 416 428 431 432 437 442 445 450',
    'mq040_03_ripperdoc.scene': '450 457 471 478 507 528 611 612 615 618 619 623 624 864 866',
    'mq042_nomad_02_car_found.scene': '175 176 558 772',
}


def normal(path):
    result = Resource(read(path)).normalize()
    assert not result['errors'], result['errors']
    return result


def expanded(resource, value, seen=frozenset()):
    """Resolve handles without the graph/debug omissions of model.clean()."""
    if isinstance(value, dict):
        if 'HandleId' in value or 'HandleRefId' in value:
            key = resource.hid(value)
            assert key not in seen, 'Unexpected cyclic resource metadata'
            return expanded(resource, resource.d(value), seen | {key})
        return {k: expanded(resource, v, seen) for k, v in value.items()}
    if isinstance(value, list):
        return [expanded(resource, v, seen) for v in value]
    return value


def johnny(payload, aids):
    # Typed identities and actual entity bindings, never a world marker's name.
    for x in walk(payload):
        if x.get('$type') == 'scnActorId' and x.get('id') in aids:
            return True
        if x.get('$type') == 'scnPerformerId' and x.get('id') in [(a << 8) | 1 for a in aids]:
            return True
        if x.get('$type') == 'gameEntityReference' and (
                'johnny' in x.get('dynamicEntityUniqueName', {}).get('$value', '').lower()
                or 'johnny' in x.get('sceneActorContextName', {}).get('$value', '').lower()
                or x.get('reference', {}).get('$value') == '#johnny'):
            return True
    return False


def without_removed_ids(value, removed):
    if isinstance(value, dict):
        return {k: without_removed_ids(v, removed) for k, v in value.items()}
    if isinstance(value, list):
        result = []
        for v in value:
            if isinstance(v, dict) and v.get('$type') == 'scnSceneEventId' and str(v['id']) in removed:
                continue
            after = without_removed_ids(v, removed)
            if isinstance(after, dict) and after.get('$type') == 'scnSceneEventSymbol' and not after['sceneEventIds']:
                continue
            result.append(after)
        return result
    return value


def dest(node, ordinal=0, name=0):
    return {'$type': 'scnInputSocketId', 'nodeId': {'$type': 'scnNodeId', 'id': int(node)},
            'isockStamp': {'$type': 'scnInputSocketStamp', 'name': name, 'ordinal': ordinal}}


def expected_wires(base, nodes):
    bypass = {}
    for nid in ACTOR_NODES[base].split():
        q = nodes[nid]['payload']['questNode']
        assert 'johnny' in json.dumps(q).lower()
        outputs = [s for s in nodes[nid]['payload']['outputSockets'] if s['destinations']]
        assert len(outputs) <= 1
        bypass[nid] = copy.deepcopy(outputs[0]['destinations']) if outputs else []
    for nid, node in nodes.items():
        q = node['payload'].get('questNode', {})
        if q.get('$type') == 'questJournalNodeDefinition' and any(
                x.get('$type') == 'gameJournalPath' and ('johnny' in x.get('realPath', '').lower()
                or (base == 'mq018_02_fortuneteller.scene' and nid in ('1119', '1141'))) for x in walk(q)):
            bypass[nid] = [copy.deepcopy(d) for s in node['payload']['outputSockets'] for d in s['destinations']]
    explicit = {}
    if base == 'mq029_01a_garage.scene':
        explicit = {('80', 0, 0): [dest(25, 1)], ('25', 0, 0): [dest(62, 1), dest(32, 1)], ('32', 0, 0): [dest(2)]}
    elif base == 'mq029_01b_josie_body.scene':
        explicit = {('1', 0, 0): [dest(2)]}
    elif base == 'mq017_streetkid_01a_johnny.scene':
        explicit = {(nid, 0, 0): [dest(2)] for nid, node in nodes.items() if node['type'] == 'scnStartNode'}
    elif base == 'mq017_streetkid_03_confront_thugs.scene':
        bypass.update({'507': [dest(184)], '1024': [dest(1311, 3)], '922': [], '1924': [], '2242': []})
        explicit = {('1927', 0, 0): [dest(1921)]}
    elif base == 'mq042_nomad_02_car_found.scene':
        bypass.update({'561': [], '781': []})
        explicit = {('771', 0, 0): [dest(107, 1)], ('107', 0, 0): [dest(2), dest(658, 1), dest(660, 1)],
                    ('992', 5, 0): [dest(1000, 1), dest(771, 1)]}
    elif base == 'mq018_05_brooklyn.scene':
        bypass['71'] = [dest(77)]
    elif base == 'mq018_06_solar.scene':
        bypass['78'] = [dest(394)]
    elif base == 'mq018_07_protein.scene':
        bypass['82'] = [dest(88)]
    elif base == 'mq018_02_fortuneteller.scene':
        bypass['109'] = [dest(932, 1)]

    def resolve(d, seen=()):
        nid = str(d['nodeId']['id'])
        if nid not in bypass:
            return [d]
        assert nid not in seen
        p = nodes[nid]['payload']
        name, ordinal = d['isockStamp']['name'], d['isockStamp']['ordinal']
        if p['$type'] == 'scnChoiceNode':
            active = name == 0 and ordinal == 0
        else:
            active = name != 1026 and p['isockMappings'][ordinal]['$value'] != 'CutDestination'
        if not active:
            return []
        values = []
        for next_dest in bypass[nid]:
            values.extend(resolve(copy.deepcopy(next_dest), seen + (nid,)))
        return values

    outputs = {}
    for nid, node in nodes.items():
        sockets = copy.deepcopy(node['payload']['outputSockets'])
        for s in sockets:
            key = (nid, s['stamp']['name'], s['stamp']['ordinal'])
            expanded = [d2 for d1 in explicit.get(key, s['destinations']) for d2 in resolve(copy.deepcopy(d1))]
            s['destinations'] = []
            for d in expanded:
                if d not in s['destinations']:
                    s['destinations'].append(d)
        outputs[nid] = sockets
    return outputs, set(bypass)


def main():
    assert not (HERE / 'verification_04.json').exists()
    plan_path, rb_path = HERE / 'input_04/plan.json', HERE / 'readback_04/manifest.json'
    plan, rb = read(plan_path), read(rb_path)
    checks, groups, deltas, models = [], collections.Counter(), {}, {}
    def check(group, name, passed):
        assert passed, (group, name)
        checks.append({'group': group, 'name': name, 'pass': True})
        groups[group] += 1
    check('pins', 'Thirteen cooked resources pinned to exact plan', rb['plan_sha256'] == sha(plan_path) and len(rb['resources']) == 13)
    check('pins', 'Pinned 150-event user decision', sha(plan['approved_speech']) == plan['approved_speech_sha256'])
    approved = read(plan['approved_speech'])['events']
    totals, removed_all = collections.Counter(), []
    donor_row = plan['native_text_donor']
    donor = Resource(read(donor_row['json']))
    donor_loc = donor.clean(donor.root['locStore'])
    for edit in plan['edits']:
        dep = edit['depot']
        base = dep.split('\\')[-1]
        cooked, = [r for r in rb['resources'] if r['depot'] == dep]
        check('pins', dep, all(sha(path) == digest for path, digest in [
            (edit['source']['raw'], edit['source']['sha256']), (edit['source']['json'], edit['source']['json_sha256']),
            (edit['edited_json'], edit['edited_json_sha256']), (cooked['raw'], cooked['sha256']), (cooked['json'], cooked['json_sha256'])]))
        old, new = normal(edit['source']['json']), normal(cooked['json'])
        check('roundtrip', base, new == normal(edit['edited_json']))
        models[base] = new
        deltas[dep] = compare_graph(old, new)
        if base == 'mq017_streetkid_00_main.questphase':
            check('phase', 'All cleanup prefab, metadata and nested graph identities unchanged',
                  old['metadata'] == new['metadata'] and old['root_prefabs'] == new['root_prefabs']
                  and old['embedded_files'] == new['embedded_files'] and set(old['graphs']) == set(new['graphs']))
            for gp, og in old['graphs'].items():
                ng = new['graphs'][gp]
                check('phase', gp + ' exact edges, nodes and entry identities', og['edges'] == ng['edges']
                      and og['entries'] == ng['entries'] and set(og['nodes']) == set(ng['nodes']))
                for nid, on in og['nodes'].items():
                    expected = copy.deepcopy(on)
                    if gp == 'root/4' and nid == '6':
                        check('phase', 'Source wait targets absent Johnny camera focus',
                              expected['payload']['condition']['type']['objectRef']['reference']['$value'] == '#johnny')
                        expected['payload']['condition'] = {'$type': 'questTimeCondition', 'type': {
                            '$type': 'questRealtimeDelay_ConditionType', 'hours': 0, 'miliseconds': 50, 'minutes': 0, 'seconds': 0}}
                        for key in ['payload_sha256', 'conditions', 'node_refs']:
                            expected[key] = ng['nodes'][nid][key]
                    check('phase', gp + '/' + nid + ' entire node contract', expected == ng['nodes'][nid])
            continue
        before, after = old['graphs']['scene'], new['graphs']['scene']
        aids = {a['actorId']['id'] for a in old['metadata']['actors'] if 'johnny' in a['actorName'].lower()}
        check('identity', base + ' saved nodes, entry/exit and embedded resources',
              set(before['nodes']) == set(after['nodes']) and before['entries'] == after['entries']
              and old['embedded_files'] == new['embedded_files'])
        selected = {str(e['event_id']): e for e in approved if e['depot'] == dep}
        wires, bypassed = expected_wires(base, before['nodes'])
        check('wiring', base + ' independent absent-actor allowlist', bypassed == {b['node'] for b in edit['changes']['bypassed_nodes']})
        removed_ids = set()
        for nid, old_node in before['nodes'].items():
            op, np = old_node['payload'], after['nodes'][nid]['payload']
            expected = copy.deepcopy(op)
            expected['outputSockets'] = wires[nid]
            if 'actorBehaviors' in expected:
                expected['actorBehaviors'] = [a for a in expected['actorBehaviors'] if a['actorId']['id'] not in aids]
            if 'events' in expected:
                retained = []
                had_selection = False
                actual_events = {str(e['id']['id']): e for e in np['events']}
                for e in expected['events']:
                    eid = str(e['id']['id'])
                    if eid in selected:
                        check('speech', base + '/' + eid, e['$type'] == 'scnDialogLineEvent' and str(selected[eid]['node_id']) == nid)
                        removed_ids.add(eid)
                        totals[selected[eid]['speaker_role']] += 1
                        had_selection = True
                    elif e['$type'] != 'scnDialogLineEvent' and johnny(e, aids):
                        removed_ids.add(eid)
                    else:
                        retained.append(e)
                may_retime = had_selection and not base.startswith('mq040')
                for e in retained:
                    eid = str(e['id']['id'])
                    check('events', base + '/' + eid + ' retained', eid in actual_events)
                    if may_retime:
                        new_start = actual_events[eid]['startTime']
                        check('timing', base + '/' + eid + ' only remove elapsed time', 0 <= new_start <= e['startTime'])
                        e['startTime'] = new_start
                if may_retime:
                    new_duration = np['sectionDuration']['stu']
                    check('timing', base + '/' + nid + ' bounded duration', 50 <= new_duration <= op['sectionDuration']['stu']
                          and all(e['startTime'] + e['duration'] <= new_duration for e in retained))
                    # A surviving animation/voice interval cannot be shortened or
                    # internally reordered by moving its callbacks.
                    old_events = {str(e['id']['id']): e for e in op['events']}
                    points = {}
                    protected = []
                    for e in retained:
                        orig = old_events[str(e['id']['id'])]
                        for a, b in [(orig['startTime'], e['startTime']), (orig['startTime'] + orig['duration'], e['startTime'] + e['duration'])]:
                            check('timing', base + '/' + nid + ' simultaneous callbacks', a not in points or points[a] == b)
                            points[a] = b
                        if e['duration']:
                            protected.append((orig['startTime'], orig['startTime'] + orig['duration']))
                    pairs = sorted(points.items())
                    check('timing', base + '/' + nid + ' callback order', all(a2 > a1 and b2 > b1 for (a1, b1), (a2, b2) in zip(pairs, pairs[1:])))
                    for (a1, b1), (a2, b2) in zip(pairs, pairs[1:]):
                        if any(a <= a1 and a2 <= b for a, b in protected):
                            check('timing', base + '/' + nid + ' protected native interval', a2-a1 == b2-b1)
                    expected['sectionDuration']['stu'] = new_duration
                expected['events'] = retained
            if (base == 'mq029_01a_garage.scene' and nid == '32') or (base == 'mq042_nomad_02_car_found.scene' and nid == '771'):
                expected['questNode']['condition'] = {'$type': 'questTimeCondition', 'type': {
                    '$type': 'questRealtimeDelay_ConditionType', 'hours': 0, 'miliseconds': 50, 'minutes': 0, 'seconds': 0}}
            if base == 'mq018_02_fortuneteller.scene' and nid == '809':
                for key in ('mode', 'ataParams', 'atgoParams', 'atwParams', 'mappinParams', 'displayNameOverride', 'localizedDisplayNameOverride', 'shapeParams'):
                    if key in before['nodes']['64']['payload']:
                        expected[key] = copy.deepcopy(before['nodes']['64']['payload'][key])
            expected = without_removed_ids(expected, removed_ids | {str(e['event_id']) for e in approved if e['depot'] == dep})
            # References to presentation events can occur before their section.
            all_removed = {e['id'] for e in edit['changes']['removed_speech'] + edit['changes']['removed_presentation']}
            expected = without_removed_ids(expected, all_removed)
            check('payload', base + '/' + nid + ' complete cooked payload', np == expected)
            check('identity', base + '/' + nid + ' socket schema', old_node.get('embedded_sockets') == after['nodes'][nid].get('embedded_sockets'))
        check('events', base + ' independent exact removal inventory', removed_ids == {e['id'] for e in edit['changes']['removed_speech'] + edit['changes']['removed_presentation']})
        check('wiring', base + ' no removed operation has incoming signal', not any(e[2] in bypassed for e in after['edges']))
        # Use activation-aware traversal only; dormant legacy nodes stay serialized.
        reachable = set()
        pending = list(after['entries'].values())
        while pending:
            nid = pending.pop()
            if nid in reachable:
                continue
            reachable.add(nid)
            p = after['nodes'][nid]['payload']
            if p['$type'] == 'scnQuestNode':
                check('actor', base + '/' + nid + ' no reachable actor action', not johnny(p['questNode'], aids))
            elif p['$type'] == 'scnChoiceNode':
                check('actor', base + '/' + nid + ' no reachable Johnny menu', not johnny(p, aids))
            for edge in after['edges']:
                if edge[0] != nid:
                    continue
                target = after['nodes'][edge[2]]['payload']
                name, ordinal = map(int, edge[3].split(':'))
                if target['$type'] == 'scnQuestNode' and (name == 1026 or target['isockMappings'][ordinal]['$value'] == 'CutDestination'):
                    continue
                if target['$type'] == 'scnChoiceNode' and (name, ordinal) != (0, 0):
                    continue
                pending.append(edge[2])
        oldr, newr = Resource(read(edit['source']['json'])), Resource(read(cooked['json']))
        expected_root = without_removed_ids(expanded(oldr, oldr.root), removed_ids)
        for actor in expected_root['actors']:
            if actor['actorId']['id'] in aids:
                for flag in ('isEnabled', 'alwaysSpawned', 'spawnOnStart'):
                    actor['spawnDespawnParams'][flag] = 0
        if base == 'mq018_02_fortuneteller.scene':
            option, = [o for o in expected_root['screenplayStore']['options'] if o['itemId']['id'] == 1026]
            option['locstringId']['ruid'] = '2089382164102328324'
            for descriptor in donor_loc['vdEntries']:
                if str(descriptor['locstringId']['ruid']) != '2089382164102328324':
                    continue
                entry = copy.deepcopy(descriptor)
                payload = copy.deepcopy(donor_loc['vpEntries'][descriptor['vpeIndex']])
                loc = expected_root['locStore']
                assert payload not in loc['vpEntries']
                entry['vpeIndex'] = len(loc['vpEntries'])
                loc['vpEntries'].append(payload)
                loc['vdEntries'].append(entry)
        new_root = expanded(newr, newr.root)
        check('identity', base + ' node serialization order retained',
              [n['nodeId'] for n in expected_root['sceneGraph']['graph']] == [n['nodeId'] for n in new_root['sceneGraph']['graph']])
        expected_root['sceneGraph']['graph'] = new_root['sceneGraph']['graph']
        check('metadata', base + ' entire remaining resource preserved', new_root == expected_root)
        removed_all.extend(removed_ids)
    check('speech', 'All 89 Johnny and 61 V approved events removed', totals == {'JOHNNY': 89, 'V': 61})
    baseline = read(BASE / 'package_manifest.json')
    members = {str(p.relative_to(OUT / 'archive_source')).replace('/', '\\'): sha(p) for p in (OUT / 'archive_source').rglob('*') if p.is_file()}
    changed = sorted(d for d, h in members.items() if h != baseline['source_resources'][d])
    check('inventory', 'Exact 1581 resource inventory', set(members) == set(baseline['source_resources']) and len(members) == 1581)
    check('inventory', 'Only thirteen approved resources change, including KOLD and Sweet byte preservation', changed == sorted(e['depot'] for e in plan['edits']))
    files = {p.relative_to(OUT / 'package').as_posix(): sha(p) for p in (OUT / 'package').rglob('*') if p.is_file()}
    check('inventory', 'Other fifty Core package files exact', files == {r['path']: r['sha256'] for r in baseline['files'] if r['path'] != ARCHIVE})
    cpath = WS / 'prealpha/prepared_encounters_pe1/compile_01/result.json'
    compiled = read(cpath)
    check('compile', 'Inherited complete 148-source compile', compiled['status'] == 'PASS_CURRENT_REGISTERED_SOURCE_COMPILE' and len(compiled['source_origins']) == 148)
    pins, sidecars = {}, []
    for source, staged in compiled['source_origins'].items():
        digest = compiled['staged_sources'][staged]
        check('compile', source, sha(source) == sha(staged) == digest)
        pins[source] = digest
    for source, digest in compiled['input_pins'].items():
        if source in pins:
            continue
        actual = sha(source)
        if source.endswith('.ts'):
            check('compile', 'Normal timestamp sidecar', Path(source).stat().st_size == 16)
            sidecars.append({'path': source, 'previous_sha256': digest, 'current_sha256': actual, 'bytes': 16})
        else:
            check('compile', source, actual == digest)
        pins[source] = actual
    write(HERE / 'compile_inventory_04.json', {'status': 'PASS_UNCHANGED_CURRENT_SOURCES_MATCH_PE1_COMPLETE_COMPILE', 'compile_result': str(cpath),
          'compile_result_sha256': sha(cpath), 'compiled_sha256': compiled['compiled_sha256'], 'source_count': 148,
          'input_pins': pins, 'timestamp_sidecar': sidecars, 'scripts_changed': 0, 'new_compile_run': False, 'game_writes': 0, 'save_writes': 0})
    write(HERE / 'verification_04.json', {'status': 'PASS_JB1_COOKED_DIALOGUE_PRESENTATION_AND_WIRING_CONSTRAINTS', 'plan_sha256': sha(plan_path),
          'cooked_sha256': sha(rb_path), 'checks': len(checks), 'check_groups': dict(groups), 'details': checks, 'graph_deltas': deltas,
          'changed_depots': changed, 'archive_payloads': 1581, 'retained_archive_payloads': 1568, 'speech_cuts': dict(totals),
          'removed_event_count': len(removed_all), 'scripts_changed': 0, 'compile_inventory_sha256': sha(HERE / 'compile_inventory_04.json'),
          'new_depots': 0, 'new_ArchiveXL_phase_ids': 0, 'native_resource_overrides': 0,
          'limits': 'Complete serialized payload constraints; native engine scheduling, actor absence, live branches and saved-scene upgrades are separate qualifications.',
          'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'status': 'PASS', 'checks': len(checks), 'speech_cuts': dict(totals), 'resources_changed': 13, 'scripts_changed': 0}))


if __name__ == '__main__':
    main()
