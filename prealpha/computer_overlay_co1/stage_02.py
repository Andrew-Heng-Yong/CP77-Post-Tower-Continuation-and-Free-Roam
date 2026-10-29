"""Build the selected browser compatibility candidate without game writes."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess

GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
ROOT = Path(__file__).resolve().parent
SOURCE = GAME / 'r6/scripts/virtual-atelier-full/SetupNewTab.reds'
ZIP = Path(r'C:\Users\Ayong\Downloads\Virtual Atelier 2987 1.6.4 2026-10-25T17-42Z HncQn22j7.zip')
CANDIDATE = ROOT / 'candidate_02/SetupNewTab.reds'
OUT = ROOT / 'candidate_02/compile_01'
assert not CANDIDATE.exists() and not OUT.exists(), 'Preserve previous evidence'
original = SOURCE.read_bytes()
old = (b'  let root: ref<inkCompoundWidget> = this.GetWidget(n"page/linkPanel/panel") as inkCompoundWidget;\r\n'
       b'  if (!IsDefined(root)) {\r\n'
       b'    root = this.GetWidget(n"Page/linkPanel/panel") as inkCompoundWidget;\r\n'
       b'  };\r\n'
       b'  root.RemoveAllChildren();\r\n')
new = (b'  // Replace the complete native web page body; news widgets live outside linkPanel/panel.\r\n'
       b'  let root: ref<inkCompoundWidget> = this.GetWidget(n"page") as inkCompoundWidget;\r\n'
       b'  if !IsDefined(root) {\r\n'
       b'    root = this.GetWidget(n"Page") as inkCompoundWidget;\r\n'
       b'  };\r\n'
       b'  if !IsDefined(root) {\r\n'
       b'    root = this.GetRootCompoundWidget();\r\n'
       b'  };\r\n'
       b'  root.RemoveAllChildren();\r\n')
assert original.count(old) == 1
CANDIDATE.parent.mkdir(parents=True)
CANDIDATE.write_bytes(original.replace(old, new))
scripts, cache = OUT / 'scripts', OUT / 'cache'
cache.mkdir(parents=True)
pins = {}
for name, base in (
    ('game', GAME / 'r6/scripts'),
    ('Codeware', GAME / 'red4ext/plugins/Codeware/Scripts'),
    ('ArchiveXL', GAME / 'red4ext/plugins/ArchiveXL/Scripts'),
    ('TweakXL', GAME / 'red4ext/plugins/TweakXL/Scripts'),
    ('mod_settings', GAME / 'red4ext/plugins/mod_settings'),
):
    for path in base.rglob('*.reds'):
        pins[str(path)] = sha256(path.read_bytes()).hexdigest()
        dest = scripts / name / path.relative_to(base)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
shutil.copyfile(CANDIDATE, scripts / 'game/virtual-atelier-full/SetupNewTab.reds')
for name in ('final.redscripts', 'final.redscripts.ts'):
    shutil.copyfile(GAME / 'r6/cache' / name, cache / name)
paths = OUT / 'compile_paths.txt'
paths.write_text('', encoding='utf-8')
cmd = [GAME / 'engine/tools/scc.exe', '-compile', scripts, '-compilePathsFile', paths,
       '-customCacheDir', cache, '-outputCacheFile', cache / 'compiled.redscripts', cache / 'final.redscripts']
run = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, timeout=300)
log = run.stdout + run.stderr
(OUT / 'scc.log').write_text(log, encoding='utf-8')
unchanged = all(sha256(Path(p).read_bytes()).hexdigest() == h for p, h in pins.items())
import zipfile
with zipfile.ZipFile(ZIP) as z:
    archive_original = z.read('r6/scripts/virtual-atelier-full/SetupNewTab.reds')
proof = {
    'status': 'PASS' if run.returncode == 0 and 'Compilation complete' in log and unchanged and archive_original == original else 'FAIL',
    'source_sha256': sha256(original).hexdigest().upper(),
    'candidate_sha256': sha256(CANDIDATE.read_bytes()).hexdigest().upper(),
    'archive_source_identical_to_installed': archive_original == original,
    'source_count': len(pins), 'source_hashes_unchanged': unchanged,
    'game_writes': 0, 'exit_code': run.returncode, 'log_tail': log[-500:]
}
(OUT / 'result.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof, indent=2))
