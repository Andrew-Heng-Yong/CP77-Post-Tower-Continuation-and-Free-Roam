"""Stage and verify the one-resource ML1 successor to the installed JB3 build."""

import json
import shutil
import stat
import sys
import zipfile
from pathlib import Path

from plan import HERE, PRIVATE_MAP, read, sha, write_new, root


OUT = HERE / 'candidate_01'
PLAN_PATH = HERE / 'plan.json'
ASSET_PATH = HERE / 'assets_01/providers.json'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'


def verify_inputs():
    plan = read(PLAN_PATH)
    manifest = read(plan['installed_manifest'])
    assert sha(plan['installed_manifest']) == plan['installed_manifest_sha256']
    assert sha(plan['capture']) == plan['capture_sha256']
    game = Path(manifest['game_root'])
    for row in manifest['core_files'] + manifest['required_files']:
        assert sha(game / row['path']) == row['sha256'], row['path']
    for row in plan['english_configs']:
        assert sha(row['config']) == row['sha256']

    asset_proof = read(ASSET_PATH)
    assert asset_proof['plan_sha256'] == sha(PLAN_PATH)
    assert asset_proof['archive_count'] == read(plan['capture'])['archives_indexed']
    providers = {r['depot']: r for r in asset_proof['providers']}
    assert len(providers) == len(asset_proof['providers'])
    assert set(providers) == set(plan['asset_depots'] + plan['other_custom_maps'])
    for r in providers.values():
        assert sha(r['raw']) == r['sha256'], r['depot']
    rig_refs = {r['depot'] for r in asset_proof['rig_providers']}
    for depot in plan['asset_depots']:
        provider = providers[depot]
        assert provider['rig'] in rig_refs and provider['clips']
        assert Path(provider['archive']).name == 'lang_en_voice.archive'
    private_keys = {row['private']['key'] for row in plan['additions']}
    assert len(private_keys) == 2
    for name in plan['other_custom_maps']:
        provider = providers[name]
        assert provider['language'] == 'en-us'
        assert not private_keys.intersection(provider['scene_keys'])
    assert {r['depot'] for r in asset_proof['english_voice_map_names']} == {plan['native_map']['depot']}

    clip_checks = []
    for row in plan['additions']:
        names = {name.lower() for name in providers[row['monk_anim_set']]['clips']}
        for line in row['retained_monologue_lines']:
            matches = sorted(names.intersection((line['male_clip'].lower(), line['female_clip'].lower())))
            assert matches, (row['private']['depot'], line['line'])
            clip_checks.append({'scene': row['private']['depot'], 'actor': row['monk_actor_name'],
                                'line': line['line'], 'matching_clips': matches})
    assert len(clip_checks) == 41
    return plan, manifest, clip_checks


def plain_tree(path):
    for p in (path, *path.rglob('*')):
        assert not (p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT), p


def prepare():
    plan, manifest, checks = verify_inputs()
    assert not OUT.exists(), 'Fresh candidate directory required'
    candidate = Path(manifest['source_candidate'])
    package_manifest = candidate / 'package_manifest.json'
    assert sha(package_manifest) == manifest['package_manifest_sha256']
    prior = read(package_manifest)
    raw = candidate / 'archive_source'
    package = candidate / 'package'
    plain_tree(raw)
    plain_tree(package)
    observed = {str(path.relative_to(raw)).replace('/', '\\'): sha(path) for path in raw.rglob('*') if path.is_file()}
    assert observed == prior['source_resources'] and len(observed) == 1636
    assert observed[PRIVATE_MAP] == plan['existing_map']['sha256']
    for row in manifest['core_files']:
        assert sha(package / row['path']) == row['sha256'], row['path']
    assert len([p for p in package.rglob('*') if p.is_file()]) == 51
    shutil.copytree(raw, OUT / 'archive_source')
    shutil.copytree(package, OUT / 'package')
    write_new(OUT / 'prepared.json', {'status': 'VERIFIED_ML1_INPUTS', 'plan_sha256': sha(PLAN_PATH),
              'asset_capture_sha256': sha(ASSET_PATH), 'base_package_manifest': str(package_manifest),
              'base_package_manifest_sha256': sha(package_manifest), 'clip_checks': checks, 'game_writes': 0})
    print(json.dumps({'candidate': str(OUT), 'monk_clip_checks': len(checks), 'source_members': len(observed)}))


