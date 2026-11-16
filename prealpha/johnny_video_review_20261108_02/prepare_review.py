"""Prepare eight new editable YouTube review sections; documentation only."""
from pathlib import Path
import hashlib
import json
import re
import sqlite3

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
DB = WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
REGISTRY = WS / 'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json'
POLICY = WS / 'prealpha/johnny_dialogue_scope_audit_20261107_01/scope_policy.json'
PRIOR = WS / 'prealpha/johnny_video_review_20261108_01/review_manifest.json'
CURRENT = WS / 'prealpha/johnny_batch2_jb1/deployment_01/installed_manifest_01.json'
PACKAGE = WS / 'prealpha/johnny_batch2_jb1/candidate_04/package_manifest.json'
NEXT = [
    ('mq003_orbitals', 'Space Oddity',
     'Watch the orbital-pod discovery and Johnny commentary there. Record any Talk prompt, camera wait or inspection dependency. Preserve the actual encounter, inspection and loot.'),
    ('mq010_barry', 'Happy Together',
     'Watch the columbarium/grave visit, including the optional investigation branch. Distinguish replies to Johnny from V talking to Barry or the other NPCs. Preserve investigation choices and their outcomes.'),
    ('mq015_wizardbook', 'Spellbound',
     'Watch the stash/book inspection and Johnny commentary. Preserve the actual book acquisition, inspection/read actions, payment choices and handoff progression.'),
    ('mq019_paparazzi', 'Violence',
     'Watch the manager conversation and nearby Johnny commentary. Separate replies to Johnny from V addressing the other characters. Preserve the investigation, information handoff and player outcome choices.'),
    ('mq026_conspiracy', "The Prophet's Song",
     'Check Johnny exchanges around the prophet and the later smuggler meeting. Note branches not shown by the video. Preserve the actual meeting, clues/item pickup and NPC outcomes.'),
    ('mq030_melisa', 'Bullets',
     'Watch the Melissa conversation around the shop encounter and aftermath. Preserve the real fight, NPC conversations, shop/service recovery and cleanup. This is a video dialogue review; the previously accepted gameplay test does not need repeating.'),
    ('mq032_sacrum', 'Sacrum Profanum / Losing My Religion',
     'Watch the monk request, Maelstrom rescue and epilogue. Check alternate lethal/nonlethal commentary. Preserve the rescue, player approach, NPC reactions and original outcomes. These two titles refer to one review assignment.'),
    ('mq050_ken_block_tribute', "I'm in Love with My Car",
     'Watch the car discovery and Johnny opening comment. Separate V reactions to Johnny from observations about the situation. Preserve the original inspection and vehicle-acquisition actions.'),
]
HANDLED = {'mq016_bartmoss', 'mq036_overload', 'mq029_tourist', 'mq017_streetkid',
           'mq042_nomad', 'mq040_biosculpt', 'mq018_writer'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')


def main():
    out, evidence = HERE / 'output_01', HERE / 'evidence_01'
    assert not out.exists() and not evidence.exists()
    ids = [q[0] for q in NEXT]
    assert len(ids) == len(set(ids)) == 8 and not HANDLED.intersection(ids)
    registry = {r['id']: r for r in read(REGISTRY)['decision_registry']}
    assert all(registry[q]['decision'] == 'INCLUDE' for q in ids)
    assert sha(DB) == 'A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E'
    installed, package = read(CURRENT), read(PACKAGE)
    assert installed['core_epoch'] == 'JB1' and sha(PACKAGE) == installed['package_manifest_sha256']
    archive, = [r for r in installed['core_files'] if r['path'].endswith('zzzz_PTFR_Combined.archive')]
    assert sha(Path(installed['game_root']) / archive['path']) == archive['sha256']
    previous = {q['id']: q for q in read(PRIOR)['quest_groups']}
    db = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    records = []
    for qid, title, hint in NEXT:
        code = qid.split('_')[0]
        pattern = re.compile(r'(?:^|\\)' + re.escape(code) + r'(?:\\|_|\.|$)')
        source_rows = db.execute('''SELECT DISTINCT r.resource_id,r.depot,r.scope,r.raw_sha256
            FROM resources r JOIN search_items s USING(resource_id)
            WHERE s.kind='DIALOGUE_EVENT' AND s.speaker_role='JOHNNY' AND s.depot LIKE ?
            ORDER BY r.depot,r.resource_id''', ('%' + code + '%',)).fetchall()
        sources = [dict(r) for r in source_rows if pattern.search(r['depot'])]
        assert sources and qid in previous
        private = []
        for depot, digest in sorted(package['source_resources'].items()):
            if pattern.search(depot) and depot.endswith(('.scene', '.questphase')):
                p = Path(installed['source_candidate']) / 'archive_source' / depot
                assert p.is_file() and sha(p) == digest
                private.append({'depot': depot, 'sha256': digest})
        assert private
        for source in sources:
            if source['scope'] == 'CURRENT_PTFR_PAYLOAD':
                assert package['source_resources'].get(source['depot']) == source['raw_sha256']
        records.append({'id': qid, 'title': title, 'registry_row': registry[qid],
            'watch_prompt': hint, 'indexed_bound_johnny_sources': sources,
            'current_private_resource_pins': private, 'status': 'AWAITING_HUMAN_NOTES',
            'qualification': 'INCLUDE registry entry and indexed bound Johnny speech; current private resources pinned. Native/shared exact callers, entry sockets, alternate branches and saved-owner availability still require review before implementation.'})
    db.close()
    out.mkdir()
    evidence.mkdir()
    lines = ['EIGHT-QUEST REMOVAL AND REWIRE NOTES - BATCH 3', '8 November 2026', '',
        'Edit this file while watching playthroughs. Add or delete rows freely.',
        'Use Johnny: / V: followed by at least five consecutive quoted words.',
        'For a shorter line or OPTION:, copy the whole line/label.',
        'An option and its spoken reply are separate: list both, or write BOTH.',
        'You may explicitly write "Remove all Johnny dialogue in this quest".',
        'A video URL is useful. Add timestamps when needed to locate an exchange.', '',
        'REWIRING: write observed sequence -> desired sequence. Include Johnny-only',
        'waits, Talk prompts, camera checks or forced actions that should be skipped.',
        'State the clues/items/choices/objectives/outcomes that must still happen.',
        'Write "No rewiring needed" after reviewing, or "Unsure: ..." if unclear.',
        'Blank fields and watch-point prompts select no cuts or rewires.', '',
        'VISUAL CLEANUP: Johnny entity/shadow, digital spawn/glitch effect, title/name,',
        'scanner identity, cigarette and smoke. Note locations/timing if relevant.',
        'Unseen branches will be checked against source; a video need not show all routes.',
        'The seven quests already handled by KM2, SD1 and JB1 are not reassigned here.']
    for number, record in enumerate(records, 1):
        lines += ['', '=' * 72, f"{number}. {record['title'].upper()}",
            'Video URL:', 'V voice (optional):',
            'Playthrough search: Cyberpunk 2077 ' + record['title'] + ' full walkthrough', '',
            'WATCH POINTS (prompts only, not selections)', record['watch_prompt'], '',
            'DIALOGUE / OPTIONS TO REMOVE', 'Johnny:', 'V:', 'OPTION:', '',
            'REWIRE NOTES', 'Observed sequence / Johnny dependency:',
            'Desired sequence (or "No rewiring needed"):',
            'Clues/items/choices/objectives/outcomes to preserve:', '',
            'VISUAL / INTERACTION REMNANTS', 'Location, timestamp or description:', '',
            'UNSEEN BRANCHES / UNSURE CUT BOUNDARIES', 'Notes:']
    lines += ['', '=' * 72, 'Return this edited file or paste the notes in chat. No game IDs are needed.',
              'This batch prepares review notes only; implementation follows the returned decisions.']
    notes = out / 'Eight_quest_removal_and_rewire_notes.txt'
    with notes.open('x', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    original = evidence / 'original_notes.txt'
    with original.open('xb') as f:
        f.write(notes.read_bytes())
    text = notes.read_text(encoding='utf-8')
    assert len(re.findall(r'^\d+\. ', text, re.M)) == 8
    assert text.count('\nREWIRE NOTES\n') == text.count('\nDIALOGUE / OPTIONS TO REMOVE\n') == 8
    assert sha(original) == sha(notes)
    protocol = {'schema': 3, 'recorded_date': '2026-11-08', 'status': 'CURRENT_EIGHT_QUEST_USER_REVIEW',
        'previous_protocol': str(PRIOR.parent / 'review_protocol.json'), 'quest_ids': ids,
        'notes': str(notes), 'quote_rule': 'Speaker plus five consecutive words, or full short line/option. Option and spoken reply separate unless BOTH.',
        'rewire_rule': 'Observed -> desired sequence, dependencies to skip and outcomes to preserve. No rewiring needed / Unsure are valid explicit entries. Blank means unreviewed.',
        'visual_targets': ['entity/shadow', 'digital spawn/glitch effect', 'title/name', 'scanner identity', 'cigarette', 'smoke'],
        'selection_rule': 'Only explicit returned notes select proposals. Watch prompts and blanks select nothing. Resolve exact event/option identities, variants, connected choices and callers before implementation.',
        'implementation_or_deployment_authorized': False}
    write(HERE / 'review_protocol.json', protocol)
    manifest = {'schema': 1, 'recorded_date': '2026-11-08', 'status': 'EIGHT_QUEST_HUMAN_REVIEW_PREPARED',
        'scope': 'Eight new editable removal/option/presentation/rewiring note sections. No implementation.',
        'input_pins': {str(p): sha(p) for p in [DB, REGISTRY, POLICY, PRIOR, CURRENT, PACKAGE]},
        'quest_ids': ids, 'quests': records, 'notes': str(notes), 'notes_initial_sha256': sha(notes),
        'original_notes': str(original), 'already_handled_quest_ids': sorted(HANDLED),
        'source_index_limit': 'Pre-JP1 source snapshot. No edited prior-batch resource is reassigned. Versioned scenes remain source evidence; no separate quest count is inferred.',
        'qualification_limit': 'Review leads, not proof every branch runs on the current save. No admission, owner or reward replay is authorized.',
        'approved_removals': 0, 'approved_rewires': 0, 'game_writes': 0, 'save_writes': 0, 'builds': 0}
    write(HERE / 'review_manifest.json', manifest)
    write(HERE / 'checkpoint.json', {'schema': 1, 'status': 'AWAITING_EIGHT_QUEST_DIALOGUE_OPTION_AND_REWIRE_NOTES',
        'recorded_date': '2026-11-08', 'notes': 'output_01/Eight_quest_removal_and_rewire_notes.txt',
        'manifest': 'review_manifest.json', 'protocol': 'review_protocol.json', 'quest_ids': ids,
        'installed_baseline': str(CURRENT), 'installed_epoch': 'JB1',
        'next_action': 'User reviews eight quests on video and edits the notes. Source-match returned quotes/options and review branch/rewiring dependencies before implementation.',
        'approved_removals': 0, 'approved_rewires': 0, 'implementation_authorized': False,
        'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'quests': len(records), 'notes': str(notes), 'sections_checked': 8, 'game_writes': 0, 'save_writes': 0}))


if __name__ == '__main__':
    main()
