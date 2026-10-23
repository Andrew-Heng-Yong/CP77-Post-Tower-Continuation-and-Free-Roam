"""Independent bitwise CRC32 and strict-type native payload comparison."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'prealpha/sidejobs_s27'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def bitwise_id(name):
    assert type(name) is str
    data = name.encode('utf-8')
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
    return ((crc ^ 0xFFFFFFFF) & 0xFFFFFFFF) | (len(data) << 32)


def normalize(value, ids=None):
    if isinstance(value, dict):
        if value.get('$type') == 'TweakDBID':
            assert set(value) == {'$type', '$storage', '$value'}
            assert type(value['$value']) is str
            if value['$storage'] == 'string':
                number = bitwise_id(value['$value'])
            else:
                assert value['$storage'] == 'uint64'
                assert re.fullmatch(r'[0-9]+', value['$value'])
                number = int(value['$value'])
                assert 0 <= number <= 0xFFFFFFFFFFFFFFFF
            if ids is not None:
                ids.append({'storage': value['$storage'], 'value': value['$value'], 'id': number})
            return {'$type': 'TweakDBID', '$storage': 'uint64', '$value': str(number)}
        return {key: normalize(child, ids) for key, child in value.items()}
    if isinstance(value, list):
        return [normalize(child, ids) for child in value]
    return value


def exact_types(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(exact_types(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(exact_types(a, b) for a, b in zip(left, right))
    return left == right


def compare(left, right):
    return exact_types(normalize(left), normalize(right))


def verify(revision):
    folder = HERE / 'build' / revision
    manifest = read(folder / 'build.json')
    assert sha(HERE / 'raw_compare.py') == manifest['source_pins']['prealpha/sidejobs_s27/raw_compare.py']
    mutations = 0
    for name, expected in [('GameplayRestriction.NoTimeSkip', 131161243162),
                           ('GameplayRestriction.BlockFastTravel', 151159473294),
                           ('ReactionPresets.NoReaction', 115253861404)]:
        assert bitwise_id(name) == expected
        a = {'$type': 'TweakDBID', '$storage': 'string', '$value': name}
        b = {'$type': 'TweakDBID', '$storage': 'uint64', '$value': str(expected)}
        assert compare(a, b)
        assert not compare(a, b | {'$value': str(expected + 1)})
        assert not compare(a, {'$type': 'NodeRef', '$storage': 'uint64', '$value': str(expected)})
        mutations += 3
    for a, b in [({'flag': True}, {'flag': 1}), ({'number': 1}, {'number': 1.0}),
                 ({'value': '1'}, {'value': 1}), ([1, 2], [2, 1]),
                 ({'a': 1}, {'a': 1, 'b': 0}), ({'id': 1}, {'id': 2}),
                 ({'socket': 'In1'}, {'socket': 'In2'})]:
        assert not compare(a, b)
        mutations += 1
    for bad in [ {'$type': 'TweakDBID', '$storage': 'uint64', '$value': '-1'},
                 {'$type': 'TweakDBID', '$storage': 'uint64', '$value': '18446744073709551616'},
                 {'$type': 'TweakDBID', '$storage': 'uint64', '$value': True},
                 {'$type': 'TweakDBID', '$storage': 'uint64', '$value': '1', 'extra': 0},
                 {'$type': 'TweakDBID', '$storage': 'other', '$value': '1'}]:
        try:
            normalize(bad)
        except AssertionError:
            mutations += 1
        else:
            raise AssertionError('Malformed TweakDBID accepted')
    rows = []
    for source in manifest['native_source_readbacks']:
        assert sha(ROOT / source['raw']) == source['raw_sha256']
        assert sha(ROOT / source['witness']) == source['witness_sha256']
        assert sha(folder / source['fresh']) == source['fresh_sha256']
        old, new = read(ROOT / source['witness'])['Data'], read(folder / source['fresh'])['Data']
        left_ids, right_ids = [], []
        left, right = normalize(old, left_ids), normalize(new, right_ids)
        assert exact_types(left, right), source['witness']
        assert len(left_ids) == len(right_ids)
        representations = sum(a['storage'] != b['storage'] or a['value'] != b['value']
                              for a, b in zip(left_ids, right_ids))
        rows.append({'witness': source['witness'], 'fresh': source['fresh'],
                     'tweakdbids': len(left_ids), 'representation_changes': representations,
                     'strict_non_tweak_payload_equal': True})
    return {'status': 'PASS_INDEPENDENT_STRICT_NATIVE_NORMALIZATION_NOT_LIVE',
            'build_sha256': sha(folder / 'build.json'), 'reviewer_sha256': sha(Path(__file__)),
            'normalizer_sha256': sha(HERE / 'raw_compare.py'), 'mutation_cases': mutations,
            'native_readbacks': len(rows), 'tweakdbids': sum(row['tweakdbids'] for row in rows),
            'representation_changes': sum(row['representation_changes'] for row in rows), 'rows': rows,
            'allowed_difference': 'Only exact three-key TweakDBID resolved-string versus decimal uint64 representation, validated with an independent bitwise CRC32+UTF8-length implementation.',
            'strict_types': True, 'game_writes': 0}


if __name__ == '__main__':
    result = verify(sys.argv[1])
    output = ROOT / 'research/sidejobs_s27/runtime' / sys.argv[2]
    assert not output.exists(), 'Immutable review receipt'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))
