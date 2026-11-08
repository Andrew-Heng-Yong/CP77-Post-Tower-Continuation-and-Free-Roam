"""Pure source/index helpers. Importing this module has no write side effects."""

import gzip
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parents[1]
PREVIOUS = WORKSPACE / 'prealpha/johnny_dialogue_index_20261107_01'
COVERAGE = WORKSPACE / 'prealpha/johnny_dialogue_coverage_20261107_01'
INDEX = TASK / 'index_05'


def read(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8-sig') as stream:
        return json.load(stream)


def write(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def encode(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


def scalar(data):
    if isinstance(data, dict):
        for key in ('$value', 'id', 'ruid', 'val', 'value', 'mask'):
            if key in data:
                return scalar(data[key])
    return data


def walk(data, path=''):
    if isinstance(data, dict):
        yield path, data
        for key, child in data.items():
            yield from walk(child, path + '/' + key)
    elif isinstance(data, list):
        for ordinal, child in enumerate(data):
            yield from walk(child, path + '/' + str(ordinal))


def resource_id(archive, key):
    return hashlib.sha256((str(Path(archive)).casefold() + '|' + str(key)).encode()).hexdigest()[:24]


def depot_key(depot):
    if depot.isdecimal():
        return depot
    result = 14695981039346656037
    for byte in depot.replace('/', '\\').lower().encode():
        result = ((result ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return str(result)
