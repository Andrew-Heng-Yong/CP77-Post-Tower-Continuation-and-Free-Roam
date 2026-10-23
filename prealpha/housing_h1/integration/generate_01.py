"""Make explicit successor copies of the installed entry/baseline scripts.

Saved class/field names remain unchanged. Originals are immutable inputs.
Housing runtime integration is completed against its reviewed API before build.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
INPUTS = {
    'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds': '386A6496EAF1ACB485FB2D4CF8F09BCE6AA2E85538D0598E548ABA83B9EBFAC2',
    'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds': '8E29C4573988049564808BDB7DFE815351793C8621300E8858AA9C827EACF3ED',
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def fields(text):
    return re.findall(r'\b(?:public|private|protected)\s+persistent\s+let\s+(\w+)\s*:\s*([^;]+);', text)


def entry_successor(text):
    text = replace_once(text,
        '  // This package is for the user-selected ManualSave10 Things Done Changed run.\n'
        '  // Disable this constant for production. It never creates a history certificate.\n'
        '  public static func DevelopmentLateEnding() -> Bool { return true; }',
        '  // Public beta never infers fresh quest history from a late-ending fixture.\n'
        '  // Keep the saved arm field and API for old saves, but disable new admission.\n'
        '  public static func DevelopmentLateEnding() -> Bool { return false; }')
    text = replace_once(text,
        '  private func Activated() -> Bool { return !this.faulted && this.Completed() && (this.endingObserved || this.certified || this.DevelopmentArmed()); }',
        '  // Continue an already completed, acknowledged handoff without replaying it\n'
        '  // or manufacturing a pre-Tower certificate for any unissued quest.\n'
        '  private func EstablishedHandoff() -> Bool {\n'
        '    return this.Fact(n"PTFRPA2_Started") == 1 && this.Fact(n"PTFRPA2_Teleported") == 1 &&\n'
        '      this.Fact(n"PTFRPA2_ControlReady") == 1 && this.Fact(n"PTFRPA2_Prepared") == 1 &&\n'
        '      this.Fact(n"PTFRPA2_Reveal") == 1 && this.Fact(n"PTFRPA2_Finished") == 1 &&\n'
        '      this.Fact(n"PTFRPA3_CoverReleased") == 1 && this.Fact(n"PTFRPA4_CameraAligned") == 1 &&\n'
        '      this.Fact(n"PTFRPA2_Fault") == 0;\n'
        '  }\n'
        '  private func Activated() -> Bool { return !this.faulted && this.Completed() && (this.endingObserved || this.certified || this.EstablishedHandoff()); }')
    return text


def generate(revision):
    assert re.fullmatch(r'integration_\d{2}', revision)
    out = HERE / 'build' / revision
    out.mkdir(parents=True, exist_ok=False)
    files = []
    for relative, digest in INPUTS.items():
        source = GAME / relative
        assert sha(source) == digest, 'Installed source drift: ' + relative
        original = source.read_text(encoding='utf-8-sig')
        modified = entry_successor(original) if relative.endswith('/PreAlphaEntry.reds') else original
        assert fields(original) == fields(modified), 'Saved fields changed'
        dest = out / 'package' / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(modified, encoding='utf-8', newline='\n')
        files.append(dict(relative=relative, before_sha256=digest, sha256=sha(dest), persistent_fields=fields(original)))
    report = dict(status='ENTRY_SUCCESSOR_HOUSING_INTEGRATION_PENDING', files=files,
                  source_pins={str(Path(__file__).relative_to(ROOT)).replace('\\', '/'): sha(__file__)},
                  late_fixture_disabled=True, saved_fields_retained=True,
                  established_handoff_grants_quest_certificate=False)
    (out / 'component.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], output=str(out)), indent=2))


if __name__ == '__main__':
    generate(sys.argv[1])
