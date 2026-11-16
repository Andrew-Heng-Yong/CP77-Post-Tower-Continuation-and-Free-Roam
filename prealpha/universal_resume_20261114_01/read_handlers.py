"""Bind saved native registrations to their authored nodes without entering a quest."""
import argparse
from binascii import crc_hqx
from collections import Counter, defaultdict
from contextlib import closing
from functools import cache
import json
from pathlib import Path
import sqlite3
import struct
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
PRESERVATION = PREALPHA / 'handler_preservation_hp1_20261112_01'
REGISTRY = PREALPHA / 'quest_resume_registry_20261112_01'
RD10 = PREALPHA / 'resume_dispatcher_rd10_kirk_20261113_01'
GIGS = PREALPHA / 'resume_dispatcher_rd5_gigs_20261113_01'
BATCH = PREALPHA / 'resume_dispatcher_rd6_batch50_20261113_01'
sys.path.insert(0, str(PRESERVATION))
from analyze import framed, freezer, paths, phase_hash
from prepare import read, sha, write

sys.path.insert(0, str(REGISTRY))
from model import value, walk


ROOTS = ('base\\quest\\cyberpunk2077.quest', 'ep1\\quest\\ep1.quest')
DELAYS = {'questRealtimeDelay_ConditionType', 'questGameTimeDelay_ConditionType'}
INPUTS = {
    RD10 / 'deployment_01/installed_manifest_01.json': 'AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8',
    RD10 / 'archive_01/readback.json': '5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81',
    REGISTRY / 'registry_02/registry.sqlite3': 'BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9',
    REGISTRY / 'activities_01/registry.json': 'C3DF208583C05209CCB62E56331046769AE3FD0397503EAAF7D602B02B6E1F0A',
    PRESERVATION / 'checkpoint.json': 'E7541F213234DB499707C71D57211FF894E88D2405B6BFD9A5D35C06F7688194',
    GIGS / 'evidence_01/batch_assessment.json': 'E12CFF4425667D6A4DBDD3CB4A48D9F161CED530ABC058FC62AD3B088FEE7354',
    GIGS / 'saves_01/AutoSave-3/manifest.json': '6238020F12F1B11C6DA1DFFC329041E22283C41CBDE6AB3931A0D0CFD8227B10',
    GIGS / 'saves_01/AutoSave-5/manifest.json': 'E3E7DA3B5349BD2883CB3555C96800822090849D6D571D9F5FC7E8D68DA806D0',
    BATCH / 'evidence_04/installed_readback.json': '1527E0946B23D197D28FBB02DB7002129C46EEDCDEB9B6C5B80D7D5EE0E9CA0C',
    BATCH / 'evidence_04/provider_watch.json': '5A4206BA599DC4F4240708BCB5EE81F0C6215AF51A7CF0A63A1326BEFA236B0D',
}


def pin(file, expected):
    if sha(file) != expected:
        raise ValueError(f'Input hash changed: {file}')
    return file


