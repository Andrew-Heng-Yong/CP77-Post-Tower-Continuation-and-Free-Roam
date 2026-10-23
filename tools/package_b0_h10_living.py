"""Package only validated workspace artifacts; no installation or save access."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/B0_H10_Living'
VAL = ROOT / 'research/b0_h10_living/validation'
NAME = 'TowerContinued_B0_H10_Living.archive'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    tests = json.loads((VAL / 'test_results.json').read_text())
    assert tests['status'] == 'PASS' and tests['runtime_tested'] is False
    for path, digest in tests['tested_sha256'].items():
        assert sha(ROOT / path) == digest, f'Tests are stale: {path}'
    build = json.loads((VAL / 'build_manifest.json').read_text())
    assert sha(OUT / NAME).upper() == build['sha256']
    xl = ROOT / 'archive/b0_h10_living' / (NAME + '.xl')
    assert sha(OUT / (NAME + '.xl')) == sha(xl)
    entries = {
        'archive/pc/mod/' + NAME: OUT / NAME,
        'archive/pc/mod/' + NAME + '.xl': xl,
        'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_B0_H10_Living/init.lua':
            ROOT / 'diagnostics/PTFR_B0_H10_Living/init.lua',
        'README_H10_LIVING_PROBE.md': ROOT / 'docs/b0_h10_living_probe.md',
    }
    package = OUT / 'TowerContinued_B0_H10_Living_Probe.zip'
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as z:
        for dest, source in entries.items():
            z.write(source, dest)
    with zipfile.ZipFile(package) as z:
        assert sorted(z.namelist()) == sorted(entries)
        assert z.testzip() is None
        for dest, source in entries.items():
            assert hashlib.sha256(z.read(dest)).hexdigest() == sha(source)
    result = dict(status='PASS_PACKAGE', package=str(package), sha256=sha(package),
                  entries={dest: sha(source) for dest, source in entries.items()},
                  archive_resources=build['resources'], vanilla_replacements=[], runtime_tested=False)
    (OUT / 'package_manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
