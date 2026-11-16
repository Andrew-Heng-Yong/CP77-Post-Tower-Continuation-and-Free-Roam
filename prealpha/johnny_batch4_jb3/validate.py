"""Verify cooked resources and bounded native handoffs before packaging."""

from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
import sys

from prepare import BUNKER, HERE, INPUT, JB2, OUT, PRE, RESUME, closure, name, refs, remap
from edit_scenes import BatchScene
from resources import Resource, load, read, sha, value, write

sys.path.append(str(PRE / 'johnny_batch2_jb1'))
from flow_fixtures import Signals


def model(doc):
    normalized = Resource(doc).normalize()
    assert not normalized['errors'], normalized['errors']
    return normalized


def phase_parity(row, original_doc, cooked, aliases):
    source = row['source']['depot']
    assert remap(original_doc, aliases) == row['reference_changes']
    original = model(original_doc)
    assert original['graphs'].keys() == cooked['graphs'].keys(), source
    for key in ('metadata', 'root_prefabs', 'embedded_files', 'refs'):
        assert original[key] == cooked[key], (source, key)
    for path, old in original['graphs'].items():
        new = cooked['graphs'][path]
        assert old['entries'] == new['entries'] and old['nodes'] == new['nodes'], (source, path)
        before = Counter(map(tuple, old['edges']))
        after = Counter(map(tuple, new['edges']))
        removed, added = before - after, after - before
        if name(source) == BUNKER and path == 'root':
            assert removed == {('240', 'False', '138', 'in_johnny_max_jones'): 1,
                               ('217', 'Out1', '215', 'in_johnny_all_dead'): 1}
            assert not added
        elif name(source) == BUNKER and path == 'root/238':
            assert removed == {('5', 'Out1', '15', 'In'): 1}
            assert added == {('5', 'Out1', '1', 'In'): 1}
        else:
            assert not removed and not added, (source, path, removed, added)


def scene_parity(row, src, doc, cooked, selected):
    depot = row['source']['depot']
    ev = row['scene_evidence']
    before, after = (m['graphs']['scene'] for m in (src, cooked))
    assert before['entries'] == after['entries'] and before['nodes'].keys() == after['nodes'].keys()
    orig_meta, new_meta = src['metadata'], cooked['metadata']
    for key in ('entryPoints', 'exitPoints', 'screenplayStore', 'playerActors', 'locStore'):
        assert orig_meta[key] == new_meta[key], (depot, key)
    ids = set(ev['actor_ids'])
    presentation = BatchScene(doc, name(depot))
    assert presentation.actor_ids == ids
    presentation.props = {int(i): n for i, n in ev['removed_props'].items()}
    presentation.prop_performers = {(i << 8) | 2 for i in presentation.props}
    assert [p for p in orig_meta.get('props', []) if p['propId']['id'] not in presentation.props] == new_meta.get('props', [])
    for a, b in zip(orig_meta['actors'], new_meta['actors'], strict=True):
        expected = deepcopy(a)
        if a['actorId']['id'] in ids:
            expected['acquisitionPlan'] = 'spawnDespawn'
            for f in ('isEnabled', 'alwaysSpawned', 'spawnOnStart', 'keepAlive', 'findInWorld', 'prefetchAppearance'):
                expected['spawnDespawnParams'][f] = 0
        assert b == expected, (depot, a['actorName'])

    cut = {e['id']: e for e in ev['events_removed']}
    assert selected == {i: e['speaker'] for i, e in cut.items() if 'speaker' in e}, depot
    speech_speakers = {line['itemId']['id']: line['speaker']['id']
                       for line in new_meta['screenplayStore']['lines']}
    option_menus = {str(r['node']) for r in ev['options_removed']}
    removed = set()
    for i, node in before['nodes'].items():
        old, new = node['payload'], after['nodes'][i]['payload']
        assert old['$type'] == new['$type']
        if old['$type'] == 'scnChoiceNode':
            assert new['options'] == ([] if i in option_menus else old['options']), (depot, i)
        timing = ev['duration_changes'].get(i)
        shifts = {r['event']: r for r in timing['shifted_events']} if timing else {}
        expected_events = []
        for e in old.get('events', []):
            eid = str(e['id']['id'])
            if eid in cut:
                assert cut[eid]['node'] == int(i) and cut[eid]['kind'] == e['$type']
                if e['$type'] == 'scnDialogLineEvent':
                    is_johnny = speech_speakers[e['screenplayLineId']['id']] in ids
                    assert is_johnny == (selected[eid] == 'JOHNNY'), (depot, eid)
                else:
                    assert presentation.targeted(e), (depot, eid)
                removed.add(eid)
                continue
            expected = deepcopy(e)
            if eid in shifts:
                assert e['startTime'] == shifts[eid]['before']
                expected['startTime'] = shifts[eid]['after']
            expected_events.append(expected)
        assert new.get('events', []) == expected_events, (depot, i)
        if timing:
            assert old['sectionDuration']['stu'] == timing['before_ms']
            assert new['sectionDuration']['stu'] == timing['after_ms']
        else:
            assert old.get('sectionDuration') == new.get('sectionDuration'), (depot, i)
        if i not in after['reachable']:
            continue
        assert i not in option_menus
        assert not presentation.targeted(new.get('questNode')), (depot, i)
        assert not any(b['actorId']['id'] in ids for b in new.get('actorBehaviors', [])), (depot, i)
        for e in new.get('events', []):
            if e['$type'] == 'scnDialogLineEvent':
                assert speech_speakers[e['screenplayLineId']['id']] not in ids, (depot, i, e['id'])
            else:
                assert not presentation.targeted(e), (depot, i, e['id'])
    assert removed == cut.keys()
    return Counter(selected.values())


