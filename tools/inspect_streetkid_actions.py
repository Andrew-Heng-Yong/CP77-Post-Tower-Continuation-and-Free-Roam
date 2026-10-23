"""Compact vanilla Streetkid choice, prop, reflection and localization report."""
import json
from pathlib import Path
from audit_scene_actor_ids import walk

ROOT=Path(__file__).resolve().parent.parent
PATH=ROOT/'research/b0_general_mirrors_devices/q000_meet_fixer/json/base/quest/main_quests/prologue/q000/scenes/q000_kid_01b_meet_your_fixer.scene.json'
s=json.loads(PATH.read_text(encoding='utf-8'))['Data']['RootChunk']
nodes={h['Data']['nodeId']['id']:h['Data'] for h in s['sceneGraph']['Data']['graph']}


def compact(n):
    result={'id':n['nodeId']['id'],'type':n['$type'],
            'edges':[{'socket':o['stamp'],'to':[d['nodeId'] for d in o['destinations']]} for o in n.get('outputSockets',[])]}
    if 'options' in n: result['options']=n['options']
    if 'sectionDuration' in n: result['duration']=n['sectionDuration']
    if 'events' in n:
        result['events']=[{'i':i,'type':e['Data']['$type'],'time':e['Data'].get('startTime'),
                           'performer':e['Data'].get('performer'),
                           'interesting':{k:v for k,v in e['Data'].items() if any(w in k.lower() for w in ('animname','prop','attach','item','target','entity','socket','osock'))}}
                          for i,e in enumerate(n['events'])]
    if 'questNode' in n: result['quest']=n['questNode']
    return result


def main():
    choices=[n for n in nodes.values() if n['$type']=='scnChoiceNode' and any(w in json.dumps(n.get('options',[])).lower() for w in ('fix_nose','drink','get_up','stand'))]
    selected={n['nodeId']['id'] for n in choices}|{197,404,757,765}
    for n in choices:
        selected.update(d['nodeId']['id'] for o in n['outputSockets'] for d in o['destinations'])
    result={'choices_and_targets':[compact(nodes[i]) for i in sorted(selected)],
            'props':s['props'],'screenplay':[o for o in s['screenplayStore']['options'] if any(w in json.dumps(o).lower() for w in ('nose','drink','get_up','stand'))]}
    out=ROOT/'research/b0_streetkid_seat_mirror_s2/original_actions_audit.json'
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    for n in choices:
        print(json.dumps(compact(n),ensure_ascii=False))
    for p in s['props']:
        print('PROP',json.dumps(p,ensure_ascii=False))
    print('DETAILS',out)


if __name__=='__main__': main()
