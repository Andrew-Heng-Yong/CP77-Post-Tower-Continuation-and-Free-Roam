"""Prepare isolated S29 resource copies and fresh-entry contracts."""
from common import *
import copy,re
out=ROOT/'prealpha/sidejobs_s29/prepared_04'
assert not out.exists();out.mkdir()
plan=read(ROOT/'research/sidejobs_s29/contracts_review_01.json')
targets={r['id']:r for r in read(ROOT/'research/sidejobs_s29/scope_01.json')['targets']}
audit=read(ROOT/'research/sidejobs_s29/presentation_audit_01.json')
for row in read(ROOT/'research/sidejobs_s29/native_05/inventory.json')['rows']:
    if row['depot'] in INDEX:assert INDEX[row['depot']]['sha256']==row['sha256']
    INDEX[row['depot']]=row
pins={};changes=[];inputs=[];meta=metadata()
def pin(dep):
    row=INDEX[dep]
    for k,h in [('raw','sha256'),('json','json_sha256')]:
        assert sha(ROOT/row[k])==row[h];pins[row[k]]=row[h]
    return read(ROOT/row['json'])
def target(dep):return 'towercontinued\\sidejobs_s29\\native\\'+dep
deps=sorted({d for j in plan['jobs'] for d in j['reachable']+[j['native']]})
mapping={d:target(d) for d in deps}
objects={d:pin(d) for d in deps}
def save(dep,obj,original):
    # An event being removed may own the first serialized definition of a
    # shared animation parameter. Re-emit definitions at their first surviving
    # reference; preserve identity/cycles rather than dropping shared payloads.
    definitions={**handles(load(original)),**handles(obj)};seen=set()
    def canonical(v):
        if isinstance(v,list):return [canonical(x) for x in v]
        if not isinstance(v,dict):return v
        key=v.get('HandleId',v.get('HandleRefId'))
        if key is not None and key in definitions:
            if key in seen:return {'HandleRefId':key}
            seen.add(key);return {'HandleId':key,'Data':canonical(definitions[key])}
        return {k:canonical(x) for k,x in v.items()}
    obj=canonical(obj)
    p=out/'json'/(dep+'.json');p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    inputs.append(dict(depot=dep,expected=p.relative_to(ROOT).as_posix(),native=original,raw=INDEX[original]['raw']))
for s in audit['scenes']:
    dep=s['depot']
    if dep not in objects:continue
    root=objects[dep]['Data']['RootChunk'];hh=handles(root)
    performers=set(s['performers']);owned=set(s['owned_instances']);others=set(s['other_instances'])
    assert not owned&others
    instances={w['workspotInstanceId']['id']:w['dataId']['id'] for w in root['workspotInstances']}
    data={instances[w] for w in owned};otherdata={instances[w] for w in others}
    shared=data&otherdata
    splits=[]
    for old in sorted(shared):
        newid=max(deref(w,hh)['dataId']['id'] for w in root['workspots'])+1
        wrapper=copy.deepcopy(next(w for w in root['workspots'] if deref(w,hh)['dataId']['id']==old))
        wrapper['HandleId']=str(max(int(v['HandleId']) for v in walk(root) if 'HandleId' in v)+1)
        wrapper['Data']['dataId']['id']=newid;root['workspots'].append(wrapper)
        for w in root['workspotInstances']:
            if w['workspotInstanceId']['id'] in owned and w['dataId']['id']==old:w['dataId']['id']=newid
        data.remove(old);data.add(newid);splits.append({'from':old,'to':newid})
    props={p['id'] for p in s['props']}
    if props:
        # Removing only unused definitions; remap remaining prop IDs densely.
        actual=[v for v in walk(root) if v.get('$type')=='scnPropId' and v['id'] in props]
        assert len(actual)==len(props),('Live Johnny prop reference',dep,actual)
        root['props']=[p for p in root['props'] if p['propId']['id'] not in props]
        pm={p['propId']['id']:i for i,p in enumerate(root['props'])}
        symbols=root['debugSymbols']['performersDebugSymbols']
        root['debugSymbols']['performersDebugSymbols']=[x for x in symbols if x['performerId']['id'] not in {(i<<8)|2 for i in props}]
        for v in walk(root):
            if v.get('$type')=='scnPropId' and v['id'] in pm:v['id']=pm[v['id']]
            if v.get('$type')=='scnPerformerId' and v['id']&255==2 and v['id']>>8 in pm:v['id']=(pm[v['id']>>8]<<8)|2
    removed=[];muted=[]
    for wrap in root['sceneGraph']['Data']['graph']:
        n=deref(wrap,hh);keep=[]
        for ew in n.get('events',[]):
            e=deref(ew,hh);typ=e.get('$type')
            if e.get('performerId',{}).get('id') in performers and typ in ['scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent']:
                removed.append(e['id']['id']);continue
            if typ=='scnPlaySkAnimEvent' and e.get('performer',{}).get('id') in performers:
                assert e['muteAnimEvents'] in ['0','STANDARD'];e['muteAnimEvents']='STANDARD';muted.append(e['id']['id'])
            keep.append(ew)
        if 'events' in n:n['events']=keep
    for symbol in root['debugSymbols']['sceneEventsDebugSymbols']:
        symbol['sceneEventIds']=[v for v in symbol['sceneEventIds'] if v['id'] not in removed]
    root['debugSymbols']['sceneEventsDebugSymbols']=[v for v in root['debugSymbols']['sceneEventsDebugSymbols'] if v['sceneEventIds']]
    ws=[]
    for ww in root['workspots']:
        w=deref(ww,hh)
        if w['dataId']['id'] not in data:continue
        d=value(w['workspotResource']['DepotPath']);td=target(d)
        if td not in {i['depot'] for i in inputs}:
            obj=pin(d);edits=[]
            for v in walk(obj['Data']['RootChunk']):
                if v.get('$type')=='animAnimNode_WorkspotHub':
                    assert v['eventFilterType'] in ['Default','Mute'];v['eventFilterType']='Mute';edits.append('mute_events')
                if v.get('$type')=='workWorkspotTree' and v.get('initialActions'):
                    assert all(a['Data']['$type']=='workEquipItemToSlotAction' for a in v['initialActions'])
                    edits.append(copy.deepcopy(v['initialActions']));v['initialActions']=[]
            assert edits, d
            save(td,obj,d);changes.append(dict(kind='workspot',native=d,target=td,changes=edits))
        w['workspotResource']['DepotPath']['$value']=td;ws.append(d)
    changes.append(dict(kind='scene',native=dep,props=sorted(props),removed_events=removed,muted_events=muted,workspots=ws,workspot_binding_splits=splits))
