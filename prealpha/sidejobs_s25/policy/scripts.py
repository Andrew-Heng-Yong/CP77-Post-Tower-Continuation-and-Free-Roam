"""Generate only bounded data-array replacements; method logic stays byte-identical."""
import json, re, sys
from pathlib import Path
from prepare import ROOT, HERE, read, sha, array


def replace_array(text, name, wanted):
    before, pattern = array(text, name)
    new, count = re.subn(pattern, lambda m: m[1] + json.dumps(wanted) + m[3], text)
    assert count == 1
    return new, {'method': name, 'before': before, 'after': wanted}


def transform(text, script):
    changes = []
    for row in script['rows']:
        i = row['index']
        if row['narrowed']:
            for prefix in ('StatesA', 'StatesB'):
                values, _ = array(text, prefix + str(i))
                for change in row['narrowed']: values[change['index']] = 1
                text, delta = replace_array(text, prefix + str(i), values); changes.append(delta)
        if row['exclusion_fact']:
            names, _ = array(text, 'FactNames' + str(i))
            assert row['exclusion_fact'] not in names
            text, delta = replace_array(text, 'FactNames' + str(i), names + [row['exclusion_fact']]); changes.append(delta)
            for prefix in (('FactValues',) if script['version'] == 'S22' else ('FactMin', 'FactMax')):
                values, _ = array(text, prefix + str(i))
                text, delta = replace_array(text, prefix + str(i), values + [0]); changes.append(delta)
    # Manual status only; no logging or automatic behavior added.
    old = 'Current Failed/Inactive policy'
    if old in text:
        assert text.count(old) == 1
        text = text.replace(old, 'New activation Inactive-only; existing issued progress preserved')
        changes.append({'status_text_before': old, 'status_text_after': 'New activation Inactive-only; existing issued progress preserved'})
    return text, changes


def main(build):
    plan = read(HERE / 'plan02.json'); outputs = []
    for spec in plan['scripts']:
        source = ROOT / spec['source']; text = source.read_text(encoding='utf-8-sig')
        new, changes = transform(text, spec)
        target = build / 'scripts' / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists()
        target.write_text(new, encoding='utf-8', newline='\n')
        outputs.append({'source': spec['source'], 'source_sha256': sha(source), 'path': target.relative_to(ROOT).as_posix(),
                        'relative': spec['relative'], 'sha256': sha(target), 'method_deltas': changes})
    (build / 'script_replacements.json').write_text(json.dumps(outputs, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main(Path(sys.argv[1]))
