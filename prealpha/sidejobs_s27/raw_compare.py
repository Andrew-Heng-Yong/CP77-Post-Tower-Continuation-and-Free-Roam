"""Compare CR2W JSON payloads allowing only resolved vs numeric TweakDBID spelling."""
import json
import sys
import zlib
from pathlib import Path


def canonical(value):
    if isinstance(value, list):
        return [canonical(v) for v in value]
    if not isinstance(value, dict):
        return value
    if value.get('$type') == 'TweakDBID':
        assert set(value) == {'$type', '$storage', '$value'}, value
        storage, raw = value['$storage'], value['$value']
        assert storage in ('string', 'uint64'), value
        assert isinstance(raw, str), value
        if storage == 'string':
            encoded = raw.encode('utf-8')
            number = zlib.crc32(encoded) | (len(encoded) << 32)
        else:
            assert raw and raw.isascii() and raw.isdecimal(), value
            number = int(raw)
        assert 0 <= number < (1 << 64), value
        return {'$type': 'TweakDBID', '$storage': 'uint64', '$value': str(number)}
    return {k: canonical(v) for k, v in value.items()}


def payload(path):
    return strict(canonical(json.loads(Path(path).read_text(encoding='utf-8-sig'))['Data']))


def strict(value):
    # JSON spelling preserves bool/int/float distinctions that Python == loses.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def self_test():
    # Numeric witnesses independently read from the official binary by WolvenKit.
    for name, expected in [('GameplayRestriction.NoTimeSkip', 131161243162),
                           ('GameplayRestriction.BlockFastTravel', 151159473294),
                           ('ReactionPresets.NoReaction', 115253861404)]:
        named = {'$type': 'TweakDBID', '$storage': 'string', '$value': name}
        numeric = {'$type': 'TweakDBID', '$storage': 'uint64', '$value': str(expected)}
        assert canonical(named) == canonical(numeric)
        assert canonical(named) != canonical(numeric | {'$value': str(expected + 1)})
    assert canonical({'id': 1, 'value': 'a'}) != canonical({'id': 2, 'value': 'a'})
    assert canonical([1, 2]) != canonical([2, 1])
    assert strict(canonical({'v': True})) != strict(canonical({'v': 1}))
    assert strict(canonical({'v': 1.0})) != strict(canonical({'v': 1}))
    for invalid in ('-1', '+1', '1.0', str(1 << 64), '', '１２', 1, True):
        try:
            canonical({'$type': 'TweakDBID', '$storage': 'uint64', '$value': invalid})
        except AssertionError:
            pass
        else:
            raise AssertionError(f'Invalid ID accepted: {invalid!r}')


if __name__ == '__main__':
    self_test()
    assert payload(sys.argv[1]) == payload(sys.argv[2]), 'Native payload mismatch beyond TweakDBID spelling'
