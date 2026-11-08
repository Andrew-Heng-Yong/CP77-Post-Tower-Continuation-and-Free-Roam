"""UNEXECUTED coordinator helper recipe. Pure functions; no file/game I/O.

Coordinator must inspect, import with QR13 root on sys.path, verify input files
against the fresh manifest, and own all invocation/output/serialization. Worker B
has neither imported nor executed this module. This is not a runtime resource.
"""
import copy
from resource_edit import Edit,Resource,STANDARD,value

EXPECTED_NATIVE={
 r'base\quest\minor_quests\minorquests.questphase':'89E902A6BCC783325642A6DC6D1D856BB144651136C58D423FEA6B421EFCE85A',
 r'base\quest\cyberpunk2077.questphase':'78D8AFD0784575216B090F003610CA973BE9D1781BAB948C9E4DC12006D750B2',
 r'base\quest\bugfixing.questphase':'0C8B09F5C1A4553AC15DD4BD40B12EFE20F899817F708ECDC438B28646AC27BA',
 r'base\quest\bugfixing\quest_bugfixing.questphase':'A15ACF6C3824F0F947943138480131582D24BE69402EC82CD90D5D7B165D8D60',
 r'base\quest\minor_quests\mq037\mq037_brendan.questphase':'CEBDE896D88AEEBB927C59AA184830965DD22E1EDD19D716EC3558F78825EF0D',
 r'base\quest\minor_quests\mq037\scenes\mq037_01_brendan_scenes.scene':'4ED7F040BFBE1F424825AFF57C33FBB1C007D52D19243475C9543BD84A3514D2',
 r'base\quest\bugfixing\minor_quests\mq037\mq037_quest_bugfixes.questphase':'D272A7D9610FCE5A0C670A1BCBF30B4A9C4DDA23EF87467105A74759D80150F9',
}
def validate_provider_manifest(manifest):
    """Does not read paths. Coordinator first validates actual raw/json hashes."""
    resources=manifest['resources'];assert len(resources)==7
    assert {r['depot']for r in resources}==set(EXPECTED_NATIVE)
    assert all(r.get('decode_error')is None and r['sha256']==EXPECTED_NATIVE[r['depot']]for r in resources)
    return [{'depot':r['depot'],'sha256':r['sha256'],'json_sha256':r['json_sha256']}for r in resources]

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from _walk(v)
    elif isinstance(x,list):
        for v in x:yield from _walk(v)

def _raw_graph(resource,path):
    g=resource.d(resource.root['graph'])
    for part in path.split('/')[1:]:
        node=next(resource.d(h)for h in g['nodes']if resource.d(h)['id']==int(part))
        g=resource.d(node['phaseGraph'])
    return g

def _clone_graph(ed,source,path,models):
    """Deep clone payload handles; rebuild every nested edge from the source."""
    old=_raw_graph(source,path);g=ed.clone({k:v for k,v in old.items()if k!='nodes'},source);g['nodes']=[];nodes={}
    model=models['graphs'][path]
    for h in old['nodes']:
        n=source.d(h);ident=str(n['id']);p=ed.clone({k:v for k,v in n.items()if k not in ('sockets','phaseGraph')},source)
        nested=source.d(n.get('phaseGraph'))
        if isinstance(nested,dict)and'nodes'in nested:p['phaseGraph']=ed.h(_clone_graph(ed,source,path+'/'+ident,models))
        elif 'phaseGraph'in n:p['phaseGraph']=copy.deepcopy(n['phaseGraph'])
        nodes[ident]=ed.add(g,p,[(s['name'],s['type'])for s in model['nodes'][ident]['sockets']])
    for a,s,b,t in model['edges']:ed.link(nodes[a],s,nodes[b],t)
    return g

def _unlink_old(ed,a,s,b,t):
    x,sd=ed.socket(a,s);y,td=ed.socket(b,t);found=[]
    for h in sd['connections']:
        c=ed.r.d(h)
        if ed.r.hid(c['source'])==str(x)and ed.r.hid(c['destination'])==str(y):found.append(ed.r.hid(h))
    assert len(found)==1,('Expected one original edge',a['id'],s,b['id'],t)
    for data in (sd,td):data['connections']=[h for h in data['connections']if ed.r.hid(h)not in found]

