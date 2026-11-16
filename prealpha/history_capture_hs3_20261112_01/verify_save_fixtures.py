"""Bounded real-save/source checks, without engine execution or save mutation."""
import re
from pathlib import Path
from common import HERE, RED, LUA, baseline, read, sha, write
from test_protocol import expression


def unwrap(value):
    while isinstance(value, dict) and '$value' in value:
        value = value['$value']
    return value


def main():
    out = HERE / 'verification_saves_01'
    assert not out.exists()
    evidence = HERE / 'fixtures_saves_01'
    manifest = read(evidence / 'manifest.json')
    assert manifest['status'] == 'PASS_READ_ONLY_SAVE_FIXTURE_EXTRACTION'
    assert not manifest['fact_name_hash_collisions'] and not manifest['journal_path_hash_collisions']
    m, game = baseline()
    script = HERE / 'candidate_04/package' / RED
    source = script.read_text(encoding='utf-8')
    native = source.split('public class CaptureArchiveHS3 extends ScriptableSystem {', 1)[1]
    predicate = expression(native, 'private func GateOpen(ticket: Int32,route: Int32) -> Bool {')
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append(name)

    def accepts(facts, ticket=1, route=1):
        return bool(eval(predicate, {'__builtins__': {}}, {'facts': facts, 'ticket': ticket, 'route': route}))

    saves, snapshots, projections = {}, {}, {}
    for row in manifest['saves']:
        slot = row['slot']
        saved = read(evidence / (slot + '.json'))
        check(slot + ': current body and metadata unchanged',
              sha(saved['source']) == saved['sha256'] == row['sha256'] and
              sha(Path(saved['source']).parent / 'metadata.9.json') == saved['metadata_sha256'])
        scalar = read(evidence / (slot + '_PTFR.HistorySnapshotHS1.SnapshotStateHS1.json'))
        snapshots[slot] = {k: unwrap(v) for k, v in scalar.items() if not k.startswith('$')}
        # Preserve nulls in evidence. This predicate fixture explicitly uses the
        # native named-fact API's zero-for-absent behavior, not graph-store guesses.
        facts = {k: (0 if v is None else (v - 2**32 if v >= 2**31 else v)) for k, v in saved['facts'].items()}
        projections[slot] = facts
        check(slot + ': no new capture admitted without a native gate', not accepts(facts))
        check(slot + ': no preexisting HS3 certificate claimed',
              'PTFR.HistorySnapshotHS1.CaptureArchiveHS3' not in saved['snapshot_systems'])
        saves[slot] = saved
    manual = saves['ManualSave-26']
    check('ManualSave-26 binds the earlier intact pre-cutoff fixture',
          manual['sha256'] == '6BEFAEE9EA1FA77A515C5A1EC9C867EA5B5DACB166D637D24B1423260E9C2AA4')
    # These overlays are hypothetical source-bound native gate transitions in
    # an offline fixture. They are never sent to the game or written to a save.
    opened = {'PTFRHS3_GateOpen': 1, 'PTFRHS3_GateTicket': 1, 'PTFRHS3_GateRoute': 1,
              'PTFRHS3_GateResult': 0, 'q307_point_of_no_return': 1}
    check('ManualSave-26 facts are compatible with reaching the direct Tower gate',
          accepts({**projections['ManualSave-26'], **opened}))
    for slot in ('AutoSave-2', 'AutoSave-16', 'ManualSave-27'):
        check(slot + ': teardown history rejected even with a hypothetical open gate',
              not accepts({**projections[slot], **opened}))
    skippy = 'quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy'
    journal = [r for r in manual['journal_matches'] if skippy in r['paths']]
    check('ManualSave-26 tracks Deliver Skippy with its matching saved journal record',
          manual['tracked'] == skippy and len(journal) == 1 and journal[0]['uint32_at_4'] == 2)
    data = read(HERE / 'evidence_01/catalogue.json')
    check('Actual Skippy total 97 and delivery path are included in the new catalogue',
          manual['facts']['mq007_skippy_enemies_total'] == 97 and
          'mq007_skippy_enemies_total' in data['facts'] and any(r['path'] == skippy for r in data['journals']))
    frozen = snapshots['AutoSave-16']
    check('AutoSave-16 retains an original frozen schema-1 certificate header',
          frozen['frozen'] == 1 and frozen['ready'] == 1 and frozen['origin'] == 'pre_ending')
    restored = source.split('public func Restored() -> Void {', 1)[1].split('private func Register()', 1)[0]
    check('Selected restore source cannot clear that header from early boundary reads',
          'this.Boundary()' not in restored and not re.search(r'this\.(frozen|ready|origin|fileToken|rows)\s*=', restored))
    damaged = snapshots['AutoSave-2']
    check('AutoSave-2 missing flags are not treated as a frozen certificate',
          all(k not in damaged for k in ('ready', 'frozen', 'origin', 'fileToken')) and
          'public func CanCompareRetainedHistory() -> Bool { return false; }' in source)
    check('ManualSave-27 retains fallback provenance rather than pre-cutoff provenance',
          snapshots['ManualSave-27']['origin'] == 'post_ending_fallback')
    token = frozen['fileToken']
    assert re.fullmatch(r'[A-Za-z0-9_]+', token)
    export = (game / LUA).parent / ('snapshot_hs1_' + token + '.json')
    document = read(export)
    check('AutoSave-16 own saved token selects its matching retained export header',
          document['schema'] == frozen['schema'] and document['catalogue'] == frozen['catalogue'] and
          document['revision'] == frozen['revision'] and document['origin'] == frozen['origin'] and len(document['rows']) == 158)
    out.mkdir()
    result = {'status': 'PASS_BOUNDED_REAL_SAVE_AND_SOURCE_FIXTURES', 'count': len(checks), 'checks': checks,
              'candidate_sha256': sha(script), 'fixture_manifest_sha256': sha(evidence / 'manifest.json'),
              'tool_sha256': sha(__file__), 'snapshots': snapshots,
              'export': {'path': str(export), 'sha256': sha(export)},
              'game_writes': 0, 'save_writes': 0, 'gameplay': 'NOT_RUN',
              'limits': ['Gate overlays are offline hypothetical transitions, not observed engine execution.',
                         'The dynamic save parser exposes scalar headers but omits snapshot arrays; array integrity and new HS3 persistence are not certified here.',
                         'Raw journal records are retained; no optional/counter/timer/owner decoder is asserted.',
                         'Missing serialized named facts are projected to zero only for the native fact API predicate fixture.']}
    write(out / 'verification.json', result)
    report = '''# Real-save fixtures — 12 November 2026

Read-only checks passed for four actual current save bodies. Manual Save 26 is
the preferred prospective gameplay fixture. **No save was loaded into the game,
and candidate 04 is still staged rather than installed.**

| Save | Observed source evidence | Use for HS3 testing |
| --- | --- | --- |
| Manual Save 26 | Same pinned intact body; before native cutoff; schema-1 candidate revision 143; tracks Deliver Skippy; Skippy total counter 97 | Run normally to Reed's capture gate; the candidate predicate accepts the hypothetical native gate transition applied only to this offline fixture |
| AutoSave-16 | Hospital; native cutoff/retirement facts present; frozen pre-ending schema-1 revision 159 and its own matching export token retained | Frozen legacy-history reload regression; no retroactive HS3 capture |
| AutoSave-2 | Viktor; native cutoff/retirement facts present; revision 159 retained but ready/frozen/origin/token absent from parsed header | Conservative handling of already-damaged history; cannot exercise the prospective capture gate |
| Manual Save 27 | After credits; fallback revision 160 retained | Old post-Tower compatibility without relabelling fallback as pre-cutoff history |

All four bodies and metadata hashes were checked before and after extraction,
and again during verification. The actual candidate's native gate expression
rejects all four as currently saved because no HS3 gate is open. For the three
late saves it still rejects a hypothetical open gate because native teardown
has already occurred. No injected facts were sent to the game or saved.

The selected restore source no longer clears the old frozen header on an early
boundary read. The new catalogue contains Manual Save 26's actual Deliver Skippy
path and counter field. AutoSave-16's own token binds its existing 158-row export;
this is a diagnostic comparison, not a product import or fixed revision override.

Limits: the dynamic save parser omits snapshot arrays, so this report does not
certify their shape or contents. The selected raw journal bytes and named facts
are preserved separately. This is a real-save/source compatibility fixture,
not engine execution, stage ownership proof, or an HS3 save/reload pass. Continue
with the project's gameplay test card after an authorized guarded deployment.
'''
    (out / 'REPORT.md').write_text(report, encoding='utf-8', newline='\n')
    baseline()
    print(f'PASS: {len(checks)} bounded checks across four real saves; no gameplay or save writes.')


if __name__ == '__main__':
    main()
