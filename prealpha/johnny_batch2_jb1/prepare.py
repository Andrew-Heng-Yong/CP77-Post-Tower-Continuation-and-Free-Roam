"""Author the user-approved five-quest Johnny removal on the exact SD1 source.

No game/save writes. Old node, option, line, resource and actor IDs remain.
Absent-actor cancellation inputs are dropped rather than treated as activation.
"""
from pathlib import Path
import collections
import copy
import importlib.util
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
BASE = WS / 'prealpha/sweet_dreams_sd1/candidate_02'
OUT = HERE / 'candidate_04'
INPUT = HERE / 'input_04'
INSTALLED = WS / 'prealpha/sweet_dreams_sd1/deployment_01/installed_manifest_01.json'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
spec = importlib.util.spec_from_file_location('jb1_authoring_api', WS / 'prealpha/kold_mirage_km2/prepare.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
read, sha, write = api.read, api.sha, api.write
sys.path.insert(0, str(WS / 'prealpha/quest_restoration_qr13'))
from resource_edit import Edit
from model import Resource
from common import walk


def actor_reference(payload, actor_ids):
    performers = {(i << 8) | 1 for i in actor_ids}
    for value in walk(payload):
        kind = value.get('$type')
        if kind == 'scnActorId' and value.get('id') in actor_ids:
            return True
        if kind == 'scnPerformerId' and value.get('id') in performers:
            return True
        if kind == 'gameEntityReference':
            if ('johnny' in value.get('dynamicEntityUniqueName', {}).get('$value', '').lower()
                    or 'johnny' in value.get('sceneActorContextName', {}).get('$value', '').lower()
                    or value.get('reference', {}).get('$value') == '#johnny'):
                return True
    return False


def compress_section(node, r):
    """Collapse removed speech/silence; retain every surviving event's duration.

    Each surviving non-socket interval is protected. In unprotected intervals,
    distinct authored callback times stay ordered, with a 1ms separation. No
    physical animation, retained VO, device/player action or socket is deleted.
    """
    events = [r.d(h) for h in node['events']]
    duration = node['sectionDuration']['stu']
    protected = [(e['startTime'], e['startTime'] + e['duration']) for e in events
                 if e['$type'] != 'scneventsSocket' and e['duration'] > 0]
    anchors = sorted({0, duration} | {t for e in events for t in (e['startTime'], e['startTime'] + e['duration'])})
    assert anchors[-1] <= duration
    translated = {0: 0}
    for before, after in zip(anchors, anchors[1:]):
        keep = any(a <= before and after <= b for a, b in protected)
        translated[after] = translated[before] + (after - before if keep else min(1, after - before))
    changes = []
    for e in events:
        start = e['startTime']
        assert translated[start + e['duration']] - translated[start] == e['duration'], e['$type']
        if start != translated[start]:
            changes.append({'event': str(e['id']['id']), 'before': start, 'after': translated[start]})
            e['startTime'] = translated[start]
    after = max(50, translated[duration])
    assert after <= duration
    node['sectionDuration']['stu'] = after
    return {'before_ms': duration, 'after_ms': after, 'shifted_events': changes,
            'protected_intervals': protected}


def neutral_bot_choice(r, nodes, donor):
    node = nodes['809']
    device = nodes['64']
    before = r.clean(node)
    assert node['mode'] == 'attachToWorld' and node['displayNameOverride'] == 'LocKey#37443'
    assert node['options'][0]['screenplayOptionId']['id'] == 1026
    for key in ('mode', 'ataParams', 'atgoParams', 'atwParams', 'mappinParams',
                'displayNameOverride', 'localizedDisplayNameOverride', 'shapeParams'):
        if key in device:
            node[key] = copy.deepcopy(device[key])
    assert node['atgoParams']['nodeRef']['$value'] == '#mq018_ent_fortuneteller_relay'
    loc_id = '2089382164102328324'
    store = r.d(r.root['screenplayStore'])
    option, = [o for o in store['options'] if o['itemId']['id'] == 1026]
    old_loc_id = option['locstringId']['ruid']
    option['locstringId']['ruid'] = loc_id
    target_loc = r.d(r.root['locStore'])
    source_loc = donor.d(donor.root['locStore'])
    descriptors = [v for v in source_loc['vdEntries'] if str(v['locstringId']['ruid']) == loc_id]
    assert len(descriptors) == 4 and {v['localeId'] for v in descriptors} == {'db_db', 'en_us', 'pl_pl'}
    copied = []
    for d in descriptors:
        assert not any(v['locstringId'] == d['locstringId'] and v['localeId'] == d['localeId']
                       and v['signature'] == d['signature'] and v['variantId'] == d['variantId']
                       for v in target_loc['vdEntries'])
        payload = copy.deepcopy(source_loc['vpEntries'][d['vpeIndex']])
        matches = [i for i, v in enumerate(target_loc['vpEntries']) if v == payload]
        if matches:
            index, = matches
        else:
            index = len(target_loc['vpEntries'])
            target_loc['vpEntries'].append(payload)
        descriptor = copy.deepcopy(d)
        descriptor['vpeIndex'] = index
        target_loc['vdEntries'].append(descriptor)
        copied.append({'descriptor': descriptor, 'payload': payload})
    return {'node': '809', 'option_id': 1026, 'before': before, 'old_locstring': old_loc_id,
            'new_locstring': loc_id, 'native_text_only_donor': True,
            'localized_label_variants': copied,
            'outcome_and_activation_cancellation_edges_preserved': True}


def prepare_scene(row, selected, donor):
    doc = read(row['json'])
    ed = Edit(doc)
    r = ed.r
    graph = r.d(r.root['sceneGraph'])
    nodes = {str(r.d(h)['nodeId']['id']): r.d(h) for h in graph['graph']}
    actors = [r.d(h) for h in r.root['actors'] if 'johnny' in r.d(h)['actorName'].lower()]
    assert actors
    aids = {a['actorId']['id'] for a in actors}
    for actor in actors:
        assert actor['acquisitionPlan'] in ('spawnDespawn', 'findInContext')
        for flag in ('isEnabled', 'alwaysSpawned', 'spawnOnStart'):
            actor['spawnDespawnParams'][flag] = 0
    chosen = {str(e['event_id']): e for e in selected}
    removed_speech, removed_presentation, timings, actor_behaviors = [], [], [], []
    for nid, node in nodes.items():
        if 'actorBehaviors' in node:
            removed = [a for a in node['actorBehaviors'] if a['actorId']['id'] in aids]
            if removed:
                actor_behaviors.append({'node': nid, 'removed': copy.deepcopy(removed)})
                node['actorBehaviors'] = [a for a in node['actorBehaviors'] if a not in removed]
        kept, had_selected = [], False
        for h in node.get('events', []):
            event = r.d(h)
            event_id = str(event['id']['id'])
            if event_id in chosen:
                assert event['$type'] == 'scnDialogLineEvent' and str(nid) == str(chosen[event_id]['node_id'])
                removed_speech.append({'node': nid, 'id': event_id, 'speaker': chosen[event_id]['speaker_role'],
                                       'payload': r.clean(event)})
                had_selected = True
            elif event['$type'] != 'scnDialogLineEvent' and actor_reference(r.clean(event), aids):
                removed_presentation.append({'node': nid, 'id': event_id, 'type': event['$type'],
                                             'payload': r.clean(event)})
            else:
                kept.append(h)
        if 'events' in node:
            node['events'] = kept
            # Raymond's actual following/investigation and NPC pacing stay authored.
            if had_selected and 'mq040' not in row['depot']:
                change = compress_section(node, r)
                if change['before_ms'] != change['after_ms'] or change['shifted_events']:
                    timings.append({'node': nid, **change})
    assert {e['id'] for e in removed_speech} == set(chosen)
    before_edges = {nid: copy.deepcopy(n['outputSockets']) for nid, n in nodes.items()}
    bypass = {}
    reasons = {}

    def d(nid, ordinal=0, name=0):
        return api.destination(int(nid), ordinal, name)

    def outs(nid):
        sockets = [s for s in nodes[str(nid)]['outputSockets'] if s['destinations']]
        assert len(sockets) <= 1, (row['depot'], nid, sockets)
        return copy.deepcopy(sockets[0]['destinations']) if sockets else []

    def skip(nid, targets=None, reason='Absent Johnny actor operation'):
        nid = str(nid)
        bypass[nid] = outs(nid) if targets is None else [d(*t) for t in targets]
        reasons[nid] = reason

    def set_out(nid, stamp, targets):
        socket, = [s for s in nodes[str(nid)]['outputSockets']
                   if (s['stamp']['name'], s['stamp']['ordinal']) == stamp]
        socket['destinations'] = [d(*t) for t in targets]

    def timer(nid, ms):
        q = r.d(nodes[str(nid)]['questNode'])
        assert q['$type'] == 'questPauseConditionNodeDefinition'
        q['condition'] = ed.h({'$type': 'questTimeCondition', 'type': ed.h({
            '$type': 'questRealtimeDelay_ConditionType', 'hours': 0, 'miliseconds': ms, 'minutes': 0, 'seconds': 0})})
        bypass.pop(str(nid), None)
        reasons.pop(str(nid), None)

    allowed_actor_ops = {'questUseWorkspotNodeDefinition', 'questPauseConditionNodeDefinition',
                         'questPuppetAIManagerNodeDefinition', 'questFXManagerNodeDefinition',
                         'questSpawnManagerNodeDefinition', 'questTeleportPuppetNodeDefinition',
                         'questMovePuppetNodeDefinition', 'questVehicleNodeDefinition'}
    for nid, n in nodes.items():
        if n['$type'] != 'scnQuestNode':
            continue
        q = r.d(n['questNode'])
        clean = r.clean(q)
        if actor_reference(clean, aids):
            assert q['$type'] in allowed_actor_ops, (nid, q['$type'])
            skip(nid)
        if q['$type'] == 'questJournalNodeDefinition':
            paths = [x['realPath'] for x in walk(clean) if x.get('$type') == 'gameJournalPath']
            if any('johnny' in p.lower() or 'talk_jonny' in p.lower() for p in paths):
                skip(nid, reason='Bypass removed Talk to Johnny objective; native continuation retained')

    explicit = []
    basename = row['depot'].split('\\')[-1]
    bot_choice = None
    if basename == 'mq029_01a_garage.scene':
        set_out(80, (0, 0), [(25, 1)])
        timer(32, 50)
        set_out(25, (0, 0), [(62, 1), (32, 1)])
        set_out(32, (0, 0), [(2, 0)])
        explicit.append('Destroyed-bike inspection: retained V inspection bark/delay -> native clue INSPECTED callback -> unblock content -> 50ms -> original terminating exit. Photo route unchanged.')
    elif basename == 'mq029_01b_josie_body.scene':
        set_out(1, (0, 0), [(2, 0)])
        explicit.append('Body clue entry reaches original nonterminating exit directly. Read-note entry, player choice and message-box exit unchanged.')
    elif basename == 'mq017_streetkid_01a_johnny.scene':
        for nid, node in nodes.items():
            if node['$type'] == 'scnStartNode':
                set_out(nid, (0, 0), [(2, 0)])
        explicit.append('Skip whole early Johnny exchange to the existing End0 callback; the parent phase continues to Kirk.')
    elif basename == 'mq017_streetkid_03_confront_thugs.scene':
        skip(507, [(184, 0)], 'Truck opened -> retain V situation reaction, then native Return to Kirk continuation; no Johnny/world-position wait')
        skip(1024, [(1311, 3)], 'Native post-fight completion replaces final Johnny-only exchange')
        for nid in (922, 1924, 2242):
            skip(nid, [], 'Discard Johnny presentation-only receipt/auxiliary branch; do not fabricate actor acknowledgement')
        set_out(1927, (0, 0), [(1921, 0)])
        explicit.append('Preserve opening the truck, V clothes reaction, return-to-Kirk, NPC confrontation, native combat outcomes and completion. Old Johnny-comment receipt cannot hold the post-encounter barrier.')
    elif basename == 'mq042_nomad_02_car_found.scene':
        skip(561, [], 'Leave-car ending waits for native player exit animation, not a Johnny conversation')
        skip(781, [], 'No empty Talk to Johnny objective after player enters the car')
        timer(771, 50)
        set_out(771, (0, 0), [(107, 1)])
        set_out(107, (0, 0), [(2, 0), (658, 1), (660, 1)])
        assert [(v['nodeId']['id'], v['isockStamp']['ordinal']) for v in next(s for s in nodes['992']['outputSockets'] if s['stamp']['name'] == 5)['destinations']] == [(1000, 1)]
        set_out(992, (5, 0), [(1000, 1), (771, 1)])
        explicit.append('Buy/take paths preserve driver-mount, UI and VehicleFPP restriction cleanup. Leave-car path completes only after section992 native V exit/unmount/control transition plus one tick; Lana actions stay authored.')
    elif basename == 'mq018_05_brooklyn.scene':
        skip(71, [(77, 0)], 'Remove two Johnny dialogue options; join authored router-stage cleanup')
    elif basename == 'mq018_06_solar.scene':
        skip(78, [(394, 0)], 'Remove two Johnny dialogue options; join authored router-stage cleanup')
    elif basename == 'mq018_07_protein.scene':
        skip(82, [(88, 0)], 'Remove two Johnny dialogue options; join authored router-stage cleanup')
    elif basename == 'mq018_02_fortuneteller.scene':
        skip(109, [(932, 1)], 'Skip two Johnny options through useful original bot-interaction branch; preserve native socket callbacks')
        bot_choice = neutral_bot_choice(r, nodes, donor)
        explicit.append('Bot leave-connected option1026 moves from Johnny position/title to bot relay and neutral native [Leave] text. Activation, cancellation, hacking prerequisites and three original outcome routes remain.')

    # Resolve incoming edges through removed nodes. A cancellation is never an
    # activation: forwarding it would prematurely finish quests or device hacks.
    dropped_cancellations = []
    def resolve(dest, stack=()):
        nid = str(dest['nodeId']['id'])
        if nid not in bypass:
            return [dest]
        assert nid not in stack, ('Bypass cycle', nid, stack)
        node = nodes[nid]
        stamp = dest['isockStamp']
        if node['$type'] == 'scnQuestNode':
            mappings = node['isockMappings']
            ordinal = stamp['ordinal']
            cut = stamp['name'] == 1026 or (ordinal < len(mappings) and mappings[ordinal]['$value'] == 'CutDestination')
        elif node['$type'] == 'scnChoiceNode':
            cut = (stamp['name'], stamp['ordinal']) != (0, 0)
        else:
            raise AssertionError((nid, node['$type']))
        if cut:
            dropped_cancellations.append({'destination': copy.deepcopy(dest), 'reason': 'Removed-node cancellation does not signal its continuation'})
            return []
        result = []
        for target in bypass[nid]:
            result.extend(resolve(copy.deepcopy(target), stack + (nid,)))
        return result

    for nid, node in nodes.items():
        for socket in node['outputSockets']:
            # No stale destinations even in serialized but now dormant nodes.
            after = []
            for dest in socket['destinations']:
                after.extend(resolve(dest))
            unique = []
            for dest in after:
                if dest not in unique:
                    unique.append(dest)
            socket['destinations'] = unique
    rewires = [{'node': nid, 'before': old, 'after': copy.deepcopy(nodes[nid]['outputSockets'])}
               for nid, old in before_edges.items() if old != nodes[nid]['outputSockets']]
    removed_ids = {e['id'] for e in removed_speech + removed_presentation}
    api.cleanup_event_ids(doc, removed_ids)
    current = Resource(doc)
    current.handles = r.handles | current.handles
    edited = api.ordered(doc, current)
    model = Resource(edited).normalize()
    assert not model['errors'], model['errors']
    assert set(model['graphs']['scene']['nodes']) == set(nodes)
    return edited, {'johnny_actor_ids': sorted(aids), 'disabled_actors': [a['actorName'] for a in actors],
                    'removed_speech': removed_speech, 'removed_presentation': removed_presentation,
                    'removed_actor_behaviors': actor_behaviors, 'timings': timings, 'rewires': rewires,
                    'bypassed_nodes': [{'node': n, 'targets': t, 'reason': reasons[n]} for n, t in bypass.items()],
                    'dropped_cancellations': dropped_cancellations, 'explicit_contracts': explicit,
                    'neutral_bot_choice': bot_choice,
                    'interruption_scenarios_and_phase_callers_unchanged': True}


def prepare_cleanup_phase(row):
    doc = read(row['json'])
    ed = Edit(doc)
    node = ed.node(ed.graph('root/4'), 6)
    before = ed.r.clean(node['condition'])
    assert node['$type'] == 'questPauseConditionNodeDefinition'
    assert before['type']['$type'] == 'questCameraFocus_ConditionType'
    assert before['type']['objectRef']['reference']['$value'] == '#johnny'
    node['condition'] = ed.h({'$type': 'questTimeCondition', 'type': ed.h({
        '$type': 'questRealtimeDelay_ConditionType', 'hours': 0, 'miliseconds': 50, 'minutes': 0, 'seconds': 0})})
    current = Resource(doc)
    current.handles = ed.r.handles | current.handles
    result = api.ordered(doc, current)
    assert not Resource(result).normalize()['errors']
    return result, {'graph': 'root/4', 'node': '6', 'before_condition': before, 'delay_ms': 50,
                    'reason': 'Native post-encounter cleanup must not wait for camera focus on absent Johnny. Retain native deactivation, crowd release, both vehicle-distance waits, both AND barriers and checkpoint.',
                    'edge_changes': 0, 'prefab_changes': 0, 'reward_changes': 0}


def main():
    assert not OUT.exists() and not INPUT.exists()
    capture_path = HERE / 'source_01/manifest.json'
    capture = read(capture_path)
    assert capture['status'] == 'PASS_JB1_CURRENT_AND_TEXT_DONOR_PROVIDERS' and not capture['issues']
    sources = {row['depot']: row for row in capture['resources'] if row['scope'] == 'CURRENT_PRIVATE'}
    donor_row, = [row for row in capture['resources'] if row['scope'] == 'NATIVE_TEXT_DONOR']
    assert sha(donor_row['json']) == donor_row['json_sha256'] and sha(donor_row['raw']) == donor_row['sha256']
    donor = Resource(read(donor_row['json']))
    selections_path = HERE / 'analysis_02/approved_speech.json'
    selected = read(selections_path)['events']
    by_depot = collections.defaultdict(list)
    for event in selected:
        by_depot[event['depot']].append(event)
    assert len(selected) == 150 and len(by_depot) == 12
    installed = read(INSTALLED)
    game = Path(installed['game_root'])
    for row in installed['core_files'] + installed['required_files']:
        assert sha(game / row['path']) == row['sha256'], row['path']
    baseline = read(BASE / 'package_manifest.json')
    assert len(baseline['source_resources']) == 1581 and len(baseline['files']) == 51
    for depot, digest in baseline['source_resources'].items():
        p = BASE / 'archive_source' / depot
        assert not (p.stat().st_file_attributes & 0x400) and sha(p) == digest, depot
    OUT.mkdir()
    shutil.copytree(BASE / 'archive_source', OUT / 'archive_source')
    for row in baseline['files']:
        assert sha(BASE / 'package' / row['path']) == row['sha256']
        if row['path'] == ARCHIVE:
            continue
        target = OUT / 'package' / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASE / 'package' / row['path'], target)
    INPUT.mkdir()
    edits = []
    for depot, events in sorted(by_depot.items()):
        row = sources[depot]
        assert sha(row['raw']) == row['sha256'] == baseline['source_resources'][depot]
        assert sha(row['json']) == row['json_sha256']
        doc, changes = prepare_scene(row, events, donor)
        path = INPUT / (str(len(edits)).zfill(2) + '.json')
        write(path, doc)
        edits.append({'depot': depot, 'source': row, 'edited_json': str(path),
                      'edited_json_sha256': sha(path), 'changes': changes})
    cleanup, = [d for d in sources if d.endswith('mq017_streetkid_00_main.questphase')]
    row = sources[cleanup]
    assert sha(row['raw']) == row['sha256'] == baseline['source_resources'][cleanup]
    assert sha(row['json']) == row['json_sha256']
    doc, changes = prepare_cleanup_phase(row)
    path = INPUT / '12.json'
    write(path, doc)
    edits.append({'depot': cleanup, 'source': row, 'edited_json': str(path),
                  'edited_json_sha256': sha(path), 'changes': changes})
    plan = {'schema': 1, 'epoch': 'JB1', 'predecessor': 'SD1', 'candidate': str(OUT),
            'authorization': 'Current user five-quest removal/rewire notes, all seventeen additions and explicit Raymond V-reply approval.',
            'scope': '150 approved dialogue events and their Johnny-only presentation/menus/dependencies in twelve private scenes, plus one absent-actor camera wait in the native private Small Man cleanup phase. Preserve native gameplay, NPC pacing, earned choices, outcomes and IDs.',
            'installed_baseline': str(INSTALLED), 'installed_baseline_sha256': sha(INSTALLED),
            'baseline_package': str(BASE / 'package_manifest.json'), 'baseline_package_sha256': sha(BASE / 'package_manifest.json'),
            'source_capture': str(capture_path), 'source_capture_sha256': sha(capture_path),
            'approved_speech': str(selections_path), 'approved_speech_sha256': sha(selections_path),
            'edits': edits, 'native_text_donor': donor_row, 'archive_payloads': 1581,
            'new_depots': 0, 'new_ArchiveXL_phase_ids': 0, 'scripts_changed': [],
            'quest_resets': 0, 'save_writes': 0, 'game_writes': 0, 'installed': False,
            'saved_stage_scope': 'Prospective resource update before the affected scenes. No reset/replay and no certification of upgrading an already-running saved scene.'}
    write(INPUT / 'plan.json', plan)
    cp = read(HERE / 'checkpoint.json')
    cp.update(status='AUTHORED_PENDING_COOK_AND_INDEPENDENT_VERIFICATION', candidate='candidate_04',
              plan='input_04/plan.json', edited_resources=len(edits), deployment_status='NOT_PREPARED')
    (HERE / 'checkpoint.json').write_text(json.dumps(cp, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'resources': len(edits), 'speech_cuts': sum(len(e['changes'].get('removed_speech', [])) for e in edits),
                      'presentation_cuts': sum(len(e['changes'].get('removed_presentation', [])) for e in edits),
                      'section_timings': sum(len(e['changes'].get('timings', [])) for e in edits),
                      'scripts_changed': 0, 'game_writes': 0, 'save_writes': 0}))


if __name__ == '__main__':
    main()
