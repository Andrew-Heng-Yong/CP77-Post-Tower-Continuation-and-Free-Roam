"""Select source-only checks needed to close the Step 1 boundary ledger."""

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from prepare import TASK, WORKSPACE, STEP1, read, sha, write


def main():
    output = TASK / 'evidence_04'
    if output.exists():
        raise SystemExit('Use a fresh follow-up output')
    prepared = read(TASK / 'evidence_01/prepared.json')
    frozen = read(TASK / 'evidence_03/frozen_inventory.json')['rows']
    tables = {}
    for name in ['evidence_02/tables.jsonl', 'evidence_03/tables.jsonl']:
        for line in (TASK / name).read_text(encoding='utf-8-sig').splitlines():
            row = json.loads(line)
            tables[(row['archive'].casefold(), row['key'])] = row
    resources = read(STEP1 / 'capture.json')['resources'] + read(STEP1 / 'capture_additions.json')['resources']
    raw_resources = {(r['archive'].casefold(), r['key']): r for r in resources}
    voice_graphs = []
    markers = [b'questPlayVoiceset_NodeType', b'questAudio_NodeType', b'questScene_NodeType',
               b'workPlaySound', b'workPlayVoice', b'workVoice']
    for row in resources:
        if Path(row['depot']).suffix not in {'.questphase', '.quest', '.gamedef'}:
            continue
        data = Path(row['raw']).read_bytes()
        if b'questPlayVoiceset_NodeType' in data:
            assert hashlib.sha256(data).hexdigest().upper() == row['sha256']
            voice_graphs.append({**row, 'evidence': 'EXACT_SERIALIZED_TYPE_NAME_LEAD'})
    for row in tables.values():
        if ('questPlayVoiceset_NodeType' in row['export_classes'] or
                'questPlayVoiceset_NodeType' in row['speech_name_leads']):
            if (row['archive'].casefold(), row['key']) not in raw_resources:
                voice_graphs.append({**row, 'evidence': 'CR2W_NAME_OR_EXPORT_TABLE_LEAD'})
    requests = {}

    def select(archive, key, depot, reason, raw=None, expected=None):
        identity = (archive.casefold(), str(key))
        request = requests.setdefault(identity, {
            'archive': archive, 'key': str(key), 'depot': depot,
            'reasons': [], 'raw': raw, 'sha256': expected,
        })
        request['reasons'].append(reason)

    for row in frozen:
        table = tables.get((row['archive'].casefold(), row['key']))
        if row['unnamed'] and Path(row['archive']).name == 'lang_en_text.archive' and table and table['root_type'] == 'JsonResource':
            select(row['archive'], row['key'], row['depot'], 'UNNAMED_ENGLISH_TEXT', expected=table['sha256'])
        if row['extension'] in {'.audio_metadata', '.voicetags'}:
            select(row['archive'], row['key'], row['depot'], 'VOICE_IDENTITY_METADATA', expected=table['sha256'] if table else None)
    for row in voice_graphs:
        select(row['archive'], row['key'], row['depot'], 'VOICESET_DISPATCH_GRAPH', row.get('raw'), row['sha256'])
    sound_classes = defaultdict(list)
    for row in tables.values():
        if row['requested_depot'] and Path(row['requested_depot']).suffix in {'.workspot', '.scenerid', '.animgraph'}:
            matches = [t for t in row['export_classes'] if re.search(r'(?i)(sound|voice|speech|bark|dialog)', t)]
            if matches:
                select(row['archive'], row['key'], row['requested_depot'], 'SUPPORT_SPEECH_OR_SOUND_CLASS', expected=row['sha256'])
                for match in matches:
                    sound_classes[match].append(row['depot'])
    output.mkdir()
    write(output / 'requests.json', {'archives': prepared['archives'],
        'resources': sorted(requests.values(), key=lambda r: (r['archive'], int(r['key']))),
        'voice_graph_leads': voice_graphs, 'support_sound_classes': dict(sound_classes),
        'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'requests': len(requests),
        'reasons': dict(Counter(reason for r in requests.values() for reason in r['reasons'])),
        'support_classes': {k: len(v) for k, v in sound_classes.items()}}, indent=2))


if __name__ == '__main__':
    main()
