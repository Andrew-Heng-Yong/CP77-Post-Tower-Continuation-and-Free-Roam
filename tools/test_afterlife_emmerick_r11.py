"""Exact NPC-only scene delta, typed-identity and R10 live gate regression."""
import copy
import hashlib
import json
from pathlib import Path

from audit_scene_actor_ids import audit_scene_actor_ids, walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/afterlife_world/interactions_r11/emmerick'
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
LOGS = GAME / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rejects(scene):
    try:
        audit_scene_actor_ids(scene)
    except ValueError:
        return True
    return False


old = read(ROOT / 'research/afterlife_world/interactions_r8/emmerick.scene.json')['Data']['RootChunk']
new = read(OUT / 'emmerick.scene.json')['Data']['RootChunk']
expected = copy.deepcopy(old)
expected['playerActors'] = []
section = next(x['Data'] for x in expected['sceneGraph']['Data']['graph'] if x['Data']['nodeId']['id'] == 441)
assert section['actorBehaviors'][0]['actorId']['id'] == 1
section['actorBehaviors'].pop(0)
assert expected['debugSymbols']['performersDebugSymbols'][1]['performerId']['id'] == 257
expected['debugSymbols']['performersDebugSymbols'].pop(1)
assert len(expected['screenplayStore']['lines']) == 9
assert len(expected['screenplayStore']['options']) == 2
expected['screenplayStore']['lines'] = []
expected['screenplayStore']['options'] = []
assert expected == new, 'Only the five documented unused-player removals are permitted'
identity = audit_scene_actor_ids(new)
assert identity['actor_ids'] == [0]
assert len(new['sceneGraph']['Data']['graph']) == 5
assert new['actors'] == old['actors']
new_section = next(x['Data'] for x in new['sceneGraph']['Data']['graph'] if x['Data']['nodeId']['id'] == 441)
old_section = next(x['Data'] for x in old['sceneGraph']['Data']['graph'] if x['Data']['nodeId']['id'] == 441)
assert new_section['events'] == old_section['events'], 'Root motion/timing must be byte-equivalent at JSON level'
assert all(v.get('$type') not in ('scnDialogLineEvent', 'scnChoiceNode') for _, v in walk(new['sceneGraph']))
mutants = []
header_only = copy.deepcopy(old)
header_only['playerActors'] = []
mutants.append(header_only)
for path in ('debug', 'behavior', 'screenplay'):
    m = copy.deepcopy(new)
    if path == 'debug':
        m['debugSymbols']['performersDebugSymbols'] = old['debugSymbols']['performersDebugSymbols']
    elif path == 'behavior':
        next(x['Data'] for x in m['sceneGraph']['Data']['graph'] if x['Data']['nodeId']['id'] == 441)['actorBehaviors'] = old_section['actorBehaviors']
    else:
        m['screenplayStore']['lines'] = old['screenplayStore']['lines']
    mutants.append(m)
assert all(rejects(m) for m in mutants)

trace_path = LOGS / 'afterlife_interactions_20261006T185525Z.jsonl'
behavior_path = LOGS / 'afterlife_behavior_20261006T185531Z.jsonl'
trace = [json.loads(x) for x in trace_path.read_text().splitlines()]
behavior = [json.loads(x) for x in behavior_path.read_text().splitlines()]
by_time = {r['utc']: r for r in trace}
before = by_time['2026-10-06T18:55:56Z']
cancel = by_time['2026-10-06T18:55:57Z']
assert before['facts']['PTFRAL8_EStage'] == 3
assert before['facts']['PTFRAL8_EContinue'] == 1
assert all(k in before['status'] for k in ['anchor=true', 'facingDot=1.000000', 'workspot=true', 'playerScene=false'])
assert cancel['facts']['PTFRAL8_EStage'] == 8
assert cancel['facts']['PTFRAL8_ECancelled'] == 1
assert 'resolved=true permit=false playerScene=true otherActive=false' in cancel['status']
assert {r['facts']['PTFRAL8_ERequests'] for r in trace} == {0}
anchor = (-1458.48499, 1026.3302, 16.7932014)
close = []
for r in trace:
    distance = sum((r['position'][axis] - anchor[i]) ** 2 for i, axis in enumerate(('x', 'y', 'z'))) ** .5
    if distance <= 5:
        assert r['facts']['PTFRAL8_EContinue'] == 0 and 'playerScene=true' in r['status']
        close.append({'utc': r['utc'], 'distance_to_authored_start_m': distance, 'stage': r['facts']['PTFRAL8_EStage']})
assert len(close) >= 5
matched = next(r for r in behavior if r['utc'] == '2026-10-06T18:56:04Z')
em = next(a for a in matched['actors'] if 'Character.Emmerick' in a['record'])
assert not any(em[k] for k in ['in_scene', 'in_combat', 'dead', 'defeated'])
assert em['in_workspot'] and 'Relaxed' in em['high_level_state']
assert all(abs(em['position'][axis] - anchor[i]) < .0001 for i, axis in enumerate(('x', 'y', 'z')))
claire = next(a for a in matched['actors'] if 'Character.Claire' in a['record'])
assert claire['in_scene']

# Model only the revised player admission rule, explicitly not engine proof.
def free(s):
    return s['defined'] and not any(s[k] for k in ('dead', 'combat', 'dialogue', 'workspot', 'mounted', 'tokens')) and s['high'] in (1, 2) and s['tier'] in (1, 2)

base = dict(defined=True, dead=False, combat=False, dialogue=False, workspot=False, mounted=False, tokens=False, high=1, tier=1, ambient_scene=True)
assert free(base), 'Passive ambient ownership must not veto the NPC-only scene'
negative_cases = 0
for key in ('dead', 'combat', 'dialogue', 'workspot', 'mounted', 'tokens'):
    assert not free(dict(base, **{key: True}))
    negative_cases += 1
assert not free(dict(base, defined=False))
negative_cases += 1
for key in ('high', 'tier'):
    for value in (-1, 0, 3, 4, 5, 6):
        assert not free(dict(base, **{key: value}))
        negative_cases += 1
assert free(dict(base, high=2, tier=2))

result = dict(status='PASS_R11_EMMERICK_SCENE_AND_LOG_AUDIT_LIVE_PENDING', scene_identity=identity,
              exact_delta_groups=5, typed_reference_mutants_rejected=len(mutants), player_guard_model_negatives=negative_cases,
              source_scene_sha256=sha(ROOT / 'build/AfterlifeInteractionsR10/source/towercontinued/afterlife_interactions_r8/emmerick.scene'),
              candidate_scene_sha256=sha(ROOT / 'build/AfterlifeInteractionsR11/source/towercontinued/afterlife_interactions_r8/emmerick.scene'),
              trace=dict(path=str(trace_path), sha256=sha(trace_path), rows=len(trace), first=trace[0]['utc'], last=trace[-1]['utc']),
              behavior=dict(path=str(behavior_path), sha256=sha(behavior_path), rows=len(behavior)),
              proven_failure='Player IsEntityInScene blanket gate revoked permission at18:55:57Z before proximity admission; no scene dispatched',
              close_samples=close, matched_emmerick=em, claire_scene_correlation_only=True,
              player_dialogue_tier_not_recorded=True, live_animation_proven=False)
(OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: result[k] for k in ('status', 'scene_identity', 'typed_reference_mutants_rejected', 'player_guard_model_negatives')}))
