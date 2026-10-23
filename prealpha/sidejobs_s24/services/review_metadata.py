"""Independent final metadata-exception review, confined to services evidence."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def catalogue(path):
    """Traverse serialized handle trees independently of the audited verifier."""
    data = read(path)
    handles = {}
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, dict):
            if 'HandleId' in node and 'Data' in node:
                handles[node['HandleId']] = node['Data']
            stack.extend(node.values())
    result = {}
    pending = [(data['Data']['RootChunk']['entry'], ())]
    while pending:
        wrapper, parent = pending.pop()
        node = wrapper.get('Data', handles.get(wrapper.get('HandleRefId'), wrapper))
        path = parent + ((node['id'],) if node.get('id') else ())
        cls = node.get('$type', '')
        if cls.startswith('gameJournal'):
            key = '/'.join(path)
            assert key not in result or result[key] == cls, key
            result[key] = cls
        pending.extend((child, path) for child in node.get('entries', []))
    return result


def main():
    revision, filename = sys.argv[1:]
    assert re.fullmatch(r's24_\d{2}', revision)
    assert re.fullmatch(r'review_metadata_\d{2}\.json', filename)
    dest = ROOT / 'research/sidejobs_s24/services' / filename
    assert not dest.exists(), 'Immutable independent review receipt'
    build = ROOT / 'prealpha/sidejobs_s24/build' / revision
    m, test, audit = (read(build / name) for name in ('build.json', 'tests.json', 'resource_check.json'))
    assert m['status'] == 'BUILT_S24_LIVE_PENDING'
    assert test['status'] == 'PASS_NOT_LIVE' and test['build_sha256'] == sha(build / 'build.json')
    assert test['tester_sha256'] == sha(ROOT / 'prealpha/sidejobs_s24/test.py')
    assert audit['status'] == 'PASS_RESOURCE_AUDIT' and audit['build_sha256'] == sha(build / 'build.json')
    assert audit['checker_sha256'] == sha(ROOT / 'prealpha/sidejobs_s24/resource_check.ps1')
    proof = ROOT / m['journal_metadata_proof']
    metadata = read(proof)
    assert metadata['status'] == 'PASS_USED_JOURNAL_METADATA_ALL_VARIANTS'
    assert m['source_pins'][m['journal_metadata_proof']] == sha(proof)
    assert metadata == read(build / 'journal_metadata_check.json'), 'Aggregate independently reran verifier'
    assert audit['metadata_variant_proof'] == m['journal_metadata_proof']
    assert audit['metadata_variant_proof_sha256'] == sha(proof)
    assert audit['exact_byte_resources'] == audit['official_comparisons'] - 1
    for rel, digest in m['source_pins'].items():
        assert sha(ROOT / rel) == digest, rel
    for rel, digest in metadata['source_pins'].items():
        assert m['source_pins'][rel] == digest, rel
    for rel in ('prealpha/sidejobs_s24/ep1/verify_journal_metadata.py',
                'prealpha/sidejobs_s24/ep1/inspect.py', 'tools/catalog_gig_rollout_r2.py'):
        assert m['source_pins'][rel] == sha(ROOT / rel), rel
    assert metadata['verifier_sha256'] == sha(ROOT / 'prealpha/sidejobs_s24/ep1/verify_journal_metadata.py')
    depot = 'base\\journal\\cooked_journal.journal'
    assert metadata['metadata_only_depot'] == depot
    assert depot not in m['resources'] and all(path.startswith('towercontinued\\') for path in m['resources'])
    assert m['official_overrides'] == []
    expected = {
        'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Cyberpunk 2077\\archive\\pc\\content\\basegame_4_gamedata.archive': '7108238DED82952D291837A8A6E30ACE5430E1D9B4C2D8D6A7E33DCC70E438E8',
        'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Cyberpunk 2077\\archive\\pc\\ep1\\ep1_2_gamedata.archive': '55B6E39E338A1B3C116AF074B00CFB9D5745F7D495F59541F8EA49D0B182832B',
    }
    assert {v['archive']: v['sha256'] for v in metadata['variants']} == expected
    assert audit['metadata_variants'] == expected
    used = {}
    owners = []
    for contract in metadata['contracts']:
        c = read(ROOT / contract)
        for owner in c.get('owners', [c]):
            owners.append(owner['id'])
            for entry in owner['journals']:
                assert entry['path'] not in used or used[entry['path']] == entry['class']
                used[entry['path']] = entry['class']
            contact = owner.get('contact') or (owner.get('contact_copy') or {}).get('path') or owner.get('contact_target')
            if contact:
                used[contact] = 'gameJournalContact'
    assert len(owners) == len(set(owners)) == 7
    assert used['contacts/wakako_okada'] == 'gameJournalContact'
    base_used = {p: c for p, c in used.items() if not p.startswith('ep1/')}
    ep1_used = {p: c for p, c in used.items() if p.startswith('ep1/')}
    assert {v['path']: v['class'] for v in metadata['base_paths']} == base_used
    assert {v['path']: v['class'] for v in metadata['ep1_paths']} == ep1_used
    assert metadata['total_used_paths'] == len(used)
    checked = 0
    for variant in metadata['variants']:
        assert variant['depot'] == depot and sha(ROOT / variant['raw']) == variant['sha256']
        assert sha(ROOT / variant['json']) == variant['json_sha256']
        cat = catalogue(ROOT / variant['json'])
        for path, cls in base_used.items():
            assert cat.get(path) == cls, (variant['archive'], path)
            checked += 1
        assert variant['metadata_checks'] == len(base_used)
    cat = catalogue(ROOT / 'research/sidejobs_s24/ep1/native_02/json/ep1/journal/cooked_journal.journal.json')
    for path, cls in ep1_used.items():
        assert cat.get(path) == cls, path
        checked += 1
    source_paths = [
        'prealpha/sidejobs_s24/build.ps1', 'prealpha/sidejobs_s24/test.py',
        'prealpha/sidejobs_s24/resource_check.ps1', 'prealpha/sidejobs_s24/deploy.ps1',
        'prealpha/sidejobs_s24/test_deploy.py', m['journal_metadata_proof'],
        'prealpha/sidejobs_s24/ep1/verify_journal_metadata.py',
    ]
    result = {
        'status': 'PASS_FINAL_METADATA_EXCEPTION_REVIEW_NOT_LIVE',
        'build': revision, 'build_sha256': sha(build / 'build.json'),
        'reviewer': 's24_services_audit', 'review_script_sha256': sha(Path(__file__)),
        'source_pins': {p: sha(ROOT / p) for p in source_paths},
        'aggregate_tests_sha256': sha(build / 'tests.json'),
        'resource_audit_sha256': sha(build / 'resource_check.json'),
        'native_resources': len(m['resources']), 'owners': owners,
        'base_paths_in_each_variant': len(base_used), 'ep1_paths': len(ep1_used),
        'independent_path_class_checks': checked, 'blocking_findings': [],
        'conclusion': 'Exception is restricted to metadata from the base cooked journal, which is never shipped. Both exact official archive-to-byte variants are bound. Independent catalogue traversal confirms all seven owners and Wakako contact; all other native gameplay resources retain exact byte verification.',
        'limits': 'No whole-journal byte/semantic equivalence is claimed. Native gameplay, Nix lease, calls/SMS, rewards, Johnny visibility and reload still require live testing. This receipt performs no installation/game/save/cache/settings writes.',
    }
    dest.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': checked, 'receipt': str(dest), 'sha256': sha(dest)}))


if __name__ == '__main__':
    main()
