"""Read back native payloads, entry ownership, phone routing and progression."""
from common import *
import copy,importlib.util,re
spec=importlib.util.spec_from_file_location('rawcompare',ROOT/'prealpha/sidejobs_s27/raw_compare.py');rc=importlib.util.module_from_spec(spec);spec.loader.exec_module(rc)
folder=ROOT/'prealpha/sidejobs_s29/build/native_04';c=read(folder/'component.json');p=read(ROOT/c['prepared']);checks=0
def check(ok,why):
    global checks
    assert ok,why;checks+=1
def normalized(obj):
    hh=handles(obj);seen={}
    def visit(v):
        if isinstance(v,list):return [visit(x) for x in v]
        if not isinstance(v,dict):return v
        key=v.get('HandleId',v.get('HandleRefId'))
        if key is not None and key in hh:
            if key in seen:return {'ref':seen[key]}
            seen[key]=len(seen);return {'handle':seen[key],'value':visit(hh[key])}
        if v.get('$type')=='TweakDBID':return rc.canonical(v)
        return {k:visit(v[k]) for k in sorted(v)}
    return visit(obj)
def graphs(obj):
    r=SafeResource(obj);return {g['path']:g for g in flatten(r,obj['Data']['RootChunk'])}
def rb(dep):return read(folder/'readback'/(dep+'.json'))
def index(g):return {n['id']:n for n in g['nodes']}
for f,h in c['source_pins'].items():check(sha(ROOT/f)==h,('pin',f))
for d,h in c['resources'].items():check(sha(folder/'source'/d)==h,('resource',d))
check(len(c['boots'])==23 and len(set(c['boots']))==23,'16 entries plus 7 phone supports')
check(len(p['jobs'])==16 and sum(len(j['journal_ids']) for j in p['jobs'])==18,'all requested journal entries')
check(c['official_overrides']==[] and c['mod_overrides']==[r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'],'one scoped PTFR cleanup override')
transforms={t['depot']:t for t in c['transforms']}
for inp in p['inputs']:
    exp=read(ROOT/inp['expected']);act=rb(inp['depot'])
    if inp['depot'] not in transforms:
        check(normalized(exp['Data'])==normalized(act['Data']),('exact serialization',inp['depot']))
        continue
    t=transforms[inp['depot']];old=graphs(exp);new=graphs(act)
    er=copy.deepcopy(old)
    if t['kind']=='subset':
        keep=set(t['ids']);er={gp:g for gp,g in er.items() if gp=='root' or int(gp.split('/')[1]) in keep}
        er['root']['nodes']=[n for n in er['root']['nodes'] if n['id'] in keep]
        er['root']['nodes'].append({'$type':'questInputNodeDefinition','id':65000,'socketName':{'$type':'CName','$storage':'string','$value':'In1'}})
        er['root']['edges']=sorted(t['edges'])
    else:
        gp=t['graph'];eg=er[gp];an=index(new[gp]);eg['edges'].remove(t['edge'])
        if t['kind']=='nix_release':
            check(an[64000]['type']=={'$type':'questSetVar_NodeType','factName':'nix_default_on','setExactValue':1,'value':0},'native Nix availability release only')
            check({v['factName']:v['value'] for v in walk(an[64001]) if v.get('$type')=='questVarComparison_ConditionType'}=={'nix_default_on':0,'PTFRB0S4NIX_OwnerActive':0},'actual Nix release acknowledgement')
            eg['edges'] += [[6,'Out',64000,'In'],[64000,'Out',64001,'In'],[64001,'Out',3,'In1']]
        else:
            check({v['factName']:v['value'] for v in walk(an[64000]) if v.get('$type')=='questVarComparison_ConditionType'}=={'elcoyote_barman_default_on':0,'PTFRB0STPEPE_OwnerActive':0},'actual Pepe release acknowledgement')
            eg['edges'] += [[11,'Out',64000,'In'],[64000,'Out',2,'In']]
        eg['edges'].sort();eg['nodes'] += [an[i] for i in t['nodes']]
    check(set(er)==set(new),('retained nested graphs',inp['depot']))
    for gp,g in er.items():
        check(index(g)==index(new[gp]) and g['edges']==new[gp]['edges'],('exact phase delta',inp['depot'],gp))
    check(normalized({k:v for k,v in exp['Data']['RootChunk'].items() if k!='graph'})==normalized({k:v for k,v in act['Data']['RootChunk'].items() if k!='graph'}),('root prefab metadata',inp['depot']))
# Whole native trees preserve their dialog, objective and reward nodes. Copies
# may change resource references or the documented Johnny presentation only.
for inp in p['inputs']:
    if not inp['depot'].endswith('.scene'):continue
    original=read(ROOT/p['index'][inp['native']]['json']);expected=read(ROOT/inp['expected'])
    a=original['Data']['RootChunk'];b=expected['Data']['RootChunk']
    for key in ['actors','playerActors','dialogLineCollection','locStore','screenplayStore']:
        if key in a:check(normalized(a[key])==normalized(b[key]),('cast and spoken content',inp['native'],key))
    ah=handles(original);bh=handles(expected)
    an=[deref(x,ah) for x in a['sceneGraph']['Data']['graph']];bn=[deref(x,bh) for x in b['sceneGraph']['Data']['graph']]
    check([n['nodeId'] for n in an]==[n['nodeId'] for n in bn],('scene node IDs unchanged',inp['native']))
    performers={(x['actorId']['id']<<8)|1 for x in a['actors'] if x['actorName'].lower() in ['johnny','silverhand']}
    for old,new in zip(an,bn):
        # Dialog events and all narrative event types retain their timing/data.
        def narrative(n,hh):return [deref(e,hh) for e in n.get('events',[]) if deref(e,hh).get('$type') not in ['scnPlaySkAnimEvent','scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent']]
        # Normalize full documents so shared definitions remain available.
        check(len(narrative(old,ah))==len(narrative(new,bh)),('narrative events retained',inp['native'],old['nodeId']))
        oe={deref(e,ah)['id']['id']:deref(e,ah) for e in old.get('events',[])};ne={deref(e,bh)['id']['id']:deref(e,bh) for e in new.get('events',[])}
        for k in oe.keys()-ne.keys():check(oe[k].get('performerId',{}).get('id') in performers and oe[k]['$type'] in ['scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent'],('only Johnny visual events removed',inp['native'],k))
        check(ne.keys()<=oe.keys(),'no invented scene events')
for rec in c['recipes']:
    j=next(j for j in p['jobs'] if j['id']==rec['id']);gs=graphs(rb(rec['depot']));g=gs['root'];ns=index(g)
    check(g['edges']==sorted(rec['edges']),('entry edge readback',j['id']))
    check(ns[65003]['condition']==ns[65004]['condition'],('atomic native recheck',j['id']))
    pairs={v['factName']:v['value'] for v in walk(ns[65003]['condition']) if v.get('$type')=='questVarComparison_ConditionType' and v['comparisonType']=='Equal'}
    for f,v in rec['guard'].items():check(pairs.get(f)==v,('guard',j['id'],f))
    check(pairs[j['tag']+'_Issued']==0 and pairs[j['tag']+'_Permit']==1,'one durable claim')
    check([65004,'True',65005,'In'] in g['edges'] and [65004,'False',65003,'In'] in g['edges'],'synchronous claim and retry')
    check([65006,'Out',rec['child'],j['input']] in g['edges'],'normal child port')
    journals={(v['path']['realPath'],value(v['path']['className']),v['state']) for v in walk(ns[65003]['condition']) if v.get('$type')=='questJournalEntryState_ConditionType'}
    check(journals=={(x['path'],x['class'],{1:'Inactive',3:'Succeeded'}[x['states'][0]]) for x in j['journals']},('runtime/native journals',j['id']))
    if j['parent']:
        old=graphset(j['parent']['depot']);oldnodes=index(old['root'])
        for ident in j['parent']['ids']:
            ex=copy.deepcopy(oldnodes[ident])
            if ident==rec['child']:ex['phaseResource']['DepotPath']['$value']=j['private_native']
            check(ex==ns[ident],('normal parent payload',j['id'],ident))
    check(not any(v.get('$type')=='questSetVar_NodeType' and not v['factName'].startswith('PTFR') for n in ns.values() if n['id']>=65000 for v in walk(n)),'no new story writes in wrapper')
old=graphs(read(ROOT/'prealpha/sidejobs_s27/build/s27_03/readback/towercontinued_gig_phone_u9_fixer_cleanup.questphase.json'))
new=graphs(rb(r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'))
on=index(old['root']);nn=index(new['root'])
for i,n in on.items():check(n==nn[i],('old phone cleanup payload',i))
oe=copy.deepcopy(old['root']['edges']);changed=0
for e in oe:
    if e[0] in [1011,1002,1003] and e[2]==6:e[2]=1240;e[3]='In';changed+=1
check(changed==3 and all(e in new['root']['edges'] for e in oe),'existing cleanup routing retained')
for ctc in p['contacts']:
    dep='towercontinued\\sidejobs_s29\\phone\\'+ctc['name']+'.questphase';g=graphs(rb(dep))['root'];ns=index(g)
    facts={v['factName']:v['value'] for v in walk(ns[1003]['condition']) if v.get('$type')=='questVarComparison_ConditionType'}
    claim='PTFRS22_SQ025_SupportIssued' if ctc['name']=='delamain' else 'PTFRS29_PHONE_'+ctc['name']+'_Issued'
    check(facts[claim]==0 and ns[1004]['type']['factName']==claim,'shared phone claim identity')
    check(not any('count' in f or '_Issued' in f and f==('PTFRS29_'+ctc['consumer']+'_Issued') and v!=0 for f,v in facts.items()),'no historical counter balance or circular owner admission')
    check(ns[1002]['condition']==ns[1003]['condition'],'phone synchronous recheck')
    check([1004,'Out',ctc['init'],'In1'] in g['edges'],'original controller input')
    if ctc['name']=='delamain':check(all('holo_'+n+'_calls_v_active' in facts for n in ['delamain','delamain_angry','delamain_sad','delamain_mean','delamain_manic','delamain_scared','delamain_deep','delamain_suicidal']),'all Delamain contacts idle')
rt=ROOT/'prealpha/sidejobs_s29/runtime_06';text=(rt/'SideJobsS29.reds').read_text();m=read(rt/'manifest.json')
check(sha(Path(m['installed_snapshot']))==m['before'],'installed snapshot baseline')
check('this.rows[i].states[0]==1' in (rt/'SnapshotStateHS1.reds').read_text(),'active/completed/failed baseline denied')
check('this.Own(i, "Issued") != 0' in text and 'Separate consecutive ticks' in text and 'GameplayReleased' in text,'readiness and repeat guard')
check('SetFactStr(name, value)' in text and len(re.findall(r'\.SetFact',text))==1,'runtime writes only owned Permit')
out=folder/'tests_01.json';check(not out.exists(),'immutable test evidence')
report=dict(status='PASS_OFFLINE_NOT_GAMEPLAY',checks=checks,component_sha256=sha(folder/'component.json'),tester_sha256=sha(__file__),limitations=['Engine scene, inventory escrow, quest completion and save reload require user testing.','Unsupported existing progress is preserved and deferred, never reconstructed by replay.'])
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
