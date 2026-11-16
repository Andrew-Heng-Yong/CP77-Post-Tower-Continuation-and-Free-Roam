"""Access the pinned Batch 3 source capture and edit its private successor."""

from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
WS = HERE.parents[1]
REVIEW = WS / 'prealpha/johnny_video_review_20261108_02/review_01'
BASE = WS / 'prealpha/johnny_batch2_jb1/candidate_04'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'

sys.path.insert(0, str(WS / 'prealpha/quest_restoration_qr13'))
from resource_edit import Edit as ResourceEdit
from common import walk, value
from model import Resource


class Edit(ResourceEdit):
    def h(self, data):
        handle = super().h(data)
        self.r.handles[handle['HandleId']] = data
        return handle


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def source_rows():
    rows = read(REVIEW / 'source_01/manifest.json')['resources']
    return {row['depot']: row for row in rows}


def load(row):
    assert sha(row['raw']) == row['sha256'] and sha(row['json']) == row['json_sha256'], row['depot']
    return read(row['json'])


def destination(node, ordinal=0, name=0):
    return {'$type': 'scnInputSocketId', 'nodeId': {'$type': 'scnNodeId', 'id': int(node)},
            'isockStamp': {'$type': 'scnInputSocketStamp', 'name': name, 'ordinal': ordinal}}


def stamp(data):
    return data['name'], data['ordinal']


def scene_nodes(r):
    return {r.d(h)['nodeId']['id']: r.d(h) for h in r.d(r.root['sceneGraph'])['graph']}


def actor_reference(payload, actor_ids):
    performers = {(actor_id << 8) | 1 for actor_id in actor_ids}
    for item in walk(payload):
        kind = item.get('$type')
        if kind == 'scnActorId' and item.get('id') in actor_ids:
            return True
        if kind == 'scnPerformerId' and item.get('id') in performers:
            return True
        if kind == 'NodeRef' and value(item) == '#johnny':
            return True
        if kind == 'gameEntityReference':
            if item.get('reference', {}).get('$value') == '#johnny':
                return True
            names = (item.get(field, {}).get('$value', '') for field in (
                'dynamicEntityUniqueName', 'sceneActorContextName'))
            if any('johnny' in str(name).lower() for name in names):
                return True
    return False


def order_handles(doc, originals):
    """Retain definitions moved away from their remaining reference sites."""
    handles = originals | Resource(doc).handles
    seen = set()

    def emit(item, path=()):
        if isinstance(item, list):
            return [emit(v, path + (i,)) for i, v in enumerate(item)]
        if not isinstance(item, dict):
            return item
        if 'HandleId' in item or 'HandleRefId' in item:
            handle = str(item.get('HandleId', item.get('HandleRefId')))
            if handle not in handles:
                assert handle in ('-1', '0'), (handle, path)
                return item
            if handle in seen:
                return {'HandleRefId': handle}
            seen.add(handle)
            return {'HandleId': handle, 'Data': emit(handles[handle], path + ('Data',))}
        return {key: emit(v, path + (key,)) for key, v in item.items()}

    return emit(doc)