def fixtures(scenes, phases):
    cases = {}

    def run(label, filename, start, *, ends=(), stops=(), held=(), ordinal=0, **inputs):
        trace = Signals(scenes[filename + '.scene'], stop=stops, **inputs).start(start, ordinal).run()
        assert [e[1] for e in trace.ends] == list(map(str, ends)), (label, trace.result())
        assert [e[1] for e in trace.stopped] == list(map(str, stops)), (label, trace.result())
        assert [e[1] for e in trace.held] == list(map(str, held)), (label, trace.result())
        cases[label] = trace.result()
        return trace

    run('razor_returns_to_real_choice', 'mq025_08_finale', 558, stops=(546,))
    run('war_pigs_briefcase_objective', 'mq041_corpo_02_confrontation', 1, stops=(414,))
    for section in (212, 1006, 1028, 1041, 1055, 1069):
        t = run(f'war_pigs_native_reward_{section}', 'mq041_corpo_02_confrontation', section, ends=(2,))
        assert [i for _, i, *_ in t.trace].count('527') == 1
        assert t.journal == {'quests/minor_quest/mq041_corpo': 'Succeeded'}
    for start, end in ((39, 44), (47, 88), (50, 92), (52, 95), (54, 98)):
        t = run(f'freedom_native_release_{start}', 'mq059_play_vos', start, ends=(end,),
                held=(273,) if start == 52 else ())
        assert t.facts == {'mq060_johnny_talk': 0}
    run('freedom_tablet_stays_interactive', 'mq059_play_vos', 400, held=(421,))
    run('shot_apartment_enables_devices', 'mq305_03_apartment_johnny', 295, ends=(297,))
    for menu in (173, 176, 178):
        run(f'shot_wrong_plant_callback_{menu}', 'mq305_03_apartment_johnny', menu,
            choices={str(menu): 0}, stops=(229,))
    run('shot_keycard_grant_and_followup', 'mq305_03_apartment_johnny', 291,
        ordinal=1, ends=(404,), stops=(407, 459))
    run('shot_lab_local_bark_finishes', 'mq305_04b_lab_exploration', 2661, ends=(2663,))
    run('shot_hands_native_handoff', 'mq305_05_outcome_mr_hands', 251, ends=(253,))
    t = run('aaron_alley_to_success_and_cleanup', 'mq306_04a_aaron_meeting', 361, ordinal=3, ends=(36, 214))
    assert t.journal == {'ep1/quests/minor_quest/mq306_dumpster/04a_aaron_meeting/04a_alley': 'Succeeded',
                         'ep1/quests/minor_quest/mq306_dumpster': 'Succeeded'}
    run('pony_waits_for_approach', 'mws_se5_07', 1, held=(50,))
    run('pony_waits_for_clue', 'mws_se5_07', 1, held=(54,), acknowledgements=(50,))
    run('pony_clue_completes', 'mws_se5_07', 1, ends=(2,), acknowledgements=(50, 54))
    run('pony_waits_for_mount', 'mws_se5_07_camp', 1, held=(12,), acknowledgements=(48, 24))
    t = run('pony_retains_porsche_spawn', 'mws_se5_07_camp', 1, ends=(2,), acknowledgements=(48, 24, 12))
    assert '18' in [i for _, i, *_ in t.trace]
    run('flying_drugs_computer_handoff', 'sts_bls_ina_03_interactions', 74, ends=(77,))
    for explained in (True, False):
        t = run(f'flying_drugs_antenna_explained_{explained}', 'sts_bls_ina_03_interactions', 109,
                ends=(118,), conditions={'112': explained})
        assert t.facts == ({} if explained else {'#ina_03_antenna_explained': 1})
    run('minefield_waits_for_body_choice', 'sts_bls_ina_07_comments', 183, held=(400,))
    t = run('minefield_body_to_world_callback', 'sts_bls_ina_07_comments', 183, ends=(342,), choices={'400': 0})
    assert t.facts == {'#ina_07_body_scan': 1}
    run('minefield_chase_continues', 'sts_bls_ina_07_comments', 266, ends=(269,))
    for start, choice, end in ((10, 127, 13), (16, 131, 17)):
        run(f'trevor_clue_{choice}_waits', 'sts_bls_ina_08_johnny', start, held=(choice,))
        run(f'trevor_clue_{choice}_finishes', 'sts_bls_ina_08_johnny', start,
            choices={str(choice): 0}, ends=(end,))
    for start, end in ((119, 120), (25, 28)):
        run(f'trevor_cleanup_{start}', 'sts_bls_ina_08_johnny', start, ends=(end,))
    for start in (1, 47):
        run(f'inconvenient_killer_approach_{start}', 'sts_cct_dtn_02_johnny', start, ends=(2,))

    # Connect the exercised exit points to their original phase listeners.
    callbacks = {
        'mq041_corpo_02_confrontation.questphase': [
            ('5', 'End 0', '12', 'In'), ('5', 'End 0', '15', 'In')],
        'mq305_02_apartment.questphase': [
            ('176', 'out_enter_apartment', '229', 'In'), ('126', 'out_got_keycard', '211', 'In')],
        'mq305_outcome.questphase': [('125', 'out_johnny_sold_data', '50', 'Succeeded')],
        'mq306_04a_aaron_meeting.questphase': [('1', 'johnny_terminating', '71', 'In')],
    }
    for filename, expected in callbacks.items():
        assert set(expected) <= set(map(tuple, phases[filename]['graphs']['root']['edges'])), filename
    return cases


