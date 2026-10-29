import json,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
group_report=read(ROOT/'conversation_native_01/report_01.json')
scene_report=read(ROOT/'conversation_scenes_native_01/report_01.json')
checks=[]
def check(name,ok):
    checks.append({'name':name,'pass':bool(ok)})
    assert ok,name
group_inputs=(ROOT/'conversation_resources_01.txt').read_text().splitlines()
scene_inputs=(ROOT/'conversation_scenes_01.txt').read_text().splitlines()
scenes=[]
for name in group_inputs:
    hits=[x for x in group_report['hits'] if x['depot']==name]
    check('Unique native group winner '+name,len(hits)==1 and '\\mod\\' not in hits[0]['archive'])
for name in scene_inputs:
    hits=[x for x in scene_report['hits'] if x['depot']==name]
    check('Unique native scene winner '+name,len(hits)==1 and '\\mod\\' not in hits[0]['archive'])
    hit=hits[0];p=Path(hit['copy']+'.json');d=read(p)
    nodes=d['Data']['RootChunk']['sceneGraph']['Data']['graph']
    types=collections.Counter(x.get('$type','') for x in walk(d))
    check('Only native dialogue scene nodes '+name,all(x['Data']['$type'] in ['scnStartNode','scnSectionNode','scnEndNode'] for x in nodes))
    event_types={t for t in types if t.endswith('Event')}
    check('Only dialogue line events '+name,event_types<= {'scnDialogLineEvent'})
    check('No quest node or persistent-state writes '+name,not any(t.startswith('quest') for t in types))
    scenes.append({'resource':name,'binary':hit['copy'],'sha256':hit['sha256'],'json':str(p),'json_sha256':sha(p),'nodes':len(nodes),'dialogue_events':types['scnDialogLineEvent']})
check('All15conversation groups and286scenes',len(group_inputs)==15 and len(scene_inputs)==286)
report={'status':'PASS_NATIVE_AMBIENT_CONVERSATIONS','checks':checks,'groups':group_report['hits'],'scenes':scenes,'eligible_node_types':['worldInterestingConversationsAreaNode','worldPatrolSplineNode','worldAudioSignpostTriggerNode'],'reason':'Generic conversation resources contain only authored dialogue, no quest/AI/progress/reward/reset operations. Preserve native conversation selection limits, triggers, interruption and return policy. Patrol splines are authored geometry/support; audio signpost node18 has matched ow_generic_START/STOP with5s exit cooldown.','archives':{'groups':group_report['archives'],'scenes':scene_report['archives']},'source_inventory':str(ROOT/'prefab_inventory_01.json'),'source_inventory_sha256':sha(ROOT/'prefab_inventory_01.json'),'game_writes':0,'save_writes':0}
(ROOT/'conversation_assessment_01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'scenes':len(scenes)}))
