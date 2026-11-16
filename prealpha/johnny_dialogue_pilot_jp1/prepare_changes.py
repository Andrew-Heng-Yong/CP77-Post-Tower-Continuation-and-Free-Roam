"""Prepare the user-approved two-quest JP1 scene delta on the exact HH1 baseline."""
import copy
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
HH1 = WS / 'prealpha/heavy_hearts_hh1'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
EXPECTED_NOTES = '1CCD7D05B00AB66F731D906607B40C52964E7FA58188AE467E3C55579598A66B'
FREEZER = '90c76218185ecad8483a5352'
AFTERLIFE = '2d49b0f9bcf9127de6fb95e7'
SCAV = 'f5f09f0d05a46385941a20d0'
# Exact matches were reviewed against speaker, quest, scene, full variants and branch.
MATCHES = [
    (23, FREEZER, '28', 3), (24, FREEZER, '28', 8), (25, FREEZER, '82', 1),
    (26, FREEZER, '82', 3), (27, FREEZER, '42', 2), (28, FREEZER, '42', 5),
    (29, FREEZER, '284', 0), (30, FREEZER, '284', 3), (33, FREEZER, '90', 1),
    (35, FREEZER, '93', 2), (36, FREEZER, '90', 2), (37, FREEZER, '98', 1),
    (38, FREEZER, '98', 3), (39, FREEZER, '108', 1), (40, FREEZER, '108', 3),
    (43, AFTERLIFE, '916', 1), (44, AFTERLIFE, '64', 11),
    (57, SCAV, '3', 5), (58, SCAV, '3', 21), (59, SCAV, '3', 27),
    (60, SCAV, '21', 4), (61, SCAV, '21', 6), (62, SCAV, '28', 3), (63, SCAV, '28', 5),
]
AI_V_CUTS = [
    (FREEZER, '85', 1, 'Direct question to Johnny after he identifies Bartmoss.'),
    (FREEZER, '93', 1, 'Direct objection to Johnny\'s proposal to search the freezer.'),
    (FREEZER, '106', 1, 'Explicitly asks Johnny for agreement about consulting Nix; the native Nix objective is retained.'),
    (FREEZER, '116', 0, 'Direct reply to Johnny\'s encouragement to contact Nix.'),
    (AFTERLIFE, '916', 2, 'Dismissive response immediately after Johnny\'s warning about jacking in.'),
    (AFTERLIFE, '981', 2, 'Explicitly tells Johnny to shut up.'),
]
sys.path.insert(0, str(WS / 'tools/parity_audit'))
from model import Resource


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), path
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def files(root):
    root = Path(root).resolve()
    pending = [root]
    found = {}
    while pending:
        folder = pending.pop()
        for e in os.scandir(folder):
            stat = e.stat(follow_symlinks=False)
            assert not getattr(stat, 'st_file_attributes', 0) & 0x400, e.path
            p = Path(e.path)
            assert p.resolve().is_relative_to(root), p
            if e.is_dir(follow_symlinks=False):
                pending.append(p)
            else:
                found[p.relative_to(root).as_posix()] = p
    return found


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for child in obj.values():
            yield from walk(child)
    elif isinstance(obj, list):
        for child in obj:
            yield from walk(child)


