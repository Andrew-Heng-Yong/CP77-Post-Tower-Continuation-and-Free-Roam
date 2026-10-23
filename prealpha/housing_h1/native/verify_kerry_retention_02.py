"""Read-only current Tower fact-retention audit; no save or runtime inference."""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = 'research/housing_h1/native/tower_sources_01/inventory.json'
FACTS = {'sq028_kerry_friend', 'sq028_kerry_relationship'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def walk(obj, path='$'):
    if isinstance(obj, dict):
        yield path, obj
        for key, val in obj.items():
            yield from walk(val, path + '.' + key)
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            yield from walk(val, path + '[' + str(idx) + ']')


def validate_write(obj):
    assert obj['$type'] == 'questSetVar_NodeType', 'unclassified earned-fact mutation'
    # Even debug writes may only retain/increase truth, never erase earned access.
    assert obj['setExactValue'] == 1 and obj['value'] == 1, 'earned Kerry fact reset'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    out = Path(parser.parse_args().output).resolve()
    assert not out.exists(), 'Use a new receipt path'
    inv = read(ROOT / INVENTORY)
    pins = {INVENTORY: sha(ROOT / INVENTORY)}
    self_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    pins[self_path] = sha(ROOT / self_path)
    extractor = 'prealpha/housing_h1/native/extract_tower_01.ps1'
    assert sha(ROOT / extractor) == inv['extractor_sha256']
    pins[extractor] = sha(ROOT / extractor)
    assert len(inv['rows']) == 35
    reads, writes, managers, sources = [], [], collections.Counter(), []
    assertions = 0
    for row in inv['rows']:
        for kind in ['raw', 'json']:
            assert sha(ROOT / row[kind]) == row[kind + '_sha256'], row[kind]
            pins[row[kind]] = row[kind + '_sha256']
            assertions += 1
        obj = read(ROOT / row['json'])
        handles = {v['HandleId']: v['Data'] for _, v in walk(obj) if 'HandleId' in v}
        def resolve(handle):
            if 'HandleId' in handle:
                return handle['Data']
            return handles[handle['HandleRefId']]
        local_managers = 0
        for path, item in walk(obj):
            if item.get('$type') == 'questFactsDBManagerNodeDefinition':
                op = resolve(item['type'])
                assert op['$type'] == 'questSetVar_NodeType', ('unknown fact operator', row['depot'], path)
                managers[op['$type']] += 1
                local_managers += 1
                assertions += 1
            if isinstance(item.get('factName'), str) and item.get('factName') in FACTS:
                entry = {'depot': row['depot'], 'json_path': path, 'payload': item}
                if item.get('$type') == 'questVarComparison_ConditionType':
                    assert (item['comparisonType'], item['value']) in [('Greater', 0), ('GreaterOrEqual', 1)]
                    reads.append(entry)
                else:
                    validate_write(item)
                    assert row['depot'] == r'ep1\quest\main_quests\q307\test\q307_00_chickentest.scene'
                    writes.append(entry)
                assertions += 1
        sources.append({'depot': row['depot'], 'raw': row['raw'], 'raw_sha256': row['raw_sha256'],
                        'json': row['json'], 'json_sha256': row['json_sha256'], 'fact_manager_nodes': local_managers})
    assert managers == {'questSetVar_NodeType': 322}
    assert len(reads) == 6 and len(writes) == 2
    assert all(r['payload']['factName'] == 'sq028_kerry_relationship' for r in reads + writes)
    assert any(r['depot'].endswith('q307_03_hospital.questphase') for r in reads)
    assert sum(r['depot'].endswith('q307_03a_friends_holocall.scene') for r in reads) == 3
    assert any(r['depot'].endswith('q307_despawn.questphase') for r in sources)
    assert any(r['depot'].endswith('q307_bugfixing.questphase') for r in sources)
    assertions += 7
    negatives = 0
    for key, value in [('value', 0), ('value', -1), ('setExactValue', 0), ('$type', 'UnknownFactClear')]:
        bad = copy.deepcopy(writes[0]['payload'])
        bad[key] = value
        try:
            validate_write(bad)
        except AssertionError:
            negatives += 1
        else:
            raise AssertionError('Negative reset fixture unexpectedly accepted')
    # The final component never sets earned Kerry state: it consumes native history.
    component_path = 'prealpha/housing_h1/native/build/native_06/component.json'
    component = read(ROOT / component_path)
    pins[component_path] = sha(ROOT / component_path)
    for name in ['h10_owner', 'kerry_visitor_owner']:
        path = 'prealpha/housing_h1/native/build/native_06/readback/' + name + '.json'
        obj = read(ROOT / path)
        assert not any(v.get('$type') == 'questSetVar_NodeType' and isinstance(v.get('factName'), str) and v.get('factName') in FACTS for _, v in walk(obj))
        assert FACTS <= {v.get('factName') for _, v in walk(obj) if v.get('$type') == 'questVarComparison_ConditionType'}
        pins[path] = sha(ROOT / path)
        assertions += 2
    result = {
        'status': 'PASS_CURRENT_TOWER_EARNED_KERRY_FACT_RETENTION',
        'checks': assertions, 'negative_cases': negatives, 'resources': len(sources),
        'fact_manager_types': dict(managers), 'earned_fact_reads': reads, 'earned_fact_writes': writes,
        'friend_reads_or_writes': 0,
        'conclusion': 'The audited current Tower quest, phases, scenes, despawn and bugfix sources contain no operation clearing either earned Kerry access fact. Native post-coma hospital and friend-call branches still consult the relationship fact. The housing component only reads the two native earned facts and never backfills them.',
        'debug_boundary': 'The two native chickentest writes set relationship=1. They are reported, not dispatched by housing and never accepted as an earned-history certificate. Housing retains genuine existing fact history; it cannot certify a manually modified or debug-created save.',
        'scope': 'Every current named q307 .quest/.questphase/.scene resource plus the exact q307 despawn and bugfix phases. Shared generic quest controllers outside these resources are not claimed exhaustively scanned. This is native source evidence, not engine/save reload or live-world proof.',
        'sources': sources, 'source_pins': dict(sorted(pins.items())),
        'official_archive_pins': {a['path']: a['sha256'] for a in inv['archives']},
        'verifier': self_path, 'verifier_sha256': sha(__file__),
        'native_component': component_path, 'native_component_sha256': sha(ROOT / component_path),
        'game_writes': 0, 'save_writes': 0, 'runtime_fact_writes': 0, 'live_verified': False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['status', 'checks', 'negative_cases', 'resources']}))


if __name__ == '__main__':
    main()
