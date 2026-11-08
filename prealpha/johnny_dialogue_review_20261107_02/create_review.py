"""Transcribe every caller-qualified Johnny event in five complete quest closures.

Context alternatives follow source graph edges, stop at scene/ordering boundaries,
and never manufacture continuity between separately triggered conversations.
"""
import collections
import gzip
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path
from prepare_sources import TASK, WS, load, sha

sys.path.insert(0, str(WS / 'tools/parity_audit'))
from model import Resource

DB = WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
DB_SHA = 'A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E'


def json_source(path):
    path = Path(path)
    if path.suffix == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8-sig') as stream:
            return json.load(stream)
    return load(path)


def pointer(obj, path):
    for part in path.lstrip('/').split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


class Scene:
    def __init__(self, row, con, verified_sources, providers, local_fact_seed=None):
        self.row = row
        self.resource = row['resource']
        self.con = con
        self.verified_sources = verified_sources
        self.providers = providers
        self.check_source(self.resource)
        self.raw = Resource(json_source(self.resource['json_path']))
        self.model = self.raw.normalize()
        assert not self.model['errors'], self.model['errors']
        self.graph = self.model['graphs']['scene']
        self.nodes = self.graph['nodes']
        self.adj = collections.defaultdict(list)
        for edge in self.graph['edges']:
            destination = self.nodes[edge[2]]
            if destination['type'] == 'scnQuestNode':
                mappings = destination['payload'].get('isockMappings', [])
                ordinal = int(edge[3].split(':')[1])
                if ordinal < len(mappings) and mappings[ordinal].get('$value') == 'CutDestination':
                    continue  # Cancellation is not dialogue playback.
            self.adj[edge[0]].append(edge)
        entries = self.graph['entries']
        self.called_entries = sorted({name for caller in row['callers'] if caller['may_reachable_in_phase']
                                      for name in caller['entry_names'] if name in entries})
        self.reachable = {entries[name] for name in self.called_entries}
        todo = list(self.reachable)
        while todo:
            for edge in self.adj[todo.pop()]:
                if edge[2] not in self.reachable:
                    self.reachable.add(edge[2])
                    todo.append(edge[2])
        self.lines = {str(x['itemId']['id']): x for x in self.raw.root['screenplayStore']['lines']}
        self.actors = {str(x['actorId']['id']): x for x in self.raw.root['actors']}
        self.players = {str(x['actorId']['id']): x for x in self.raw.root['playerActors']}
        self.events = {}
        self.sections = {}
        self.root_id = self.resource['resource_id'] + '/root'
        for nid, node in self.nodes.items():
            if nid not in self.reachable:
                continue
            spoken = []
            for ordinal, raw in enumerate(node['payload'].get('events', [])):
                if raw.get('$type') == 'scnDialogLineEvent':
                    key = f'{self.root_id}/scene/{nid}/event/{ordinal}'
                    e = self.transcribe(key, raw, ordinal)
                    self.events[key] = e
                    spoken.append(e)
            if spoken:
                self.sections[nid] = sorted(spoken, key=lambda e: (float(e['event']['start_time']), e['event']['event_ordinal']))
        self.choice_cache = {}
        self.rejected_fact_paths = []
        self.local_fact_seed = local_fact_seed or {}
        self.local_fact_states = self.propagate_local_fact()
        self.projections = {}
        self.forward = collections.defaultdict(list)
        self.backward = collections.defaultdict(list)
        self.boundaries = collections.defaultdict(list)
        self.build_event_graph()

    def check_source(self, resource):
        for pk, hk in [('raw_path', 'raw_sha256'), ('json_path', 'json_sha256')]:
            path = resource[pk]
            if path not in self.verified_sources:
                actual = sha(path)
                assert actual == resource[hk], (path, actual, resource[hk])
                self.verified_sources[path] = actual

    def transcribe(self, key, raw, ordinal):
        row = dict(self.con.execute('select * from events where event_key=?', (key,)).fetchone())
        item = dict(self.con.execute('select * from search_items where item_key=?', (key,)).fetchone())
        line = self.lines[str(raw['screenplayLineId']['id'])]
        assert str(raw['id']['id']) == row['event_id']
        assert str(raw['screenplayLineId']['id']) == row['line_id']
        assert str(raw['startTime']) == row['start_time'] and str(raw['duration']) == row['duration']
        assert ordinal == row['event_ordinal']
        assert str(line['locstringId']['ruid']) == item['loc_id']
        actor = str(line['speaker']['id'])
        if actor in self.players:
            assert item['speaker_role'] == 'V'
            speaker = 'V'
        else:
            name = self.actors[actor]['actorName']
            if item['speaker_role'] == 'JOHNNY':
                assert name.lower().startswith('johnny'), name
                speaker = 'Johnny'
            else:
                speaker = name
        locs = [dict(r) for r in self.con.execute("select * from localization where loc_id=? and locale='en_us' and root_id is null", (item['loc_id'],))]
        assert locs and any(r['text'] for r in locs), (key, item['loc_id'])
        for loc in locs:
            provider_id = loc['provider_resource_id']
            if provider_id not in self.providers:
                provider = dict(self.con.execute('select * from resources where resource_id=?', (provider_id,)).fetchone())
                self.check_source(provider)
                self.providers[provider_id] = {'resource': provider, 'data': json_source(provider['json_path'])}
            assert pointer(self.providers[provider_id]['data'], loc['source_path']) == loc['text']
        variants = {r['gender']: r['text'] for r in locs}
        female = variants.get('female', '')
        male = variants.get('male', '') or female
        assert female and male
        sid = 'J5-' + hashlib.sha256(key.encode()).hexdigest()[:10].upper()
        return {'short_id': sid, 'event_key': key, 'event': row, 'speaker': speaker,
                'speaker_actor_id': actor, 'speaker_role': item['speaker_role'], 'loc_id': item['loc_id'],
                'text_variants': {'female': female, 'male': male}, 'localization': locs,
                'raw_line': line, 'raw_event': raw, 'decision': 'PENDING_HUMAN_REVIEW'}

    def choices(self, node):
        if node not in self.choice_cache:
            choices = {}
            for row in self.con.execute("select * from choices where root_id=? and graph_path='scene' and node_id=?", (self.root_id, node)):
                r = dict(row)
                texts = sorted({x[0] for x in self.con.execute("select text from localization where root_id=? and loc_id=? and locale='en_us' and text<>''", (self.root_id, r['loc_id']))})
                label = texts[0] if len(texts) == 1 and '\x00' not in texts[0] else 'interaction (displayed caption unresolved)'
                choices[r['output_stamp']] = {'label': label, 'choice_key': r['choice_key'],
                                             'conditions': json.loads(r['conditions_json']), 'source': r}
            self.choice_cache[node] = choices
        return self.choice_cache[node]

    def transition_note(self, edge):
        node = self.nodes[edge[0]]
        p = node['payload']
        if node['type'] == 'scnChoiceNode':
            choice = self.choices(edge[0]).get(edge[1])
            return {'kind': 'CHOICE', 'node': edge[0], **choice} if choice else None
        q = p.get('questNode', {})
        if q.get('$type') == 'questConditionNodeDefinition':
            mappings = p.get('osockMappings', [])
            ordinal = int(edge[1].split(':')[1])
            branch = mappings[ordinal].get('$value') if ordinal < len(mappings) else edge[1]
            return {'kind': 'CONDITION', 'node': edge[0], 'branch': branch, 'condition': q.get('condition')}
        if q.get('$type') == 'questPauseConditionNodeDefinition':
            return {'kind': 'WAIT', 'node': edge[0], 'condition': q.get('condition')}
        return None

    def project(self, source):
        """Find next spoken sections while retaining exact choices/control paths."""
        found = []
        ends = []
        source_payload = self.nodes[source]['payload']
        last = float(self.sections[source][-1]['event']['start_time'])
        socket_times = {}
        for e in source_payload.get('events', []):
            if e.get('$type') == 'scneventsSocket':
                stamp = e['osockStamp']
                socket_times[f'{stamp["name"]}:{stamp["ordinal"]}'] = float(e['startTime'])
        for first in self.adj[source]:
            if first[1] in socket_times and socket_times[first[1]] < last:
                # A parallel helper is not evidence that another section follows all local speech.
                ends.append({'reason': 'PARALLEL_TIMED_OUTPUT', 'edge': first})
                continue
            stack = [(first[2], [first], frozenset({source}), [])]
            visits = 0
            while stack:
                node, path, seen, notes = stack.pop()
                visits += 1
                assert visits < 30000, ('Projection needs manual expansion', source)
                if node in seen:
                    ends.append({'reason': 'CONTROL_CYCLE', 'path': path})
                    continue
                if node in self.sections:
                    found.append({'target_section': node, 'path': path, 'notes': notes})
                    continue
                if len(path) > 100:
                    ends.append({'reason': 'CONTROL_DEPTH_HOLD', 'path': path})
                    continue
                if node not in self.reachable:
                    continue
                next_edges = self.adj[node]
                if self.nodes[node]['type'] == 'scnChoiceNode':
                    valid = self.choices(node)
                    next_edges = [e for e in next_edges if e[1] in valid]
                if not next_edges:
                    ends.append({'reason': 'SCENE_OR_CONTROL_BOUNDARY', 'path': path})
                for edge in next_edges:
                    note = self.transition_note(edge)
                    stack.append((edge[2], path + [edge], seen | {node}, notes + ([note] if note else [])))
        unique = {}
        for f in found:
            key = (f['target_section'], json.dumps(f['notes'], sort_keys=True))
            unique.setdefault(key, f)
        self.projections[source] = {'connections': list(unique.values()), 'boundaries': ends}
        return list(unique.values()), ends

    def link(self, a, b, evidence):
        self.forward[a].append({'event_key': b, 'evidence': evidence})
        self.backward[b].append({'event_key': a, 'evidence': evidence})

    def build_event_graph(self):
        for section, spoken in self.sections.items():
            for a, b in zip(spoken, spoken[1:]):
                self.link(a['event_key'], b['event_key'], {'kind': 'AUTHORED_SECTION_TIME', 'section': section})
            connections, ends = self.project(section)
            for connection in connections:
                self.link(spoken[-1]['event_key'], self.sections[connection['target_section']][0]['event_key'],
                          {'kind': 'CONDITIONAL_SOURCE_PATH', **connection})
            self.boundaries[spoken[-1]['event_key']] = ends

    def contexts(self, target, direction, count):
        links = self.forward if direction == 'after' else self.backward
        stack = [(target, [], [], frozenset({target}))]
        results = {}
        expansions = 0
        while stack:
            current, selected, evidence, seen = stack.pop()
            expansions += 1
            assert expansions < 250000, ('Context needs manual expansion', target, direction)
            if len(selected) == count:
                key = tuple(selected)
                if self.fact_path_possible(evidence if direction == 'after' else list(reversed(evidence)),
                                           target if direction == 'after' or not selected else selected[-1]):
                    results.setdefault(key, {'events': selected, 'evidence': evidence, 'complete': True})
                continue
            candidates = [e for e in links[current] if e['event_key'] not in seen]
            if not candidates:
                key = tuple(selected)
                if self.fact_path_possible(evidence if direction == 'after' else list(reversed(evidence)),
                                           target if direction == 'after' or not selected else selected[-1]):
                    results.setdefault(key, {'events': selected, 'evidence': evidence, 'complete': False,
                                             'boundary': 'Scene entry/end, independent trigger, parallel timing, or repeated-topic boundary; no fixed continuation is asserted.'})
                continue
            for link in candidates:
                e = self.events[link['event_key']]
                next_selected = selected + [e['event_key']] if direction == 'before' or e['speaker'] == 'V' else selected
                stack.append((e['event_key'], next_selected, evidence + [link['evidence']], seen | {e['event_key']}))
        result = list(results.values()) or [{'events': [], 'evidence': [], 'complete': False,
                                             'boundary': 'Context requires additional ordering evidence.'}]
        if direction == 'before':
            for r in result:
                r['events'].reverse()
                r['evidence'].reverse()
        # Shorter paths ending at a control helper are not alternative dialogue routes
        # when their selected lines are a strict suffix/prefix of a longer result.
        result = [r for r in result if r['complete'] or not any(
            len(s['events']) > len(r['events']) and
            (s['events'][-len(r['events']):] == r['events'] if direction == 'before' and r['events'] else
             s['events'][:len(r['events'])] == r['events']) for s in result)]
        return sorted(result, key=lambda r: (not r['complete'], r['events']))

    def propagate_local_fact(self):
        """Propagate one source-proven fresh-entry flag through this scene."""
        if not self.local_fact_seed:
            return {}
        assert len(self.local_fact_seed) == 1
        name, initial = next(iter(self.local_fact_seed.items()))
        seeds = [self.graph['entries'][n] for n in self.called_entries]
        todo = [(n, initial) for n in seeds]
        seen = set()
        states = collections.defaultdict(set)
        while todo:
            node, value = todo.pop()
            if (node, value) in seen:
                continue
            assert len(seen) < 10000 and abs(value) < 100, 'Unbounded fact loop needs manual review.'
            seen.add((node, value))
            states[node].add(value)
            payload = self.nodes[node]['payload']
            q = payload.get('questNode', {})
            t = q.get('type', {})
            if q.get('$type') == 'questFactsDBManagerNodeDefinition' and t.get('$type') == 'questSetVar_NodeType' and t.get('factName') == name:
                value = t['value'] if t.get('setExactValue') else value + t['value']
            edges = self.adj[node]
            if self.nodes[node]['type'] == 'scnChoiceNode':
                edges = [e for e in edges if e[1] in self.choices(node)]
            c = q.get('condition', {}).get('type', {})
            if q.get('$type') == 'questConditionNodeDefinition' and isinstance(c, dict) and c.get('$type') == 'questVarComparison_ConditionType' and c.get('factName') == name:
                assert c['comparisonType'] == 'GreaterOrEqual'
                expected = value >= c['value']
                mappings = payload['osockMappings']
                edges = [e for e in edges if mappings[int(e[1].split(':')[1])]['$value'] == ('True' if expected else 'False')]
            todo.extend((e[2], value) for e in edges)
        return {n: sorted(values) for n, values in states.items()}

    def fact_path_possible(self, evidence, start_event):
        if self.local_fact_seed:
            name = next(iter(self.local_fact_seed))
            node = self.events[start_event]['event']['node_id']
            return any(self._fact_path_possible(evidence, {name: value}) for value in self.local_fact_states.get(node, []))
        return self._fact_path_possible(evidence, {})

    def _fact_path_possible(self, evidence, initial):
        """Reject a branch contradicted by a known authored write on that path.

        Unknown native/history/skill values remain conditional. This is a narrow
        consistency check, not an engine execution model or owner simulation.
        """
        facts = dict(initial)

        def evaluate(condition):
            if not isinstance(condition, dict):
                return None
            kind = condition.get('$type')
            if kind == 'questLogicalCondition':
                vals = [evaluate(c) for c in condition.get('conditions', [])]
                if condition.get('operation') == 'AND':
                    return False if False in vals else True if vals and all(v is True for v in vals) else None
                if condition.get('operation') == 'OR':
                    return True if True in vals else False if vals and all(v is False for v in vals) else None
            if kind == 'questFactsDBCondition':
                t = condition.get('type', {})
                if t.get('$type') != 'questVarComparison_ConditionType' or t.get('factName') not in facts:
                    return None
                a, b = facts[t['factName']], t['value']
                operations = {'Equal': lambda: a == b, 'NotEqual': lambda: a != b,
                              'Greater': lambda: a > b, 'GreaterOrEqual': lambda: a >= b,
                              'Less': lambda: a < b, 'LessOrEqual': lambda: a <= b}
                op = operations.get(t.get('comparisonType'))
                return op() if op else None
            return None

        for link in evidence:
            for edge in link.get('path', []):
                payload = self.nodes[edge[0]]['payload']
                q = payload.get('questNode', {})
                if q.get('$type') == 'questFactsDBManagerNodeDefinition':
                    write_fact = q.get('type', {})
                    if write_fact.get('$type') == 'questSetVar_NodeType':
                        name = write_fact['factName']
                        if write_fact.get('setExactValue'):
                            facts[name] = write_fact['value']
                        elif name in facts:
                            facts[name] += write_fact['value']
                if q.get('$type') == 'questConditionNodeDefinition':
                    mappings = payload.get('osockMappings', [])
                    ordinal = int(edge[1].split(':')[1])
                    label = mappings[ordinal].get('$value') if ordinal < len(mappings) else None
                    result = evaluate(q.get('condition'))
                    if result is not None and label in ('True', 'False') and result != (label == 'True'):
                        self.rejected_fact_paths.append({'edge': edge, 'known_authored_facts': dict(facts),
                                                         'condition': q.get('condition')})
                        return False
        return True


