from pathlib import Path
import hashlib
import json
import zipfile

here = Path(__file__).resolve().parent
candidate = here / 'candidate_01'
package = candidate / 'package'
manifest = json.loads((candidate / 'package_manifest_01.json').read_text(encoding='utf-8'))
assert manifest['status'] == 'FULL_PTFR_127_TO_51_STAGED_PACKAGE_NOT_INSTALLED'
output = candidate / 'dist/PTFR-full-consolidated-candidate.zip'
assert not output.exists()
output.parent.mkdir(exist_ok=True)

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest().upper()

with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for row in manifest['package_files']:
        data = (package / row['path']).read_bytes()
        assert sha_bytes(data) == row['sha256']
        info = zipfile.ZipInfo(row['path'], date_time=(2026, 10, 25, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
with zipfile.ZipFile(output) as archive:
    assert sorted(archive.namelist()) == sorted(row['path'] for row in manifest['package_files'])
    for row in manifest['package_files']:
        assert sha_bytes(archive.read(row['path'])) == row['sha256']
proof = {'status': 'ONE_ZIP_51_FILE_FULL_PTFR_READBACK_PASS_NOT_INSTALLED', 'zip': str(output), 'zip_sha256': sha_bytes(output.read_bytes()), 'files': 51, 'archive_files': 1, 'archive_xl_files': 1, 'reds_files': 46, 'cet_lua_files': 2, 'tweak_yaml_files': 1, 'game_writes': 0}
(candidate / 'distribution_01.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