def compile_identity(game):
    proof = JB2 / 'compile_01/result.json'
    c = read(proof)
    assert c['status'] == 'PASS_JB2_COMPLETE_SOURCE_COMPILE' and c['exit_code'] == 0
    assert len(c['sources']) == c['source_count'] == 148
    inputs = {p for root in ('r6/scripts', 'red4ext/plugins') for p in (game / root).rglob('*.reds')}
    assert inputs == {Path(p) for p in c['sources']}
    assert all(sha(p) == digest for p, digest in c['input_pins'].items())
    for location, record in c['sources'].items():
        original = Path(location)
        bundled = OUT / 'package' / original.relative_to(game)
        assert sha(bundled if bundled.is_file() else original) == record['sha256'], location
    return {'result': str(proof), 'sha256': sha(proof), 'matching_sources': len(inputs)}


def main():
    out = HERE / 'verification_01.json'
    assert not out.exists()
    plan_path = INPUT / 'plan.json'
    rb_path = HERE / 'readback_01/manifest.json'
    pl, rb = read(plan_path), read(rb_path)
    assert rb['plan_sha256'] == sha(plan_path)
    assert sha(INPUT / 'received_notes.txt') == pl['notes_sha256']
    assert sha(pl['selection']) == pl['selection_sha256']
    selection = read(pl['selection'])
    rb_rows = {r['depot']: r for r in rb['resources']}
    assert rb_rows.keys() == {r['depot'] for r in pl['edits']}
    selected = defaultdict(dict)
    for e in selection['events']:
        selected[e['depot']][e['event_id']] = e['speaker']
    scenes, originals, phases, dependencies = {}, {}, {}, {}
    removed = Counter()
    for row in pl['edits']:
        depot, source = row['depot'], row['source']['depot']
        assert depot.startswith('towercontinued\\')
        original_doc, cooked_doc = load(row['source']), load(rb_rows[depot])
        assert sha(row['edited_json']) == row['edited_json_sha256']
        cooked = model(cooked_doc)
        assert model(read(row['edited_json'])) == cooked, depot
        if row['scene_evidence']:
            originals[name(source)] = model(original_doc)
            removed.update(scene_parity(row, originals[name(source)], cooked_doc, cooked, selected[source]))
            scenes[name(source)] = cooked
        else:
            phase_parity(row, original_doc, cooked, pl['aliases'])
            phases[name(source)] = cooked
        dependencies[depot] = refs(cooked_doc)
    assert removed == {'JOHNNY': 60, 'V': 21}
    for root, targets in pl['registered_routes'].items():
        reached = closure(root, dependencies)
        for source in targets:
            if source in pl['aliases']:
                assert pl['aliases'][source] in reached and source not in reached, (root, source)
    assert not pl['registered_routes'][RESUME]
    for depot, proof in pl['s23_resume'].items():
        assert sha(OUT / 'archive_source' / depot) == proof['sha256']
        assert sha(proof['json']) == proof['json_sha256']
        assert refs(read(proof['json'])) == set(proof['scene_or_phase_references'])
    for option in selection['retained_options']:
        g = scenes[name(option['depot'])]['graphs']['scene']
        n = g['nodes'][option['node_id']]['payload']
        assert option['node_id'] in g['reachable']
        assert int(option['option_id']) in {o['screenplayOptionId']['id'] for o in n['options']}
    for group in selection['removed_option_groups']:
        for option in group:
            g = scenes[name(option['depot'])]['graphs']['scene']
            assert not g['nodes'][option['node_id']]['payload']['options']
            assert option['node_id'] not in g['reachable']
    dispatches = [(name(r['caller_depot']), r['caller_node'], r['voiceset_entry'], 0)
                  for r in selection['dispatches']]
    dispatches += [('mq305_04b_lab_exploration.scene', '2667', 'reaction_location_bad_var_3', 0),
                   ('mq306_01_intro.scene', '1633', 'reaction_general_var_6', 0),
                   ('mq305_03_apartment_johnny.scene', '442', 'scene_insult_var_2', 1)]
    for filename, node, bark, is_player in dispatches:
        g = originals[filename]['graphs']['scene']
        q = g['nodes'][node]['payload']['questNode']
        param, = q['type']['params']
        assert node in g['reachable'] and q['$type'] == 'questVoicesetManagerNodeDefinition'
        assert value(param['voicesetName']) == bark and param['isPlayer'] == is_player
        assert node not in scenes[filename]['graphs']['scene']['reachable']
    case_data = fixtures(scenes, phases)
    write(out, {
        'status': 'PASS_JB3_COOKED_AND_BOUNDED_FLOW', 'plan_sha256': sha(plan_path),
        'readback_sha256': sha(rb_path), 'resources': len(rb_rows),
        'removed_scene_cues': dict(removed), 'textless_johnny_cues': 1,
        'local_dispatches_removed': dispatches, 'options_removed': 4,
        'compile_identity': compile_identity(Path(pl['game_root'])),
        'fixture_count': len(case_data), 'fixtures': case_data,
        'scope': 'Offline readback and bounded signals. Live presentation, native engine execution and saved-phase transitions are pending.',
        'game_writes': 0, 'save_writes': 0,
    })
    print(f'Validated {len(rb_rows)} resources, {sum(removed.values())} scene cues, and {len(case_data)} signal fixtures.')


if __name__ == '__main__':
    main()