def build_wrapper_document(wrapper_doc,native_bugfix_doc,plan,provider_manifest):
    """Return a newly modified in-memory doc. NO save/write/serialization call."""
    validate_provider_manifest(provider_manifest)
    # Snapshot original handles for safe common-guard copying before mutation.
    before=Resource(copy.deepcopy(wrapper_doc));bm=before.normalize();source=Resource(native_bugfix_doc);sm=source.normalize()
    assert not bm['errors']and not sm['errors']
    assert ['1004','True','1008','In']in bm['graphs']['root']['edges']
    ids=set(bm['graphs']['root']['nodes']);assert not ids&{str(i)for i in range(1100,1107)}
    assert any(s['name']=='CYB-661474_reinject'for s in sm['graphs']['root/38']['nodes']['75']['sockets'])
    assert not any(s['name']=='CYB-661474_reinject'for s in bm['graphs']['root']['nodes']['34']['sockets'])
    doc=copy.deepcopy(wrapper_doc);ed=Edit(doc);g=ed.graph('root')
    # Coordinator repair: original connection objects can own peer socket
    # definitions. Rebuild every root socket/edge before removing one edge.
    oldnodes={i:ed.node(g,int(i))for i in bm['graphs']['root']['nodes']}
    for i,n in oldnodes.items():
        n['sockets']=[ed.h({'$type':'questSocketDefinition','name':{'$type':'CName','$storage':'string','$value':s['name']},'type':s['type'],'connections':[]})for s in bm['graphs']['root']['nodes'][i]['sockets']]
    for a,s,b,t in bm['graphs']['root']['edges']:ed.link(oldnodes[a],s,oldnodes[b],t)
    ed.r=Resource(doc)
    original_condition=next(before.d(h)for h in _raw_graph(before,'root')['nodes']if before.d(h)['id']==1002)['condition']
    common_list=before.d(original_condition)['conditions']
    bugfix_graph=_raw_graph(source,'root/38');bn={n['id']:n for n in map(source.d,bugfix_graph['nodes'])}

    def earned_condition(include_actor=False):
        conditions=[];retained_facts=set()
        for cond in common_list:
            normalized=before.clean(cond);parts=list(_walk(normalized))
            if any(x.get('$type')=='questJournalEntryState_ConditionType'and x['path']['realPath'].startswith('quests/minor_quest/mq037_')for x in parts):continue
            facts=[x.get('factName')for x in parts if x.get('$type')=='questVarComparison_ConditionType']
            if any(f and(f.startswith('mq037_')or f=='hey_rey_techstore_01_default_on')for f in facts):continue
            conditions.append(ed.clone(cond,before));retained_facts.update(facts)
        required=dict(plan['required_fact_equalities']);required['hey_rey_techstore_01_default_on']=0
        required['mq037_vandal_painted_brendan']=0
        for name,number in required.items():
            if name not in retained_facts:conditions.append(ed.fact(name,number))
        for path,state in plan['required_earned_journals'].items():
            cls='gameJournalQuest'if path.count('/')==2 else'gameJournalQuestObjective'
            conditions.append(ed.journal(path,cls,state))
        if include_actor:conditions.append(ed.clone(bn[70]['condition'],source))
        return ed.logic('AND',conditions)

    # Preserve each complete original predicate as one OR arm, with original
    # handle IDs moved intact underneath the new logical wrapper.
    for ident in [1002,1004]:
        n=ed.node(g,ident);old=n['condition'];n['condition']=ed.logic('OR',[old,earned_condition()])
    selector=ed.add(g,{'$type':'questConditionNodeDefinition','id':1100,'condition':earned_condition()},[('CutDestination','CutDestination'),('In','Input'),('True','Output'),('False','Output')])
    actor_wait=ed.add(g,{'$type':'questPauseConditionNodeDefinition','id':1101,'condition':earned_condition(True)},STANDARD)
    p=ed.clone({k:v for k,v in bn[100].items()if k not in ('sockets','phaseGraph')},source);p['id']=1102;p['phaseGraph']=ed.h(_clone_graph(ed,source,'root/38/100',sm))
    injector=ed.add(g,p,[(s['name'],s['type'])for s in sm['graphs']['root/38']['nodes']['100']['sockets']])
    p=ed.clone({k:v for k,v in bn[101].items()if k!='sockets'},source);p['id']=1103
    loop=ed.add(g,p,[(s['name'],s['type'])for s in sm['graphs']['root/38']['nodes']['101']['sockets']])
    recheck=ed.add(g,{'$type':'questConditionNodeDefinition','id':1104,'condition':earned_condition(True)},[('CutDestination','CutDestination'),('In','Input'),('True','Output'),('False','Output')])
    claims=[]
    for ident,suffix in [(1105,'Issued'),(1106,'Entered')]:
        claims.append(ed.add(g,{'$type':'questFactsDBManagerNodeDefinition','id':ident,'type':ed.h({'$type':'questSetVar_NodeType','factName':'PTFRS23_MQ037_'+suffix,'setExactValue':1,'value':1})},STANDARD))
    body=ed.node(g,34)
    socket=next(source.d(h)for h in bn[75]['sockets']if value(source.d(h)['name'])=='CYB-661474_reinject')
    new_socket=ed.clone({k:v for k,v in socket.items()if k!='connections'},source);new_socket['connections']=[];body['sockets'].append(ed.h(new_socket))
    _unlink_old(ed,ed.node(g,1004),'True',ed.node(g,1008),'In')
    for a,s,b,t in [(ed.node(g,1004),'True',selector,'In'),(selector,'False',ed.node(g,1008),'In'),(selector,'True',actor_wait,'In'),(actor_wait,'Out',injector,'In1'),(injector,'inject_out',recheck,'In'),(injector,'loop_out',loop,'In'),(loop,'Out',actor_wait,'In'),(recheck,'False',ed.node(g,1002),'In'),(recheck,'True',claims[0],'In'),(claims[0],'Out',claims[1],'In'),(claims[1],'Out',body,'CYB-661474_reinject')]:ed.link(a,s,b,t)
    # Exact native safe_out is deliberately unconnected: aborts without claiming
    # ownership. Do not loop immediately while another scene/section is active.
    result=ed.ordered();after=Resource(result).normalize();assert not after['errors']
    for edge in bm['graphs']['root']['edges']:
        if edge!=['1004','True','1008','In']:assert edge in after['graphs']['root']['edges']
    for ident in ['1005','1006','1007','1008','54','80','55']:assert bm['graphs']['root']['nodes'][ident]['payload']==after['graphs']['root']['nodes'][ident]['payload']
    assert bm['graphs']['root']['nodes']['34']['payload']==after['graphs']['root']['nodes']['34']['payload']
    assert sm['graphs']['root/38/100']==after['graphs']['root/1102']
    return result

if __name__=='__main__':raise SystemExit('UNEXECUTED RECIPE: coordinator must inspect/import and own all output; no standalone action.')
