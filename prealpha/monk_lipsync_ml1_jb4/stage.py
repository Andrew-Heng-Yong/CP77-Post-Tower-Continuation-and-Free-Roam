"""Apply the verified ML1 lip map to the current JB4 package."""

import argparse
from pathlib import Path
import shutil
import sys
from zipfile import ZIP_DEFLATED, ZipFile

HERE = Path(__file__).resolve().parent
JB4 = HERE.parent / 'johnny_batch6_jb4'
ML1 = HERE.parent / 'monk_lipsync_ml1'
BASE = JB4 / 'candidate_02'
OUT = HERE / 'candidate_01'
INSTALLED = JB4 / 'deployment_01/installed_manifest_01.json'
BASE_MANIFEST = BASE / 'package_manifest.json'
PLAN = HERE / 'plan.json'
PROOF = OUT / 'readback/archive.json'
BUNDLE = HERE / 'ML1_JB4_Core51_01.zip'
MAP = r'towercontinued\sidejob_repair_sr1\en-us.lipmap'
MAP_SHA = '8CF46F202E58185AE366175C22BC72EE79623439F7010DDFC034BAEB0D96BE43'

sys.path.insert(0, str(JB4))
from baseline import ARCHIVE, inventory, plain, read, sha, write


def checked(path, digest):
    path = Path(path)
    plain(path)
    assert sha(path) == digest, path
    return path


def baseline():
    installed = read(checked(INSTALLED, '305CFCF4F47A4F01AA080B51265C2E1A1830FFD334F68AC2C1134EA1CE5BBE49'))
    assert installed['core_epoch'] == 'JB4' and Path(installed['source_candidate']) == BASE
    manifest = read(checked(BASE_MANIFEST, installed['package_manifest_sha256']))
    assert manifest['files'] == installed['core_files'] and len(manifest['source_resources']) == 1723
    assert len(installed['core_files']) == 51 and len(installed['required_files']) == 26
    game = Path(installed['game_root'])
    for row in installed['core_files'] + installed['required_files']:
        p = checked(game / row['path'], row['sha256'])
        assert p.resolve().is_relative_to(game) and p.stat().st_size == row['bytes'], p
    return installed, manifest


def original_plan():
    return read(checked(ML1 / 'plan.json', '9F539AA1DE543679EC2CC24620C584BF982DD848BBCF669F50CEEA295C51AA26'))


def prepared_proof():
    path = ML1 / 'candidate_01/prepared.json'
    return read(checked(path, '7DF8235C42626E3A865B2A19111A36016F3F26472E730D702A7A3D54EA7B6C13'))


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    installed, base = baseline()
    source = BASE / 'archive_source'
    assert inventory(source, '\\') == base['source_resources']
    assert inventory(BASE / 'package') == {r['path']: r['sha256'] for r in base['files']}

    ml1 = original_plan()
    prepared = prepared_proof()
    assert prepared['plan_sha256'] == sha(ML1 / 'plan.json') and len(prepared['clip_checks']) == 41
    settings = Path(installed['save_root']).parents[2] / 'AppData/Local/CD Projekt Red/Cyberpunk 2077/UserSettings.json'
    groups = read(settings)['data']
    languages = [option['value'] for group in groups for option in group.get('options', [])
                 if option.get('name') == 'VoiceOver']
    assert languages == [ml1['voice_over']] == ['en-us'], languages

    old_rows = [ml1['existing_map'], *(r['private'] for r in ml1['additions'])]
    assert ml1['existing_map']['depot'] == MAP
    for row in old_rows:
        assert base['source_resources'][row['depot']] == row['sha256'], row['depot']
    donor = read(checked(ML1 / 'candidate_01/package_manifest.json',
                         'F3A0A83E189411266976EFAE43051AB414C5B40B59C214066A19A5F81CF475AF'))
    assert donor['status'] == 'STAGED_ML1_READBACK_VERIFIED' and donor['changed_depots'] == [MAP]
    assert donor['after_map_sha256'] == MAP_SHA
    fixed = checked(ML1 / 'candidate_01/archive_source' / MAP, MAP_SHA)
    assets = read(checked(ML1 / 'assets_01/providers.json', prepared['asset_capture_sha256']))
    assert assets['plan_sha256'] == prepared['plan_sha256']
    rows = old_rows + [ml1['native_map'], *(r['native'] for r in ml1['additions'])]
    rows += assets['providers'] + assets['rig_providers']
    providers = [{'depot': r['depot'], 'key': r['key'], 'archive': r['archive'], 'sha256': r['sha256']} for r in rows]
    assert len(providers) == len({(r['depot'], r['archive']) for r in providers})
    for config in ml1['english_configs']:
        checked(config['config'], config['sha256'])

    shutil.copytree(source, OUT / 'archive_source')
    shutil.copyfile(fixed, OUT / 'archive_source' / MAP)
    for row in base['files']:
        if row['path'] == ARCHIVE:
            continue
        p = OUT / 'package' / row['path']
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASE / 'package' / row['path'], p)
    (OUT / 'package' / ARCHIVE).parent.mkdir(parents=True, exist_ok=True)
    write(PLAN, {
        'status': 'VERIFIED_ML1_JB4_SOURCE', 'voice_over': 'en-us',
        'installed_manifest': str(INSTALLED), 'installed_manifest_sha256': sha(INSTALLED),
        'base_package_manifest': str(BASE_MANIFEST), 'base_package_manifest_sha256': sha(BASE_MANIFEST),
        'game_root': installed['game_root'], 'archive_before': installed['archive_sha256'],
        'map': MAP, 'map_after': MAP_SHA, 'providers': providers, 'english_configs': ml1['english_configs'],
        'original_plan_sha256': sha(ML1 / 'plan.json'), 'clip_count': len(prepared['clip_checks']),
        'scene_keys': [r['private']['key'] for r in ml1['additions']],
    })
    print(f"Prepared the verified monk map over {len(base['source_resources'])} JB4 resources.")


