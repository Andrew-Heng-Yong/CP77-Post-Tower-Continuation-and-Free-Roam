import hashlib
import json
import zipfile
from pathlib import Path

here = Path(__file__).resolve().parent
prod = here / 'production_01'
manifest = json.loads((prod / 'install_manifest_01.json').read_text(encoding='utf-8'))
assert len(manifest['files']) == 3
assert all(row['before'] is not None for row in manifest['files'])

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

out_dir = prod / 'dist'
out_dir.mkdir(exist_ok=True)
archive = out_dir / 'PTFR-SR1-existing-install-three-file-update.zip'
assert not archive.exists(), 'Distribution ZIP already exists; use a successor'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
    for row in manifest['files']:
        path = prod / 'package' / row['target']
        assert sha(path) == row['after']
        info = zipfile.ZipInfo(row['target'], date_time=(2026, 10, 26, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        output.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
with zipfile.ZipFile(archive) as check:
    assert sorted(check.namelist()) == sorted(row['target'] for row in manifest['files'])
    for row in manifest['files']:
        assert hashlib.sha256(check.read(row['target'])).hexdigest().upper() == row['after']
result = {'status': 'ONE_ZIP_THREE_REPLACEMENTS_READBACK_PASS', 'zip': str(archive), 'zip_sha256': sha(archive), 'files': 3, 'standalone_full_mod': False, 'game_writes': 0}
(prod / 'distribution_01.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
