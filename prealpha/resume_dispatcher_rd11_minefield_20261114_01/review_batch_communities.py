"""Compare saved community entries for the other four reviewed entrances."""
from collections import Counter
from pathlib import Path

from read_community import HERE, PREALPHA, inspect, read, sha, write

SECTORS = {
    'always_loaded_0.streamingsector': ('sts_ep1_12_', 'sts_ep1_13_'),
    'always_loaded_1.streamingsector': ('dtn_03_', 'loc_sts_cct_dtn_03_default_state_bouncers'),
    'always_loaded_2.streamingsector': ('nid_02_',),
}


def source_keys(manifest):
    sources = {}
    locker = None
    for row in read(manifest)['rows']:
        sector = row['depot'].rsplit('\\', 1)[-1]
        path = PREALPHA.parent / row['export']
        assert sha(path) == row['export_sha256']
        root = read(path)['Data']['RootChunk']
        if sector == 'always_loaded_1.streamingsector':
            locker, = (ref['$value'] for ref in root['nodeRefs']
                       if ref['$storage'] == 'string' and ref['$value'].endswith('/#dtn_03_security_locker'))
        for handle in root['nodes']:
            node = handle.get('Data', {})
            if node.get('$type') != 'worldCompiledCommunityAreaNode':
                continue
            name = node['debugName']['$value'].strip('{}')
            if name.startswith(SECTORS[sector]):
                assert name not in sources, name
                sources[name] = int(node['sourceObjectId']['hash'])
    assert len(sources) == len(set(sources.values())) == 24
    assert locker
    return sources, locker


def summarized(target):
    assert target['in_outer_list'] and target['spawner_row'] is None
    return Counter((row['phase'], row['row']['memory_0x46_u8'],
                    bool(row['row']['array_0x00'] or row['row']['array_0x20']))
                   for row in target['entry_rows'])


def main():
    sources = HERE / 'evidence_02/world_sources.json'
    capture = HERE / 'capture_01/manifest.json'
    keys, locker = source_keys(sources)
    records = {}
    digests = {}
    for item in read(capture)['saves']:
        path = Path(item['trailing_path'])
        assert sha(path) == item['trailing_sha256']
        records[item['slot']] = inspect(path.read_bytes(), list(map(int, item['outer_keys'])), keys)
        digests[item['slot']] = item['source_sha256']

    assert set(records) == {'ManualSave-26', 'AutoSave-3', 'AutoSave-5'}
    pre = records['ManualSave-26']
    counts = {name: summarized(target) for name, target in pre.items()}
    assert all(counts == {name: summarized(target) for name, target in sample.items()} for sample in records.values())
    for name, expected in {
        'nid_02_com': {('A', 1, True): 1},
        'nid_02_combat_com': {('A', 1, True): 11, ('reinforcement', 0, False): 6},
        'dtn_03_com': {('Default', 1, True): 5},
        'dtn_03_combat_com': {('Default', 1, True): 8, ('A', 1, True): 1, ('B', 1, True): 1},
        'loc_sts_cct_dtn_03_default_state_bouncers': {('default', 0, True): 1},
        'sts_ep1_12_main_com': {('default', 1, True): 2},
        'sts_ep1_12_courier_scene_com': {('01default', 1, True): 1},
        'sts_ep1_12_combat_com': {('default', 1, True): 15},
        'sts_ep1_13_cars_com': {('A', 1, True): 3, ('a', 1, True): 1},
        'sts_ep1_13_hands_guy_com': {('A', 1, True): 1},
        'sts_ep1_13_combat_com': {('A', 1, True): 19, ('a', 1, True): 2},
    }.items():
        assert counts[name] == expected, name

    def without_offsets(target):
        return {row['inner']: (row['phase'], {field: value for field, value in row['row'].items()
                if field not in ('start_offset', 'end_offset')}) for row in target['entry_rows']}

    exact = {name: all(without_offsets(sample[name]) == without_offsets(target) for sample in records.values())
             for name, target in pre.items()}
    evidence = HERE / 'evidence_02/batch_communities.json'
    if evidence.exists():
        raise FileExistsError(evidence)
    write(evidence, {'status': 'SAVED_COMMUNITIES_ONLY', 'world_sources_sha256': sha(sources),
                     'capture_sha256': sha(capture), 'save_sha256': digests, 'locker_reference': locker,
                     'exact_rows_equal_by_community': exact, 'samples': records,
                     'runtime_admission': 0, 'game_writes': 0, 'save_writes': 0})
    print(f'Compared {len(keys)} communities in {len(records)} fixtures. {sum(exact.values())} match every entry field.')


if __name__ == '__main__':
    main()
