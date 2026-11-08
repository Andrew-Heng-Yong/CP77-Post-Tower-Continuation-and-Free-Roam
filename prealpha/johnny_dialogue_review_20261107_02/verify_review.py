"""Independent readback checks for five-quest human review J5-03."""
import collections
import json
import re
from pathlib import Path
from prepare_sources import TASK, WS, load, sha


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def raw_edges(path):
    data = load(path)
    handles = {str(n['HandleId']): n['Data'] for n in walk(data) if 'HandleId' in n and 'Data' in n}

    def deref(node):
        if 'HandleId' in node:
            return node['Data']
        if 'HandleRefId' in node:
            return handles[str(node['HandleRefId'])]
        return node

    graph = deref(data['Data']['RootChunk']['sceneGraph'])
    edges = set()
    for item in graph['graph']:
        node = deref(item)
        for i, sock in enumerate(node.get('outputSockets', [])):
            stamp = sock.get('stamp', {})
            out = f'{stamp.get("name", 0)}:{stamp.get("ordinal", i)}'
            for dest in sock.get('destinations', []):
                inp = dest.get('isockStamp', {})
                edges.add((str(node['nodeId']['id']), out, str(dest['nodeId']['id']),
                           f'{inp.get("name", 0)}:{inp.get("ordinal", 0)}'))
    return edges


def main():
    m = load(TASK / 'evidence_05/review_manifest.json')
    inventory = load(TASK / 'evidence_03/quest_dialogue_inventory.json')
    doc = WS / m['document']
    text = doc.read_text(encoding='utf-8-sig')
    assert sha(doc) == m['document_sha256']
    assert doc.read_bytes() == (WS / m['preserved_original']).read_bytes()
    items = {e['event_key']: e for e in m['items']}
    by_id = {e['short_id']: e for e in m['items']}
    centers = re.findall(r'^JOHNNY LINE\n\[(J5-[0-9A-F]{10})\]', text, re.M)
    expected = []
    expected_source = set()
    raw_cache = {}
    checked_paths = 0
    for q in inventory['quests']:
        for scene in q['scenes']:
            if any(c['entry_names'] and c['may_reachable_in_phase'] for c in scene['callers']):
                expected_source.update(e['item_key'] for e in scene['johnny_events'])
    for q in m['quests']:
        assert q['registry']['decision'] == 'INCLUDE'
        for scene in q['scenes']:
            raw_cache[scene['resource']['depot']] = raw_edges(scene['resource']['json_path'])
        for entry in q['review_items']:
            expected.append(items[entry['target']]['short_id'])
            assert items[entry['target']]['speaker'] == 'Johnny'
            for direction, maximum in [('before', 3), ('after_v', 5)]:
                for context in entry[direction]:
                    assert len(context['events']) <= maximum
                    if context['complete']:
                        assert len(context['events']) == maximum
                    if direction == 'after_v':
                        assert all(items[k]['speaker'] == 'V' for k in context['events'])
                    for evidence in context['evidence']:
                        if 'path' not in evidence:
                            continue
                        path = evidence['path']
                        assert all(tuple(edge) in raw_cache[entry['source_scene']] for edge in path)
                        assert all(a[2] == b[0] for a, b in zip(path, path[1:]))
                        checked_paths += 1
    assert centers == expected and len(set(centers)) == 49
    assert {r['target'] for q in m['quests'] for r in q['review_items']} == expected_source
    all_ids = re.findall(r'^\[(J5-[0-9A-F]{10})\]', text, re.M)
    assert len(all_ids) == m['counts']['displayed_entries']
    assert set(all_ids) == set(by_id)
    assert {i for i in all_ids if by_id[i]['speaker'] == 'Johnny'} == set(centers)
    # Source regression: the recognized/unrecognized paths must not be mixed.
    freezer = next(s for q in m['quests'] for s in q['scenes'] if s['resource']['resource_id'] == '90c76218185ecad8483a5352')
    assert freezer['local_fact_seed'] == {'mq016_recognized_bartmoss': 0}
    assert freezer['local_fact_states']['28'] == [0]
    assert freezer['local_fact_states']['98'] == [1]
    assert freezer['local_fact_states']['101'] == [0]
    first = next(r for q in m['quests'] for r in q['review_items'] if r['target'].endswith('/scene/28/event/3'))
    for context in first['after_v']:
        nodes = [items[e]['event']['node_id'] for e in context['events']]
        if '82' in nodes:
            assert '101' not in nodes
        if '85' in nodes:
            assert '98' not in nodes
    # Supplement the index's zero scene dispatches with raw phase graph inspection.
    phases = load(TASK / 'evidence_03/phase_graphs.json')
    voice_candidates = []
    for depot, model in phases.items():
        for node in walk(model['model']):
            typ = node.get('$type', '')
            if ('Voiceset' in typ or 'VoiceSet' in typ) and 'johnny' in json.dumps(node).lower():
                voice_candidates.append({'depot': depot, 'type': typ, 'payload': node})
    assert not voice_candidates, 'Additional Johnny dispatch candidates require transcript review.'
    assert m['counts']['approved_removal_events'] == 0
    report = {'status': 'PASS_WITH_EXPLICIT_CONTEXT_BOUNDARIES', 'revision': m['revision'],
              'quest_counts': {q['title']: len(q['review_items']) for q in m['quests']},
              'all_qualified_johnny_occurrences_accounted_for': 49,
              'displayed_entries': len(all_ids), 'unique_event_ids': len(set(all_ids)),
              'context_source_paths_checked_against_raw_scene_edges': checked_paths,
              'kold_mirage_recognition_regression': 'PASS',
              'additional_johnny_phase_voiceset_candidates': voice_candidates,
              'excluded_import_only_scenes': m['excluded_import_only_scenes'],
              'document_sha256': sha(doc), 'original_copy_identical': True,
              'limits': m['limits'], 'game_writes': 0, 'save_writes': 0}
    target = TASK / 'qa_03/independent_verification.json'
    assert not target.exists()
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('excluded_import_only_scenes', 'limits')}, indent=2))


if __name__ == '__main__':
    main()
