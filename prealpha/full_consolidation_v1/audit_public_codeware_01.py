"""Compare the installed Codeware files with the verified public 1.21.1 ZIP."""

import hashlib
import json
import zipfile
from pathlib import Path

here = Path(__file__).resolve().parent
workspace = here.parent.parent
archive = workspace / 'diagnostics/core_updates_20261025_01/downloads/Codeware-1.21.1.zip'
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
output = workspace / 'diagnostics/public_codeware_install_20261025_01/preflight_01.json'


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


assert sha(archive.read_bytes()) == '7CEA413C39BBA6DEA15DE558E95BB0E04F63AF3D3CB35C6D854ED65382FD41A7'
rows = []
with zipfile.ZipFile(archive) as package:
    for member in package.infolist():
        if member.is_dir():
            continue
        relative = member.filename.replace('\\', '/')
        assert not relative.startswith('/') and '..' not in Path(relative).parts
        expected = sha(package.read(member))
        target = game / relative
        actual = sha(target.read_bytes()) if target.is_file() else None
        rows.append({'path': relative, 'public_sha256': expected, 'installed_sha256': actual, 'matches': actual == expected})

assert len(rows) == 9
assert len({row['path'].lower() for row in rows}) == 9
different = [row for row in rows if not row['matches']]
assert len(different) == 1 and different[0]['path'].endswith('/Codeware.Global.reds')
assert different[0]['installed_sha256'] == '9736FEBC39BF88AD920068737BA6BBD0BC78F39D3E785FB629558E39AAAF990B'
assert different[0]['public_sha256'] == '83CEBFDAF60443608ACD211B1AC6253AE6C67295BAB97275B4961506EB878A76'
output.parent.mkdir(parents=True, exist_ok=True)
report = {'status': 'PUBLIC_CODEWARE_ONE_SCRIPT_DIFF', 'version': '1.21.1', 'rows': rows, 'game_writes': 0, 'save_writes': 0}
output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'package_files': len(rows), 'different': different}))
