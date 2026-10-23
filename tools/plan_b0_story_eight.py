"""S4 exact service-only scene deltas and bounded native owner plans."""
import copy,json
from inspect_story_eight import *
from audit_b0_claire import COMMON,sha
from plan_b0_ordinary_vendor_batch import nm,edge_set
from test_b0_ordinary_vendor_batch import handles
OUT=ROOT/'research/b0_story_eight'
SCENES={
 'nix':('nix_default', [1,308], {'hide':[(6,3)]}),
 'yoko':('wat_kab_netrunner_01',[4],{'copy':[(4,0,380,1)],'hide':[(779,i)for i in [2,4,5,6,7]],'disable_actors':[1]}),
 'mateo':('wat_kab_foodshop_02',[95],{'keep':[(95,0,[3,296]),(3,0,[91]),(47,0,[141])],
     'copy':[(68,0,68,1)],'hide':[(21,0),(21,1)],'rename':{'q004_ready_to_reset_mateo_default':'PTFRB0S4MATEO_Reset'},
     'clear':[(91,0)],'disable_actors':[1,2]}),
 'fingers':('wbr_jpn_ripdoc_02',[1],{}),
 'viktor':('victor_vector_default',[1,640],{'copy':[(1,0,411,1),(411,0,411,1)],'hide':[(840,i)for i in [0,1,6,7]]+[(351,1)],
     'keep':[(1,0,[136,834]),(411,0,[136,834]),(411,1,[136,834])],'disable_actors':[]}),
 'karim':('mq023_03_street_vendor',[1116],{'disable_actors':[0]}),
 'ronald':('q302_05_bar',[920],{'hide':[(839,i)for i in [3,4,5]],'clear':[(4197,0)],
     'rename':{s:'PTFRB0S4RONALD_'+t for s,t in [('q302_caliente_ronald_lookat_loop','LookAt'),('q302_ronald_dialogue_active','Dialogue'),('q302_ronnie_reminder','Reminder')]},
     'disable_actors':[i for i in range(15) if i!=5]}),
 'bill':('sts_10_bill_default',[6],{'copy':[(140,0,92,0),(182,0,108,0)],'keep':[(140,0,[186,211]),(182,0,[230])],
     'disable_actors':[1]}),
}

def scene_delta(r,key):
    r=copy.deepcopy(r);ns=nodes(r);ops=SCENES[key][2]
    for a,o,b,p in ops.get('copy',[]): ns[a]['outputSockets'][o]['destinations']=copy.deepcopy(ns[b]['outputSockets'][p]['destinations'])
    for a,o,ids in ops.get('keep',[]):
        dest=ns[a]['outputSockets'][o]['destinations'];assert set(ids)<=set(d['nodeId']['id']for d in dest),(key,a,ids,dest)
        ns[a]['outputSockets'][o]['destinations']=[d for d in dest if d['nodeId']['id']in ids]
    for a,o in ops.get('clear',[]): ns[a]['outputSockets'][o]['destinations']=[]
    for a,o in ops.get('hide',[]):
        ns[a]['outputSockets'][o]['destinations']=[]
        base=1000000+a*100+o*5
        ns[a]['options'][o]['questCondition']={'HandleId':str(base),'Data':{
          '$type':'questLogicalCondition','operation':'AND','conditions':[
          {'HandleId':str(base+1+v*2),'Data':{'$type':'questFactsDBCondition','type':{'HandleId':str(base+2+v*2),'Data':{
          '$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRB0S4_Never','value':v}}}}for v in (0,1)]}}
    for v in walk(r):
        if isinstance(v.get('factName'),str) and v['factName'] in ops.get('rename',{}):v['factName']=ops['rename'][v['factName']]
        if v.get('$type')=='ResourcePath' and v.get('$value','').endswith('\\'+SCENES[key][0]+'.scene'):
            v['$value']='towercontinued\\b0_story_eight\\'+key+'.scene'
    for idx in ops.get('disable_actors',[]):
        a=r['actors'][idx]
        for v in walk(a):
            for k in ['isEnabled','spawnOnStart','alwaysSpawned','isAlwaysSpawned']:
                if k in v:v[k]=0
    return r