def verify():
    plan, manifest, checks = verify_inputs()
    prepared = read(OUT / 'prepared.json')
    assert sha(PLAN_PATH) == prepared['plan_sha256'] and sha(ASSET_PATH) == prepared['asset_capture_sha256']
    base_pkg = Path(prepared['base_package_manifest'])
    assert sha(base_pkg) == prepared['base_package_manifest_sha256']
    base = read(base_pkg)
    cooked = read(OUT / 'readback/lipmap.json')['Data']['RootChunk']
    before = root(plan['existing_map'])
    stock = root(plan['native_map'])
    assert {k: v for k, v in cooked.items() if k not in ('scenePaths', 'sceneEntries')} == {
        k: v for k, v in before.items() if k not in ('scenePaths', 'sceneEntries')}
    assert len(cooked['scenePaths']) == len(cooked['sceneEntries']) == len(set(cooked['scenePaths'])) == 50
    assert cooked['scenePaths'][:48] == before['scenePaths'] and cooked['sceneEntries'][:48] == before['sceneEntries']
    for i, row in enumerate(plan['additions'], 48):
        assert str(cooked['scenePaths'][i]) == row['private']['key']
        donor = stock['sceneEntries'][row['native_map_index']]
        assert cooked['sceneEntries'][i] == donor == row['donor']
        assert str(stock['scenePaths'][row['native_map_index']]) == row['native']['key']
    assert {str(x) for x in cooked['scenePaths'][48:]}.isdisjoint(str(x) for x in stock['scenePaths'])

    packed = read(OUT / 'readback/archive.json')
    source = OUT / 'archive_source'
    actual = {str(p.relative_to(source)).replace('/', '\\'): sha(p) for p in source.rglob('*') if p.is_file()}
    assert len(actual) == len(packed['members']) == 1636
    assert actual == {row['depot']: row['sha256'] for row in packed['members']}
    assert set(actual) == set(base['source_resources'])
    assert [name for name in actual if actual[name] != base['source_resources'][name]] == [PRIVATE_MAP]
    pkg = OUT / 'package'
    assert packed['archive_sha256'] == sha(pkg / ARCHIVE)
    assert packed['map_sha256'] == actual[PRIVATE_MAP]
    files = [{'path': row['path'], 'sha256': sha(pkg / row['path']), 'bytes': (pkg / row['path']).stat().st_size}
             for row in manifest['core_files']]
    prior_files = {row['path']: row['sha256'] for row in manifest['core_files']}
    assert [r['path'] for r in files if r['sha256'] != prior_files[r['path']]] == [ARCHIVE]
    assert {p.relative_to(pkg).as_posix() for p in pkg.rglob('*') if p.is_file()} == set(prior_files)
    target = HERE / 'ML1_Core51_01.zip'
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for row in files:
            z.write(pkg / row['path'], row['path'])
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None and len(z.namelist()) == 51 and set(z.namelist()) == set(prior_files)
        assert all(z.read(row['path']) == (pkg / row['path']).read_bytes() for row in files)
    write_new(OUT / 'package_manifest.json', {'status': 'STAGED_ML1_READBACK_VERIFIED', 'epoch': 'ML1',
              'predecessor': 'JB3', 'before_installed_manifest': plan['installed_manifest'],
              'before_installed_manifest_sha256': plan['installed_manifest_sha256'], 'files': files,
              'archive_payloads': len(actual), 'source_resources': actual, 'changed_depots': [PRIVATE_MAP],
              'changed_paths': [ARCHIVE], 'retained_archive_members': len(actual) - 1,
              'retained_core_files': len(files) - 1, 'new_xl_registrations': 0,
              'before_map_sha256': plan['existing_map']['sha256'], 'after_map_sha256': actual[PRIVATE_MAP],
              'archive_sha256': packed['archive_sha256'], 'zip': str(target), 'zip_sha256': sha(target),
              'clip_checks': len(checks), 'lipmap_rows': len(cooked['scenePaths']),
              'archive_readback_sha256': sha(OUT / 'readback/archive.json'), 'gameplay_validation': 'PENDING',
              'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'zip': str(target), 'zip_sha256': sha(target), 'archive': packed['archive_sha256'],
                      'packaged_paths': len(files), 'readback_members': len(actual), 'lipmap_rows': 50,
                      'lines_checked': len(checks)}))


if __name__ == '__main__':
    actions = {'prepare': prepare, 'verify': verify}
    actions[sys.argv[1]]()
