"""Create a source-pinned, editable text pilot. Never changes game resources."""
import gzip
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
DB = WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
RID = 'd188654bc4d684017f46e12d'
ROOT = RID + '/root'
EXPECTED_DB = 'A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E'
sys.path.insert(0, str(WS / 'tools/parity_audit'))
from model import Resource


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def load(path):
    path = Path(path)
    if path.suffix == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8-sig') as stream:
            return json.load(stream)
    return json.loads(path.read_text(encoding='utf-8-sig'))


def pointer(obj, path):
    for key in path.lstrip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    output = TASK / 'output_01'
    qa = TASK / 'qa_01'
    assert not output.exists() and not qa.exists(), 'Use a fresh output revision.'
    baseline = DB.stat()
    assert sha(DB) == EXPECTED_DB, 'Selected index changed.'
    con = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    scene = dict(con.execute('select * from resources where resource_id=?', (RID,)).fetchone())
    resource_model = Resource(load(scene['json_path']))
    normalized = resource_model.normalize()
    assert not normalized['errors'], normalized['errors']
    graph = normalized['graphs']['scene']
    source_checks = []

    def check_source(source):
        for path_key, sha_key in [('raw_path', 'raw_sha256'), ('json_path', 'json_sha256')]:
            actual = sha(source[path_key])
            assert actual == source[sha_key], (path_key, source['depot'], actual)
            source_checks.append({'path': source[path_key], 'sha256': actual})

    check_source(scene)
    raw_lines = {str(x['itemId']['id']): x for x in resource_model.root['screenplayStore']['lines']}
    raw_actors = {str(x['actorId']['id']): x for x in resource_model.root['actors']}
    raw_players = {str(x['actorId']['id']): x for x in resource_model.root['playerActors']}
    provider_cache = {}
    event_cache = {}

    def event(key):
        if key in event_cache:
            return event_cache[key]
        row = dict(con.execute('select * from events where event_key=?', (key,)).fetchone())
        item = dict(con.execute('select * from search_items where item_key=?', (key,)).fetchone())
        raw = graph['nodes'][row['node_id']]['payload']['events'][row['event_ordinal']]
        line = raw_lines[row['line_id']]
        assert raw['$type'] == row['type'] == 'scnDialogLineEvent'
        assert str(raw['id']['id']) == row['event_id']
        assert str(raw['screenplayLineId']['id']) == row['line_id']
        assert str(line['locstringId']['ruid']) == item['loc_id']
        assert str(raw['startTime']) == row['start_time']
        assert str(raw['duration']) == row['duration']
        actor_id = str(line['speaker']['id'])
        if item['speaker'] == 'V':
            assert actor_id in raw_players
        elif item['speaker'] == 'Johnny':
            assert raw_actors[actor_id]['actorName'] == 'Johnny'
        else:
            raise AssertionError(('Unexpected speaker', item['speaker']))
        variants = [dict(r) for r in con.execute(
            "select * from localization where loc_id=? and locale='en_us' and root_id is null",
            (item['loc_id'],))]
        assert variants
        for variant in variants:
            provider_id = variant['provider_resource_id']
            if provider_id not in provider_cache:
                provider = dict(con.execute('select * from resources where resource_id=?', (provider_id,)).fetchone())
                check_source(provider)
                provider_cache[provider_id] = {'resource': provider, 'json': load(provider['json_path'])}
            assert pointer(provider_cache[provider_id]['json'], variant['source_path']) == variant['text']
        by_gender = {v['gender']: v['text'] for v in variants}
        female = by_gender.get('female', '')
        male = by_gender.get('male', '') or female
        assert female and male
        result = {'event_key': key, 'event': row, 'speaker': item['speaker'],
                  'speaker_actor_id': actor_id, 'addressee_actor_id': str(line['addressee']['id']),
                  'gender_mask': line['usage']['playerGenderMask']['mask'],
                  'loc_id': item['loc_id'], 'text_variants': {'female': female, 'male': male},
                  'localization_rows': variants, 'raw_event': raw, 'raw_line': line,
                  'decision': 'PENDING_HUMAN_REVIEW'}
        event_cache[key] = result
        return result

    def section(node):
        rows = con.execute("select event_key from events where root_id=? and node_id=? and type='scnDialogLineEvent' order by cast(start_time as real),event_ordinal", (ROOT, str(node)))
        return [event(row[0]) for row in rows]

    # Choice 825 activates BOTH sections; sorting their authored start times preserves V's reply.
    parallel = section(827) + section(4304)
    parallel.sort(key=lambda e: (float(e['event']['start_time']), e['event']['event_ordinal']))
    assert parallel[0]['speaker'] == 'V'
    assert float(parallel[0]['event']['start_time']) + float(parallel[0]['event']['duration']) <= float(parallel[1]['event']['start_time'])
    timeline = section(635) + parallel + section(854) + section(868) + section(3844) + section(858)
    timeline_keys = [e['event_key'] for e in timeline]
    assert len(timeline_keys) == len(set(timeline_keys))

    # Exact connected route. These are source edges, not a claim of a gameplay observation.
    route_edges = [
        ['4941', '0:0', '635', '0:0'], ['635', '2:1', '825', '0:0'],
        ['825', '0:0', '827', '0:0'], ['825', '0:0', '4304', '0:0'],
        ['4304', '2:0', '856', '0:0'], ['856', '0:0', '854', '0:0'],
        ['854', '0:0', '1448', '0:1'], ['1448', '0:0', '866', '0:0'],
        ['866', '0:2', '2987', '0:1'], ['2987', '0:1', '4565', '0:1'],
        ['4565', '0:0', '868', '0:0'], ['868', '2:0', '3001', '0:0'],
        ['3001', '0:0', '5201', '0:0'], ['5201', '0:0', '1446', '0:1'],
        ['1446', '0:0', '866', '0:0'], ['866', '0:1', '2985', '0:1'],
        ['2985', '0:0', '4762', '0:1'], ['4762', '0:0', '3844', '0:0'],
        ['3844', '2:0', '3001', '0:0'], ['866', '0:0', '858', '0:0'],
        ['858', '0:0', '1328', '0:0']]
    indexed_edges = set(tuple(e) for e in graph['edges'])
    for edge in route_edges:
        assert tuple(edge) in indexed_edges, edge
    # First topic uses the FALSE branch after 1448 writes zero; the loop writes one.
    for node, value in [('1448', 0), ('1446', 1)]:
        fact = graph['nodes'][node]['payload']['questNode']['type']
        assert fact['factName'] == 'sq023_j_smokes' and fact['setExactValue'] == 1 and fact['value'] == value
    for node in ['2985', '2987']:
        cond = graph['nodes'][node]['payload']['questNode']['condition']['type']
        assert cond['factName'] == 'sq023_j_smokes' and cond['comparisonType'] == 'Equal' and cond['value'] == 1

    choices = []
    for node, stamp in [('825', '0:0'), ('856', '0:0'), ('866', '0:2'), ('866', '0:1'), ('866', '0:0')]:
        row = dict(con.execute('select * from choices where root_id=? and node_id=? and output_stamp=?', (ROOT, node, stamp)).fetchone())
        labels = [dict(r) for r in con.execute("select * from localization where root_id=? and loc_id=? and locale='en_us'", (ROOT, row['loc_id']))]
        text = {r['text'] for r in labels if r['text']}
        assert len(text) == 1
        choices.append({'choice': row, 'english_label': text.pop(), 'localization_rows': labels})

    anchors = [('4304', 2), ('4304', 9), ('4304', 16), ('854', 6), ('854', 16), ('3844', 3)]
    windows = []
    for number, (node, ordinal) in enumerate(anchors, 1):
        key = f'{ROOT}/scene/{node}/event/{ordinal}'
        pos = timeline_keys.index(key)
        assert timeline[pos]['speaker'] == 'Johnny'
        before = timeline[pos - 3:pos]
        after = [e for e in timeline[pos + 1:] if e['speaker'] == 'V'][:5]
        assert len(before) == 3
        windows.append({'excerpt_id': f'P1-E{number:02d}', 'anchor': key,
                        'before': [e['event_key'] for e in before],
                        'after_v': [e['event_key'] for e in after],
                        'following_v_available': len(after),
                        'boundary': 'End of the selected discussion; [Stand] interaction follows.' if len(after) < 5 else None})
    included = {k for w in windows for k in w['before'] + [w['anchor']] + w['after_v']}
    ordered = [e for e in timeline if e['event_key'] in included]
    for number, e in enumerate(ordered, 1):
        e['short_id'] = f'P1-L{number:03d}'
    mapping = {e['event_key']: e for e in ordered}
    displayed = sum(1 + len(w['before']) + len(w['after_v']) for w in windows)

    contexts = load(TASK / 'evidence_02/context_source_graphs.json')
    for source in contexts:
        s = source['source']
        assert sha(s['raw']) == s['sha256'] and sha(s['json']) == s['json_sha256']
        assert not source['normalized']['errors']
    entry = contexts[0]['normalized']['graphs']['root']
    assert entry['nodes']['65003']['type'] == 'questPauseConditionNodeDefinition'
    assert any(r.get('factName') == 'PostTowerFreeRoamActive' and r.get('value') == 1 for r in entry['nodes']['65003']['reads'])
    parent = contexts[1]['normalized']['graphs']['root']
    caller = contexts[2]['normalized']['graphs']['root']
    assert any(r.endswith('sq023_restaurant.questphase') for r in parent['nodes']['33']['refs'])
    assert ['2', 'Out', '52', 'cigarette_in'] in caller['edges']
    assert scene['depot'] in caller['nodes']['52']['refs']
    registry_path = WS / 'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json'
    registry = load(registry_path)
    selection = [r for r in registry['decision_registry'] if r['id'] in ('sq023_hit_order', 'sq023_bd_passion')]
    assert len(selection) == 2 and all(r['decision'] == 'INCLUDE' for r in selection)

    document = [
        'JOHNNY DIALOGUE REMOVAL — HUMAN REVIEW PILOT 01',
        'Revision P1 | English | 7 November 2026',
        '',
        f'{displayed} displayed dialogue entries in six excerpts; {len(ordered)} unique event occurrences.',
        'Repeated context uses the same ID. Each ID represents one spoken event, including both V variants.',
        '',
        'HOW TO REVIEW',
        'Delete every transcript entry you want to KEEP in the game. Leave only entries you want REMOVED, keeping their [P1-Lxxx] IDs and text together.',
        'For a repeated ID, keeping one copy requests removal of that event. Delete every copy if you want that event kept. Headings and notes are ignored.',
        'Where V has different female/male wording, both variants are shown under one ID; keep or delete that whole entry. Flag a note if you want only one variant changed.',
        'The three preceding lines are from any speaker. The following list contains the next five V lines on the stated route; intervening Johnny lines are omitted from that list. Context is not a removal recommendation.',
        'Save your edited copy and return it for ID matching. No removal is approved or implemented by this original pilot.',
        '',
        'QUEST AND ROUTE',
        'Sinnerman family — There Is A Light That Never Goes Out (SQ023). V and Johnny discuss Joshua after the restaurant meeting.',
        'This samples the current private PTFR scene and its connected post-Tower entry sources. Access still depends on native quest progression and preserved history; this is source review, not a new gameplay test.',
        'One route only, in this order:',
    ]
    document += [f'  {i}. {c["english_label"]}' for i, c in enumerate(choices, 1)]
    document += [
        'Menu labels describe the route. They are not selectable removal entries in this pilot.',
        'Other choices and duplicate authored branches will receive their own event IDs in later batches.',
        'The final excerpt has four following V entries before this discussion ends; no unrelated fifth line has been added.',
        '',
    ]

    def transcribe(key):
        e = mapping[key]
        texts = e['text_variants']
        prefix = f'[{e["short_id"]}] {e["speaker"]}: '
        if texts['female'] == texts['male']:
            return [prefix + texts['female']]
        return [prefix, '    Female V: ' + texts['female'], '    Male V: ' + texts['male']]

    for window in windows:
        document += ['=' * 72, f'EXCERPT {window["excerpt_id"]}', '', 'THREE PRECEDING LINES — ANY SPEAKER']
        for key in window['before']:
            document += transcribe(key) + ['']
        document += ['JOHNNY ANCHOR'] + transcribe(window['anchor']) + ['', 'FOLLOWING V LINES — ON THE ROUTE ABOVE']
        for key in window['after_v']:
            document += transcribe(key) + ['']
        if window['boundary']:
            document += ['[Context boundary: only four following V entries remain before the discussion ends and [Stand] becomes available.]', '']
    document += ['END OF PILOT — keep IDs attached to your retained removal selections.', '']
    content = '\r\n'.join(document)
    output.mkdir()
    qa.mkdir()
    path = output / 'Johnny_dialogue_review_pilot_01.txt'
    path.write_bytes(content.encode('utf-8-sig'))
    original = TASK / 'evidence_02/original_review_pilot_01.txt'
    assert not original.exists()
    original.write_bytes(path.read_bytes())
    manifest = {'schema': 1, 'revision': 'P1', 'status': 'PILOT_AWAITING_HUMAN_REVIEW',
                'document': str(path.relative_to(WS)), 'document_sha256': sha(path),
                'original_copy': str(original.relative_to(WS)),
                'source_index': str(DB.relative_to(WS)), 'source_index_sha256': EXPECTED_DB,
                'scene_resource': scene, 'localization_providers': [v['resource'] for v in provider_cache.values()],
                'selected_route_choices': choices, 'selected_route_edges': route_edges,
                'route_fact_state': ['854 -> 1448 writes sq023_j_smokes=0; first topic uses 2987 False -> 4565 -> 868',
                                     '868 -> 3001 -> 5201 -> 1446 writes sq023_j_smokes=1; second topic uses 2985 True -> 4762 -> 3844'],
                'route_timeline': [{'event_key': e['event_key'], 'speaker': e['speaker']} for e in timeline],
                'source_qualification': {'status': 'CURRENT_PRIVATE_PTFR_CALLER_SOURCE_QUALIFIED_NOT_LIVE_TESTED',
                                         'registry': str(registry_path.relative_to(WS)), 'registry_sha256': sha(registry_path),
                                         'registry_entries': selection, 'caller_evidence': 'context_source_graphs.json',
                                         'limits': 'Native prerequisites, ownership and progression still apply. Graph reachability is not an executing-owner or gameplay guarantee.'},
                'windows': windows, 'items': ordered,
                'counts': {'displayed_dialogue_entries': displayed, 'unique_event_occurrences': len(ordered),
                           'johnny_anchors': len(anchors), 'approved_removal_events': 0},
                'review_rules': {'retained_ids': 'REQUEST_REMOVAL_PENDING_IMPORT_AND_TECHNICAL_REVIEW',
                                 'repeated_ids': 'DEDUPE_BY_EXACT_EVENT_KEY', 'partial_text_edits': 'HOLD_FOR_REVIEW',
                                 'choice_labels': 'ROUTE_CONTEXT_NOT_REMOVAL_SELECTIONS'},
                'game_writes': 0, 'save_writes': 0}
    dump(TASK / 'evidence_02/review_manifest.json', manifest)
    actual_text = path.read_text(encoding='utf-8-sig')
    actual_ids = re.findall(r'^\[(P1-L\d{3})\]', actual_text, re.M)
    expected_ids = [mapping[k]['short_id'] for w in windows for k in w['before'] + [w['anchor']] + w['after_v']]
    assert actual_ids == expected_ids
    assert Counter(actual_ids) == Counter(expected_ids)
    assert sha(path) == sha(original)
    assert DB.stat().st_size == baseline.st_size and DB.stat().st_mtime_ns == baseline.st_mtime_ns
    verification = {'status': 'PASS', 'displayed_entries': len(actual_ids), 'unique_event_ids': len(set(actual_ids)),
                    'johnny_anchor_count': len(windows), 'context_counts': [[len(w['before']), len(w['after_v'])] for w in windows],
                    'verified': ['Selected index SHA256; read-only connection and unchanged file metadata',
                                 'Scene and localization raw/export hashes; exact external English source pointers',
                                 'Every event ordinal, event ID, line ID, loc ID, speaker binding, raw authored time and gender usage',
                                 'All explicit route edges; parallel choice reply order; zero-to-one fact transition selects distinct topic event copies',
                                 'Private caller phases/export hashes, post-Tower gate, scene input, selected SQ023 family',
                                 'Every displayed ID in order; repeated ID deduplication; preserved original exact bytes'],
                    'source_checks': source_checks, 'document_sha256': sha(path),
                    'not_tested': ['Gameplay, animation or audio delivery', 'Other routes or whole-game Step 3 coverage',
                                   'Any resource edit, build, deployment or save mutation'],
                    'game_writes': 0, 'save_writes': 0}
    dump(qa / 'verification.json', verification)
    print(json.dumps({'document': str(path), 'counts': manifest['counts'],
                      'context_counts': verification['context_counts'], 'verification': 'PASS'}, indent=2))


if __name__ == '__main__':
    main()
