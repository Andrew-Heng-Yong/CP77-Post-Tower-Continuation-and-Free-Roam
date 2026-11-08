"""Independently check inventory denominators and preservation for this run."""

import ast
import gzip
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from prepare import TASK, WORKSPACE, STEP1, STEP2, read, sha, write


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for item in obj.values():
            yield from walk(item)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk(item)


def expected_ns(stamp):
    seconds = int(datetime.fromisoformat(stamp[:19]).replace(tzinfo=timezone.utc).timestamp())
    fraction = re.search(r'\.(\d+)', stamp)
    return seconds * 1000000000 + int(fraction.group(1).ljust(9, '0')) if fraction else seconds * 1000000000


def main():
    result_path = TASK / 'verification.json'
    if result_path.exists():
        raise SystemExit('Preserve the verification receipt; use a fresh successor')
    prepared = read(TASK / 'evidence_01/prepared.json')
    base = read(STEP1 / 'baseline.json')
    expected = {}

    def pin(path, digest):
        path = str(Path(path).resolve())
        if path in expected:
            assert expected[path] == digest
        expected[path] = digest

    for row in base['checks']:
        pin(row['path'], row['sha256'])
    pin(base['installed_manifest']['path'], base['installed_manifest']['sha256'])
    for row in prepared['protected_checks']:
        pin(row['path'], row['expected'])
    for row in prepared['pins']:
        pin(row['path'], row['sha256'])
    exports = [json.loads(s) for s in (TASK / 'evidence_05/exports.jsonl').read_text().splitlines()]
    for row in exports:
        pin(row['raw'], row['sha256'])
        pin(row['json'], row['json_sha256'])
    for row in read(TASK / 'evidence_07/speech_source_review.json')['additional_config_inputs']:
        pin(row['path'], row['sha256'])
    hash_discrepancies = [{'path': path, 'expected': digest, 'actual': actual}
                         for path, digest in expected.items() if (actual := sha(path)) != digest]
    assert not hash_discrepancies, hash_discrepancies[:3]

    archive_changes = []
    for row in prepared['archives']:
        info = Path(row['path']).stat()
        if info.st_size != row['bytes'] or info.st_mtime_ns != expected_ns(row['mtime_utc']):
            archive_changes.append(row['path'])
    known_archives = {str(Path(r['path']).resolve()).casefold() for r in prepared['archives']}
    current_archives = {str(p.resolve()).casefold() for p in (Path(prepared['game_root']) / 'archive/pc').rglob('*.archive')}
    assert not archive_changes and known_archives == current_archives
    for directory in ['mods', 'r6/cache/modded']:
        root = Path(prepared['game_root']) / directory
        assert not root.exists() or not list(root.rglob('*.archive'))

    original = read(STEP1 / 'capture.json')
    unresolved = read(STEP1 / 'unresolved.json')
    source = TASK / 'evidence_07'
    graph = read(source / 'graph_provider_inventory.json')
    assert Counter((r['archive_index'], r['key']) for r in graph) == Counter(
        (r['archive_index'], r['key']) for r in original['graph_provider_census'])
    assert len(graph) == 15581
    unknown = read(source / 'unnamed_entry_inventory.json')
    frozen = read(TASK / 'evidence_03/frozen_inventory.json')
    ids = {(r['archive'], r['key']) for r in unknown}
    assert len(ids) == len(unknown) == 9729
    assert ids == {(r['archive'], r['key']) for r in frozen['rows'] if r['unnamed']}
    assert all(r['observed'] == r['expected'] for r in frozen['unknown_counts'])
    assert sum(r['classification'] == 'SCENE_ALREADY_INDEXED' for r in unknown) == 59
    assert all(r['indexed_resource_id'] for r in unknown if r['root_type'] == 'scnSceneResource')
    missing = read(source / 'missing_reference_review.json')
    assert {r['depot'] for r in missing} == {r['depot'] for r in unresolved['missing_candidates']}
    assert len(missing) == 91
    private_hashes = {r['key']: r['sha256'] for r in original['private_readback']}
    case_aliases = [r for r in missing if r['classification'] == 'RESOURCEPATH_CASE_ALIAS_RESOLVED']
    assert len(case_aliases) == 26
    private_alias_count = 0
    for row in case_aliases:
        alias = row['normalized_lookup']
        assert alias['sanitized'] == row['depot'].lower()
        assert len(alias['providers']) == 1
        if alias['resource_key'] in private_hashes:
            assert private_hashes[alias['resource_key']] == alias['providers'][0]['sha256']
            private_alias_count += 1
        else:
            assert row['depot'] == 'mod\\arman3_lizzies_bds\\characters\\entities\\Mitch.ent'
            assert alias['providers'][0]['archive'].lower().endswith('lizziesbds.archive')
    assert private_alias_count == 25
    providers = read(source / 'provider_collision_review.json')
    assert {r['depot'] for r in providers} == {r['depot'] for r in unresolved['multiple_provider_depots']}
    assert len(providers) == 41
    assert Counter(r['classification'] for r in providers) == {
        'EQUIVALENT_CAPTURED_BYTES': 16, 'DIFFERENT_PROVIDERS_RETAINED': 25}
    opaque = read(source / 'opaque_boundary_review.json')
    assert {(r['archive'],r['sha256']) for r in opaque} == {
        (r['archive'],r['sha256']) for r in unresolved['opaque_provider_payloads']}
    assert len(opaque) == 55 and all(r['root_type'] for r in opaque)
    outside = read(source / 'outside_scene_review.json')
    original_outside = read(STEP1 / 'scene_census_outside_closure.json')['providers']
    assert {(r['archive_index'],r['key']) for r in outside} == {(r['archive_index'],r['key']) for r in original_outside}
    assert len(outside) == 4513 and all(r['index_status'] == 'INDEXED' for r in outside)
    speech = read(source / 'speech_source_review.json')['candidates']
    old_speech = read(STEP1 / 'entry_sources.json')['speech_api_candidates']
    assert {(r['path'],r['line']) for r in speech} == {(r['path'],r['line']) for r in old_speech}
    assert len(speech) == 113
    conversations = read(source / 'conversation_inventory.json')
    assert len(conversations) == 32 and sum(len(r['links']) for r in conversations) == 685
    assert len({x['target_depot'] for r in conversations for x in r['links']}) == 658
    assert len({r['depot'] for r in conversations if r['original_seed']}) == 16
    support = read(source / 'support_inventory.json')
    assert len(support) == 3436 and sum(not r['providers'] for r in support) == 58
    assert {r['depot'] for r in support} == set(prepared['support_reference_sources'])
    assert all(r.get('next_action') for rows in [graph, unknown, missing, providers, opaque, outside, speech, support]
               for r in rows)
    boundaries = read(TASK / 'evidence_09/boundary_ledger.json')['boundaries']
    assert len(boundaries) == 11 and all(r.get('next_action') and (TASK / r['evidence']).is_file() for r in boundaries)

    raw_voice_params = 0
    raw_text_entries = []
    raw_support_sounds = 0
    for row in exports:
        obj = json.loads(gzip.decompress(Path(row['json']).read_bytes()))
        for item in walk(obj):
            if 'VOICESET_DISPATCH_GRAPH' in row['reasons'] and item.get('$type') == 'questPlayVoiceset_NodeType':
                raw_voice_params += len(item.get('params', []))
            if 'UNNAMED_ENGLISH_TEXT' in row['reasons'] and item.get('$type') == 'localizationPersistenceSubtitleEntry':
                raw_text_entries.append((row['archive'],row['key'],item))
            if 'SUPPORT_SPEECH_OR_SOUND_CLASS' in row['reasons'] and item.get('$type') == 'animAnimEvent_Sound':
                raw_support_sounds += 1
    dispatch = read(source / 'voiceset_dispatch_inventory.json')['dispatches']
    assert raw_voice_params == len(dispatch) == 3433
    assert len({(r['source_archive'],r['source_key'],r['graph_path'],r['node_id'],r['operation_ordinal'],r['param_ordinal']) for r in dispatch}) == 3433
    assert raw_support_sounds == len(read(source / 'support_sound_event_inventory.json')) == 382
    texts = read(source / 'additional_english_subtitles.json')
    assert len(raw_text_entries) == len(texts['entries']) == 1617
    assert Counter((a,b,json.dumps(c,sort_keys=True)) for a,b,c in raw_text_entries) == Counter(
        (r['archive'],r['key'],json.dumps(r['entry'],sort_keys=True)) for r in texts['entries'])
    nonempty = {str(item['stringId']) for a,b,item in raw_text_entries if item.get('femaleVariant') or item.get('maleVariant')}
    assert len(nonempty) == 1560
    recovered = texts['unresolved_spoken_or_stored_items_with_new_candidates']
    assert Counter(r['kind'] for r in recovered) == {'DIALOGUE_EVENT':308,'STORED_LINE':10}
    assert all(r['loc_id'] in nonempty and r['text_source'] == 'UNRESOLVED' for r in recovered)

    authored = [*TASK.glob('*.py'), *TASK.glob('*.ps1'), *TASK.glob('*.md'), TASK / 'checkpoint.json',
        WORKSPACE / 'docs/johnny_dialogue_removal_plan_20261107.md',
        STEP1.parent / 'REPORT.md', STEP1.parent / 'checkpoint.json',
        STEP2 / 'REPORT.md', STEP2 / 'README.md', STEP2 / 'checkpoint.json']
    for path in authored:
        text = path.read_text(encoding='utf-8-sig')
        assert all(line == line.rstrip() for line in text.splitlines()), path
        if path.suffix == '.py':
            ast.parse(text, filename=str(path))
        if path.suffix == '.json':
            json.loads(text)
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^\n)]+)\)', text):
                if '://' not in target and not target.startswith('#'):
                    resolved = (path.parent / target.split('#',1)[0]).resolve()
                    assert resolved.exists() or resolved == result_path, (path, target)
    ignored_samples = [TASK/'evidence_01/prepared.json', TASK/'evidence_07/additional_english_subtitles.json',
                       Path(exports[0]['json'])]
    for path in ignored_samples:
        check = subprocess.run(['git','-c','safe.directory='+str(WORKSPACE),
            'check-ignore','--no-index','-q',str(path)],cwd=WORKSPACE,capture_output=True)
        assert check.returncode == 0, (path,check.stderr)
    tool_pins = [{'path':str(path),'sha256':sha(path)} for path in [*TASK.glob('*.py'),*TASK.glob('*.ps1'),
        WORKSPACE/'tools/build_phase2a.ps1', WORKSPACE/'tools/parity_audit/model.py',WORKSPACE/'tools/parity_audit/common.py']]
    result = {'schema':1,'status':'PASS','verified_utc':datetime.now(timezone.utc).isoformat(),
        'exact_file_hash_checks':len(expected),'hash_discrepancies':hash_discrepancies,
        'original_baseline_checks_reverified':len(base['checks']),
        'archive_metadata_checks':len(prepared['archives']),'archive_metadata_changes':archive_changes,
        'archive_path_set_unchanged':True,'graph_provider_entries':len(graph),'unnamed_entries':len(unknown),
        'missing_candidates':len(missing),'case_aliases_confirmed':len(case_aliases),
        'private_phase_aliases_confirmed':private_alias_count,'external_entity_aliases_confirmed':1,
        'multiple_provider_depots':len(providers),'opaque_import_tables':len(opaque),
        'outside_scene_keys':len(outside),'script_candidates':len(speech),
        'independent_serialized_voiceset_param_count':raw_voice_params,
        'independent_subtitle_entry_count':len(raw_text_entries),
        'nonempty_subtitle_ids':len(nonempty),'independent_support_sound_event_count':raw_support_sounds,
        'explicit_boundary_categories':len(boundaries),'authored_files_syntax_links_whitespace_checked':len(authored),
        'bulk_evidence_git_ignored':True,'tool_pins':tool_pins,
        'game_writes':0,'save_writes':0,'existing_index_writes':0,'step3_started':False}
    write(result_path,result)
    print(json.dumps({k:v for k,v in result.items() if k != 'tool_pins'},indent=2))


if __name__ == '__main__':
    main()
