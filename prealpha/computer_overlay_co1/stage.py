"""Stage a reversible computer-page compatibility candidate; no game writes."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess

GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
ROOT = Path(__file__).resolve().parent
SOURCE = GAME / 'r6/scripts/virtual-atelier-full/SetupNewTab.reds'
CANDIDATE = ROOT / 'candidate_01/SetupNewTab.reds'
OUT = ROOT / 'candidate_01/compile_01'
assert not CANDIDATE.exists() and not OUT.exists(), 'Preserve existing candidate'
original = SOURCE.read_bytes()
old = (b'  let root: ref<inkCompoundWidget> = this.GetWidget(n"page/linkPanel/panel") as inkCompoundWidget;\r\n'
       b'  if (!IsDefined(root)) {\r\n'
       b'    root = this.GetWidget(n"Page/linkPanel/panel") as inkCompoundWidget;\r\n'
       b'  };\r\n'
       b'  root.RemoveAllChildren();\r\n')
new = (b'  // The default internet page can leave news widgets outside linkPanel/panel.\r\n'
       b'  // Replace the page body so Atelier does not share it with the news site.\r\n'
       b'  let root: ref<inkCompoundWidget> = this.GetRootCompoundWidget();\r\n'
       b'  root.RemoveAllChildren();\r\n')
assert original.count(old) == 1, 'Source function changed; review before staging'
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
proof = {
    'status': 'PASS' if run.returncode == 0 and 'Compilation complete' in log else 'FAIL',
    'source_sha256': sha256(original).hexdigest().upper(),
    'candidate_sha256': sha256(CANDIDATE.read_bytes()).hexdigest().upper(),
    'source_count': len(pins), 'source_hashes_unchanged': all(sha256(Path(p).read_bytes()).hexdigest() == h for p, h in pins.items()),
    'game_writes': 0, 'exit_code': run.returncode, 'log_tail': log[-1500:]
}
(OUT / 'result.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof, indent=2))
