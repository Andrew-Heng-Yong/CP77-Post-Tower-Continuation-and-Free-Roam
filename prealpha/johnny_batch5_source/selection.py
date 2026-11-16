"""Resolve the exact Batch 5 worksheet approved for the source edit."""

from collections import Counter, defaultdict
from pathlib import Path

from resources import read, sha


NOTES_PIN = '5B6797230EB11F7B2004A2625226749BEA20B3B43FBF4D87B50BFC62C2F8D20C'
REVIEW_PIN = '2821737EF95F90B71D28018C2B14666D90448D75D85813FEFFCBC927C78E83EA'


def select(batch):
    revised_path = batch / 'review_02/findings.json'
    assert sha(revised_path) == REVIEW_PIN
    revised = read(revised_path)
    previous_path = Path(revised['previous_findings'])
    assert previous_path == batch / 'review_01/findings.json'
    assert sha(previous_path) == revised['previous_findings_sha256']
    previous = read(previous_path)
    assignment = read(batch / 'review_manifest.json')
    notes = batch / assignment['notes']
    prior_notes = batch / 'review_02/received_notes.txt'
    assert sha(prior_notes) == revised['notes_sha256']
    assert sha(notes) == NOTES_PIN, 'Batch 5 worksheet changed after this selection'

    sound, = revised['remaining_johnny_review_items']
    v, = previous['situational_context']
    assert sound['review_id'] == 'B5-10' and sound['quest_id'] == v['quest_id'] == 'sts_wbr_jpn_12'
    extra = (
        'V: ' + v['line']['text'].replace('\n', ' / ') + '\n'
        + 'J [B5-10]: ' + sound['line']['text'] + '\n\n'
    )
    anchor = 'J [B5-11]:'
    before = prior_notes.read_text(encoding='utf-8-sig')
    assert before.count(anchor) == 1
    assert notes.read_text(encoding='utf-8-sig') == before.replace(anchor, extra + anchor)

    backs = revised['whole_exchange']
    backs_quest, = [q for q in assignment['quests'] if q['id'] == backs['quest_id']]
    backs_scene, = backs_quest['indexed_bound_johnny_sources']
    decisions = list(revised['decisions'])
    decisions.extend({'depot': backs_scene['depot'], 'line': line, 'selection': 'WHOLE_MENU'}
                     for line in backs['additional_events'])
    decisions += [
        {'depot': sound['depot'], 'line': sound['line'], 'selection': 'B5-10'},
        {'depot': sound['depot'], 'line': v['line'], 'selection': 'V_SOUND_REACTION'},
    ]
    cuts = defaultdict(dict)
    for d in decisions:
        line = d['line']
        assert line['event_id'] not in cuts[d['depot']]
        cuts[d['depot']][line['event_id']] = {**line, 'speaker': line['speaker_role']}
    assert Counter(d['line']['speaker_role'] for d in decisions) == {'JOHNNY': 49, 'V': 23}
    assert len(cuts) == len(assignment['quests']) == 10
    assert [int(o['option_id']) for o in backs['options']] == [2, 258, 514]

    preserved = previous['held_without_connected_caller'] + previous['separate_prologue_occurrence']
    assert len(preserved) == 5 and all(p['line']['event_id'] not in cuts[p['depot']] for p in preserved)
    return notes, cuts, {
        'review_sha256': REVIEW_PIN,
        'worksheet_sha256': NOTES_PIN,
        'scene_dialogue_events': {'Johnny': 49, 'V': 23},
        'backs_choice_ids': [2, 258, 514],
        'retained_other_entry_events': preserved,
        'latest_additions': ['B5-10', 'V_SOUND_REACTION'],
    }
