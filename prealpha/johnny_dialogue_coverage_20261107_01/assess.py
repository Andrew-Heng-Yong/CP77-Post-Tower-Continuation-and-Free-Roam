"""Close each Step 1 inventory item and assess (without editing) Step 2."""

import gzip
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from prepare import TASK, WORKSPACE, STEP1, STEP2, read, sha, write

sys.path.insert(0, str(WORKSPACE / 'tools/parity_audit'))
from model import Resource
from common import walk, value

OUT = TASK / 'evidence_07'


def resource_key(depot):
    if depot.isdecimal():
        return depot
    result = 14695981039346656037
    for byte in depot.replace('/', '\\').lower().encode('utf-8'):
        result = ((result ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return str(result)


def identity(row):
    return row['archive'].casefold(), row.get('key', row.get('depot_key'))


def load_export(row):
    data = Path(row['json']).read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != row['json_sha256']:
        raise ValueError('Export hash changed')
    return json.loads(gzip.decompress(data))


def main():
    if OUT.exists():
        raise SystemExit('A fresh assessment directory is required')
    prepared = read(TASK / 'evidence_01/prepared.json')
    initial = read(STEP1 / 'capture.json')
    additions = read(STEP1 / 'capture_additions.json')
    resources = initial['resources'] + additions['resources']
    old_by = {identity(r): r for r in resources}
    unresolved = read(STEP1 / 'unresolved.json')
    entries = read(STEP1 / 'entry_sources.json')
    refinement = read(STEP1 / 'refinement.json')
    frozen = read(TASK / 'evidence_03/frozen_inventory.json')
    aliases = {r['depot']: r for r in read(TASK / 'evidence_06/path_aliases.json')['rows']}
    tables = {}
    for name in ['evidence_02/tables.jsonl', 'evidence_03/tables.jsonl']:
        for line in (TASK / name).read_text(encoding='utf-8-sig').splitlines():
            row = json.loads(line)
            if identity(row) in tables:
                assert tables[identity(row)]['sha256'] == row['sha256']
            tables[identity(row)] = row
    exports = [json.loads(s) for s in (TASK / 'evidence_05/exports.jsonl').read_text().splitlines()]
    assert len(exports) == 476 and all(r['status'] == 'EXPORTED' for r in exports)
    conn = sqlite3.connect(Path(prepared['database']['path']).as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    db_resources = {r['resource_id']: dict(r) for r in conn.execute('SELECT * FROM resources')}
    db_by_key = defaultdict(list)
    for row in db_resources.values():
        db_by_key[row['depot_key']].append(row)
    db_by_identity = {identity(r): r for r in db_resources.values()}
    # The preceding preparation pinned the full DB. Integrity and source checks
    # on these same bytes are reused, rather than rerunning the old verifier.
    assert sha(prepared['database']['path']) == prepared['database']['sha256']
    assert read(STEP2 / 'index_02/verification.json')['status'] == 'PASS'

    references = []
    reverse = defaultdict(list)

    def add_reference(source, target, evidence):
        if not target or target in {'0', 'None'}:
            return
        row = {'source_depot': source['depot'], 'source_archive': source['archive'],
               'source_key': source.get('key', source.get('depot_key')),
               'source_sha256': source.get('sha256', source.get('raw_sha256')),
               'target_depot': target, 'target_key': resource_key(target), 'evidence': evidence}
        references.append(row)
        reverse[row['target_key']].append(row)

    for row in resources:
        for target in row['imports']:
            add_reference(row, target, 'DECODED_CR2W_IMPORT')
        for target in set(row['binary_graph_reference_candidates']) - set(row['imports']):
            add_reference(row, target, 'BINARY_REFERENCE_LEAD')
    for row in tables.values():
        if identity(row) not in old_by or old_by[identity(row)]['status'] == 'OPAQUE':
            for target in row['imports']:
                add_reference(row, target, 'CR2W_HEADER_IMPORT')
    for row in conn.execute('SELECT * FROM aux_links'):
        add_reference(db_resources[row['resource_id']], row['target_depot'],
                      'CONVERSATION_SERIALIZED_SCENE_TARGET')

    graph_inventory = []
    for row in initial['graph_provider_census']:
        archive = initial['archives'][row['archive_index']]['path']
        ident = archive.casefold(), row['key']
        source = old_by.get(ident) or tables.get(ident)
        assert source is not None, ('Unaccounted graph provider', ident)
        graph_inventory.append({**row, 'archive': archive,
            'source_sha256': source['sha256'], 'root_type': source['root_type'],
            'inventory_evidence': 'EXISTING_DECODE' if ident in old_by and old_by[ident]['status'] != 'OPAQUE' else 'HEADER_TABLES',
            'next_action': 'Use actual entry sockets and eligibility evidence for route review. This resource reference census does not prove execution.'})
    unknown_inventory = []
    unknown_scene_missing = []
    for row in frozen['rows']:
        if not row['unnamed']:
            continue
        source = tables.get(identity(row)) or old_by.get(identity(row))
        assert source is not None
        kind = source['root_type']
        indexed = db_by_identity.get(identity(row))
        magic = source.get('magic')
        if kind == 'scnSceneResource':
            assert indexed, ('Unindexed unnamed scene', identity(row))
            decision = 'SCENE_ALREADY_INDEXED'
            action = 'Review actual post-Tower routes during Step 3; retain hash-key identity even when the depot name is unavailable.'
        elif kind == 'JsonResource' and Path(row['archive']).name == 'lang_en_text.archive':
            decision = 'ADDITIONAL_ENGLISH_SUBTITLE_PROVIDER'
            action = 'Step 2 successor must add this exact provider and qualify dialogue text lookups. Do not use external subtitle text as choice captions.'
        elif kind in {'questQuestPhaseResource', 'questQuestResource', 'gsmGameDefinition'}:
            decision = 'GRAPH_CALLER_HEADER_INVENTORIED'
            action = 'Use the retained imports and source identity as caller leads. Trace connected entries before proposing an edit.'
        elif not kind:
            assert source.get('status') == 'NON_CR2W_SIGNATURE'
            decision = 'NON_CR2W_MEDIA_SIGNATURE'
            action = 'Use the retained signature and exact source hash for any later media lookup; media identity alone does not select a dialogue event.'
        else:
            decision = 'SUPPORT_TYPE_INVENTORIED'
            action = 'Retain as typed support. Trace actor/caller dependencies when reviewing a related event; no dialogue exclusion is inferred from a filename.'
        unknown_inventory.append({**row, 'root_type': kind, 'magic': magic,
            'source_sha256': source['sha256'], 'classification': decision,
            'indexed_resource_id': indexed['resource_id'] if indexed else None,
            'next_action': action})
    assert len(unknown_inventory) == 9729
    assert all(r['observed'] == r['expected'] for r in frozen['unknown_counts'])

    source_text = {row['path']: Path(row['path']).read_text(encoding='utf-8-sig').splitlines()
                   for row in entries['source_files']}
    lexical = defaultdict(list)
    for row in refinement['literal_resource_references']:
        line = source_text[row['path']][row['line'] - 1]
        lexical[row['depot']].append({**row, 'text': line,
            'comment_only': line.lstrip().startswith(('#', '//', '--'))})
    missing_inventory = []
    for row in unresolved['missing_candidates']:
        alias = aliases[row['depot']]
        inbound = reverse[resource_key(row['depot'])]
        lex = lexical[row['depot']]
        if alias['providers']:
            classification = 'RESOURCEPATH_CASE_ALIAS_RESOLVED'
            action = 'Use the sanitized depot/key and retain the original spelling in provenance. No game-resource change is required.'
        elif lex and all(r['comment_only'] for r in lex) and not inbound:
            classification = 'COMMENT_ONLY_REFERENCE_WITHOUT_PROVIDER'
            action = 'Keep as inactive source evidence. Recheck if that external configuration is enabled or changes.'
        elif inbound:
            classification = 'SERIALIZED_REFERENCE_WITHOUT_PROVIDER'
            action = 'Trace the actual calling node and route before deciding whether this absent dependency affects post-Tower content. Keep its availability unknown.'
        else:
            classification = 'EXTERNAL_LEXICAL_REFERENCE_WITHOUT_PROVIDER'
            action = 'Preserve this external-mod compatibility boundary and inspect its caller/optional entitlement before treating it as required dialogue support.'
        missing_inventory.append({**row, 'classification': classification,
            'normalized_lookup': alias, 'source_references': inbound,
            'source_literals': lex, 'next_action': action})
    assert len(missing_inventory) == 91

    collision_inventory = []
    for row in unresolved['multiple_provider_depots']:
        identical = len({p['sha256'] for p in row['providers']}) == 1
        assert identical == row['payloads_identical']
        collision_inventory.append({**row,
            'classification': 'EQUIVALENT_CAPTURED_BYTES' if identical else 'DIFFERENT_PROVIDERS_RETAINED',
            'next_action': 'No dialogue-byte ambiguity within these captured providers.' if identical else
                'Resolve the executing provider before patching or approving an occurrence. All provider payloads and references remain in the inventory; lexical order is not load-order proof.'})

    opaque_inventory = []
    for row in unresolved['opaque_provider_payloads']:
        source = next(r for r in resources if r['depot'] == row['depot'] and r['archive'] == row['archive'])
        table = tables[identity(source)]
        assert table['sha256'] == row['sha256'] and table['status'] == 'CR2W_TABLES_READ'
        opaque_inventory.append({**row, 'key': source['key'],
            'header_status': 'IMPORT_TABLE_RECOVERED_OBJECT_DECODE_STILL_OPAQUE',
            'root_type': table['root_type'], 'imports': table['imports'],
            'next_action': 'Step 2 needs a supported decoder or a documented hold for this scene; preserve exact bytes and do not invent its transcript.' if row['depot'].endswith('.scene') else
                'Resolve placement/actor/caller scope during route review, or retain an explicit placement hold. Header imports do not prove full world-node parity.'})

    conversations = []
    seeds = set(read(STEP2 / 'evidence_01/prepared.json')['conversation_seeds'])
    missing_conversation_targets = set()
    for resource in db_resources.values():
        if resource['kind'] != 'CONVERSATIONS':
            continue
        links = []
        for link in conn.execute('SELECT * FROM aux_links WHERE resource_id=?', (resource['resource_id'],)):
            target_key = resource_key(link['target_depot'])
            targets = db_by_key[target_key]
            absent = not targets
            if absent:
                missing_conversation_targets.add(link['target_depot'])
                assert not aliases[link['target_depot']]['providers']
            links.append({**dict(link), 'target_key': target_key,
                'target_resource_ids': [r['resource_id'] for r in targets],
                'classification': 'NO_PROVIDER_IN_PINNED_ARCHIVE_SET' if absent else 'TARGET_INDEXED',
                'next_action': 'Check the calling group and route before deciding whether the absent source is required.' if absent else
                    'Preserve group conditions/interruptions and review the actual route later.'})
        conversations.append({'resource_id': resource['resource_id'], 'depot': resource['depot'],
            'archive': resource['archive'], 'source_sha256': resource['raw_sha256'],
            'original_seed': resource['depot'] in seeds, 'links': links})
    assert len(conversations) == 32
    assert len(missing_conversation_targets) == 25
    assert len({r['depot'] for r in conversations if r['original_seed']}) == len(seeds) == 16

    outside = []
    role_counts = {r['resource_id']: dict(r) for r in conn.execute(
        "SELECT resource_id, SUM(kind='DIALOGUE_EVENT') AS dialogue_events, "
        "SUM(kind='DIALOGUE_EVENT' AND speaker_role='JOHNNY') AS johnny_events "
        'FROM search_items GROUP BY resource_id')}
    for row in read(STEP1 / 'scene_census_outside_closure.json')['providers']:
        archive = initial['archives'][row['archive_index']]['path']
        indexed = db_by_identity[(archive.casefold(), row['key'])]
        inbound = reverse[row['key']]
        counts = role_counts.get(indexed['resource_id'], {})
        outside.append({**row, 'archive': archive, 'resource_id': indexed['resource_id'],
            'source_sha256': indexed['raw_sha256'], 'index_status': indexed['status'],
            'dialogue_events': counts.get('dialogue_events', 0), 'johnny_events': counts.get('johnny_events', 0),
            'incoming_references': inbound,
            'classification': 'INDEXED_WITH_CALLER_LEADS' if inbound else 'INDEXED_NO_INBOUND_LEAD_IN_DEFINED_INPUTS',
            'next_action': 'Step 3 must determine actual post-Tower route eligibility; keep this scene in the denominator until that is resolved.'})
    assert len(outside) == 4513 and all(r['index_status'] == 'INDEXED' for r in outside)

    speech_inventory = []
    for row in entries['speech_api_candidates']:
        name = Path(row['path']).name
        if name == 'Codeware.Global.reds':
            kind = 'NATIVE_API_OR_TYPE_DECLARATION'
            action = 'Use as API definitions. A declaration is not a playback invocation.'
        elif name == 'FactFinder.reds':
            kind = 'FACT_SOURCE_METADATA'
            action = 'Keep this source mapping as metadata. It is not a speech call.'
        elif name == 'LizziesBDs.Audio.reds':
            kind = 'EXTERNAL_VOICEOVER_MAP_REGISTRATION'
            action = 'Trace registered voice maps and external-mod presentation when an affected event depends on them. Do not alter the unrelated mod.'
        elif name == 'Codeware.Localization.reds' or 'HasVar("/language", "VoiceOver")' in row['text'] or 'SetLanguage(scnDialogLineLanguage.Origin)' in row['text']:
            kind = 'LANGUAGE_SELECTION'
            action = 'Preserve language selection. It does not supply a dialogue-event identity.'
        else:
            kind = 'UI_OR_CONFIGURABLE_SOUND_PATH'
            action = 'Preserve the UI sound path. Configurable sound providers remain a dynamic compatibility boundary if their settings change.'
        lines = source_text[row['path']]
        assert lines[row['line'] - 1].strip() == row['text'].strip()
        speech_inventory.append({**row, 'source_sha256': next(r['sha256'] for r in entries['source_files'] if r['path'] == row['path']),
            'classification': kind, 'context': [{'line': i+1, 'text': lines[i]}
               for i in range(max(0, row['line']-4), min(len(lines), row['line']+3))],
            'next_action': action})
    assert len(speech_inventory) == 113
    qtt = Path(prepared['game_root']) / 'bin/x64/plugins/cyber_engine_tweaks/mods/QuestTrackingToggle'
    dynamic_inputs = []
    for name in ['mod_user_settings.json', 'soundEvents.txt']:
        path = qtt / name
        dynamic_inputs.append({'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size})
    qtt_settings = read(qtt / 'mod_user_settings.json')
    qtt_sound_names = (qtt / 'soundEvents.txt').read_text().splitlines()

    support_inventory = []
    for target, sources in prepared['support_reference_sources'].items():
        matches = [r for r in tables.values() if r.get('requested_depot') == target]
        absent = not matches
        if absent:
            assert not aliases[target]['providers']
        support_inventory.append({'depot': target, 'source_depots': sources,
            'providers': [{'archive': r['archive'], 'key': r['key'], 'sha256': r['sha256'],
               'root_type': r['root_type'], 'imports': r['imports'],
               'speech_name_leads': r['speech_name_leads'],
               'speech_export_classes': [t for t in r['export_classes'] if re.search(r'(?i)(sound|voice|speech|bark|dialog)', t)]}
               for r in matches],
            'classification': 'NO_PROVIDER_IN_PINNED_ARCHIVE_SET' if absent else 'HEADER_DEPENDENCIES_INVENTORIED',
            'next_action': 'Trace the specific actor and caller for any related edit; this support inventory does not approve animation or audio removal.'})

    voice_dispatch = []
    support_sound_events = []
    voice_metadata = []
    new_texts = []
    normalization_issues = []
    for row in exports:
        obj = load_export(row)
        if 'UNNAMED_ENGLISH_TEXT' in row['reasons']:
            for entry in walk(obj):
                if entry.get('$type') == 'localizationPersistenceSubtitleEntry':
                    new_texts.append({'archive': row['archive'], 'key': row['key'], 'depot': row['depot'],
                        'source_sha256': row['sha256'], 'entry': entry})
        if 'VOICE_IDENTITY_METADATA' in row['reasons']:
            for entry in walk(obj):
                if entry.get('$type') == 'locVoiceTag':
                    target = entry.get('voicesetScenePath', '')
                    voice_metadata.append({'source_depot': row['depot'], 'source_archive': row['archive'],
                        'source_sha256': row['sha256'], 'voice_tag': entry,
                        'indexed_scene_resource_ids': [r['resource_id'] for r in db_by_key[resource_key(target)]] if target else [],
                        'next_action': 'Use exact voice tag and scene-entry mapping for Step 2 dispatch indexing; actor binding still needs its caller context.'})
        if 'SUPPORT_SPEECH_OR_SOUND_CLASS' in row['reasons']:
            for number, entry in enumerate(walk(obj)):
                if entry.get('$type') == 'animAnimEvent_Sound':
                    support_sound_events.append({'source_depot': row['depot'], 'source_archive': row['archive'],
                        'source_sha256': row['sha256'], 'serialized_object_ordinal': number, 'payload': entry,
                        'next_action': 'Step 2 should expose sound-event identities as support leads. Resolve event metadata and actor/caller before treating one as speech.'})
        if 'VOICESET_DISPATCH_GRAPH' in row['reasons']:
            normalized = Resource(obj).normalize()
            if normalized['errors']:
                normalization_issues.append({'depot': row['depot'], 'errors': normalized['errors']})
            for graph_path, graph in normalized['graphs'].items():
                for node_id, node in graph['nodes'].items():
                    parts = [part for part in walk(node['payload']) if part.get('$type') == 'questPlayVoiceset_NodeType']
                    for operation_ordinal, part in enumerate(parts):
                        for param_ordinal, param in enumerate(part.get('params', [])):
                            puppet_text = json.dumps(param.get('puppetRef', {}), ensure_ascii=False).lower()
                            role = 'PLAYER_CONTEXT_REQUIRED' if param.get('isPlayer') else ('JOHNNY_REFERENCE_LEAD' if re.search(r'johnny|silverhand', puppet_text) else 'CALLER_BINDING_REQUIRED')
                            voice_dispatch.append({'source_depot': row['depot'], 'source_archive': row['archive'],
                                'source_key': row['key'], 'source_sha256': row['sha256'],
                                'graph_path': graph_path, 'node_id': node_id,
                                'operation_ordinal': operation_ordinal, 'param_ordinal': param_ordinal,
                                'structurally_reachable': node_id in graph['reachable'],
                                'graph_entries': graph['entries'],
                                'adjacent_edges': [e for e in graph['edges'] if e[0] == node_id or e[2] == node_id],
                                'role_lead': role, 'voiceset_name': str(value(param.get('voicesetName', ''))),
                                'payload': param, 'source_context': node['payload'],
                                'next_action': 'Step 2 must index this dispatch and bind its named entry to candidate scene events. Structural reachability does not prove post-Tower execution.'})
    new_ids = sorted({str(r['entry']['stringId']) for r in new_texts})
    text_matches = []
    for start in range(0, len(new_ids), 500):
        chunk = new_ids[start:start+500]
        text_matches.extend(dict(r) for r in conn.execute(
            'SELECT kind,item_key,resource_id,speaker_role,loc_id,text_source FROM search_items '
            'WHERE loc_id IN (' + ','.join('?' for _ in chunk) + ')', chunk))
    # External subtitle candidates apply to spoken/stored lines. Choices retain
    # their embedded locStore domain, even when a string ID collides.
    eligible = [r for r in text_matches if r['kind'] in {'DIALOGUE_EVENT', 'STORED_LINE'}]
    recovered = [r for r in eligible if r['text_source'] == 'UNRESOLVED']
    for row in recovered:
        row['scope'] = db_resources[row['resource_id']]['scope']
    assert len(new_texts) == 1617 and len(new_ids) == 1560
    assert not unknown_scene_missing

    OUT.mkdir()
    write(OUT / 'graph_provider_inventory.json', graph_inventory)
    write(OUT / 'unnamed_entry_inventory.json', unknown_inventory)
    write(OUT / 'missing_reference_review.json', missing_inventory)
    write(OUT / 'provider_collision_review.json', collision_inventory)
    write(OUT / 'opaque_boundary_review.json', opaque_inventory)
    write(OUT / 'conversation_inventory.json', conversations)
    write(OUT / 'outside_scene_review.json', outside)
    write(OUT / 'speech_source_review.json', {'candidates': speech_inventory,
        'additional_config_inputs': dynamic_inputs,
        'configured_quest_tracking_sound': qtt_settings.get('currentGameplayToggleSoundName'),
        'quest_tracking_sound_names': qtt_sound_names,
        'limits': ['The pinned installed text sources were reviewed. Native compiled scripts, TweakDB-driven selection, arbitrary plugin code and runtime-generated paths remain dynamic boundaries.',
                   'No general claim that an API declaration or arbitrary sound name transcribes a Johnny line is made.']})
    write(OUT / 'support_inventory.json', support_inventory)
    write(OUT / 'voiceset_dispatch_inventory.json', {'dispatches': voice_dispatch, 'normalization_issues': normalization_issues})
    write(OUT / 'voice_metadata_inventory.json', voice_metadata)
    write(OUT / 'support_sound_event_inventory.json', support_sound_events)
    write(OUT / 'additional_english_subtitles.json', {'providers': [r for r in exports if 'UNNAMED_ENGLISH_TEXT' in r['reasons']],
        'entries': new_texts, 'applicable_index_items': eligible, 'unresolved_spoken_or_stored_items_with_new_candidates': recovered})
    # Keep reference leads separate from any later connected invocation proof.
    with (OUT / 'reference_leads.jsonl').open('x', encoding='utf-8', newline='\n') as stream:
        for row in references:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
    english_stats = Counter((r['kind'], r['text_source']) for r in eligible)
    summary = {
        'schema': 1, 'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'step1_status': 'COMPLETE_SOURCE_INVENTORY_WITH_EXPLICIT_BOUNDARIES',
        'step2_status': 'VERIFIED_SNAPSHOT_REQUIRES_COVERAGE_SUCCESSOR',
        'protected_baseline_checks': len(prepared['protected_checks']),
        'defined_graph_provider_entries_accounted_for': len(graph_inventory),
        'original_unnamed_entries_accounted_for': len(unknown_inventory),
        'unnamed_classifications': dict(Counter(r['classification'] for r in unknown_inventory)),
        'unnamed_root_types': dict(Counter(r['root_type'] or 'NON_CR2W' for r in unknown_inventory)),
        'original_missing_reference_review': dict(Counter(r['classification'] for r in missing_inventory)),
        'provider_collision_review': dict(Counter(r['classification'] for r in collision_inventory)),
        'opaque_payloads_with_recovered_imports': len(opaque_inventory),
        'opaque_object_decode_status': '55 ORIGINAL PAYLOADS STILL OPAQUE; HEADER RECOVERY IS NOT OBJECT DECODE',
        'outside_scene_keys_accounted_for': len(outside),
        'outside_scene_classifications': dict(Counter(r['classification'] for r in outside)),
        'conversation_resources': len(conversations), 'original_conversation_seed_depots': len(seeds),
        'conversation_target_occurrences': sum(len(r['links']) for r in conversations),
        'distinct_conversation_targets': len(prepared['conversation_targets']),
        'distinct_conversation_targets_absent_from_archives': len(missing_conversation_targets),
        'speech_candidate_classifications': dict(Counter(r['classification'] for r in speech_inventory)),
        'support_unique_paths': len(support_inventory),
        'support_unique_paths_by_extension': dict(Counter(Path(r['depot']).suffix for r in support_inventory)),
        'support_unique_paths_without_provider': sum(not r['providers'] for r in support_inventory),
        'additional_source_exports': len(exports),
        'voiceset_dispatch_provider_payloads': sum('VOICESET_DISPATCH_GRAPH' in r['reasons'] for r in exports),
        'voiceset_dispatch_params': len(voice_dispatch),
        'voiceset_dispatch_role_leads': dict(Counter(r['role_lead'] for r in voice_dispatch)),
        'current_private_dispatch_params': sum(r['source_archive'].lower().endswith('zzzz_ptfr_combined.archive') for r in voice_dispatch),
        'dispatch_graph_normalization_issues': len(normalization_issues),
        'support_sound_events': len(support_sound_events),
        'voice_tag_records': len(voice_metadata),
        'additional_english_subtitle_providers': 41,
        'additional_english_subtitle_entries': len(new_texts),
        'additional_english_subtitle_ids': len(new_ids),
        'applicable_index_text_matches': [{'kind': k[0], 'source': k[1], 'count': v} for k,v in sorted(english_stats.items())],
        'unresolved_spoken_or_stored_items_with_new_candidates': dict(Counter(r['kind'] for r in recovered)),
        'johnny_dialogue_items_with_new_english_candidates': sum(r['kind'] == 'DIALOGUE_EVENT' and r['speaker_role'] == 'JOHNNY' for r in recovered),
        'current_private_unresolved_items_with_new_candidates': sum(r['scope'] == 'CURRENT_PTFR_PAYLOAD' for r in recovered),
        'selected_existing_index': prepared['database'],
        'game_writes': 0, 'save_writes': 0, 'existing_index_writes': 0,
        'step3_started': False,
        'next_actions': [
            'Step 2: create a fresh successor including the 41 additional subtitle providers; qualify text domains and verify exact-ID matches before replacing the selected snapshot.',
            'Step 2: expose voiceset dispatch identities, actor/player binding evidence, exact named-entry links, voice metadata and support sound-event leads through search/context.',
            'Step 2: recover the opaque q303 scene with supported tooling, or carry a documented availability/coverage hold. Preserve missing providers and unresolved English as explicit limits.',
            'Step 3 remains planning only. Later route and manual event review must cover native/shared sources as well as current private scenes, with the agreed three preceding lines and five following V lines.',
        ],
    }
    write(OUT / 'summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
