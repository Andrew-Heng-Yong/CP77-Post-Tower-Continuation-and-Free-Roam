"""Source-backed Sacrum restart boundary; no executable reset or game writes."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'prealpha/ncpd_scanner_n1'))
from native_inspect import SafeResource, flatten


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    output = ROOT / 'research/sidejobs_s27/restart/assessment_01.json'
    if output.exists():
        raise ValueError('Immutable evidence exists')
    base = ROOT / 'research/sidejobs_s2/sacrum_audit/native_01/json/base/quest/minor_quests/mq032'
    paths = [base / 'mq032_sacrum.questphase.json', base / 'phases/mq032_01_hook.questphase.json',
             base / 'phases/mq032_02_maelstrom.questphase.json',
             ROOT / 'prealpha/sidejobs_s2/build/s2_02/readback/mq032_sacrum.json']
    data = []
    for path in paths:
        resource = SafeResource(json.loads(path.read_text(encoding='utf-8-sig')))
        data.append({g['path']: g for g in flatten(resource, resource.obj['Data']['RootChunk'])})
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append(name)
    root, hook, maelstrom, wrapper = data
    check('Original hook and encounter start in parallel',
          [40, 'Out', 32, 'In1'] in root['root']['edges'] and [40, 'Out', 33, 'In1'] in root['root']['edges'])
    check('Hook completion enters already-running encounter', [32, 'Out1', 33, 'hook_done'] in root['root']['edges'])
    casualty = []
    for node_id in [2, 3, 4, 5, 10]:
        node = next(n for n in maelstrom['root/43/66']['nodes'] if n['id'] == node_id)
        condition = node['condition']['type']
        check(f'Native casualty check {node_id}', condition['$type'] == 'questCharacterKilled_ConditionType'
              and condition['defeated'] == condition['killed'] == condition['unconscious'] == 1)
        casualty.append(condition)
    brother = next(n for n in maelstrom['root']['nodes'] if n['id'] == 35)['condition']['type']
    check('Monk defeat is separately tracked', brother['defeated'] == brother['killed'] == brother['unconscious'] == 1)
    s2nodes = {n['id']: n for n in wrapper['root']['nodes']}
    check('Existing S2 has durable issuance before original child',
          [1002, 'True', 1003, 'In'] in wrapper['root']['edges'] and [1003, 'Out', 4, 'In1'] in wrapper['root']['edges'])
    check('Existing refusal branch does not rearm itself',
          [1002, 'False', 1005, 'In'] in wrapper['root']['edges'] and
          not any(e[0] == 1005 for e in wrapper['root']['edges']))
    check('Existing wrapper has no retirement output', not any(n['$type'] == 'questOutputNodeDefinition' for n in s2nodes.values()))
    sources = paths + [Path(__file__), ROOT / 'research/sidejobs_s2/sacrum_audit/assessment.md',
                       ROOT / 'research/sidejobs_s26/restart/assessment_01.json',
                       ROOT / 'prealpha/ncpd_scanner_n1/native_inspect.py',
                       ROOT / 'tools/test_gig_pilot_r1.py', ROOT / 'tools/audit_activity_batches_b1.py']
    report = {
        'status': 'RESTART_BOUNDARY_AUDITED_NOT_IMPLEMENTED', 'checks': len(checks), 'check_names': checks,
        'candidate': 'mq032_sacrum', 'new_runtime_or_reset_files': 0, 'game_writes': 0, 'save_writes': 0,
        'findings': [
            'Sacrum starts hook and Maelstrom in parallel. Early dialogue facts alone cannot prove the encounter has no casualties or optional looted weapon.',
            'The stock encounter checks five exact enemy entries and the captured monk for killed, defeated or unconscious state; preserving completed root/objective is required because the main quest reward precedes mq032_complete.',
            'A reset could potentially reuse the existing unissued and unrefused S2 owner after a bounded fact/journal reset; no second gameplay owner is necessary.',
            'The existing wrapper has no targeted retirement acknowledgement; adding new listeners to a serialized running graph is not verified to arm them.'
        ],
        'rejected_shortcuts': ['Reset all mq032 facts', 'Clear existing Issued', 'Use inactive root as proof of no progress',
                               'Assume no help means no combat', 'Refill or reset optional loot', 'Start a parallel owner'],
        'remaining_concrete_requirements': [
            'Establish that native casualty checks resolve the original persisted community while its quest prefab is not leased, or safely acquire a tested observation lease without respawning/resetting state.',
            'For issued S2 saves, implement and validate retirement of that exact saved owner before any new original beginning.',
            'For unissued S2, check Refused is zero, preserve optional loot and reject all paid/succeeded or rescued stages. Audit one-shot interruption recovery before reset writes.'
        ],
        'native_casualty_conditions': casualty + [brother],
        'policy': 'User restart-from-beginning target remains unchanged. No unsupported reset is installed; fresh expansion can proceed independently.',
        'source_pins': {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'checks': len(checks), 'output': str(output)}))


if __name__ == '__main__':
    main()
