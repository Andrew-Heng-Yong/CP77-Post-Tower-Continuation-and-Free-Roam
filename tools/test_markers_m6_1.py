"""Focused regression/source-contract checks; these cannot prove map rendering."""
import json, re, sys
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, read, sha
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

OUT = ROOT / 'research/gig_restoration/markers_m6_1'
SOURCE = 'redscript/PTFR_GigMarkersM6/GigMarkersM6.reds'
PREVIOUS = 'E1B5E4323DD4B72A95EF9B293B31C624EA87067FD26C15EA0B41541D03A09DD9'

def body(text, name):
    start = re.search(r'\bfunc ' + name + r'\(', text).end()
    start = text.index('{', start)
    level = 1
    end = start + 1
    while level:
        level += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start + 1:end - 1]

def main():
    assert not (OUT / 'install_receipt.json').exists(), 'Installed evidence pinned'
    source = (ROOT / SOURCE).read_text()
    previous = (OUT / 'predecessor/GigMarkersM6.reds').read_text()
    assert sha(OUT / 'predecessor/GigMarkersM6.reds') == PREVIOUS
    compiled = read(OUT / 'compile_result.json')
    assert compiled['status'] == 'PASS_M6_1_COMPILE_NOT_RENDERER_PROOF'
    for p, digest in compiled['sources'].items():
        assert sha(ROOT / p) == digest
    for p, digest in (compiled['dependencies'] | compiled['protected']).items():
        assert sha(p) == digest
    # No changes to eligibility, official locations, IDs or Tower detection.
    for name in ('Want', 'Location', 'Index', 'ID', 'Root', 'Own', 'Tower'):
        assert body(source, name) == body(previous, name), name
    poll = body(source, 'Poll')
    release = re.search(r'if !GigMarkersM6\.Want[^\n]+', poll)[0]
    assert release.endswith('root,state) {')
    assert not re.search(r'usable|IsVisible|NativeCandidate', release)
    assert '|| usable' in body(previous, 'Poll'), 'Regression must target the demonstrated old branch'
    assert 'this.NativeCandidate(quest)' not in poll, 'Native discovery is diagnostic only'
    assert not re.search(r'SetFact|ChangeEntryState|TrackEntry|DebugDiscover|DebugShow|SetMappinActive|SetMappinPosition', source)
    assert 'persistent let' not in source
    assert 'epoch!=this.epoch' in poll and 'jm.HasAnyDelayedStateChanges()' in poll
    assert 'GigMarkerDataM6' in body(source, 'Purge')
    assert 'IsDefined(d) && Equals(d.id,this.ID(i))' in body(source, 'Owned')
    assert 'let mine=this.Owned(i)' in body(source, 'Remove')
    assert 'Equals(ms.GetManuallyTrackedMappinID(),this.markers[i])' in body(source, 'Remove')
    assert 'root!=2 || !IsDefined(marker as QuestMappin)' in body(source, 'CanTransfer')
    assert 'IsDefined(quest) ? ms.GetMappinFromQuest(quest) : null' in poll
    # Execute the actual pure eligibility expression. Reproduce the failed H1
    # state and verify release on journal activation, terminal states, and faults.
    runtime = LuaRuntime(unpack_returned_tuples=True)
    expression = re.search(r'return (.*?);', body(source, 'Want'))[1].replace('&&', ' and ')
    want = runtime.execute('return function(tower,request,started,finished,fault,root,poi) return ' + expression + ' end')
    cases = [
        ('reported_H1', (True, 1, 1, 0, 0, 1, 2), True),
        ('quest_active', (True, 1, 1, 0, 0, 2, 2), False),
        ('quest_succeeded', (True, 1, 1, 1, 0, 3, 2), False),
        ('quest_failed', (True, 1, 1, 0, 0, 4, 2), False),
        ('not_Tower', (False, 1, 1, 0, 0, 1, 2), False),
        ('unrequested', (True, 0, 1, 0, 0, 1, 2), False),
        ('not_started', (True, 1, 0, 0, 0, 1, 2), False),
        ('finished', (True, 1, 1, 1, 0, 1, 2), False),
        ('faulted', (True, 1, 1, 0, 1, 1, 2), False),
        ('missing_journal', (True, 1, 1, 0, 0, -1, 2), False),
        ('inactive_POI', (True, 1, 1, 0, 0, 1, 1), False),
    ]
    for name, args, expected in cases:
        assert want(*args) == expected, name
    # Registration policy: zero handle retries are bounded; delayed acknowledgement
    # or a foreign/reused nonzero handle must never trigger a second registration.
    registration = re.search(r'if (Equals\(this.markers\[i\],empty\).*?) \{', poll)[1]
    expression = registration.replace('Equals(this.markers[i],empty)', '(handle==0)').replace('this.attempts[i]', 'attempts').replace('&&', ' and ')
    register = runtime.execute('return function(handle,attempts) return ' + expression + ' end')
    registration_cases = [(0, 0, True), (0, 2, True), (0, 3, False), (42, 1, False), (42, 0, False)]
    for handle, attempts, expected in registration_cases:
        assert register(handle, attempts) == expected
    trace = [json.loads(line) for line in (OUT / 'm6_failure_trace.jsonl').read_text().splitlines()]
    matches = [row for row in trace if 'Native marker present; fallback removed.' in row['markers']['sts_wbr_hil_01'] and 'root=1 fault=0' in row['status']['sts_wbr_hil_01']]
    assert matches and not any(row['errors'] for row in trace)
    failure = dict(status='M6_USER_REPORTED_MAP_FAILURE_CORROBORATED_BY_GETTER', rows=len(trace), false_handoff_rows=len(matches), first_utc=trace[0]['utc'], last_utc=trace[-1]['utc'], captured_prefix_sha256=sha(OUT / 'm6_failure_trace.jsonl'), user_reports='No Charter Hill icon and no active journal; second supplied screenshot is an internet reference, not gameplay evidence.', diagnosis='Native registered active/visible flags are insufficient evidence of map rendering; zero-position acceptance also possible but actual native position was not logged.', writes_to_loaded_world=0)
    (OUT / 'failure_result.json').write_text(json.dumps(failure, indent=2) + '\n')
    pinned = {}
    for name in ('tests.json', 'assessment.json', 'install_receipt.json', 'compile_result.json', 'manifest.json', 'deployment_tests.json'):
        path = ROOT / 'research/gig_restoration/fresh_b6' / name
        pinned[str(path.relative_to(ROOT))] = sha(path)
    result = dict(status='PASS_M6_1_SOURCE_REGRESSION_RENDERER_PENDING', source_contracts=True, eligibility_cases=len(cases), registration_cases=len(registration_cases), failure_trace_rows=len(trace), presentation_only=True, files=[dict(source=SOURCE, relative='r6/scripts/PTFR_GigMarkersM6/GigMarkersM6.reds', sha256=sha(ROOT / SOURCE), predecessor=PREVIOUS)], compile_sha256=sha(OUT / 'compile_result.json'), tools={name: sha(ROOT / name) for name in ('tools/compile_markers_m6_1.py', 'tools/test_markers_m6_1.py')}, pinned_predecessor_evidence=pinned)
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'eligibility_cases', 'registration_cases', 'failure_trace_rows')}))

if __name__ == '__main__':
    main()
