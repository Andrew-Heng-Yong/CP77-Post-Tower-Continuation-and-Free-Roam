"""Bind the final Batch 4 worksheet to its reviewed event and caller IDs."""

from collections import Counter
import re
import unicodedata

from resources import read, sha


def normalized(text):
    text = unicodedata.normalize('NFKD', text.lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace("'", '').replace('’', '')
    text = ' '.join(re.findall(r'\w+', text)).replace('gotta bad feeling', 'got a bad feeling')
    return ' '.join(w[:-1] if w.endswith('ing') and len(w) > 4 else w for w in text.split())


def spellings(line):
    return {normalized(t) for t in line['text'].splitlines()}


def event_key(line):
    return line['depot'], line['event_id']


def select(batch, notes):
    review = batch / 'review_01'
    findings_path = review / 'findings.json'
    f = read(findings_path)
    manifest = read(batch / 'review_manifest.json')
    groups = re.split(r'(?m)^\d+\. [^\r\n]+$', notes.decode('utf-8-sig'))[1:]
    by_quest = dict(zip(manifest['quest_ids'], groups, strict=True))
    items = {x['id']: x for x in f['johnny_review_items']}
    previous = {(x['quest_id'], normalized(x['quoted_anchor'])): x['matched_event']
                for x in f['quote_matches']}
    selected = {}
    for quest_id, section in by_quest.items():
        pool = [x['line'] for x in items.values() if x['quest_id'] == quest_id]
        pool += [x['line'] for x in f['associated_v_lines']
                 if items[x['related_ids'][0]]['quest_id'] == quest_id]
        for match in re.finditer(r'(?im)^(J|Johnny|V)(?: \[(B4-\d+)\])?:[ \t]*([^\r\n]+)', section):
            speaker, review_id, quote = match.groups()
            role = 'V' if speaker.lower() == 'v' else 'JOHNNY'
            text = normalized(quote)
            if review_id:
                assert items[review_id]['quest_id'] == quest_id
                event = items[review_id]['line']
                assert text in spellings(event)
            else:
                event = previous.get((quest_id, text))
                if event is None:
                    event, = [v for v in pool if v['speaker'] == role and text in spellings(v)]
            assert event['speaker'] == role
            key = event_key(event)
            assert key not in selected
            selected[key] = event
    assert len(selected) == 49
    assert 'talk to johnny(optional) before confronting frank' in by_quest['mq041_corpo']
    assert 'talk to johnny after confront frank' in by_quest['mq041_corpo']
    assert 'Talk to johnny after check the alley behind the bar' in by_quest['mq306_dumpster']
    before_frank = [x['line'] for x in items.values() if x['status'] == 'FIRST_EXCHANGE_SCOPE_REVIEW']
    before_frank += [x['line'] for x in f['associated_v_lines'] if 'B4-10' in x['related_ids']]
    before_frank += [x['matched_event'] for x in f['quote_matches'] if x['quest_id'] == 'mq041_corpo']
    for event in before_frank + [x for group in f['named_whole_exchanges'].values() for x in group]:
        selected[event_key(event)] = event
    assert all(event_key(x['line']) in selected for x in items.values())
    assert all(event_key(x['line']) in selected for x in f['associated_v_lines'])
    assert Counter(x['speaker'] for x in selected.values()) == {'JOHNNY': 63, 'V': 21}
    dispatches = [x['dispatch'] for x in items.values() if x.get('dispatch')] + [f['pony_bark_confirmed']]
    for dispatch in dispatches:
        del selected[event_key(dispatch['line'])]
    assert len(dispatches) == 4
    # This textless cue belongs to Johnny's disabled laptop actor.
    cue, = [x for x in f['freedom_untranscribed_cues'] if x['speaker'] == 'JOHNNY']
    selected[event_key(cue)] = cue
    assert Counter(x['speaker'] for x in selected.values()) == {'JOHNNY': 60, 'V': 21}
    return {
        'findings': str(findings_path), 'findings_sha256': sha(findings_path),
        'events': list(selected.values()), 'dispatches': dispatches,
        'removed_option_groups': [f['scope_options'][key] for key in
                                  ('war_pigs_before_frank', 'no_easy_way_out_after_alley')],
        'retained_options': f['scope_options']['shot_by_both_sides_plant_prompts']
                            + f['scope_options']['beat_on_the_brat_razor_question'],
        'textless_johnny_cue': cue,
    }
