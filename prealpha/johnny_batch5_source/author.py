"""Write and verify the reviewed Batch 5 JSON edits without building a payload."""

from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
BATCH = PRE / 'johnny_video_review_20261110_01'
JB3 = PRE / 'johnny_batch4_jb3'
OUT = HERE / 'source_edits_01'

sys.dont_write_bytecode = True
sys.path.extend(str(PRE / d) for d in ('johnny_batch4_jb3', 'johnny_batch3_jb2', 'johnny_batch2_jb1'))
from resources import Resource, load, read, sha, value, walk, write
from common import fnv
from scene_edits import edit_scene
from selection import select
from check_source import phase_parity, scene_parity, signal_checks


PINS = {
    BATCH / 'review_manifest.json': 'E15C9FAD8AADCD8BE471C716E0B064D0BE803AC77F4163967D78ABE3595546EB',
    BATCH / 'review_01/findings.json': '3CFBF6C16B4DAFD4CB25338804FD21D82F31B233D6EB68244CD1A39C9C858D5B',
    JB3 / 'deployment_01/installed_manifest_01.json': 'DB5E4119003F7E1BFDD6C1AB91AE9D186EB20380AFC69D61F1A889964EACC596',
    JB3 / 'candidate_01/package_manifest.json': '2CCDB16A29B7EBE3AC43193D360839BF5543EC34677179D9B7921DD91C7CEBDF',
    JB3 / 'archive_readback_01.json': 'D66D912EDA9B3FD31DDE86E13F5ED05110456A67B51B82D8B315196BBF5BB5CF',
}


def capture():
    for path, digest in PINS.items():
        assert sha(path) == digest, path
    findings = read(BATCH / 'review_01/findings.json')
    manifests = {BATCH / 'review_01' / m['path']: m['sha256'] for m in findings['source_manifests']}
    captured = {}
    for path, digest in manifests.items():
        assert sha(path) == digest, path
        m = read(path)
        assert m['status'] == 'PASS_BATCH5_CURRENT_PROVIDER_PINS' and not m['issues'], path
        captured[path.parent.name] = m['resources']
    rows = {r['depot']: r for r in captured['source_01']}
    other = {r['depot']: r for r in captured['source_02']}
    assert len(rows) == 42 and len(other) == 3 and rows.keys().isdisjoint(other)
    for depot, row in (rows | other).items():
        assert not row['decode_error'] and row['key'] == fnv(depot), depot
    return rows, other, PINS | manifests


def namespace(quests, rows, other):
    aliases, wrappers, scenes = {}, set(), {}
    for quest in quests:
        evidence = quest['connected_source_evidence']
        scene, = evidence['scenes']
        root, = quest['registered_entries']
        assert root.startswith('towercontinued\\') and root not in wrappers
        wrappers.add(root)
        scenes[scene['depot']] = scene
        linked = {c[k] for c in evidence['calls'] for k in ('source', 'target')}
        for source in linked - {root}:
            assert source.startswith('base\\') and source not in aliases, source
            aliases[source] = f"towercontinued\\johnny_batch5\\{quest['id']}\\{Path(source).name}"
    assert len(aliases) == 32 and len(scenes) == len(wrappers) == 10
    assert rows.keys() == wrappers | aliases.keys()

    base = read(JB3 / 'candidate_01/package_manifest.json')['source_resources']
    rb = read(JB3 / 'archive_readback_01.json')['resources']
    assert base == {r['depot']: r['sha256'] for r in rb}
    assert all(base[d] == rows[d]['sha256'] for d in wrappers)
    existing_keys = {r['key'] for r in rb + list(rows.values()) + list(other.values())}
    new_keys = {fnv(d) for d in aliases.values()}
    assert len(new_keys) == len(aliases) and new_keys.isdisjoint(existing_keys)
    return aliases, wrappers, scenes


def remap(doc, aliases):
    changed = Counter()
    for item in walk(doc):
        if item.get('$type') == 'ResourcePath' and value(item) in aliases:
            source = value(item)
            item['$value'] = aliases[source]
            changed[source] += 1
    return dict(changed)


