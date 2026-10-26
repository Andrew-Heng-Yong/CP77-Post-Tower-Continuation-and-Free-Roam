"""Identify only Johnny-owned presentation and required phone dependencies."""
from common import *
import re
plan=read(ROOT/'research/sidejobs_s29/plan_01.json');scenes=[];wanted=set();seen=set()
for job in plan['jobs']:
    for dep in job['closure']:
        if not dep.endswith('.scene') or dep in seen:continue
        seen.add(dep);root=load(dep)['Data']['RootChunk'];hh=handles(root)
        actors=[a for a in root['actors'] if a['actorName'].lower() in ['johnny','silverhand']]
        if not actors:continue
        aids={a['actorId']['id'] for a in actors};performers={(a<<8)|1 for a in aids}
        names={value(a['spawnDespawnParams']['dynamicEntityUniqueName']) for a in actors}
        names.discard('None');names.discard(None)
        owned=set();others=set()
        for v in walk(root):
            if v.get('$type')=='questUseWorkspotNodeDefinition':
                w=deref(v.get('paramsV1',{}),hh).get('workspotInstanceId',{}).get('id')
                if w is not None:
                    ref=v['entityReference'];mine=value(ref.get('dynamicEntityUniqueName')) in names or value(ref.get('sceneActorContextName','')).lower() in {a['actorName'].lower() for a in actors}
                    (owned if mine else others).add(w)
            if v.get('$type')=='scnPlaySkAnimEvent':
                w=deref(v.get('poseBlendOutWorkspot',{}),hh).get('workspotId',{}).get('id')
                if w is not None:(owned if v.get('performer',{}).get('id') in performers else others).add(w)
        instances={w['workspotInstanceId']['id']:w['dataId']['id'] for w in root['workspotInstances']}
        dataids={instances[i] for i in owned if i in instances}
        ws=[]
        for wrapper in root['workspots']:
            w=deref(wrapper,hh)
            if w['dataId']['id'] in dataids:
                d=value(w['workspotResource']['DepotPath']);wanted.add(d);ws.append(d)
        props=[]
        for p in root['props']:
            mine=p['entityAcquisitionPlan']=='findInEntity' and p['findEntityInEntityParams']['performerId']['id'] in performers
            if mine:props.append({'id':p['propId']['id'],'name':p['propName'],'plan':p['entityAcquisitionPlan'],'item':value(p['findEntityInEntityParams']['itemID'])})
        scenes.append(dict(depot=dep,actors=[{'id':a['actorId']['id'],'name':a['actorName'],'plan':a['acquisitionPlan']} for a in actors],performers=sorted(performers),names=sorted(names),owned_instances=sorted(owned),other_instances=sorted(others),workspots=ws,props=props))

init=graphset(r'base\quest\holocalls\holocall_initializers.questphase')['root'];cleanup=graphset(r'base\quest\holocalls\holocall_cleanup.questphase')['root']
contacts=[]
for name,consumer in [('kirk','mq017_streetkid'),('nancy','mq018_writer'),('blue_moon','mq028_stalker'),('cynthia','mq040_biosculpt'),('pepe','mq040_biosculpt'),('rachel','sq023_hit_order')]:
    dep=f'base\\quest\\holocalls\\{name}\\{name}_holocall.questphase'
    node=next(n for n in init['nodes'] if value(n.get('phaseResource',{}).get('DepotPath'))==dep)
    cn=next(n for n in cleanup['nodes'] if f'\\{name}\\' in str(value(n.get('phaseResource',{}).get('DepotPath'))))
    incoming=[e for e in cleanup['edges'] if e[2]==cn['id']];assert len(incoming)==1
    outgoing=[e for e in cleanup['edges'] if e[0]==cn['id']];assert len(outgoing)==1
    cleanupdep=value(cn['phaseResource']['DepotPath'])
    wanted.update([dep,cleanupdep,f'base\\quest\\holocalls\\{name}\\{name}_holocall.scene'])
    contacts.append(dict(name=name,consumer=consumer,init=node['id'],condition=incoming[0][0],cleanup=cn['id'],input=incoming[0][3],output=outgoing[0][1],resources=[dep,cleanupdep,f'base\\quest\\holocalls\\{name}\\{name}_holocall.scene']))
write('presentation_audit_01.json',dict(status='SCOPED_PRESENTATION_SOURCE_REVIEW',scenes=scenes,contacts=contacts))
write('dependencies_03.json',sorted(wanted))
print('Johnny scenes',len(scenes),'workspots',sum(len(s['workspots']) for s in scenes),'props',sum(len(s['props']) for s in scenes),'phone contacts',len(contacts),'resources',len(wanted))
for s in scenes:
    if set(s['owned_instances'])&set(s['other_instances']):print('SHARED INSTANCE',s['depot'])
    if s['props']:print('PROPS',s['depot'],s['props'])
