"""Check exact current-script event paths; never interprets a live or saved stage."""
from pathlib import Path
import hashlib, json, re, sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[3]
sys.path.insert(0,str(WORK/'tools/parity_audit'))
from model import Resource


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def method(text,name):
    matches = list(re.finditer(r'\bfunc\s+'+re.escape(name)+r'\(',text))
    assert len(matches)==1,(name,len(matches))
    start=matches[0].start()
    opening=text.index('{',start)
    depth=0
    for token in re.finditer(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[{}]',text[opening:]):
        if token.group()=='{': depth+=1
        elif token.group()=='}':
            depth-=1
            if depth==0:return text[start:opening+token.end()]
    raise AssertionError('Unclosed method')


def no_visual_receipt_write(body):
    return not re.search(r'SetHasVisualDestructionBeenSet\s*\(|\bm_visualDestructionSet\s*=(?!=)',body)


def main():
    output=HERE/'event_contract_01.json'
    assert not output.exists(),'Fresh output required'
    manifest=json.loads((HERE/'current_01/manifest.json').read_text())
    assert sha(manifest['input'])==manifest['input_sha256']
    for row in manifest['classes']:assert sha(row['path'])==row['sha256']
    ps=(HERE/'current_01/VehicleComponentPS.script').read_text()
    actor=(HERE/'current_01/VehicleComponent.script').read_text()
    ps_event=method(ps,'OnVehicleQuestVisualDestructionEvent')
    actor_event=method(actor,'OnVehicleQuestVisualDestructionEvent')
    getter=method(ps,'GetHasVisualDestructionBeenSet')
    door_event=method(ps,'OnVehicleQuestChangeDoorStateEvent')
    provider=json.loads((HERE.parent.parent/'providers_01/manifest.json').read_text())
    row=next(r for r in provider['resources'] if r['depot'].endswith('sts_ep1_03_gameplay.questphase'))
    assert sha(row['raw'])==row['sha256'] and sha(row['json'])==row['json_sha256']
    model=Resource(json.loads(Path(row['json']).read_text())).normalize()
    assert not model['errors']
    graph=model['graphs']['root/1']
    checks=[]

    def ck(name,ok):
        checks.append({'name':name,'pass':bool(ok)})
        assert ok,name

    ck('quest_graph_car_sequence',all(e in graph['edges']for e in [['101','Out','102','In'],['102','Out','103','In'],['103','Out','104','In']]))
    ck('exact_visual_event_type_and_nonaccumulating_argument',graph['nodes']['103']['payload']['event']['$type']=='VehicleQuestVisualDestructionEvent' and graph['nodes']['103']['payload']['event']['accumulate']==0)
    ck('ps_event_only_forwards',re.sub(r'\s+','',ps_event.split('{',1)[1].rsplit('}',1)[0])=='returnEntityNotificationType.SendThisEventToEntity;')
    ck('actor_event_two_layer_native_calls',actor_event.count('SetDestructionGridPointValues(')==2 and '0u, pointValues, evt.accumulate' in actor_event and '1u, pointValues, evt.accumulate' in actor_event)
    ck('getter_reads_generic_persistent_flag','return this.m_visualDestructionSet;' in getter and 'persistent let m_visualDestructionSet: Bool;' in ps)
    ck('visual_event_does_not_issue_that_receipt',no_visual_receipt_write(ps_event) and no_visual_receipt_write(actor_event))
    mutated=actor_event.replace('{','{ this.GetPS().SetHasVisualDestructionBeenSet(true);',1)
    ck('inserted_receipt_writer_would_invalidate_the_current_conclusion',not no_visual_receipt_write(mutated))
    ck('door_event_is_separate_ps_queue_path','QueuePSEvent' in door_event and 'EntityNotificationType.DoNotNotifyEntity' in door_event)
    actual={i:graph['nodes'][i]['payload']['actions'][0]['type']['$type'] for i in ['101','86','142','143']}
    ck('population_and_community_actions_are_not_conflated',actual=={'101':'questSpawner_NodeType','86':'questCommunityTemplate_NodeType','142':'questCommunityTemplate_NodeType','143':'questCommunityTemplate_NodeType'})
    result={'status':'CURRENT_SCRIPT_EVENT_PATHS_PROVED_NO_SPECIFIC_COMPLETION_RECEIPT',
            'base_input':{'path':manifest['input'],'sha256':manifest['input_sha256']},
            'classes':manifest['classes'],'native_graph':row,'checks':checks,
            'methods':{'ps_visual_event':ps_event,'actor_visual_event':actor_event,'generic_visual_getter':getter,'door_event':door_event},
            'action_subtypes':actual,
            'conclusion':'The persistent generic visual flag is not written by either inspected quest-visual event handler and cannot be substituted for a node103 completion receipt. Native setters, actor-state persistence and pending-event restoration still need their exact contract. Source alone does not authorize repeating the setup.',
            'limits':'Script paths only. Native imported setter semantics and saved actor identity/state are not decoded. The synthetic inserted-writer control is a source-proof control, not a repaired runtime test.',
            'runtime_changes':0,'game_calls':0,'save_writes':0}
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks)}))


if __name__=='__main__':main()