def verify_calls(quests, aliases, before, after):
    verified = []
    for quest in quests:
        for call in quest['connected_source_evidence']['calls']:
            source, target = call['source'], call['target']
            alias = aliases[target]
            for c in call['connected_calls']:
                graph, edge = c['graph'], c['edge']
                parent = after[source]['graphs'][graph]
                assert edge in before[source]['graphs'][graph]['edges'] and edge in parent['edges']
                refs = parent['nodes'][edge[2]]['refs']
                assert alias in refs and target not in refs, (source, target, edge)
                child = after[target]['graphs']['scene' if target.endswith('.scene') else 'root']
                assert child['entries'][edge[3]] == c['target_entry_node'], (source, target, edge)
                verified.append({'source': aliases.get(source, source), 'target': alias, **c})
    return verified


def main():
    assert not OUT.exists(), 'Preserve the existing source edit directory'
    rows, other, pins = capture()
    quests = read(BATCH / 'review_manifest.json')['quests']
    notes, cuts, decision = select(BATCH)
    aliases, wrappers, scenes = namespace(quests, rows, other)
    assert cuts.keys() == scenes.keys()
    for row in other.values():
        load(row)

    docs, before, after, changes = {}, {}, {}, {}
    for depot, row in rows.items():
        doc = load(row)
        before[depot] = Resource(doc).normalize()
        if depot in scenes:
            # Max's dialog/camera conditions and the Arroyo conversation need
            # to listen to their copied scene. Backs' cat tag remains native.
            scene_aliases = {depot: aliases[depot]} if Path(depot).name in (
                'sts_wat_nid_12_max_jones.scene', 'sts_std_arr_06_scn.scene') else {}
            relocated = remap(doc, scene_aliases)
            doc, change = edit_scene(doc, Path(depot).name, scenes[depot]['bound_entries'], cuts[depot])
            after[depot] = Resource(doc).normalize()
            scene_parity(depot, before[depot], after[depot], doc, cuts[depot], change, scene_aliases)
        else:
            original = deepcopy(doc)
            relocated = remap(doc, aliases)
            restored = deepcopy(doc)
            remap(restored, {target: source for source, target in aliases.items()})
            assert restored == original and relocated, depot
            after[depot] = Resource(doc).normalize()
            phase_parity(depot, before[depot], after[depot])
            change = {}
        docs[depot] = doc
        changes[depot] = {**change, 'references_rebound': relocated}

    verified_calls = verify_calls(quests, aliases, before, after)
    checks = signal_checks({Path(depot).name: model for depot, model in after.items()})
    OUT.mkdir()
    write(OUT / 'checks.json', {'status': 'PASS_BATCH5_SOURCE', 'scene_signal_fixtures': checks,
                                'verified_call_edges': verified_calls})
    snapshot = OUT / 'reviewed_worksheet.txt'
    snapshot.write_bytes(notes.read_bytes())
    assert sha(snapshot) == decision['worksheet_sha256']

    files = []
    for depot, doc in docs.items():
        target = aliases.get(depot, depot)
        path = OUT / (target + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        write(path, doc)
        assert read(path) == doc, path
        files.append({
            'source_depot': depot, 'source_key': rows[depot]['key'],
            'source_sha256': rows[depot]['sha256'], 'source_json_sha256': rows[depot]['json_sha256'],
            'output': path.relative_to(OUT).as_posix(), 'output_sha256': sha(path),
            'private_depot': target, 'private_key': fnv(target), **changes[depot],
        })
    write(OUT / 'source_manifest.json', {
        'status': 'BATCH5_EDITED_SOURCE_ONLY', 'baseline': 'JB3', 'approval': decision,
        'input_manifests': {p.relative_to(PRE).as_posix(): h for p, h in pins.items()},
        'retained_wrapper_depots': sorted(wrappers), 'new_archive_xl_registrations': [],
        'other_owners_preserved': sorted(other),
        'checks_sha256': sha(OUT / 'checks.json'), 'files': files,
    })
    print(f'Batch 5 source readback verified {len(files)} JSON files, '
          f'{len(verified_calls)} connected call edges and {len(checks)} signal fixtures.')


if __name__ == '__main__':
    main()