for d,obj in objects.items():
    for v in walk(obj):
        if isinstance(v.get('DepotPath'),dict):
            old=v['DepotPath'].get('$value')
            if old in mapping:v['DepotPath']['$value']=mapping[old]
    save(mapping[d],obj,d)
special={
 'q003_stout':['q003_stout_sex_agreed','q003_stout_sex_done','q003_stout_sex_lookat_loop','q003_stout_sex_on'],
 'sq025b_delamain_insurgence':['sq025_deep_active','sq025_fate_sealed','sq025_resurgence_del_called','sq025_resurgence_player_called','sq025_resurgence_start'],
 'q305_postcontent':['Q305_haunted_component_talk_ready'],
 'wst_ep1_09':['wst_ep1_09_start','wst_ep1_09_finished','wst_ep1_09_cleanup_done'],
 'sts_ep1_12_pickup':['wst_ep1_02_start','wst_ep1_02_finished']}
for j in plan['jobs']:
    ident=j['id'];prefix=ident[:5]
    facts=special.get(ident,sorted(f for f in j['native_writes'] if f.startswith(prefix)))
    j['facts_equal']={f:0 for f in facts};j['fact_ranges']={}
    # Messages from this job are progress even when its quest root is inactive.
    paths=set()
    for d in j['reachable']+[j['native']]:
        for n in walk(load(d)):
            p=n.get('realPath','')
            if n.get('$type')=='gameJournalPath' and p.startswith('contacts/') and (prefix in p or (ident=='sq025b_delamain_insurgence' and '/sq025_scan_results/' in p)) and p in meta:paths.add(p)
    if ident=='q003_stout':paths={p for p in paths if '/q003_stout_won/' in p}
    j['journals'] += [dict(path=p,**{'class':meta[p]},states=[1]) for p in sorted(paths)]
    if ident=='q003_stout':j['fact_ranges']={'q003_meredith_won':{'min':1,'max':2147483647},'q101_done':{'min':1,'max':2147483647}}
    if ident=='sq025b_delamain_insurgence':
        ep=[p for p,c in meta.items() if c=='gameJournalQuest' and p.endswith('/sq025_delamain')];assert len(ep)==1,ep
        j['journals'].append(dict(path=ep[0],**{'class':'gameJournalQuest'},states=[3]))
    j['native_raw']=INDEX[j['native']]['raw'];j['private_native']=mapping[j['native']]
    j['phones']=[c['name'] for c in audit['contacts'] if c['consumer']==ident]
    if ident=='sq025b_delamain_insurgence':j['phones']=['delamain']
    if j['parent']:j['parent']['raw']=INDEX[j['parent']['depot']]['raw'];pin(j['parent']['depot'])
    if j.get('native_entry_condition'):
        spec=j['native_entry_condition'];spec['raw']=INDEX[spec['depot']]['raw'];pin(spec['depot'])
    j['facts']=[dict(name=f,min=v,max=v) for f,v in j['facts_equal'].items()]+[dict(name=f,**v) for f,v in j['fact_ranges'].items()]
    j['inventory_zero']=[];j['vehicle_zero']=[]
contacts=copy.deepcopy(audit['contacts'])
contacts.append(dict(name='delamain',consumer='sq025b_delamain_insurgence',init=51,resources=[]))
for c in contacts:
    for d in c['resources']:pin(d)
    c['tag']='PTFRS22_SQ025_Support' if c['name']=='delamain' else 'PTFRS29_PHONE_'+c['name']
    c['idle']=sorted({value(v['factName']) for d in c['resources'] for v in walk(load(d)) if 'factName' in v and re.fullmatch(r'(holo|audio)_.+_(start_activate|end_activate|active|started)',str(value(v['factName'])))})
for d in [r'base\quest\holocalls\holocall_initializers.questphase',r'base\quest\holocalls\holocall_cleanup.questphase']:pin(d)
result=dict(status='PREPARED_NOT_INSTALLED',jobs=plan['jobs'],inputs=inputs,mapping=mapping,presentation=changes,contacts=contacts,index=INDEX,source_pins=pins)
(out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(plan['jobs']),'owners;',len(inputs),'resources;',len(changes),'presentation adaptations')
