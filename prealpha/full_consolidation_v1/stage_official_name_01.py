"""Stage only the public naming change, leaving unrelated working-tree edits alone."""

import subprocess


def git(*args, data=None):
    result = subprocess.run(
        ['git', '-c', 'safe.directory=C:/Users/Ayong/Documents/cp77 modding/tower ws', *args],
        input=data,
        capture_output=True,
        check=True,
    )
    return result.stdout


assert not git('diff', '--cached', '--name-only').strip(), 'Index is not empty'

name = 'Post Tower Continuation and Free Roam'
repo = 'CP77-Post-Tower-Continuation-and-Free-Roam'
paths = [
    'AGENTS.md',
    'PROJECT.md',
    'README.md',
    'ROADMAP.md',
    'docs/restoration_baseline_r1.md',
    'release/INSTALL.md',
    'release/NOTES.md',
    'release/INSTALL-v0.1.1-alpha.20261024.md',
    'release/NOTES-v0.1.1-alpha.20261024.md',
]


def replace_once(text, old, new):
    count = text.count(old)
    assert count == 1, (old, count)
    return text.replace(old, new)


for path in paths:
    original = git('show', 'HEAD:' + path).decode('utf-8')
    updated = original
    if path == 'AGENTS.md':
        updated = replace_once(
            updated,
            '# AGENTS.md — Post-Tower Free Roam / Tower Continuation Mod',
            '# AGENTS.md — ' + name,
        )
        updated = replace_once(
            updated,
            '- detect Post-Tower Free Roam state on load',
            '- detect ' + name + ' state on load',
        )
        updated = replace_once(
            updated,
            '# AGENTS.md — ' + name + '\n',
            '# AGENTS.md — ' + name + '\n\n'
            'Official public name: ' + name + '. Legacy `PTFR`, `TowerContinued`,\n'
            'and `TowerContinuation` identifiers remain for compatibility.\n',
        )
    elif path == 'PROJECT.md':
        updated = replace_once(updated, '# PROJECT.md — Post-Tower Free Roam Mod', '# PROJECT.md — ' + name)
        updated = replace_once(updated, '**Working title:** Post-Tower Free Roam / Tower Continuation Mod', '**Mod name:** ' + name)
        updated = replace_once(
            updated,
            'The project may be renamed later. The design target is a post-ending sandbox, not a new story campaign.',
            'The official name was confirmed on 25 October 2026. The design target is a post-ending sandbox, not a new story campaign. Legacy `PTFR` identifiers remain for save compatibility.',
        )
        updated = updated.replace('Post-Tower Free Roam state on load', name + ' state on load')
        updated = updated.replace('while Post-Tower Free Roam is active', 'while ' + name + ' is active')
    elif path == 'README.md':
        updated = replace_once(updated, '# Cyberpunk 2077: Tower Continuation', '# Cyberpunk 2077: ' + name)
        updated = replace_once(updated, 'Download Tower Continuation Alpha Test ZIP', 'Download ' + name + ' Alpha Test ZIP')
        updated = updated.replace('CP77-tower-continuation', repo)
        updated = replace_once(
            updated,
            '## Development status\n',
            '**' + name + '** is the mod\'s official name.\n'
            '`PTFR`, `TowerContinuation`, and `TowerContinued` remain in internal IDs and\n'
            'historical download paths for compatibility with existing saves and releases.\n\n'
            '## Development status\n',
        )
    elif path == 'ROADMAP.md':
        updated = replace_once(updated, '# Tower Continued — Development Roadmap', '# ' + name + ' — Development Roadmap')
    elif path == 'docs/restoration_baseline_r1.md':
        updated = replace_once(updated, '# Tower Continued — integrated restoration baseline R1', '# ' + name + ' — integrated restoration baseline R1')
    elif path == 'release/NOTES.md':
        updated = replace_once(updated, '# Tower Continuation pre-alpha - 23 October 2026', '# ' + name + ' pre-alpha - 23 October 2026')
        updated = updated.replace('CP77-tower-continuation', repo)
    else:
        updated = updated.replace('Tower Continuation', name)
    assert updated != original, path
    assert name in updated, path
    blob = git('hash-object', '-w', '--stdin', data=updated.encode('utf-8')).decode().strip()
    git('update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + path)

staged = git('diff', '--cached', '--name-only').decode().splitlines()
assert staged == paths or set(staged) == set(paths), staged
print('STAGED_OFFICIAL_NAME_ONLY', len(staged), 'files')
