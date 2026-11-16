"""Prepare the Batch 6 scene edits and their private phase call paths."""

from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from baseline import BASE, HERE, OUT, REVIEW, read, sha, write
from edit_batch6 import Batch6Scene, edit_scene
from resources import Resource, value, walk
from common import fnv


ASSIGNMENT = REVIEW / 'review_manifest.json'
DECISIONS = REVIEW / 'review_01/decisions.json'


def typed_refs(doc, names_by_key):
    return {names_by_key.get(str(value(p)), value(p)) for p in walk(doc)
            if p.get('$type') == 'ResourcePath' and str(value(p)) != '0'}


def remap(doc, aliases, names_by_key):
    replacements = Counter()
    for item in walk(doc):
        if item.get('$type') != 'ResourcePath':
            continue
        source = names_by_key.get(str(value(item)), value(item))
        if source in aliases:
            assert item['$storage'] == 'string' and value(item) == source, item
            replacements[source] += 1
            item['$value'] = aliases[source]
    return dict(replacements)


def dependencies(roots, edges):
    scope = set(roots)
    pending = list(roots)
    while pending:
        children = edges.get(pending.pop(), set()) - scope
        scope.update(children)
        pending.extend(children)
    return scope


def main():
    target = HERE / 'input_01/batch6_02.json'
    output = HERE / 'input_01/batch6_02'
    assert not target.exists() and not output.exists()
    assignment, review = read(ASSIGNMENT), read(DECISIONS)
    assert sha(ASSIGNMENT) == review['review_manifest_sha256']
    assert sha(REVIEW / review['filled_notes']) == review['filled_notes_sha256']
    assert review['status'] == 'SOURCE_FILLED_WORKSHEET' and review['installed_baseline'] == 'JB3'
    assert review['counts'] == {'JOHNNY': 182, 'V': 84, 'JOHNNY_BARKS': 6, 'OPTIONS': 23}
    assert [g['id'] for g in review['groups']] == assignment['dialogue_review_quest_ids'] + assignment['presentation_review_ids']

    cap_path = REVIEW / assignment['provider_scan']['manifest']
    assert sha(cap_path) == assignment['provider_scan']['manifest_sha256']
    cap = {r['depot']: r for r in read(cap_path)['resources']}
    assert len(cap) == 109
    names_by_key = {r['key']: d for d, r in cap.items()}
    original_resources = read(BASE / 'package_manifest.json')['source_resources']

    @lru_cache(None)
    def load(depot):
        row = cap[depot]
        source = cap_path.parent / row['json']
        assert not row['decode_error'] and sha(source) == row['json_sha256'], depot
        assert depot not in original_resources or row['raw_sha256'] == original_resources[depot]
        return read(source)

    phases = {d: typed_refs(load(d), names_by_key) & cap.keys() - {d}
              for d in cap if d.endswith('.questphase')}
    assignments = {q['id']: q for q in assignment['quests']}
    aliases, phase_edits, scene_specs, calls = {}, set(), {}, []
    for group in review['groups']:
        quest = assignments[group['id']]
        assert group['registered_entries'] == quest['registered_entries']
        scope = dependencies(group['registered_entries'], phases)
        specs = {s['depot']: s for s in group['scenes']}
        assert specs.keys() <= scope
        assert specs.keys().isdisjoint(scene_specs)
        scene_specs.update(specs)
        # Only native resources whose depot must change need an aliased parent.
        needed = set(specs) - original_resources.keys()
        while True:
            parents = {d for d in scope & phases.keys() if phases[d] & needed}
            phase_edits.update(parents)
            new = parents - original_resources.keys() - needed
            if not new:
                break
            needed.update(new)
        for d in needed:
            assert d not in aliases and d.startswith(('base\\', 'ep1\\')), d
            aliases[d] = f"towercontinued\\johnny_batch6\\{group['id']}\\{Path(d).name}"
        for row in quest['scenes']:
            assert row['depot'] in specs and row['source_sha256'] == specs[row['depot']]['source_sha256']
            assert row['bound_entries'].keys() == set(specs[row['depot']]['bound_entries'])
            for entry, chain in row['bound_entries'].items():
                calls.append({'scene': row['depot'], 'entry': entry, 'chain': chain})

    assert len(scene_specs) == 30
    assert len(set(aliases.values())) == len(aliases)
    b5 = read(HERE / 'input_01/batch5.json')['edits']
    assert (set(aliases.values()) | phase_edits & original_resources.keys() | scene_specs.keys() & original_resources.keys()).isdisjoint(
        {r['depot'] for r in b5})
    old_keys = {fnv(d) for d in original_resources.keys() | cap.keys() | {r['depot'] for r in b5}}
    assert not {fnv(d) for d in aliases.values()} & old_keys

    donor = Resource(load(next(d for d in scene_specs if d.endswith('\\sq023_07_restaurant.scene'))))
    output.mkdir()
    edits = []
    for depot in sorted(phase_edits | scene_specs.keys()):
        provider = cap[depot]
        original = load(depot)
        doc = deepcopy(original)
        substitutions = remap(doc, aliases, names_by_key)
        changes = {}
        if depot in scene_specs:
            spec = scene_specs[depot]
            assert spec['source_sha256'] == provider['raw_sha256']
            assert spec['source_json_sha256'] == provider['json_sha256']
            doc, changes = edit_scene(doc, spec, donor)
        else:
            assert substitutions
            reversed_doc = deepcopy(doc)
            remap(reversed_doc, {target: source for source, target in aliases.items()}, {})
            assert reversed_doc == original
        model = Resource(doc).normalize()
        assert not model['errors'], (depot, model['errors'])
        destination = aliases.get(depot, depot)
        path = output / (fnv(destination) + '.json')
        assert not path.exists()
        write(path, doc)
        assert read(path) == doc
        edits.append({
            'depot': destination, 'source_depot': depot, 'source_sha256': provider['raw_sha256'],
            'edited_json': str(path), 'edited_json_sha256': sha(path), 'is_new': destination not in original_resources,
            'reference_changes': substitutions, 'scene_changes': changes,
        })
    write(target, {
        'edits': edits, 'aliases': aliases, 'calls': calls,
        'decisions_sha256': sha(DECISIONS), 'capture_sha256': sha(cap_path),
        'providers': [{'depot': d, 'archive': r['archive'], 'sha256': r['raw_sha256']}
                      for d, r in sorted(cap.items())],
    })
    print(f'Prepared 30 scenes and {len(phase_edits)} phase edits with {len(aliases)} private depot aliases.')


if __name__ == '__main__':
    main()
