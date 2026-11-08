"""Decompile current base script cache into fresh workspace evidence only."""
from pathlib import Path
import hashlib, json, re, subprocess

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[3]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def class_source(text, name):
    pattern = r'(?m)^[ \t]*(?:(?:public|private|protected|native|abstract|importonly|final)[ \t]+)*class[ \t]+' + re.escape(name) + r'\b[^{}]*\{'
    matches = list(re.finditer(pattern, text))
    assert len(matches) == 1, (name, len(matches))
    start = matches[0].start()
    opening = text.index('{', start)
    level = 0
    for token in re.finditer(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[{}]', text[opening:]):
        t = token.group()
        if t == '{': level += 1
        elif t == '}':
            level -= 1
            if level == 0:
                return text[start:opening+token.end()] + '\n'
    raise AssertionError('Unclosed class: ' + name)


def main():
    out = HERE/'current_01'
    assert not out.exists(), 'Fresh output required'
    source = GAME/'r6/cache/final.redscripts'
    tool = WORK/'research/framework_pr63_01/redscript-cli.exe'
    exe = GAME/'bin/x64/Cyberpunk2077.exe'
    for p in [source, tool, exe, HERE]:
        assert not p.is_symlink() and not p.is_junction(), str(p)
        for parent in p.parents:
            assert not parent.is_symlink() and not parent.is_junction(), str(parent)
    source_hash = sha(source)
    tool_hash = sha(tool)
    exe_hash = sha(exe)
    assert exe_hash == 'D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'
    out.mkdir()
    output = out/'base.script'
    args = [str(tool),'decompile','-i',str(source),'-o',str(output)]
    result = subprocess.run(args, cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    (out/'decompile.log').write_bytes(result.stdout)
    assert sha(source) == source_hash and sha(tool) == tool_hash, 'Input drift'
    record = {'status': 'DECOMPILE_FAILED' if result.returncode else 'DECOMPILED_CURRENT_BASE_SCRIPTS',
              'command': args, 'exit_code': result.returncode, 'input': str(source), 'input_sha256': source_hash,
              'tool': str(tool), 'tool_sha256': tool_hash, 'exe_sha256': exe_hash,
              'input_unchanged': True, 'game_calls': 0, 'game_writes': 0, 'save_writes': 0}
    if result.returncode == 0:
        assert output.is_file() and output.stat().st_size > 0
        text = output.read_text(encoding='utf-8-sig')
        files = []
        for name in ['VehicleComponentPS','VehicleComponent','VehicleQuestVisualDestructionEvent']:
            target = out/(name+'.script')
            target.write_text(class_source(text, name), encoding='utf-8')
            files.append({'class': name, 'path': str(target), 'sha256': sha(target)})
        record.update({'decompiled_sha256': sha(output), 'classes': files,
                       'limits': 'Current installed base cache only, not modded cache or a live event trace. Native imports remain declarations, not implementation proof.'})
    (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':record['status'],'exit_code':result.returncode,'output':str(out)}))
    assert result.returncode == 0, 'Inspect preserved tool log before any successor'


if __name__ == '__main__':
    main()
