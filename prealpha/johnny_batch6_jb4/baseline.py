"""Prepare the pinned JB3 package and the reviewed profile setup overlay."""

import importlib.util
from pathlib import Path
import shutil
import stat
import sys

HERE = Path(__file__).resolve().parent
PRE = HERE.parent
JB3 = PRE / 'johnny_batch4_jb3'
BASE = JB3 / 'candidate_01'
OUT = HERE / 'candidate_02'
INSTALLED = JB3 / 'deployment_01/installed_manifest_01.json'
PROFILE = PRE / 'profile_setup_ps1'
REVIEW = PRE / 'johnny_video_review_20261110_02'
BATCH5 = PRE / 'johnny_batch5_source/source_edits_01'
sys.path.append(str(PRE / 'johnny_batch3_jb2'))
from resources import ARCHIVE, read, sha, write

XL = ARCHIVE + '.xl'


def plain(path):
    for component in (path, *path.parents):
        assert not component.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, component


def inventory(root, separator='/'):
    plain(root)
    rows = {}
    for path in root.rglob('*'):
        assert not path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, path
        if path.is_file():
            rows[path.relative_to(root).as_posix().replace('/', separator)] = sha(path)
    return rows


def installed_baseline():
    assert sha(INSTALLED) == 'DB5E4119003F7E1BFDD6C1AB91AE9D186EB20380AFC69D61F1A889964EACC596'
    manifest = read(INSTALLED)
    assert manifest['core_epoch'] == 'JB3'
    game = Path(manifest['game_root'])
    for row in manifest['core_files'] + manifest['required_files']:
        path = game / row['path']
        plain(path)
        assert path.resolve().is_relative_to(game) and sha(path) == row['sha256'], path
        assert path.stat().st_size == row['bytes'], path
    return manifest


def prepare():
    assert not OUT.exists()
    installed = installed_baseline()
    pkg = BASE / 'package_manifest.json'
    assert sha(pkg) == '2CCDB16A29B7EBE3AC43193D360839BF5543EC34677179D9B7921DD91C7CEBDF'
    manifest = read(pkg)
    files = {r['path']: r['sha256'] for r in manifest['files']}
    assert files == {r['path']: r['sha256'] for r in installed['core_files']}
    assert len(files) == 51 and inventory(BASE / 'package') == files
    assert inventory(BASE / 'archive_source', '\\') == manifest['source_resources']

    spec = importlib.util.spec_from_file_location('profile_setup_checks', PROFILE / 'test_source.py')
    ps = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ps)
    pins = read(PROFILE / 'provenance.json')
    assert pins['installed_manifest_sha256'] == sha(INSTALLED)
    assert pins['archive_sha256'] == files[ARCHIVE]
    patch = ps.read_patch(PROFILE / 'source.patch')
    assert set(patch) == set(pins['files']) and len(patch) == 3
    overlay, original, changed = {}, {}, {}
    for rel, hunks in patch.items():
        source = (BASE / 'package' / rel).read_bytes()
        result = ps.apply(source, hunks)
        assert ps.sha(source) == pins['files'][rel]['before'] == files[rel]
        assert ps.sha(result) == pins['files'][rel]['after']
        overlay[rel] = result
        original[Path(rel).name] = source.decode().replace('\r\n', '\n')
        changed[Path(rel).name] = result.decode().replace('\r\n', '\n')
    ps.source_checks(original, changed)

    for rel in sorted(files.keys() - {ARCHIVE}):
        target = OUT / 'package' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel in overlay:
            target.write_bytes(overlay[rel])
        else:
            shutil.copyfile(BASE / 'package' / rel, target)
    shutil.copytree(BASE / 'archive_source', OUT / 'archive_source')
    assert inventory(OUT / 'archive_source', '\\') == manifest['source_resources']
    write(HERE / 'baseline.json', {
        'game_root': installed['game_root'],
        'installed_manifest_sha256': sha(INSTALLED),
        'baseline_package_sha256': sha(pkg),
        'profile_patch_sha256': sha(PROFILE / 'source.patch'),
        'profile_provenance_sha256': sha(PROFILE / 'provenance.json'),
        'scripts': [{'path': rel, **pins['files'][rel]} for rel in sorted(overlay)],
        'old_archive_count': manifest['archive_payloads'],
    })
    print('Verified JB3 and applied the three pinned setup changes in the successor workspace.')


if __name__ == '__main__':
    prepare()