@cache
def token(name):
    result = 0xCBF29CE484222325
    for byte in name.encode('utf-8'):
        result = ((result ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return result


class Source:
    def __init__(self, db, archive_members, bindings):
        self.db = db
        self.by_depot = defaultdict(list)
        self.depots = {}
        for rid, depot, role, digest in db.execute('SELECT rid, depot, role, sha256 FROM resources'):
            self.by_depot[depot.lower()].append((rid, role, digest))
            self.depots[rid] = depot
        self.members = archive_members
        self.injected = defaultdict(set)
        for binding in bindings:
            parent = self.provider(binding['parent'].lower())
            if parent is None:
                continue
            address = binding.get('input', binding.get('connection', []))
            if isinstance(address, dict):
                address = address['node']
            if not address:
                start, = db.execute("SELECT id FROM nodes WHERE rid=? AND graph='root' AND type='questStartNodeDefinition'", (parent,))
                address = start
            *scopes, start_node = map(int, address)
            graph = '/'.join(('root', *(str(n) for n in scopes)))
            if self.authored_node(parent, graph, start_node) is None:
                continue
            depot = binding['path']
            node_id = crc_hqx(f'{depot}:{start_node}'.encode('utf-8'), 0xFFFF)
            self.injected[parent, graph, node_id].add(depot)

    @cache
    def provider(self, depot):
        rows = self.by_depot[depot]
        if any(role == 'OTHER_MOD' for _, role, _ in rows):
            return None
        if depot in self.members:
            matches = {rid for rid, role, digest in rows if role == 'PTFR' and digest == self.members[depot]}
        else:
            matches = {rid for rid, role, _ in rows if role == 'STOCK'}
        if len(matches) == 1:
            return next(iter(matches))
        return None

    @cache
    def authored_node(self, rid, graph, node_id):
        row = self.db.execute('SELECT parameters_json FROM nodes WHERE rid=? AND graph=? AND id=?',
                              (rid, graph, node_id)).fetchone()
        return json.loads(row[0]) if row else None

    def node(self, rid, graph, node_id):
        authored = self.authored_node(rid, graph, node_id)
        injected = self.injected.get((rid, graph, node_id), ())
        if not injected:
            return authored
        if authored is not None or len(injected) != 1:
            return None
        depot, = injected
        return {'$type': 'questPhaseNodeDefinition', 'phaseResource': {'DepotPath': depot}}

    @cache
    def scope(self, address):
        if len(address) == 1:
            root = self.provider(ROOTS[address[0]])
            return (root, 'root') if root is not None else None
        parent = self.scope(address[:-1])
        if parent is None:
            return None
        rid, graph = parent
        node_id = address[-1]
        node = self.node(rid, graph, node_id)
        if node is None or node['$type'] != 'questPhaseNodeDefinition':
            return None
        target = value(node['phaseResource']['DepotPath'])
        if target in (0, '0'):
            nested = f'{graph}/{node_id}'
            exists = self.db.execute('SELECT 1 FROM graphs WHERE rid=? AND path=?', (rid, nested)).fetchone()
            return (rid, nested) if exists else None
        if not isinstance(target, str):
            return None
        target_id = self.provider(target.replace('/', '\\').lower())
        return (target_id, 'root') if target_id is not None else None


def saved_components(file):
    manifest = read(file)
    if manifest['save_version'] != 277:
        raise ValueError('Unsupported save version')
    gap = bytes.fromhex(manifest['root_gap_hex'])
    if gap != bytes([len(ROOTS)]) + struct.pack('<QQ', *(token(depot) for depot in ROOTS)):
        raise ValueError('Saved root array does not match the two bound native roots')
    data = {}
    for row in manifest['nodes']:
        name = row['name']
        if name in ('customArray', 'eventManager', 'questPhaseFreezer'):
            item = file.parent / f'{name}.bin'
            raw = pin(item, row['sha256']).read_bytes()
            if len(raw) != row['size'] or name in data:
                raise ValueError(f'Invalid component inventory: {name}')
            data[name] = (raw, row['id'])
    addresses = paths(*data['customArray'])
    index = defaultdict(set)
    for address in addresses:
        if address[0] < len(ROOTS):
            index[phase_hash(address)].add(address)
        else:
            raise ValueError(f'Unbound phase root {address[0]}')
    events = struct.iter_unpack('<QII', framed(*data['eventManager'], 16))
    return manifest['source_sha256'], index, list(events), freezer(*data['questPhaseFreezer'])


def resolve_event(source, index, event):
    registration, phase, node_id = event
    if not registration or node_id >= 0xFFFF:
        return 'invalid_registration', None
    candidates = index.get(phase, ())
    if len(candidates) != 1:
        return ('ambiguous_path' if candidates else 'missing_path'), None
    address, = candidates
    scope = source.scope(address)
    if scope is None:
        return 'unresolved_phase', None
    node = source.node(*scope, node_id)
    if node is None:
        return 'unresolved_node', None
    types = {item['$type'] for item in walk(node) if '$type' in item}
    matches = sorted(t for t in types if token(t) == registration)
    if len(matches) != 1:
        return 'unresolved_type', None
    return 'bound', {'address': address, 'resource': scope[0], 'graph': scope[1], 'node': node_id,
                     'depot': source.depots[scope[0]],
                     'definition_type': node['$type'], 'registration_type': matches[0],
                     'delay_types': sorted(types & DELAYS)}


def inspect(source, path):
    digest, index, events, groups = saved_components(path)
    outcomes = Counter()
    handlers = []
    for event in events:
        if event == (0, 0, 0xFFFF):
            continue
        status, bound = resolve_event(source, index, event)
        outcomes[status] += 1
        if bound is not None:
            handlers.append(bound)
    return digest, outcomes, handlers, len(groups)


def descendant_handlers(handlers, owner_path):
    prefix = tuple(owner_path)
    return [row for row in handlers if row['address'][:len(prefix)] == prefix]


def verify_controls(preservation, gigs, by_slot):
    checked = 0
    for slot, sample in preservation.items():
        digest, _, handlers, _ = by_slot[slot]
        assert digest == sample['source_sha256']
        for case in sample['cases'].values():
            actual = descendant_handlers(handlers, case['root_path'])
            assert Counter((r['address'], r['node']) for r in actual) == Counter(
                (tuple(r['path']), r['node']) for r in case['handlers']), (slot, case['root_path'])
            checked += 1
    for result in gigs['stages']:
        for owner in result['source_owner_paths']:
            owner_path = [step[2] for step in owner['source_path']]
            for slot, prior in owner['controls'].items():
                fixture = 'RD5 AutoSave-5' if slot == 'AutoSave-5' else slot
                actual = descendant_handlers(by_slot[fixture][2], owner_path)
                assert Counter((r['address'], r['node']) for r in actual) == Counter(
                    (tuple(address), node) for address, node in prior['descendant_nodes']), (slot, owner_path)
                checked += 1
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=int, required=True, choices=range(1, 100), metavar='1–99')
    args = parser.parse_args()
    output = HERE / f'evidence_{args.attempt:02d}'
    if output.exists():
        raise FileExistsError(output)
    for path, digest in INPUTS.items():
        pin(path, digest)

    installed = read(RD10 / 'deployment_01/installed_manifest_01.json')
    game = Path(installed['game_root'])
    pin(game / 'archive/pc/mod/zzzz_PTFR_Combined.archive', installed['archive_sha256'])
    xl_path = 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
    xl_entry, = (row for row in installed['core_files'] if row['path'] == xl_path)
    pin(game / xl_path, xl_entry['sha256'])
    watch = read(BATCH / 'evidence_04/provider_watch.json')
    readback = read(BATCH / 'evidence_04/installed_readback.json')
    assert readback['input_sha256'] == sha(BATCH / 'evidence_04/provider_watch.json')
    assert watch['xl']['sha256'] == xl_entry['sha256']
    engine = 'D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'
    pin(game / 'bin/x64/Cyberpunk2077.exe', engine)
    members = read(RD10 / 'archive_01/readback.json')['members']
    archive_members = {row['depot'].lower(): row['sha256'] for row in members}
    assert len(archive_members) == len(members) == installed['archive_payloads']

    checkpoint = read(PRESERVATION / 'checkpoint.json')['artifacts']
    comparison = 'analysis_01/save_comparison.json'
    prior = read(pin(PRESERVATION / comparison, checkpoint[comparison]))
    save_manifests = {}
    for slot in prior:
        relative = f'saves_01/{slot}/manifest.json'
        save_manifests[slot] = pin(PRESERVATION / relative, checkpoint[relative])
    save_manifests['AutoSave-3'] = GIGS / 'saves_01/AutoSave-3/manifest.json'
    save_manifests['RD5 AutoSave-5'] = GIGS / 'saves_01/AutoSave-5/manifest.json'

    db_path = REGISTRY / 'registry_02/registry.sqlite3'
    with closing(sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True)) as db:
        other_bindings = []
        for file, digest, binding in db.execute('SELECT file, source_sha256, binding_json FROM registrations ORDER BY ordinal'):
            if Path(file).resolve() == (game / xl_path).resolve():
                continue
            if Path(file).parent == game / 'archive/pc/mod':
                other_bindings.append((file, digest, json.loads(binding)))
        for file, digest in {(file, digest) for file, digest, _ in other_bindings}:
            pin(file, digest)
        source = Source(db, archive_members, readback['bindings'] + [entry for _, _, entry in other_bindings])
        assert source.scope((0, 2, 82, 6, 21)) == (6542, 'root')
        assert source.scope((1, 0, 10, 4, 2, 30, 6, 4)) == (12821, 'root')
        by_slot = {slot: inspect(source, manifest) for slot, manifest in save_manifests.items()}
        gigs = read(GIGS / 'evidence_01/batch_assessment.json')
        controls = verify_controls(prior, gigs, by_slot)
        roster = dict(db.execute('SELECT selection, count(*) FROM quests GROUP BY selection'))

    samples = {}
    for slot, (digest, outcomes, handlers, groups) in by_slot.items():
        samples[slot] = {'save_sha256': digest, 'registration_outcomes': outcomes, 'freezer_groups': groups,
                         'definition_types': Counter(r['definition_type'] for r in handlers),
                         'delay_handlers': [r for r in handlers if r['delay_types']]}
        print(f'{slot}: {outcomes["bound"]} bound registrations, '
              f'{len(samples[slot]["delay_handlers"])} authored delay handlers')
    activities = read(REGISTRY / 'activities_01/registry.json')['rows']
    output.mkdir()
    write(output / 'assessment.json', {'status': 'OFFLINE_NATIVE_REGISTRATION_BINDING', 'engine_sha256': engine,
                                       'combined_bindings_read': len(readback['bindings']),
                                       'selected_jobs': roster['INCLUDE'], 'separate_jobs': roster['SEPARATE_SCOPE'],
                                       'activity_families': Counter(row['family'] for row in activities),
                                       'prior_owner_controls_matched': controls, 'fixtures': samples,
                                       'runtime_restoration': False, 'save_writes': 0, 'game_writes': 0})
    print(f'Matched {controls} prior owner comparisons. Wrote {output.name}/assessment.json')


if __name__ == '__main__':
    main()
