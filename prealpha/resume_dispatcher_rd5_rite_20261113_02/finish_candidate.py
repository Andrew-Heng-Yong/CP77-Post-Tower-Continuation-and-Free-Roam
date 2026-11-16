"""Stage the verified build with the exact 51-file baseline inventory."""
import shutil
from pathlib import Path
from verify_entrance import HERE, baseline, read, sha, write
from prepare_script import ACTIVITY

ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
XL = ARCHIVE + '.xl'


def main():
    installed, game = baseline()
    candidate = HERE / 'candidate_01'
    package = candidate / 'package'
    old_readback = HERE.parent / 'resume_dispatcher_rd4_20261113_01/archive_01/readback.json'
    archive = HERE / 'archive_01'
    baseline_members = {r['depot']: r['sha256'] for r in read(old_readback)['members']}
    pack = read(archive / 'readback.json')
    members = {r['depot']: r['sha256'] for r in pack['members']}
    assert pack['status'] == 'MEMBERS_VERIFIED' and len(members) == 1745
    changed = {depot for depot, digest in members.items() if baseline_members.get(depot) != digest}
    assert changed == set(pack['changes']) and len(changed) == 4 and baseline_members.keys() <= members.keys()
    compiled = read(HERE/'compile_01/result.json')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    assert sha(package/ACTIVITY) == compiled['staged_hashes'][ACTIVITY]
    assert all(sha(game/relative) == expected for relative, expected in compiled['input_pins'].items())
    assert sha(archive / Path(ARCHIVE).name) == pack['archive_sha256']
    assert not (candidate/'manifest.json').exists()
    for row in installed['core_files']:
        relative = row['path']
        if relative == ACTIVITY:
            continue
        p = package / relative
        assert not p.exists()
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive / Path(ARCHIVE).name if relative == ARCHIVE else game / relative, p)
    files = [{'path': row['path'], 'sha256': sha(package / row['path']),
              'bytes': (package / row['path']).stat().st_size} for row in installed['core_files']]
    assert {row['path'] for row, old in zip(files, installed['core_files'], strict=True)
            if row['sha256'] != old['sha256']} == {ARCHIVE, ACTIVITY}
    xl = (package/XL).read_text(encoding='utf-8-sig').lower()
    assert all(f'path: {depot}' not in xl for depot in changed if depot not in baseline_members)
    assert xl.count('path: towercontinued\\native_gigs_u9\\sts_wat_nid_05_entry.questphase') == 1
    write(candidate/'manifest.json', {'status': 'STAGED_OFFLINE', 'core_files': files,
          'baseline_manifest_sha256': '3DDA172011D2049A0EDBC4E006E6F40AE79F8751B23FAF0BEBCDC1706A62F0BC',
          'archive_payloads': len(members), 'archive_sha256': pack['archive_sha256'],
          'changed_core_paths': [ARCHIVE, ACTIVITY], 'changed_registered_paths': 0,
          'archive_readback_sha256': sha(archive/'readback.json'),
          'compile_sha256': sha(HERE/'compile_01/result.json'), 'game_writes': 0, 'save_writes': 0})
    print('Staged the 51-file candidate with exactly two changed Core files.')


if __name__ == '__main__':
    main()
