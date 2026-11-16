"""Prepare a PE1 successor for KOLD MIRAGE's actor-free native interaction flow."""
from pathlib import Path
from collections import Counter
import copy
import hashlib
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
PREDECESSOR = WS/'prealpha/prepared_encounters_pe1'
BASE = PREDECESSOR/'candidate_02'
OUT = HERE/'candidate_02'
INSTALLED = PREDECESSOR/'deployment_01/installed_manifest_01.json'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
PREFIX = 'towercontinued\\sidejobs_s29\\native\\base\\quest\\minor_quests\\mq016\\'
FREEZER = PREFIX+'scenes\\mq016_01_freezer.scene'
AFTERLIFE = PREFIX+'scenes\\mq016_02_afterlife.scene'
PHASE = PREFIX+'phases\\mq016_01_freezer.questphase'
sys.path.insert(0, str(WS/'tools/parity_audit'))
from model import Resource
from common import walk


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()


def write(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


def ordered(doc, resource):
    """Retain shared handle definitions even if their first event was removed."""
    seen = set()
    def visit(value):
        if isinstance(value, list):
            return [visit(child) for child in value]
        if not isinstance(value, dict):
            return value
        if 'HandleId' in value or 'HandleRefId' in value:
            key = resource.hid(value)
            if key not in resource.handles:
                return copy.deepcopy(value)
            if key in seen:
                return {'HandleRefId': key}
            seen.add(key)
            return {'HandleId': key, 'Data': visit(resource.handles[key])}
        return {key: visit(child) for key, child in value.items()}
    return visit(doc)


def cleanup_event_ids(value, removed):
    if isinstance(value, dict):
        for child in value.values():
            cleanup_event_ids(child, removed)
    elif isinstance(value, list):
        kept = []
        for child in value:
            if isinstance(child, dict) and child.get('$type') == 'scnSceneEventId' and str(child.get('id')) in removed:
                continue
            cleanup_event_ids(child, removed)
            if isinstance(child, dict) and child.get('$type') == 'scnSceneEventSymbol' and not child.get('sceneEventIds'):
                continue
            kept.append(child)
        value[:] = kept


def destination(node, ordinal=1, name=0):
    return {'$type': 'scnInputSocketId', 'isockStamp': {'$type': 'scnInputSocketStamp', 'name': name, 'ordinal': ordinal}, 'nodeId': {'$type': 'scnNodeId', 'id': node}}


def prepare_scene(row, name):
    doc = read(row['json'])
    r = Resource(doc)
    actor_id = 0 if name == FREEZER else 1
    performer_id = (actor_id << 8) | 1
    actor, = [r.d(a) for a in r.root['actors'] if r.d(a)['actorId']['id'] == actor_id]
    assert actor['actorName'] == 'johnny' and actor['acquisitionPlan'] == 'spawnDespawn'
    original_actor = r.clean(actor)
    for flag in ['isEnabled', 'alwaysSpawned', 'spawnOnStart']:
        actor['spawnDespawnParams'][flag] = 0
    graph = r.d(r.root['sceneGraph'])
    nodes = {str(r.d(h)['nodeId']['id']): r.d(h) for h in graph['graph']}
    removed = []
    modified = []
    def set_dest(nid, stamp, targets):
        node = nodes[str(nid)]
        socket, = [s for s in node['outputSockets'] if (s['stamp']['name'], s['stamp']['ordinal']) == stamp]
        old = copy.deepcopy(socket['destinations'])
        socket['destinations'] = [destination(*target) for target in targets]
        modified.append({'node': str(nid), 'output_stamp': list(stamp), 'before': old, 'after': copy.deepcopy(socket['destinations'])})
    for nid, node in nodes.items():
        if 'actorBehaviors' in node:
            node['actorBehaviors'] = [a for a in node['actorBehaviors'] if a['actorId']['id'] != actor_id]
        events = []
        for handle in node.get('events', []):
            event = r.d(handle)
            payload = r.clean(event)
            refs = [v for v in walk(payload) if v.get('$type') in ['scnActorId', 'scnPerformerId']]
            johnny = any(v['id'] == (actor_id if v['$type'] == 'scnActorId' else performer_id) for v in refs)
            keep = not johnny
            if name == FREEZER and nid in ['28', '101']:
                keep = event['$type'] == 'scnDialogLineEvent'
            if not keep:
                removed.append({'node': nid, 'id': str(event['id']['id']), 'type': event['$type'], 'reason': 'JOHNNY_PRESENTATION_OR_TARGET' if johnny else 'REMOVED_JOHNNY_WORKSPOT_CALLBACK'})
            else:
                events.append(handle)
        if 'events' in node:
            node['events'] = events
    duration_changes = []
    if name == FREEZER:
        # Open and prepare native scanning immediately. V's retained situational
        # reaction is a parallel bark, never a prerequisite for scanning.
        set_dest(654, (0, 0), [(47, 1), (28, 0)])
        for socket in nodes['28']['outputSockets']:
            set_dest(28, (socket['stamp']['name'], socket['stamp']['ordinal']), [])
        # Preserve native scan/focus alternatives and XOR, then the existing
        # recognition-conditioned V observation alongside the Take interaction.
        set_dest(174, (0, 0), [(308, 3), (542, 1)])
        set_dest(308, (0, 0), [(457, 1), (620, 0)])
        set_dest(620, (0, 0), [(155, 1)])
        set_dest(542, (0, 0), [])
        set_dest(101, (0, 0), [])
        # Native item grant stays behind the original single-choice Take option.
        # Its existing automatic-close branch replaces the extra Close prompt.
        set_dest(490, (0, 0), [(215, 1), (557, 1)])
        set_dest(280, (0, 0), [(428, 1), (657, 1)])
        for nid in ['28', '101']:
            node = nodes[nid]
            before = node['sectionDuration']['stu']
            after = max(r.d(e)['startTime'] + r.d(e)['duration'] for e in node['events'])
            node['sectionDuration']['stu'] = after
            duration_changes.append({'node': nid, 'before': before, 'after': after, 'reason': 'Retained V bark only; its completion has no progression output.'})
        scenario, = r.root['interruptionScenarios']
        assert scenario['id']['id'] == 0 and scenario['enabled'] == 1
        scenario['enabled'] = 0
    else:
        johnny_nodes = {'646', '650', '777', '780', '783', '785'}
        for nid, node in nodes.items():
            q = r.clean(node.get('questNode'))
            if nid in johnny_nodes:
                assert q and 'a_mq016_02_afterlife_johnny' in json.dumps(q)
        for nid, node in nodes.items():
            for socket in node.get('outputSockets', []):
                old = copy.deepcopy(socket['destinations'])
                socket['destinations'] = [d for d in old if str(d['nodeId']['id']) not in johnny_nodes]
                if socket['destinations'] != old:
                    modified.append({'node': nid, 'output_stamp': [socket['stamp']['name'], socket['stamp']['ordinal']], 'before': old, 'after': copy.deepcopy(socket['destinations'])})
        for nid in ['916', '981']:
            node = nodes[nid]
            assert len(node['events']) == 1 and r.d(node['events'][0])['$type'] == 'scnDialogLineEvent'
            before = node['sectionDuration']['stu']
            after = r.d(node['events'][0])['startTime'] + r.d(node['events'][0])['duration']
            node['sectionDuration']['stu'] = after
            duration_changes.append({'node': nid, 'before': before, 'after': after, 'reason': 'Nix speech retained; removed Johnny/V-response tail has no callbacks.'})
        # The mixed Nix crisis section 64 already exposes its rescue interactions
        # before the removed Johnny line. Keep Nix's authored animation and timers.
    ids = {e['id'] for e in removed}
    cleanup_event_ids(doc, ids)
    edited = ordered(doc, r)
    model = Resource(edited).normalize()
    assert not model['errors'], model['errors']
    result = {'actor_id': actor_id, 'performer_id': performer_id, 'before_actor': original_actor, 'actor_flags': {'isEnabled': 0, 'alwaysSpawned': 0, 'spawnOnStart': 0}, 'removed_events': removed, 'rewires': modified, 'duration_changes': duration_changes}
    return edited, result


def main():
    assert not OUT.exists() and not (HERE/'input_02').exists()
    manifest = read(INSTALLED)
    game = Path(manifest['game_root'])
    for row in manifest['core_files'] + manifest['required_files']:
        assert sha(game/row['path']) == row['sha256'], row['path']
    source_path = HERE/'source_01/manifest.json'
    capture = read(source_path)
    assert capture['status'] == 'PASS_EXACT_KM2_CURRENT_AND_NATIVE_PROVIDERS' and not capture['issues']
    sources = {r['depot']: r for r in capture['resources'] if r['scope'] == 'CURRENT_PRIVATE'}
    baseline = read(BASE/'package_manifest.json')
    for depot, digest in baseline['source_resources'].items():
        path = BASE/'archive_source'/depot
        assert not (path.stat().st_file_attributes & 0x400) and sha(path) == digest, depot
    OUT.mkdir()
    shutil.copytree(BASE/'archive_source', OUT/'archive_source')
    for row in baseline['files']:
        assert sha(BASE/'package'/row['path']) == row['sha256']
        if row['path'] == ARCHIVE:
            continue
        dest = OUT/'package'/row['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASE/'package'/row['path'], dest)
    inp = HERE/'input_02'
    inp.mkdir()
    edits = []
    for depot in [FREEZER, AFTERLIFE, PHASE]:
        row = sources[depot]
        assert sha(row['raw']) == row['sha256'] == baseline['source_resources'][depot]
        assert sha(row['json']) == row['json_sha256']
        if depot != PHASE:
            edited, changes = prepare_scene(row, depot)
        else:
            edited = read(row['json'])
            r = Resource(edited)
            graph = r.d(r.root['graph'])
            node, = [r.d(h) for h in graph['nodes'] if r.d(h)['id'] == 4]
            assert node['$type'] == 'questSceneNodeDefinition' and node['reapplyInterruptionOperationsAfterGameLoad'] == 0
            assert len(node['interruptionOperations']) == 1
            operation = r.d(node['interruptionOperations'][0])
            assert operation['enable'] == 1
            operation['enable'] = 0
            node['reapplyInterruptionOperationsAfterGameLoad'] = 1
            changes = {'node': '4', 'interruption_enable': 0, 'reapply_after_load': 1, 'reason': 'The default speaker-distance interruption has no Johnny speaker. Disable it on initial entry and on restore of the already-running pre-Open scene.'}
        target = inp/(str(len(edits)).zfill(2)+'.json')
        write(target, edited)
        edits.append({'depot': depot, 'source': row, 'edited_json': str(target), 'edited_json_sha256': sha(target), 'changes': changes})
    plan = {'schema': 1, 'epoch': 'KM2', 'predecessor': 'PE1', 'authorization': 'User requested Johnny entity/effects/objective removal and open -> scan -> take -> Nix, and selected a save before first fridge opening.', 'candidate': str(OUT), 'installed_baseline': str(INSTALLED), 'installed_baseline_sha256': sha(INSTALLED), 'baseline_package': str(BASE/'package_manifest.json'), 'baseline_package_sha256': sha(BASE/'package_manifest.json'), 'source_capture': str(source_path), 'source_capture_sha256': sha(source_path), 'edits': edits, 'scripts_changed': [], 'saved_stage_scope': 'User-selected pre-first-opening save, including its existing private Open-choice scene. No restart of native owners, no migration of scenes already beyond first Open, no fact/journal reset.', 'preserved': ['All saved resource/node/option/retained-event IDs', 'All prior JP1 speech cuts and Sweet Dreams bytes', 'V situational freezer barks and Nix dialogue', 'Native scan alternatives, single-choice Take and sole item grant', 'Native Nix objectives, rescue choices, rewards, timing and cleanup', 'PE1/KM1 admissions and all unrelated resources'], 'archive_payloads': 1581, 'new_depots': 0, 'new_ArchiveXL_phase_ids': 0, 'native_resource_overrides': 0, 'new_fact_writers': 0, 'game_writes': 0, 'save_writes': 0, 'gameplay_validation': 'PENDING_USER_TEST'}
    write(inp/'plan.json', plan)
    cp = read(HERE/'checkpoint.json')
    cp.update(status='PREPARED_PENDING_COOK_AND_VERIFICATION', candidate='candidate_02', plan='input_02/plan.json', user_selected_stage='Before the first fridge opening', next_action='Cook/read back three private resources, independently verify actual scene progression and actor suppression, pack/read back, then prepare guarded PE1 successor deployment.')
    (HERE/'checkpoint.json').write_text(json.dumps(cp, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'resources': len(edits), 'events_removed': sum(len(e['changes'].get('removed_events', [])) for e in edits), 'scripts_changed': 0, 'game_writes': 0}))


if __name__ == '__main__':
    main()
