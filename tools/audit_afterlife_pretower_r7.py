"""Bounded user pre-Tower capture and authored Emmerick phase comparison."""
import json
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/afterlife_world'
OUT = BASE / 'baseline_r7'
LOG = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Behavior_Audit\afterlife_behavior_20261006T041947Z.jsonl')

def val(x):
    return x.get('$value', x) if isinstance(x, dict) else x

def walk(x):
    if isinstance(x, dict):
        yield x
        for y in x.values():
            yield from walk(y)
    elif isinstance(x, list):
        for y in x:
            yield from walk(y)

def main():
    raw = LOG.read_bytes()
    rows = [json.loads(x) for x in raw.splitlines()]
    actors = defaultdict(list)
    for i, r in enumerate(rows):
        for a in r.get('actors', []):
            state = tuple(r.get('facts', {}).get(k) for k in ('PostTowerFreeRoamActive', 'q307_active', 'q307_done', 'q307_finished'))
            actors[(state, a['id'])].append((i, a))
    selected = []
    for (world_state, actor_id), samples in actors.items():
        first = samples[0][1]
        if not any(t in first.get('record', '') for t in ('Emmerick', 'Rogue', 'Claire', 'q005_afterlife_mercenary_male')):
            continue
        states = Counter((a.get('in_workspot'), a.get('in_scene'), a.get('high_level_state')) for _, a in samples)
        transitions = []
        last = None
        for i, a in samples:
            state = {k: a.get(k) for k in ('position', 'in_workspot', 'in_scene', 'in_combat', 'classification')}
            if state != last:
                transitions.append({'row': i, 'utc': rows[i].get('utc'), **state})
                last = state
        selected.append({'world_state': world_state, 'id': actor_id, 'record': first.get('record'), 'samples': len(samples),
                         'first': rows[samples[0][0]].get('utc'), 'last': rows[samples[-1][0]].get('utc'),
                         'states': [{'in_workspot': k[0], 'in_scene': k[1], 'high_level_state': k[2], 'count': n} for k, n in states.items()],
                         'transitions': transitions})
    facts = {k: sorted({r.get('facts', {}).get(k) for r in rows}, key=str) for k in rows[0].get('facts', {})}
    report = {'source': str(LOG), 'sha256': hashlib.sha256(raw).hexdigest(), 'rows': len(rows),
              'first': rows[0].get('utc'), 'last': rows[-1].get('utc'), 'labels': sorted({r.get('label', '') for r in rows}),
              'distinct_observed_ids': len({k[1] for k in actors}), 'facts': facts, 'selected': selected,
              'segments': [{'world_state': list(state), 'rows': sum(tuple(r.get('facts', {}).get(k) for k in ('PostTowerFreeRoamActive', 'q307_active', 'q307_done', 'q307_finished')) == state for r in rows)} for state in sorted({k[0] for k in actors})],
              'limits': 'Nearby observation, not complete census. Flags do not prove rendering or animation; baseline is user pre-Tower save with installed mods.'}
    OUT.mkdir(exist_ok=True)
    (OUT / 'capture.json').write_text(json.dumps(report, indent=2)+'\n')
    registry = json.loads((BASE / 'patron_vanilla_registry.json').read_text())
    emmerick = [r for r in registry if r['community_index'] == 115]
    (OUT / 'emmerick_vanilla.json').write_text(json.dumps(emmerick, indent=2)+'\n')
    dialogue = []
    for name, path in (
        ('Rogue', BASE/'rogue_sources/json/base/quest/secondary_characters/default_dialogues/rogue_default.scene.json'),
        ('Claire', ROOT/'research/b0_vendor_rollout/special_scene_sources/json/base/quest/tertiary_characters/default_dialogues/claire_default.scene.json'),
    ):
        raw_scene = path.read_bytes()
        scene = json.loads(raw_scene)['Data']['RootChunk']
        choices, effects, writes = [], [], []
        for h in scene['sceneGraph']['Data']['graph']:
            node = h['Data']
            node_id = node['nodeId']['id']
            if node['$type'] == 'scnChoiceNode':
                choices.append({'node': node_id, 'options': [{'caption': val(o['caption']), 'screenplay_id': o['screenplayOptionId']['id'],
                                'condition': o.get('questCondition')} for o in node.get('options', [])]})
            for n in walk(node):
                if n.get('$type') == 'scneventsVFXEvent':
                    effects.append({'node': node_id, 'action': n.get('action'), 'effect': val(n.get('effectEntry', {}).get('effectName')),
                                    'performer': n.get('performerId')})
                if n.get('$type') == 'questSetVar_NodeType':
                    writes.append({'node': node_id, 'fact': n.get('factName'), 'value': n.get('value')})
        dialogue.append({'name': name, 'source': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw_scene).hexdigest(),
                         'actors': [{'name': a['actorName'], 'acquisition': a['acquisitionPlan']} for a in scene['actors']],
                         'entries': scene['entryPoints'], 'choices': choices, 'effects': effects, 'writes': writes})
    (OUT/'dialogue_sources.json').write_text(json.dumps(dialogue, indent=2)+'\n')
    print(json.dumps({**{k: report[k] for k in ('rows', 'first', 'last', 'labels', 'distinct_observed_ids')},
                      'segments': report['segments'],
                      'selected_state_rows': len(selected),
                      'emmerick_registry_matches': len(emmerick)}, indent=2))

if __name__ == '__main__':
    main()
