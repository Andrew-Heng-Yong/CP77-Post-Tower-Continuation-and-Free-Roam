"""Pin QR13:02 for a future authorized transaction. No game/save writes or builds."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, os, stat, zipfile

H = Path(__file__).resolve().parent
W = H.parents[1]
Q13 = H.parent / 'quest_restoration_qr13'

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()

def write(p, value):
    assert not p.exists(), f'Fresh output required: {p}'
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def meta(root):
    rows = {}
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs):
            p = Path(folder) / name
            if p.lstat().st_file_attributes & 0x400:
                rows[p.relative_to(root).as_posix()] = {'kind': 'REPARSE_NOT_FOLLOWED'}
                dirs.remove(name)
        for name in files:
            p = Path(folder) / name
            s = p.lstat()
            rows[p.relative_to(root).as_posix()] = {'bytes': s.st_size, 'mtime_ns': s.st_mtime_ns,
                'kind': 'REPARSE_NOT_FOLLOWED' if stat.S_ISLNK(s.st_mode) or s.st_file_attributes & 0x400 else 'file'}
    return rows

def main():
    assert not (H / 'baseline.json').exists()
    c = read(Q13 / 'completion.json')
    assert sha(Q13 / 'completion.json') == 'F4799076732D677AC9D611C1815C4BAF62864A9AA8504A2D0FD1D2F737AA9464'
    assert sha(c['canonical_epoch']) == c['canonical_epoch_sha256']
    for r in c['artifacts'].values():
        assert sha(r['path']) == r['sha256'], r['path']
    epoch = read(c['canonical_epoch'])
    old = read(epoch['relative_to'])
    current_path = H.parent / 'quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json'
    current = read(current_path)
    game, save = Path(current['game_root']), Path(current['save_root'])
    old_rows = {r['path']: r for r in old['package_files']}
    rows = []
    for r in epoch['package_files']:
        p = r['path']; b = old_rows[p]
        assert sha(game / p) == b['sha256'], p
        assert sha(Path(epoch['candidate']) / 'package' / p) == r['sha256'], p
        rows.append({'path': p, 'before': b['sha256'], 'before_bytes': (game / p).stat().st_size,
                     'after': r['sha256'], 'after_bytes': r['bytes']})
    changed = [r['path'] for r in rows if r['before'] != r['after']]
    assert sorted(changed) == sorted(['archive/pc/mod/zzzz_PTFR_Combined.archive',
        'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds', 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'])
    installed = {}
    for r in current['files'] + current['required_files']:
        p = game / r['path']; expected = r.get('after', r.get('sha256'))
        assert sha(p) == expected, p
        installed[str(p)] = expected
    required = [{'path': Path(p).relative_to(game).as_posix(), 'sha256': s, 'bytes': Path(p).stat().st_size, 'active_only': False}
        for p, s in installed.items() if Path(p).relative_to(game).as_posix() not in old_rows]
    assert len(rows) == 51 and len(required) == 9
    compile_result = read(epoch['compile_result'])
    for p, s in compile_result['input_pins'].items():
        assert sha(p) == s, f'Current compile prerequisite drift: {p}'
    with zipfile.ZipFile(epoch['zip']) as z:
        assert z.testzip() is None
        assert sorted(z.namelist()) == sorted(r['path'] for r in rows)
        for r in rows:
            assert hashlib.sha256(z.read(r['path'])).hexdigest().upper() == r['after']
    for r in current['protected_saves'] + current['working_save_files']:
        assert sha(save / r['path']) == r['sha256'], r['path']
    sm = meta(save)
    assert all(r['kind'] == 'file' for r in sm.values()), 'Save links require review'
    files = [save / p for p in sm]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        savepins = dict(zip(map(str, files), pool.map(sha, files)))
    proofs = [{'path': str(Q13 / 'completion.json'), 'sha256': sha(Q13 / 'completion.json')},
        {'path': c['canonical_epoch'], 'sha256': c['canonical_epoch_sha256']},
        {'path': str(current_path), 'sha256': sha(current_path)}]
    proofs += [{'path': r['path'], 'sha256': r['sha256']} for r in c['artifacts'].values()]
    manifest = {'schema': 'PTFR_QR14_CORE_V1', 'component': 'Core', 'source_epoch': 'QR13:02',
        'predecessor_epoch': 'QR8:02', 'game_root': str(game), 'save_root': str(save),
        'package_root': str(Path(epoch['candidate']) / 'package'), 'zip': epoch['zip'], 'zip_sha256': epoch['zip_sha256'],
        'files': rows, 'changing_paths': changed, 'required_files': required, 'proofs': proofs,
        'compile_inputs': compile_result['input_pins'], 'process_names': current['process_names'],
        'protected_saves': current['protected_saves'], 'working_save_files': current['working_save_files'],
        'scope': 'Exactly three existing Core leaves; validate all51. No diagnostic, cache, dependency, save or other mod edits.',
        'rollback_policy': 'Restore three exact QR8 predecessor files only. Never restore saves. New QR13 save state is not undone by file rollback.'}
    write(H / 'core_manifest_01.json', manifest)
    write(H / 'baseline.json', {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'installed_pins': installed, 'save_sha256': savepins, 'save_metadata': sm, 'game_metadata': meta(game),
        'QR13_metadata': meta(Q13), 'core_paths': len(rows), 'changes': changed,
        'compile_inputs': compile_result['input_pins'], 'scope': 'Preparation only; actual installation NOT authorized.'})
    print({'status': 'PINNED_NOT_INSTALLED', 'managed': len(rows), 'changes': len(changed),
           'protected_installed': len(installed), 'save_files': len(savepins), 'compile_inputs': len(compile_result['input_pins']),
           'manifest_sha256': sha(H / 'core_manifest_01.json')})

if __name__ == '__main__':
    main()