def clean_references(obj, ids, counts):
    if isinstance(obj, dict):
        for value in obj.values():
            clean_references(value, ids, counts)
    elif isinstance(obj, list):
        kept = []
        for value in obj:
            if isinstance(value, dict) and value.get('$type') == 'scnSceneEventId' and str(value.get('id')) in ids:
                counts['event_id_references_removed'] += 1
                continue
            clean_references(value, ids, counts)
            if isinstance(value, dict) and value.get('$type') == 'scnSceneEventSymbol' and not value.get('sceneEventIds'):
                counts['empty_debug_symbols_removed'] += 1
                continue
            kept.append(value)
        obj[:] = kept


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', required=True, choices=['02', '03', '04'])
    revision = parser.parse_args().revision
    input_dir, source_dir, edit_dir, candidate_dir = [name + '_' + revision for name in ('input', 'source', 'edit', 'candidate')]
    for folder in (input_dir, source_dir, edit_dir, candidate_dir):
        assert not (HERE / folder).exists(), 'Use a fresh successor: ' + folder
    installed_path = HH1 / 'deployment_01/installed_manifest_01.json'
    installed = read(installed_path)
    assert installed['core_epoch'] == 'HH1' and installed['archive_payloads'] == 1581
    game = Path(installed['game_root'])
    assert len(installed['core_files']) == 51 and len(installed['required_files']) == 26
    for row in installed['core_files'] + installed['required_files']:
        assert sha(game / row['path']) == row['sha256'], row['path']
    old = read(HH1 / 'candidate_01/package_manifest.json')
    assert old['files'] == installed['core_files'] and len(old['source_resources']) == 1581
    notes = WS / 'prealpha/johnny_video_review_20261107_01/intake_01/user_notes_received.txt'
    assert sha(notes) == EXPECTED_NOTES
    source_review = WS / 'prealpha/johnny_dialogue_review_20261107_02/evidence_05/review_manifest.json'
    review = read(source_review)
    indexed_items = {x['event_key']: x for x in review['items']}
    source_resources = {s['resource']['resource_id']: s['resource'] for q in review['quests'] for s in q['scenes']}
    note_lines = notes.read_text(encoding='utf-8-sig').splitlines()
    selected = []
    for line_number, rid, node, ordinal in MATCHES:
        key = f'{rid}/root/scene/{node}/event/{ordinal}'
        item = copy.deepcopy(indexed_items[key])
        note = note_lines[line_number - 1]
        prefix = note.strip().split(':', 1)[0]
        assert item['speaker'] == ('V' if prefix == 'V' else 'Johnny'), (line_number, note)
        item.update(note_line=line_number, user_note=note, status='USER_REQUESTED_MATCHED_EXACT_EVENT',
                    observed_voice='male' if rid == SCAV else 'female',
                    edit_scope='Full selected event; both V variants share the event. No unlisted speech is selected.')
        selected.append(item)
    assert len(selected) == len({x['event_key'] for x in selected}) == 24
    selected_keys = {x['event_key'] for x in selected}
    for q in review['quests']:
        if q['id'] not in ('mq016_bartmoss', 'mq036_overload'):
            continue
        for r in q['review_items']:
            if r['target'] in selected_keys:
                continue
            item = copy.deepcopy(indexed_items[r['target']])
            assert item['speaker'] == 'Johnny'
            item.update(status='USER_APPROVED_ADDITIONAL_JOHNNY_LINE',
                        authority='User: ok remove these too ... proceed to implementation',
                        edit_scope='Full spoken event; all remaining Johnny speech in the two qualified quest closures.')
            selected.append(item)
            selected_keys.add(item['event_key'])
    for rid, node, ordinal, reason in AI_V_CUTS:
        key = f'{rid}/root/scene/{node}/event/{ordinal}'
        item = copy.deepcopy(indexed_items[key])
        assert item['speaker'] == 'V' and key not in selected_keys
        item.update(status='AI_SELECTED_DIRECT_REPLY_AUTHORIZED_BY_USER', classification_reason=reason,
                    authority='User authorized removing V reactions to Johnny while retaining reactions to the situation.',
                    edit_scope='Full event and both V wording variants.')
        selected.append(item)
        selected_keys.add(key)
    assert len(selected) == 37 and sum(x['speaker'] == 'Johnny' for x in selected) == 25
    con = sqlite3.connect((WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3').as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    options = []
    for line_number, menu, option_id in [(32, '88', '514'), (34, '88', '770'), (None, '40', '2'), (None, '40', '258')]:
        choice = dict(con.execute("select * from choices where root_id=? and node_id=? and option_id=?", (FREEZER + '/root', menu, option_id)).fetchone())
        text = [r[0] for r in con.execute("select text from localization where root_id=? and loc_id=? and locale='en_us' and text<>''", (FREEZER + '/root', choice['loc_id']))]
        assert len(set(text)) == 1
        options.append({'note_line': line_number, 'user_note': note_lines[line_number - 1] if line_number else 'User-added Bartmoss identification menu; approved with the additional Johnny exchange cuts.',
                        'source_choice': choice, 'text': text[0],
                        'status': 'USER_REQUESTED_OPTION_REMOVED_FROM_NORMAL_FLOW_BY_MENU_BYPASS'})
    source_root = HH1 / 'candidate_01/archive_source'
    source_files = files(source_root)
    expected = {Path(k).as_posix(): v for k, v in old['source_resources'].items()}
    assert set(source_files) == set(expected)
    candidate = HERE / candidate_dir
    for rel, path in source_files.items():
        assert sha(path) == expected[rel], rel
        dest = candidate / 'archive_source' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    for row in old['files']:
        path = HH1 / 'candidate_01/package' / row['path']
        assert sha(path) == row['sha256'], path
        if row['path'] == ARCHIVE:
            continue
        dest = candidate / 'package' / row['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    (HERE / input_dir).mkdir()
    shutil.copyfile(notes, HERE / input_dir / 'user_notes.txt')
    edits = []
    for rid in (FREEZER, AFTERLIFE, SCAV):
        resource = source_resources[rid]
        assert sha(resource['raw_path']) == resource['raw_sha256']
        assert sha(resource['json_path']) == resource['json_sha256']
        doc = read(resource['json_path'])
        raw = Resource(doc)
        targets = [x for x in selected if x['event']['root_id'] == rid + '/root']
        event_ids = {x['event']['event_id'] for x in targets}
        graph = raw.d(raw.root['sceneGraph'])
        removed = []
        durations = []
        rewire = []
        for handle in graph['graph']:
            node = raw.d(handle)
            node_id = str(node['nodeId']['id'])
            source_events = node.get('events', [])
            dead = [h for h in source_events if str((raw.d(h) or {}).get('id', {}).get('id')) in event_ids]
            if dead:
                data = [raw.d(h) for h in source_events]
                end = max(float(e.get('startTime', 0)) + float(e.get('duration', 0)) for e in data)
                section_duration = float(node.get('sectionDuration', {}).get('stu', 0))
                assert section_duration > 0 and section_duration >= end, (node_id, section_duration, end)
                durations.append({'node': node_id, 'section_duration': section_duration, 'before_max_event_end': end})
                for h in dead:
                    event = raw.d(h)
                    assert event['$type'] == 'scnDialogLineEvent'
                    removed.append(str(event['id']['id']))
                node['events'] = [h for h in source_events if h not in dead]
            if rid == FREEZER and node_id in ('28', '284'):
                output_name, old_target, new_target = (2, 40, 42) if node_id == '28' else (0, 88, 90)
                socket, = [s for s in node['outputSockets'] if s.get('stamp', {}).get('name', 0) == output_name and s.get('stamp', {}).get('ordinal', 0) == 0]
                destination, = socket['destinations']
                assert destination['nodeId']['id'] == old_target and destination['isockStamp'] == {'$type': 'scnInputSocketStamp', 'name': 0, 'ordinal': 0}
                before = copy.deepcopy(destination)
                destination['nodeId']['id'] = new_target
                rewire.append({'node': node_id, 'output_stamp': f'{output_name}:0', 'before': before, 'after': copy.deepcopy(destination),
                               'reason': 'Skip Johnny identification dialogue without changing existing recognition history.' if node_id == '28' else 'Skip Johnny menu through the native exit section, retaining its callbacks and Open path.'})
        assert set(removed) == event_ids and len(removed) == len(event_ids)
        counts = {'event_id_references_removed': 0, 'empty_debug_symbols_removed': 0}
        clean_references(raw.root['sceneGraph'], event_ids, counts)
        clean_references(raw.root['debugSymbols'], event_ids, counts)
        assert not [n for n in walk(raw.root) if n.get('$type') == 'scnSceneEventId' and str(n.get('id')) in event_ids]
        definitions = {str(n['HandleId']) for n in walk(doc) if 'HandleId' in n and 'Data' in n}
        references = {str(n['HandleRefId']) for n in walk(doc) if 'HandleRefId' in n}
        assert references <= definitions | {'-1'}, references - definitions
        source_json = HERE / source_dir / (rid + '.json')
        source_json.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resource['json_path'], source_json)
        edited_json = HERE / edit_dir / (rid + '.json')
        write(edited_json, doc)
        edits.append({'resource': resource, 'source_json': str(source_json), 'edited_json': str(edited_json),
                      'edited_json_sha256': sha(edited_json), 'removed_event_ids': sorted(event_ids),
                      'durations': durations, 'reference_cleanup': counts, 'rewire': rewire})
    unlisted = [indexed_items[r['target']] for q in review['quests'] if q['id'] in ('mq016_bartmoss', 'mq036_overload')
                for r in q['review_items'] if r['target'] not in {x['event_key'] for x in selected}]
    assert not unlisted
    v_review = []
    for q in review['quests']:
        if q['id'] not in ('mq016_bartmoss', 'mq036_overload'):
            continue
        for scene in q['scenes']:
            rid = scene['resource']['resource_id']
            for row in con.execute("select item_key,node_id,speaker,addressee,text from search_items where resource_id=? and kind='DIALOGUE_EVENT' and speaker_role='V'", (rid,)):
                data = dict(row)
                selection = next((x for x in selected if x['event_key'] == data['item_key']), None)
                data['decision'] = selection['status'] if selection else 'KEEP_SITUATION_OR_NPC_DIALOGUE'
                if selection and selection.get('classification_reason'):
                    data['reason'] = selection['classification_reason']
                elif not selection:
                    data['reason'] = 'Independent observation, self-directed situational response, or conversation with Nix/Stefan; addressee metadata alone does not make it a Johnny reaction.'
                v_review.append(data)
    write(HERE / input_dir / 'plan.json', {
        'schema': 1, 'epoch': 'JP1', 'predecessor': 'HH1',
        'revision': revision, 'candidate_directory': str(candidate),
        'authorization': 'User resumed implementation, approved the seven omitted Johnny lines and delegated additional V-to-Johnny reaction cuts, preserving situational responses.',
        'notes_sha256': EXPECTED_NOTES, 'installed_baseline': str(installed_path), 'installed_baseline_sha256': sha(installed_path),
        'baseline_package': str(HH1 / 'candidate_01/package_manifest.json'), 'baseline_package_sha256': sha(HH1 / 'candidate_01/package_manifest.json'),
        'dialogue_selections': selected, 'option_selections': options, 'edits': edits,
        'v_dialogue_classification': v_review,
        'recognition_policy': 'Bypass choice 40 directly to shared section 42; preserve the existing mq016_recognized_bartmoss value. No fabricated recognition, acknowledgement, inventory or reward fact.',
        'unlisted_johnny_events_pending_review': unlisted,
        'pickup_requirement': 'Preserve native Open and Take cyberdeck choices, conditions, controls and pickup/reward ownership; no inventory grant or forced fact.',
        'saved_scene_limit': 'Node/field/resource/event identities retained. Saves already inside bypassed menus 40/88 need separate transition qualification; test before entering the affected scene.',
        'timing_policy': 'Preserve fixed authored section duration and all unselected events/callbacks for this first pilot.',
        'source_resources': old['source_resources'], 'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'status': 'JP1_SCENE_EDITS_PREPARED_NOT_COOKED', 'spoken_events': len(selected), 'options_bypassed': len(options),
                      'scene_payloads': len(edits), 'unchanged_source_payloads': 1578, 'unlisted_johnny_pending': len(unlisted)}, indent=2))


if __name__ == '__main__':
    main()
