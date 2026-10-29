"""Package the selected uninstalled browser fix for a later combined deployment."""
from pathlib import Path
from hashlib import sha256
import json
import zipfile

root = Path(__file__).resolve().parent
candidate = root / 'candidate_02/SetupNewTab.reds'
original = root / 'candidate_02/original/SetupNewTab.reds'
compile_result = json.loads((root / 'candidate_02/compile_01/result.json').read_text())
fixture_result = json.loads((root / 'candidate_02/fixture_result_01.json').read_text(encoding='utf-8-sig'))
assert compile_result['status'] == 'PASS' and fixture_result['Status'] == 'PASS'
assert fixture_result['HashMismatchRejected'] and len(fixture_result['Actions']) == 6
assert sha256(candidate.read_bytes()).hexdigest().upper() == compile_result['candidate_sha256']
assert sha256(original.read_bytes()).hexdigest().upper() == compile_result['source_sha256']
manifest = {
    'status': 'STAGED_NOT_INSTALLED',
    'component': 'Computer News / Virtual Atelier page compatibility',
    'target': 'r6/scripts/virtual-atelier-full/SetupNewTab.reds',
    'required_current_sha256': compile_result['source_sha256'],
    'candidate_sha256': compile_result['candidate_sha256'],
    'compile_source_count': compile_result['source_count'],
    'compile_pass': True,
    'fixture_actions': 6,
    'fixture_rollback_pass': True,
    'game_writes': 0,
    'coordination': 'Deploy in the same game-closed window as the WA3 NPC successor after separate validation; this component has its own rollback.'
}
manifest_path = root / 'candidate_02/manifest.json'
if manifest_path.exists():
    assert json.loads(manifest_path.read_text()) == manifest
else:
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
package = root / 'candidate_02/computer_overlay_co1_candidate_02_ready.zip'
assert not package.exists()
members = [
    (candidate, 'candidate_02/SetupNewTab.reds'),
    (original, 'candidate_02/original/SetupNewTab.reds'),
    (root / 'candidate_02/compile_01/result.json', 'candidate_02/compile_01/result.json'),
    (manifest_path, 'candidate_02/manifest.json'),
    (root / 'deploy_02.ps1', 'deploy_02.ps1'),
]
with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for source, name in members:
        archive.write(source, name)
with zipfile.ZipFile(package) as archive:
    for source, name in members:
        assert archive.read(name) == source.read_bytes()
print(json.dumps({'status': 'PASS', 'package': str(package),
                  'sha256': sha256(package.read_bytes()).hexdigest().upper(),
                  'members': len(members), 'installed': False}, indent=2))