def read_map(row):
    checked(row['raw'], row['sha256'])
    return read(checked(row['json'], row['json_sha256']))['Data']['RootChunk']


def seal():
    installed, base = baseline()
    plan, packed = read(PLAN), read(PROOF)
    ml1 = original_plan()
    assert packed['status'] == 'PASS_ML1_JB4_ARCHIVE_READBACK' and packed['plan_sha256'] == sha(PLAN)
    assert plan['original_plan_sha256'] == sha(ML1 / 'plan.json')
    before, stock = read_map(ml1['existing_map']), read_map(ml1['native_map'])
    cooked = read(OUT / 'readback/lipmap.json')['Data']['RootChunk']
    paths, entries = 'scenePaths', 'sceneEntries'
    assert cooked[paths] == before[paths] + plan['scene_keys']
    assert cooked[entries] == before[entries] + [stock[entries][r['native_map_index']] for r in ml1['additions']]
    assert {k: v for k, v in cooked.items() if k not in (paths, entries)} == {
        k: v for k, v in before.items() if k not in (paths, entries)}
    assert len(cooked[paths]) == len(set(cooked[paths])) == 50
    assert set(cooked[paths][48:]).isdisjoint(stock[paths])

    resources = {r['depot']: r['sha256'] for r in packed['members']}
    expected = base['source_resources'] | {MAP: MAP_SHA}
    assert resources == expected == inventory(OUT / 'archive_source', '\\')
    assert len(resources) == len(packed['members']) == len({r['key'] for r in packed['members']}) == 1723
    assert packed['archive_sha256'] == sha(OUT / 'package' / ARCHIVE)
    checked(OUT / 'readback/en-us.lipmap', MAP_SHA)
    package = OUT / 'package'
    files = inventory(package)
    baseline_files = {r['path']: r['sha256'] for r in installed['core_files']}
    assert files == baseline_files | {ARCHIVE: packed['archive_sha256']}
    assert len(files) == 51 and files[ARCHIVE] != baseline_files[ARCHIVE]

    with ZipFile(BUNDLE, 'x', ZIP_DEFLATED) as z:
        for path in sorted(files):
            z.write(package / path, path)
    with ZipFile(BUNDLE) as z:
        assert len(z.namelist()) == len(files) and set(z.namelist()) == files.keys()
        assert all(z.read(p) == (package / p).read_bytes() for p in files)
    write(OUT / 'package_manifest.json', {
        'status': 'STAGED_ML1_JB4_READBACK_VERIFIED', 'epoch': 'ML1', 'predecessor': 'JB4',
        'before_installed_manifest': str(INSTALLED), 'before_installed_manifest_sha256': sha(INSTALLED),
        'files': [{'path': p, 'sha256': h, 'bytes': (package / p).stat().st_size} for p, h in sorted(files.items())],
        'source_resources': resources, 'changed_depots': [MAP], 'changed_paths': [ARCHIVE],
        'archive_payloads': len(resources), 'archive_sha256': files[ARCHIVE], 'new_xl_registrations': 0,
        'zip': str(BUNDLE), 'zip_sha256': sha(BUNDLE), 'archive_readback_sha256': sha(PROOF),
        'lipmap_rows': len(cooked[paths]), 'clip_checks': plan['clip_count'], 'gameplay_validation': 'PENDING',
    })
    print(f"Verified 51 package paths, {len(resources)} archive members, and {plan['clip_count']} monk lines.")


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('action', choices=('prepare', 'seal'))
    (prepare if cli.parse_args().action == 'prepare' else seal)()
