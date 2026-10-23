"""Regression contract for the entry and baseline housing integration."""
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('h1_integrate', HERE / 'generate_02.py')
code = importlib.util.module_from_spec(spec)
spec.loader.exec_module(code)


def main(revision):
    out = HERE / 'build' / revision
    manifest = json.loads((out / 'component.json').read_text())
    report = out / 'tests.json'
    assert not report.exists()
    for row in manifest['files']:
        source = code.prior.GAME / row['relative']
        assert code.prior.sha(source) == row['before_sha256']
        original = source.read_text(encoding='utf-8-sig')
        target = out / 'package' / row['relative']
        assert code.prior.sha(target) == row['sha256']
        actual = target.read_text(encoding='utf-8-sig')
        assert actual == code.transform(row['relative'], original)
        assert code.prior.fields(original) == code.prior.fields(actual)
    entry = (out / 'package/r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds').read_text()
    assert 'DevelopmentLateEnding() -> Bool { return false; }' in entry
    # Existing certificates, catalogues, profile transaction, arrival/camera
    # coordinator and gig dispatch semantics are unchanged by the transform.
    original = (code.prior.GAME / 'r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds').read_text(encoding='utf-8-sig')
    def method(text, name):
        start = re.search(r'\bfunc '+name+r'\([^)]*\)[^{]*\{', text).end()
        depth, end = 1, start
        while depth:
            if text[end] == '{': depth += 1
            elif text[end] == '}': depth -= 1
            end += 1
        return text[start:end-1]
    unchanged = ['Certified', 'CaptureBeforeEnding', 'Freeze', 'Dispatch', 'Classify', 'ShapeValid', 'Same', 'ReadGig', 'Restored']
    for name in unchanged:
        assert method(original, name) == method(entry, name), name
    handoff = method(entry, 'EstablishedHandoff')
    assert not re.search(r'SetFact|GiveItem|ChangeEntry|this\.\w+\s*=', handoff)
    expected = ['Started','Teleported','ControlReady','Prepared','Reveal','Finished']
    assert all('PTFRPA2_'+name in handoff for name in expected)
    assert 'PTFRPA3_CoverReleased' in handoff and 'PTFRPA4_CameraAligned' in handoff and 'PTFRPA2_Fault' in handoff
    # Model only the deliberately changed admission and reveal decisions.
    def activated(completed, faulted, observed, certified, acknowledgements, transition_fault):
        established = all(v == 1 for v in acknowledgements) and transition_fault == 0
        return not faulted and completed and (observed or certified or established)
    ack = [1]*8
    cases = []
    for index in range(8):
        missing = ack.copy(); missing[index] = 0
        assert not activated(True, False, False, False, missing, 0)
        cases.append('missing_handoff_ack_'+str(index))
    for state in [(False,False,False,False,ack,0),(True,True,False,False,ack,0),(True,False,False,False,ack,1)]:
        assert not activated(*state)
    assert activated(True,False,False,False,ack,0)
    assert activated(True,False,True,False,[0]*8,0)
    assert activated(True,False,False,True,[0]*8,0)
    cases += ['unfinished_tower_rejected','faulted_history_rejected','faulted_handoff_rejected',
              'completed_existing_handoff_continues_without_certificate','observed_ending_retained','certified_ending_retained']
    def reveal(geometry, housing, entitlement, actions, control, fault):
        return geometry and housing and (not entitlement or actions) and control and fault == 0
    assert reveal(True,True,False,False,True,0)
    assert not reveal(True,True,True,False,True,0)
    assert reveal(True,True,True,True,True,0)
    assert not reveal(True,False,False,True,True,0)
    assert not reveal(False,True,False,True,True,0)
    assert not reveal(True,True,False,True,True,1)
    cases += ['unowned_h10_does_not_deadlock_street','owned_h10_waits_actions','owned_h10_ready',
              'loss_ack_required','geometry_required','fault_blocks_reveal']
    data = dict(status='PASS_SOURCE_AND_STATE_MODEL_NOT_LIVE', component_sha256=code.prior.sha(out/'component.json'),
                tester_sha256=code.prior.sha(__file__), unchanged_methods=unchanged,
                persistence_exact=True, transition_cases=cases, case_count=len(cases))
    report.write_text(json.dumps(data, indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data,indent=2))


if __name__ == '__main__':
    main(sys.argv[1])
