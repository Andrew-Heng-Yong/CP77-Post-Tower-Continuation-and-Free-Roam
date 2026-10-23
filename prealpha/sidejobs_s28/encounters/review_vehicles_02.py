"""Independent, read-only S28 vehicle admission and private presentation review."""
import argparse, copy, hashlib, json, re, sys, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x, dict):
        yield x
        for y in x.values(): yield from walk(y)
    elif isinstance(x, list):
        for y in x: yield from walk(y)
def value(x): return x.get('$value') if isinstance(x, dict) else x
def norm(x):
    if isinstance(x, list): return [norm(v) for v in x]
    if isinstance(x, dict):
        if x.get('$type') == 'TweakDBID':
            if 'hash' in x: n = x['hash']
            elif x['$storage'] == 'string':
                b = x['$value'].encode(); n = zlib.crc32(b) | (len(b) << 32)
            else: n = int(x['$value'])
            return {'$type':'TweakDBID', 'hash':int(n)}
        return {k:norm(v) for k,v in x.items()}
    return x
def graphs(p):
    r = SafeResource(read(p)); return {g['path']:g for g in flatten(r, r.obj['Data']['RootChunk'])}
def node(gs, g, n): return next(v for v in gs[g]['nodes'] if v['id'] == n)
def paired(raw): return raw.replace('/raw/', '/json/') + '.json'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--component', required=True)
    ap.add_argument('--runtime', required=True); ap.add_argument('--output', required=True)
    args = ap.parse_args(); cp=ROOT/args.component; folder=cp.parent; runtime=ROOT/args.runtime
    output=ROOT/args.output; assert not output.exists(), 'Use a new immutable review output'
    c=read(cp); ct=read(ROOT/c['contract']); manifest=read(runtime/'manifest.json')
    pins={}; checks=[]; cases=0
    def pin(p):
        p=Path(p); p=p if p.is_absolute() else ROOT/p
        pins[p.relative_to(ROOT).as_posix()]=sha(p)
    def check(b, label):
        assert b, label
        checks.append(label)
    for p in [cp, ROOT/c['contract'], runtime/'manifest.json', runtime/'SideJobsS28.reds', Path(__file__)]: pin(p)
    for p,h in c['source_pins'].items():
        check(sha(ROOT/p)==h, 'component source pin: '+p); pin(p)
    for dep,h in c['resources'].items():
        p=folder/'source'/dep; check(sha(p)==h, 'built resource: '+dep); pin(p)
    for p,h in manifest['source_pins'].items(): check(sha(ROOT/p)==h, 'runtime source pin: '+p); pin(p)
    check(sha(runtime/'SideJobsS28.reds')==manifest['files']['SideJobsS28.reds'], 'actual generated runtime bound')
    check(c['native_runtime_predicates']==ct['native_runtime_predicates']==manifest['native_runtime_predicates'], 'native/runtime predicate agreement')
    check(len(c['resources'])==12 and len(c['boots'])==2 and not c['official_overrides'] and not c['mod_overrides'], 'two private native entries; no overrides')
    script=(runtime/'SideJobsS28.reds').read_text()
    common=['let player = context as PlayerPuppet;', 'players.GetLocalPlayerMainGameObject() as PlayerPuppet',
            '!IsDefined(localPlayer) || player != localPlayer || player.IsReplacer()']
    for key,p in ct['native_runtime_predicates'].items():
        cls=p['class'].split('.')[-1]
        match=re.search(r'public class '+re.escape(cls)+r' extends IScriptablePrereq \{(.*?)\n\}', script, re.S)
        check(match is not None, 'native class exists: '+cls); body=match[1]
        check(all(s in body for s in common), 'local non-replacer player required: '+cls)
        check('public const func IsFulfilled(game: GameInstance, context: ref<IScriptable>) -> Bool' in body, 'read-only native predicate signature: '+cls)
        check(not any(s in body for s in ['SetFact','GiveItem','AddItem','EnablePlayerVehicle','SetItemQuantity']), 'predicate has no entitlement writes: '+cls)
        if p['kind']=='vehicle_unowned':
            check('!IsDefined(player) || !IsDefined(players) || !IsDefined(vehicles)' in body, 'unknown vehicle context refuses: '+cls)
            check('return !vehicles.IsVehiclePlayerUnlocked(TDBID.Create("'+p['record']+'"));' in body, 'exact durable ownership query: '+cls)
        else:
            check(p['unloaded']=='DEFER', 'unloaded world key policy')
            check('!IsDefined(player) || !IsDefined(players) || !IsDefined(transaction)' in body, 'unknown transaction context refuses')
            check('CreateNodeRef("'+p['node_ref']+'")' in body, 'exact absolute crate lookup')
            check('ResolveNodeRef(crateRef, Cast<GlobalNodeRef>(GlobalNodeID.GetRoot()))' in body, 'global crate context')
            check('FindEntityByID(game, Cast<EntityID>(globalRef)) as GameObject' in body and 'if !IsDefined(crate) { return false; }' in body, 'unloaded crate refuses without spawning')
            check('return transaction.GetItemQuantity(crate, ItemID.CreateQuery(TDBID.Create("'+p['record']+'"))) == 0;' in body, 'typed variant-safe exact crate quantity zero')
    for rec in c['recipes']:
        o=next(x for x in ct['owners'] if x['id']==rec['id']); rp=folder/rec['readback']; pin(rp)
        check(sha(rp)==rec['readback_sha256'], 'entry readback bound: '+o['id'])
        gs=graphs(rp); ns={n['id']:n for n in gs['root']['nodes']}; edges=gs['root']['edges']; cond=ns[4]['condition']
        check(set(gs)=={'root'}, 'no hidden embedded restart graph: '+o['id'])
        check(cond['$type']=='questLogicalCondition' and cond['operation']=='AND', 'all admission restrictions conjunctive: '+o['id'])
        expected_edges=[[0,'Out',1,'In'],[1,'Out',2,'In'],[2,'Out',3,'In'],[3,'Out',4,'In'],[4,'False',3,'In'],[4,'True',5,'In'],[6,'Out',100,'In1'],[100,'Out1',101,'In']]
        if o['id']=='mq050_ken_block_tribute':
            expected_edges += [[5,'Out',90,'In'],[90,'Out',6,'In']]
            check(ns[90]['condition']=={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'q101_done','value':0}}, 'original q101 pause already implied by preclaim admission')
        else: expected_edges += [[5,'Out',6,'In']]
        check(edges==sorted(expected_edges), 'claim precedes exactly one normal main entry: '+o['id'])
        check(ns[3]['condition']['type']=={'$type':'questRealtimeDelay_ConditionType','hours':0,'miliseconds':0,'minutes':0,'seconds':1}, 'false admission retries without native main: '+o['id'])
        parent=graphs(ROOT/paired(rec['parent']['raw'])); want=copy.deepcopy(node(parent,rec['parent']['graph'],rec['parent']['node']))
        want['id']=100; want['phaseResource']['DepotPath']['$value']=rec['private_native']
        check(ns[100]==want, 'original child context and input payload: '+o['id'])
        check(not any('prefab' in k.lower() and v for k,v in read(rp)['Data']['RootChunk'].items() if k!='graph'), 'wrapper has no preclaim prefab activation: '+o['id'])
        js=[v for v in walk(cond) if v.get('$type')=='questJournalEntryState_ConditionType']
        check({(v['path']['realPath'],value(v['path']['className']),v['state']) for v in js}=={(j['path'],j['class'],'Inactive') for j in o['journals']}, 'all own root and descendant progress protected: '+o['id'])
        facts=[v for v in walk(cond) if v.get('$type')=='questVarComparison_ConditionType']
        required={**ct['common_equal'],**o['facts_equal'],**{o['tag']+'_'+s:0 for s in ['Issued','Entered','Finished','Fault']},**{o['tag']+'_'+s:1 for s in ['Ready','Revision','Permit']}}
        check({v['factName']:v['value'] for v in facts if v['comparisonType']=='Equal'}==required, 'source freshness and private owner guards complete: '+o['id'])
        check({(v['factName'],v['comparisonType'],v['value']) for v in facts if v['comparisonType']!='Equal'}=={(k,op,r[bound]) for k,r in o['fact_ranges'].items() for op,bound in [('GreaterOrEqual','min'),('LessOrEqual','max')]}, 'exact prerequisite range: '+o['id'])
        raw_prereqs=[v for v in walk(read(rp)) if v.get('$type')=='DynamicBaseClass']
        check([v['$className'] for v in raw_prereqs]==o['native_predicates'] and all(set(v)=={'$type','$className'} for v in raw_prereqs), 'actual CR2W native RTTI names and no serialized override fields: '+o['id'])
        ps=[v for v in walk(cond) if v.get('$type')=='questPrereq_ConditionType']
        check([v['prereq']['$className'] for v in ps]==o['native_predicates'] and all(v['isObjectPlayer']==1 for v in ps), 'immediate player predicates inside AND: '+o['id'])
        writes=[v for v in walk(ns) if v.get('$type')=='questSetVar_NodeType']
        check({v['factName'] for v in writes}=={o['tag']+'_'+s for s in ['Ready','Revision','Issued','Entered','Finished']} and all(v['value']==1 and v['setExactValue']==1 for v in writes), 'only monotonic private ownership writes: '+o['id'])
        # Evaluate actual decoded admission AST, including every unknown and progressed case.
        sample={'facts':{**required,**{k:r['min'] for k,r in o['fact_ranges'].items()}},'journals':{j['path']:'Inactive' for j in o['journals']},'inventory':0,'available':False,'spawned':False,'scripts':{p:True for p in o['native_predicates']}}
        def evaluate(x,s):
            t=x['$type']
            if t=='questLogicalCondition':
                vals=[evaluate(v,s) for v in x['conditions']]
                return all(vals) if x['operation']=='AND' else not any(vals) if x['operation']=='NOR' else (_ for _ in ()).throw(AssertionError('unsupported logical operator'))
            if 'type' in x: return evaluate(x['type'],s)
            if t=='questVarComparison_ConditionType':
                v=s['facts'].get(x['factName']); n=x['value']; op=x['comparisonType']
                return v is not None and {'Equal':lambda:v==n,'GreaterOrEqual':lambda:v>=n,'LessOrEqual':lambda:v<=n}[op]()
            if t=='questJournalEntryState_ConditionType': return s['journals'].get(x['path']['realPath'])==x['state']
            if t=='questPrereq_ConditionType': return s['scripts'].get(x['prereq']['$className']) is True
            if t=='questInventory_ConditionType': return s['inventory']==0 and x['quantity']==0 and x['comparisonType']=='Equal' and x['isPlayer']==1
            if t=='questVehicleAvailable_ConditionType': return s['available']
            if t=='questVehicleSpawned_ConditionType': return s['spawned']
            raise AssertionError(t)
        check(evaluate(cond,sample), 'native positive admission fixture: '+o['id']); cases+=1
        for group in ['facts','journals','scripts']:
            for key,base in sample[group].items():
                options=[None, base+1 if base==0 else 0] if group=='facts' else [None,'Active','Succeeded','Failed'] if group=='journals' else [None,False]
                for val in options:
                    s=copy.deepcopy(sample);s[group][key]=val
                    check(not evaluate(cond,s), 'native contradiction refuses '+o['id']+' '+group+' '+key+' '+str(val));cases+=1
        for group in (['available','spawned','inventory'] if o['inventory_zero'] else ['available']):
            s=copy.deepcopy(sample);s[group]=1
            check(not evaluate(cond,s), 'native retained entitlement refuses '+o['id']+' '+group);cases+=1
    pres=read(ROOT/'research/sidejobs_s28/vehicles/presentation_01.json');pin('research/sidejobs_s28/vehicles/presentation_01.json')
    for inp in c['presentation']['inputs']:
        actual_path=folder/'readback'/(inp['depot'].rsplit('\\',1)[-1]+'.json');pin(actual_path);pin(inp['original'])
        actual=read(actual_path)['Data']; expected=copy.deepcopy(read(ROOT/inp['original'])['Data'])
        if inp['kind']=='workspot':
            hubs=[v for v in walk(expected) if v.get('$type')=='animAnimNode_WorkspotHub']
            check(len(hubs)==1 and hubs[0]['eventFilterType']=='Default', 'one original workspot hub: '+inp['depot']);hubs[0]['eventFilterType']='Mute'
            check(all(not v.get('initialActions') and not v.get('globalProps') for v in walk(expected)), 'no independent initial workspot items: '+inp['depot'])
        elif inp['kind']=='phase':
            allowed={v['old']:v['new'] for v in inp['replacements']};seen=[]
            for v in walk(expected):
                if 'DepotPath' in v and value(v['DepotPath']) in allowed:
                    old=value(v['DepotPath']);seen.append(old);v['DepotPath']['$value']=allowed[old]
            check(sorted(seen)==sorted(v['old'] for v in inp['replacements']), 'exact reference-only ancestor cloning: '+inp['depot'])
        else:
            root=expected['RootChunk']; actualroot=actual['RootChunk']; donor=read(ROOT/inp['donor'])['Data']['RootChunk'];pin(inp['donor'])
            actor=next(v for v in root['actors'] if v['actorId']['id']==0)
            check(actor['acquisitionPlan']=='spawnDespawn' and value(actor['spawnDespawnParams']['specRecordId'])=='Character.Silverhand', 'JV1-compatible actual Johnny actor: '+inp['depot'])
            use=next(v for v in walk(root) if v.get('$type')=='questUseWorkspotNodeDefinition' and v['id']==inp['node']); param=use['paramsV1']['Data']
            check(value(param['workspotNode'])==inp['anchor'] and value(use['entityReference']['dynamicEntityUniqueName'])==value(actor['spawnDespawnParams']['dynamicEntityUniqueName']), 'original command targets Johnny and original anchor: '+inp['depot'])
            check(not root['workspots'] and not root['workspotInstances'], 'private mapping does not replace existing scene mappings: '+inp['depot'])
            template=next(v for v in walk(donor) if v.get('$type')=='scnUseSceneWorkspotParamsV1')
            param['$type']='scnUseSceneWorkspotParamsV1'
            for k in ['itemOverride','playAtActorLocation','workspotInstanceId']:param[k]=copy.deepcopy(template[k])
            param['workspotInstanceId']['id']=65000;param['workspotNode']={'$type':'NodeRef','$storage':'uint64','$value':'0'}
            check(param['playAtActorLocation']==0 and param['itemOverride']['itemOverrides']==param['itemOverride']['propOverrides']==[], 'anchored playback with no item overrides: '+inp['depot'])
            inst=copy.deepcopy(next(v for v in donor['workspotInstances'] if v['workspotInstanceId']['id']==712))
            inst['dataId']['id']=4282800001;inst['workspotInstanceId']['id']=65000;inst['originMarker']['nodeRef']['$value']=inp['anchor'];inst['localTransform']=copy.deepcopy(actor['spawnDespawnParams']['spawnOffset'])
            check(inst['playAtActorLocation']==0 and inst['originMarker']['type']=='Global' and inst['localTransform']=={'$type':'Transform','orientation':{'$type':'Quaternion','i':0,'j':0,'k':0,'r':1},'position':{'$type':'Vector4','W':0,'X':0,'Y':0,'Z':0}}, 'same world anchor and identity offset: '+inp['depot'])
            data=copy.deepcopy(next(v for v in walk(donor) if v.get('$type')=='scnWorkspotData_ExternalWorkspotResource'));data['dataId']['id']=4282800001;data['workspotResource']['DepotPath']={'$type':'ResourcePath','$storage':'string','$value':inp['workspot']}
            handle=max(int(v['HandleId']) for v in walk(expected) if 'HandleId' in v)+1
            root['workspotInstances']=[inst];root['workspots']=[{'HandleId':str(handle),'Data':data}]
            for v in walk(root):
                if v.get('$type')=='scnPlaySkAnimEvent' and v.get('performer',{}).get('id')==1:
                    check(v['muteAnimEvents']=='0', 'original Johnny body event only');v['muteAnimEvents']='STANDARD'
            rows=[v for v in pres['world_references'] if v['name']=='{'+inp['anchor'][1:]+'}'];check(bool(rows),'current world anchor witnesses exist')
            for row in rows:
                pin(row['raw']);pin(row['json']); world=read(ROOT/row['json'])
                hits=[v for v in walk(world) if v.get('$type')=='worldAISpotNode' and value(v.get('debugName'))==row['name']]
                check(len(hits)==1 and value(hits[0]['spot']['Data']['resource']['DepotPath'])==row['workspot'], 'exact current anchor/workspot correspondence: '+row['raw'])
        check(norm(actual)==norm(expected), 'entire decoded native Data has only reviewed changes: '+inp['depot'])
    world='research/sidejobs_s28/vehicles/world_03/json/ep1_1_nightcity_always_loaded_2.streamingsector.json';pin(world);pin(world.replace('/json/','/raw/').removesuffix('.json'))
    crate=ct['native_runtime_predicates']['hoon_world_key']
    check(sum(v.get('$type')=='NodeRef' and value(v)==crate['node_ref'] for v in walk(read(ROOT/world)))==1, 'absolute original Hoon crate occurs once in current compiled world')
    raw=ct['native_resources'][crate['native_target_witness']['depot']]['raw'];n=node(graphs(ROOT/paired(raw)),'root',51)
    check(any(v.get('$type')=='questInjectLoot_NodeTypeParams_OperationData' and v['quantity']==1 and norm(v['itemTDBID'])['hash']==int(crate['hash']) for v in walk(n)), 'native key inject identity and quantity retained')
    check(any(v.get('$type')=='NodeRef' and value(v)=='#mq050_main_loot' for v in walk(n)), 'crate guard protects actual native reward injection owner')
    result={'status':'PASS_INDEPENDENT_VEHICLE_ADMISSION_AND_PRESENTATION','component':args.component,'component_sha256':sha(cp),'runtime':args.runtime,'runtime_sha256':sha(runtime/'SideJobsS28.reds'),'checks':len(checks),'policy_cases':cases,'source_pins':pins,'verifier_sha256':sha(__file__),'assertions':checks,'limitations':['Read-only source and decoded payload review; no engine liveness or gameplay claim.','Hoon requires the original world crate loaded and empty; unknown or retained-progress states defer.','Unsupported unfinished states are preserved, not restarted.','Current archive/packed-resource validation and full compilation are integration responsibilities.']}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['source_pins','assertions']}))

if __name__=='__main__': main()
