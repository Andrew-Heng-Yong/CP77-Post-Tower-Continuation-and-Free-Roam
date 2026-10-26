"""Offline compile of the consolidated mod with untouched public Codeware 1.21.1."""

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parent.parent
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
baseline = here / 'reds_module_probe_01'
out = here / 'public_codeware_probe_01'
archive = workspace / 'diagnostics/core_updates_20261025_01/downloads/Codeware-1.21.1.zip'
expected_zip = '7CEA413C39BBA6DEA15DE558E95BB0E04F63AF3D3CB35C6D854ED65382FD41A7'


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


assert not out.exists(), 'Use a successor probe rather than overwrite evidence'
assert sha(archive.read_bytes()) == expected_zip
with zipfile.ZipFile(archive) as package:
    member = next(name for name in package.namelist() if name.replace('\\', '/').endswith('/Codeware.Global.reds'))
    public = package.read(member)

patched_path = baseline / 'scripts/Codeware/Codeware.Global.reds'
patched = patched_path.read_bytes()
patched_text = patched.decode('utf-8-sig').replace('\r\n', '\n')
public_text = public.decode('utf-8-sig').replace('\r\n', '\n')
assert patched_text.replace('    let result: Variant;\n        return result;\n', '') == public_text

sources = out / 'scripts'
cache = out / 'cache'
shutil.copytree(baseline / 'scripts', sources)
cache.mkdir(parents=True)
for name in ('final.redscripts', 'final.redscripts.ts'):
    shutil.copyfile(baseline / 'cache' / name, cache / name)
(sources / 'Codeware/Codeware.Global.reds').write_bytes(public)
paths = out / 'compile_paths.txt'
paths.write_text('', encoding='utf-8')
command = [
    str(game / 'engine/tools/scc.exe'), '-compile', str(sources),
    '-compilePathsFile', str(paths), '-customCacheDir', str(cache),
    '-outputCacheFile', str(cache / 'compiled.redscripts'),
    str(cache / 'final.redscripts'),
]
result = subprocess.run(command, capture_output=True, text=True, timeout=240)
log = result.stdout + result.stderr
(out / 'compile.log').write_text(log, encoding='utf-8')
proof = {
    'status': 'STOCK_CODEWARE_COMPILE_PASS' if result.returncode == 0 and 'Compilation complete' in log else 'STOCK_CODEWARE_COMPILE_FAILED',
    'codeware_version': '1.21.1',
    'public_zip_sha256': expected_zip,
    'public_global_script_sha256': sha(public),
    'local_patch_only_two_lines': True,
    'source_count': len(list(sources.rglob('*.reds'))),
    'scc_exit_code': result.returncode,
    'scc_tail': log[-3000:],
    'game_writes': 0,
    'save_writes': 0,
}
(out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in proof.items() if key != 'scc_tail'}))
