"""Integrate reviewed stable housing APIs without changing saved entry fields."""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('h1_entry', HERE / 'generate_01.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
swap = prior.replace_once


def transform(relative, original):
    if relative.endswith('/PreAlphaEntry.reds'):
        text = prior.entry_successor(original)
        text = swap(text, 'import PTFR.RestorationBaseline.*', 'import PTFR.RestorationBaseline.*\nimport PTFR.Housing.*')
        text = swap(text,
            '    if !restoration.H10ActionsArmed() { this.detail = "Waiting for H10 interaction owner admission: " + restoration.H10Status(); return; }',
            '    let housing = HousingState.Get(game);\n'
            '    if !IsDefined(housing) || !housing.HousingReadyForReveal() {\n'
            '      this.detail = "Waiting for one-time housing transition and native loss acknowledgements."; return;\n'
            '    }\n'
            '    // An unowned home must not enable services just to release street arrival.\n'
            '    if housing.Entitled("h10") && !restoration.H10ActionsArmed() {\n'
            '      this.detail = "Waiting for entitled H10 interaction owner: " + restoration.H10Status(); return;\n'
            '    }')
    else:
        text = swap(original, 'module PTFR.RestorationBaseline\n', 'module PTFR.RestorationBaseline\n\nimport PTFR.Housing.*\n')
        text = swap(text, '    // H10 interactions\n    if h10Actions &&',
            '    // H1: geometry remains public; home actions require the durable entitlement.\n'
            '    let housing = HousingState.Get(game);\n'
            '    if IsDefined(housing) && housing.HousingReadyForReveal() && housing.Entitled("h10") && h10Actions &&')
    assert prior.fields(original) == prior.fields(text), 'Existing saved fields must be retained exactly'
    return text


def main(revision):
    assert re.fullmatch(r'integration_\d{2}', revision)
    out = HERE / 'build' / revision
    out.mkdir(parents=True, exist_ok=False)
    files = []
    for relative, digest in prior.INPUTS.items():
        source = prior.GAME / relative
        assert prior.sha(source) == digest, 'Installed input changed'
        original = source.read_text(encoding='utf-8-sig')
        modified = transform(relative, original)
        path = out / 'package' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(modified, encoding='utf-8', newline='\n')
        files.append(dict(relative=relative, before_sha256=digest, sha256=prior.sha(path),
                          persistent_fields=prior.fields(modified)))
    pins = {str(p.relative_to(ROOT)).replace('\\', '/'): prior.sha(p) for p in [Path(__file__), HERE / 'generate_01.py']}
    report = dict(status='BUILT_H1_INTEGRATION_NOT_LIVE', files=files, source_pins=pins,
                  late_fixture_disabled=True, established_handoff_grants_quest_certificate=False,
                  saved_fields_retained=True, arrival_camera_modified=False,
                  house_loss_replayed=False, property_ready_required_before_reveal=True)
    (out / 'component.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'output': str(out)}, indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