def main():
    output = TASK / 'output_03'
    qa = TASK / 'qa_03'
    assert not output.exists() and not qa.exists()
    assert sha(DB) == DB_SHA
    baseline = DB.stat()
    con = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    inventory = load(TASK / 'evidence_03/quest_dialogue_inventory.json')
    sources = load(TASK / 'evidence_01/source_inventory.json')
    phases = load(TASK / 'evidence_03/phase_graphs.json')
    verified_sources = {}
    providers = {}
    quests = []
    event_map = {}
    excluded = []
    scene_models = []
    for quest in inventory['quests']:
        q = {'id': quest['id'], 'title': quest['title'], 'registry': quest['registry'], 'scenes': [], 'review_items': []}
        for row in sorted(quest['scenes'], key=lambda s: s['resource']['depot']):
            called = [c for c in row['callers'] if c['entry_names'] and c['may_reachable_in_phase']]
            if not called:
                excluded.append({'quest': quest['id'], 'resource': row['resource'],
                                 'johnny_source_events': len(row['johnny_events']), 'callers': row['callers'],
                                 'reason': 'No connected reachable scene-input caller in this quest closure. Import presence alone is not execution evidence.'})
                continue
            local_seed = {}
            if row['resource']['resource_id'] == '90c76218185ecad8483a5352':
                guard = phases[quest['entry'].lower()]['model']['graphs']['root']['nodes']['65003']
                assert guard['payload']['condition']['operation'] == 'AND'
                assert any(r.get('factName') == 'mq016_recognized_bartmoss' and r.get('comparisonType') == 'Equal' and r.get('value') == 0 for r in guard['reads'])
                local_seed = {'mq016_recognized_bartmoss': 0}
            scene = Scene(row, con, verified_sources, providers, local_seed)
            scene_models.append(scene)
            targets = sorted((e for e in scene.events.values() if e['speaker'] == 'Johnny'),
                             key=lambda e: (int(e['event']['node_id']), float(e['event']['start_time']), e['event']['event_ordinal']))
            assert len(targets) == len(row['johnny_events']), 'Unreachable Johnny events need an explicit scope decision.'
            for target in targets:
                before = scene.contexts(target['event_key'], 'before', 3)
                after = scene.contexts(target['event_key'], 'after', 5)
                q['review_items'].append({'target': target['event_key'], 'before': before, 'after_v': after,
                                          'source_scene': scene.resource['depot'], 'called_entries': scene.called_entries})
            event_map.update(scene.events)
            q['scenes'].append({'resource': scene.resource, 'callers': called,
                                'called_entries': scene.called_entries, 'johnny_event_count': len(targets),
                                'local_fact_seed': scene.local_fact_seed, 'local_fact_states': scene.local_fact_states,
                                'projections': scene.projections})
        quests.append(q)
    targets = [r['target'] for q in quests for r in q['review_items']]
    assert len(targets) == len(set(targets)) == 49, len(targets)
    for target in targets:
        assert event_map[target]['speaker'] == 'Johnny'
    assert len({e['short_id'] for e in event_map.values()}) == len(event_map)
    used = set(targets)
    for q in quests:
        for r in q['review_items']:
            for context in r['before'] + r['after_v']:
                used.update(context['events'])

    doc = [
        'JOHNNY DIALOGUE REMOVAL — FIVE-QUEST HUMAN REVIEW',
        'Revision J5-03 | English | 7 November 2026', '',
        'Every caller-qualified indexed Johnny dialogue occurrence in the five quest source closures is included: 49 Johnny entries.',
        'No total transcript-line limit. Context and alternate branches add further entries.', '',
        'HOW TO EDIT',
        'Keep only dialogue entries you want REMOVED from the game. Delete entries you want kept. Keep each retained [J5-XXXXXXXXXX] ID attached to its complete text.',
        'ANY numbered dialogue entry can be selected, including ANY Johnny line shown in preceding context. The section headings do not restrict removal selections.',
        'Repeated IDs refer to the same event. Keeping one copy requests that event once; delete every copy to leave that event unselected.',
        'Female/male V wording appears under one event ID where it differs. Keep or delete the complete entry; add a note for a variant-specific request.',
        'Headings, route descriptions and boundary notes are not removal selections. The original file approves no cuts; return your edited copy for mapping.', '',
        'READING THE CONTEXT',
        'Each Johnny entry has the preceding three spoken lines from any speaker and the next five V lines, where that sequence can be traced inside the scene.',
        'Different possible source branches are separate alternatives. Preceding and following alternatives are listed independently; they are not stitched into a single asserted playthrough.',
        'The following-V lists omit intervening Johnny/NPC lines. A V line is context, not an automatic reaction classification.',
        'Standalone barks, scene entries/exits, independent player triggers and uncertain parallel timing can leave fewer than three preceding or five following V lines. These limits are marked; unrelated dialogue is never added to fill a quota.',
        'Quest progression and player choices can place other conversations between separately triggered clips. This document does not invent their order.',
        'Choices identify source branches only and are not selectable transcript entries. Native prerequisites, life path, earned history, ownership and current admission still apply.', '',
        'QUESTS INCLUDED',
    ]
    for q in quests:
        doc.append(f'  {q["title"]}: {len(q["review_items"])} Johnny entries')
    doc += ['', 'Small Man, Big Mouth requires Streetkid history. These Boots Are Made for Walkin\' requires Nomad history. These are separate conditional quest routes.',
            'This is a source-based dialogue review. It is not a gameplay test or a patch.', '']
    shown = []

    def lines(key):
        e = event_map[key]
        shown.append(e['short_id'])
        v = e['text_variants']
        prefix = f'[{e["short_id"]}] {e["speaker"]}: '
        if v['female'] == v['male']:
            return [prefix + v['female'], '']
        return [prefix, '    Female wording: ' + v['female'], '    Male wording: ' + v['male'], '']

    def branch_label(context):
        labels = []
        conditions = []
        for e in context['evidence']:
            for n in e.get('notes', []):
                if n['kind'] == 'CHOICE' and n['label'] not in labels:
                    labels.append(n['label'])
                if n['kind'] == 'CONDITION':
                    conditions.append(n)
        label = ' → '.join(labels) if labels else 'Same authored exchange / connected source path'
        if conditions:
            label += ' (conditional source branch; exact conditions retained in the mapping)'
        return label

    number = 0
    for q in quests:
        doc += ['=' * 78, q['title'].upper(), '', 'Eligibility: ' + q['registry']['requirements'], '']
        for item in q['review_items']:
            number += 1
            doc += ['-' * 78, f'JOHNNY ENTRY {number:02d} OF {len(targets)}',
                    'Scene: ' + item['source_scene'].split('\\')[-1], '', 'PRECEDING THREE LINES — ANY SPEAKER']
            for i, context in enumerate(item['before'], 1):
                doc += [f'Before alternative {i}: ' + branch_label(context)]
                for key in context['events']:
                    doc += lines(key)
                if not context['complete']:
                    doc += [f'[Only {len(context["events"])} preceding line(s) traceable before this source boundary. Earlier in-game dialogue is not fixed by this clip.]', '']
            doc += ['JOHNNY LINE'] + lines(item['target']) + ['FOLLOWING FIVE V LINES']
            for i, context in enumerate(item['after_v'], 1):
                doc += [f'Following alternative {i}: ' + branch_label(context)]
                for key in context['events']:
                    doc += lines(key)
                if not context['complete']:
                    doc += [f'[Only {len(context["events"])} following V line(s) traceable before this source boundary. Further context requires a separately triggered conversation, repeated topic or unresolved timing.]', '']
    doc += ['END OF FIVE-QUEST REVIEW', 'Return only your retained removal selections with their event IDs.', '']
    output.mkdir()
    qa.mkdir()
    path = output / 'Johnny_review_five_quests_03.txt'
    path.write_bytes(('\r\n'.join(doc)).encode('utf-8-sig'))
    baseline_path = TASK / 'evidence_05/original_review_five_quests_03.txt'
    baseline_path.write_bytes(path.read_bytes())
    manifest = {'schema': 1, 'revision': 'J5-03', 'status': 'AWAITING_HUMAN_REVIEW',
                'request': 'Five quests worth of Johnny lines, each with three preceding lines from any speaker and five following V lines; no total line cap.',
                'source_index': str(DB.relative_to(WS)), 'source_index_sha256': DB_SHA,
                'document': str(path.relative_to(WS)), 'document_sha256': sha(path),
                'preserved_original': str(baseline_path.relative_to(WS)),
                'quests': quests, 'items': [event_map[k] for k in sorted(used)],
                'excluded_import_only_scenes': excluded,
                'verified_sources': verified_sources, 'localization_providers': [r['resource'] for r in providers.values()],
                'counts': {'quests': len(quests), 'johnny_entries': len(targets),
                           'displayed_entries': len(shown), 'unique_event_ids': len(used),
                           'before_alternatives': sum(len(r['before']) for q in quests for r in q['review_items']),
                           'after_v_alternatives': sum(len(r['after_v']) for q in quests for r in q['review_items']),
                           'approved_removal_events': 0},
                'limits': ['Scene/control boundaries and unknown ordering are explicitly marked.',
                           'Conditional graph paths are source candidates, not executing-owner or gameplay proof.',
                           'Repeated dialogue cycles are not replayed to pad a context window.',
                           'Audio delivery, nonverbal presentation, choices and legacy/native saved-owner paths need separate implementation review.'],
                'fact_path_consistency': {'rejected_contradictory_context_paths': sum(len(s.rejected_fact_paths) for s in scene_models),
                                          'evidence': [r for s in scene_models for r in s.rejected_fact_paths]},
                'generator_sha256': sha(__file__), 'game_writes': 0, 'save_writes': 0}
    write(TASK / 'evidence_05/review_manifest.json', manifest)
    text = path.read_text(encoding='utf-8-sig')
    actual_ids = re.findall(r'^\[(J5-[0-9A-F]{10})\]', text, re.M)
    assert actual_ids == shown
    assert len(re.findall(r'^JOHNNY ENTRY \d+ OF 49$', text, re.M)) == 49
    assert path.read_bytes() == baseline_path.read_bytes()
    assert DB.stat().st_size == baseline.st_size and DB.stat().st_mtime_ns == baseline.st_mtime_ns
    verification = {'status': 'PASS_WITH_EXPLICIT_CONTEXT_BOUNDARIES', 'counts': manifest['counts'],
                    'document_sha256': sha(path),
                    'checked': ['Every caller-qualified indexed Johnny event in all five source closures appears once as a Johnny review entry.',
                                'Independent raw scene event/line/speaker/time and external localization pointer checks for every transcript item.',
                                'Scene/raw/export/localization hashes and selected read-only database SHA256.',
                                'Actual phase scene-input callers; import-only unconnected scene excluded with evidence.',
                                'All retained context edges come from source graphs; choices, conditions and timing boundaries preserved.',
                                'Text readback ID order and exact original-copy equality.'],
                    'not_claimed': ['Complete runtime chronology across independently triggered scenes.',
                                    'Gameplay or save-owner validation.', 'Any approved cut, build, deployment or game/save mutation.'],
                    'game_writes': 0, 'save_writes': 0}
    write(qa / 'verification.json', verification)
    print(json.dumps({'document': str(path), 'counts': manifest['counts'], 'bytes': path.stat().st_size,
                      'verification': verification['status']}, indent=2))


if __name__ == '__main__':
    main()
