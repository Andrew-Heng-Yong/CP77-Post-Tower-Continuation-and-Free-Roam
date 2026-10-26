from pathlib import Path
import hashlib
import json
import re

here = Path(__file__).resolve().parent
game_mods = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod')
files = sorted(game_mods.glob('*TowerContinued*.archive.xl'), key=lambda p: p.name.lower())
assert len(files) == 23
out = here / 'candidate_01'
out.mkdir(exist_ok=True)
dest = out / 'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
assert not dest.exists()
dest.parent.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def sections(text):
    sections = {}
    current = None
    for line in text.splitlines():
        if line == '...':
            continue
        if line and not line[0].isspace():
            assert line.endswith(':') and line[:-1] in ('quest', 'streaming', 'localization'), line
            current = line[:-1]
            assert current not in sections
            sections[current] = []
        else:
            assert current is not None, line
            sections[current].append(line)
    return sections

phase_lines = []
phase_paths = []
streaming = []
lipmaps = {}
rows = []
for path in files:
    text = path.read_text(encoding='utf-8-sig')
    parts = sections(text)
    assert 'quest' in parts
    q = [line for line in parts['quest'] if line.strip()]
    assert q[0].strip() == 'phases:'
    body = q[1:]
    starts = [i for i, line in enumerate(body) if re.match(r'^\s*- path: ', line)]
    assert starts and starts[0] == 0
    base_indent = len(body[0]) - len(body[0].lstrip())
    assert base_indent in (2, 4)
    paths = []
    for line in body:
        leading = len(line) - len(line.lstrip())
        assert leading >= base_indent
        phase_lines.append(' ' * (4 + leading - base_indent) + line.lstrip())
        if re.match(r'^\s*- path: ', line):
            paths.append(line.split('path: ', 1)[1])
    phase_paths.extend(paths)
    if 'streaming' in parts:
        s = [line for line in parts['streaming'] if line.strip()]
        assert s[0].strip() == 'blocks:'
        base_indent = len(s[1]) - len(s[1].lstrip())
        assert base_indent in (2, 4)
        for line in s[1:]:
            leading = len(line) - len(line.lstrip())
            assert leading >= base_indent and line.lstrip().startswith('- ')
            streaming.append(line.lstrip()[2:])
    if 'localization' in parts:
        l = [line.strip() for line in parts['localization'] if line.strip()]
        assert l[0] == 'lipmaps:'
        for line in l[1:]:
            key, value = line.split(': ', 1)
            assert key not in lipmaps
            lipmaps[key] = value
    rows.append({'source': path.name, 'sha256': sha(path), 'phase_count': len(paths), 'sections': list(parts)})

assert len(phase_paths) == 742 and len(set(phase_paths)) == 742
assert len(streaming) == 13 and len(set(streaming)) == 13
assert lipmaps == {'en-us': r'towercontinued\sidejob_repair_sr1\en-us.lipmap'}
output = 'quest:\n  phases:\n' + '\n'.join(phase_lines) + '\n'
output += 'streaming:\n  blocks:\n' + ''.join('    - ' + path + '\n' for path in streaming)
output += 'localization:\n  lipmaps:\n' + ''.join('    ' + language + ': ' + path + '\n' for language, path in lipmaps.items())
dest.write_text(output, encoding='utf-8')
assert re.findall(r'(?m)^\s*- path: (.+)$', output) == phase_paths
assert re.findall(r'(?m)^\s*- (towercontinued\\.+\.streamingblock)$', output) == streaming
proof = {'status': 'XL_23_TO_1_SEMANTIC_REGISTRATION_PRESERVATION_PASS', 'sources': rows, 'phase_count': len(phase_paths), 'streaming_blocks': len(streaming), 'lipmaps': lipmaps, 'output': str(dest), 'output_sha256': sha(dest), 'game_writes': 0}
(out / 'build_xl_01.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in proof.items() if k not in ('sources', 'output')}))