def scene_report():
    for key,(name,starts,ops) in SCENES.items():
        r=scene_delta(read(find(name+'.scene'))['Data']['RootChunk'],key);ns=nodes(r);rr=reach(ns,starts)
        writes=[(i,list(scalars(ns[i],'factName')))for i in sorted(rr) if ns[i].get('questNode',{}).get('Data',{}).get('$type')=='questFactsDBManagerNodeDefinition']
        special=[(i,ns[i]['questNode']['Data']['$type'],list(scalars(ns[i],'realPath')))for i in sorted(rr) if any(t in ns[i].get('questNode',{}).get('Data',{}).get('$type','')for t in ['Journal','Reward','Spawn','ItemManager'])]
        print(key,len(rr),'WRITES',writes,'SPECIAL',special)
        if len(sys.argv)>1 and sys.argv[1]==key:
            for i in sorted(rr):
                n=ns[i]; print(i,n['$type'],[[d['nodeId']['id']for d in o.get('destinations',[])]for o in n.get('outputSockets',[])],list(scalars(n.get('questNode',{}),'factName')))

def main():
    default='default_dialogs.questphase'
    specs=[
      ('nix',default,'root/node4/node37','nix_default_on', [('mq016_active','Equal',0)],['Out1']),
      ('yoko',default,'root/node7/node32/node3','wat_kab_netrunner_01_default_on',[],['Out1']),
      ('mateo',default,'root/node7/node32/node2','wat_kab_foodshop_02_default_on',[('q004_done','Greater',0)],['Out1']),
      ('fingers',default,'root/node7/node35','wbr_jpn_ripdoc_02_default_on',[('q105_fingers_killed','Equal',0),('q105_02_active','Equal',0)],[]),
      ('viktor',default,'root/node7/node33/node3','victor_vector_default_on',[],['Out1','terminate']),
      ('karim','mq023_quest_bugfixes.questphase','root/node23','wbr_jpn_cloth_02_default_on',[('mq023_done','Greater',0)],[]),
      ('ronald','q302_ronald_tree.questphase','root','q302_ronald_tree',[('q307_ep1_killed','Equal',1),('q302_done','Greater',0)],[]),
      ('bill','bill_default.questphase','root','bill_default_on',[('q307_ep1_killed','Equal',1),('sts_ep1_10_finished','Greater',0),('sts_ep1_10_dodger_dead','Greater',0),('wst_ep1_11_hotdog_finished','Greater',0)],['Out1']),
    ]
    sites=[];(OUT/'generated').mkdir(exist_ok=True)
    for key,file,route,gate,extra,outputs in specs:
        p=find(file);old=read(p)['Data']['RootChunk'];hs=handles(old);graphs={}
        def capture(g,rr):
            graphs[rr]={'nodes':list(nm(g)),'edges':edge_set(g,hs)}
            for i,n in nm(g).items():
                if n.get('phaseGraph'):capture(n['phaseGraph']['Data'],rr+'/node'+str(i))
        capture(graph_at(old,route),route)
        def subset(rr,keep,edges=None):
            g=graphs[rr];g['nodes']=keep
            g['edges']=edges if edges is not None else [e for e in g['edges']if e[0]in keep and e[2]in keep]
            for k in list(graphs):
                if k.startswith(rr+'/node') and int(k[len(rr+'/node'):].split('/')[0])not in keep:del graphs[k]
        if key=='fingers':
            subset(route,[0,3,17,21,23,25,26]);graphs[route]['edges'].append((0,'Out',17,'In'))
        if key=='karim':
            subset(route,[0,9,11]);graphs[route]['edges'].append((0,'Out',11,'In'))
        if key=='ronald':subset(route,[0,2,3,4,5,6,7,8,9,10,13])
        if key=='bill':
            subset('root',[0,5,6,20,22,29,31],[(0,'Out',6,'In'),(0,'Out',31,'In'),(0,'Out',22,'In'),(6,'Out',29,'In'),(31,'Out',20,'In1'),(20,'Out1',31,'In'),(22,'Out',5,'In')])
            subset('root/node20',[0,1,3,8],[(0,'Out',3,'dodger_dead'),(0,'Out',8,'In'),(8,'Out',1,'In')])
        # Counters splice only scene request and native departure edges; names don't imply actor spawning.
        counters=[]
        for rr,g in graphs.items():
            for e in g['edges']:
                n=nm(graph_at(old,rr))[e[2]]
                if n['$type']=='questSceneNodeDefinition' and e[3]!='CutDestination':
                    counters.append({'route':rr,'edge':e,'suffix':'SceneRequests'})
        exits={'nix':(route+'/node5',2),'yoko':(route+'/node11',None),'mateo':(route+'/node15',None),
               'fingers':(route+'/node3',27),'viktor':(route+'/node40',32),'karim':(route+'/node9/node9',15),
               'ronald':(route,4),'bill':('root/node20',8)}
        rr,nid=exits[key]
        if nid is None:
            # Native output is reached only after the leaf's departure cleanup.
            nmap=nm(graph_at(old,rr));oid=next(i for i,n in nmap.items()if n['$type']=='questOutputNodeDefinition')
            candidates=[e for e in graphs[rr]['edges']if e[2]==oid]
        else:candidates=[e for e in graphs[rr]['edges']if e[0]==nid and e[1]=='Out']
        assert candidates,(key,'departure')
        counters.append({'route':rr,'edge':candidates[0],'suffix':'Departures'})
        name,starts,ops=SCENES[key];sp=find(name+'.scene');dto=read(sp);sr=scene_delta(dto['Data']['RootChunk'],key)
        dto['Data']['RootChunk']=sr
        (OUT/'generated'/(key+'.scene.json')).write_text(json.dumps(dto,indent=2)+'\n')
        rrset=reach(nodes(sr),starts)
        disabled={(i<<8)|1 for i in ops.get('disable_actors',[])}
        used={v['id']for i in rrset for v in walk(nodes(sr)[i])if v.get('$type')=='scnPerformerId'}
        assert not(used&disabled),(key,'disabled actor remains reachable',used&disabled)
        writes={i:list(scalars(nodes(sr)[i],'factName'))for i in sorted(rrset)if nodes(sr)[i].get('questNode',{}).get('Data',{}).get('$type')=='questFactsDBManagerNodeDefinition'}
        assert not any(f.startswith(('q0','q1','q2','q3','mq','sq','wst_','sts_ep1_'))for v in writes.values()for f in v),(key,writes)
        assert not any('questRewardManager'in nodes(sr)[i].get('questNode',{}).get('Data',{}).get('$type','')for i in rrset)
        for i in rrset:
            if nodes(sr)[i].get('questNode',{}).get('Data',{}).get('$type')=='questJournalNodeDefinition':
                assert all('service_points/'in f for f in scalars(nodes(sr)[i],'realPath')),(key,i)
        rel=lambda p:str(p.relative_to(ROOT))
        raw=lambda p:rel(p).replace('json\\','raw\\').removesuffix('.json')
        guards=[(gate,'Greater',0)]+extra
        sites.append({'key':key,'label':key.title(),'prefix':'PTFRB0S4'+key.upper()+'_','owner_json':rel(p),'owner_raw':raw(p),'owner_sha256':sha(p),
          'route':route,'input_socket':'In1','output_sockets':outputs,'scene_json':rel(sp),'scene_raw':raw(sp),'scene_sha256':sha(sp),
          'scene':str(sp).split('json\\',1)[1].removesuffix('.json'),'starts':starts,'scene_ops':ops,'reachable':sorted(rrset),
          'scene_writes':writes,'gate':gate,'guards':guards,'graphs':graphs,'counters':counters})
    (OUT/'cohort.json').write_text(json.dumps({'common_guards':COMMON,'sites':sites},indent=2)+'\n')
    print('S4 scene reachability and exact owner scope:',[(s['key'],len(s['reachable']))for s in sites])

if __name__=='__main__':
    if len(sys.argv)>1:scene_report()
    else:main()
