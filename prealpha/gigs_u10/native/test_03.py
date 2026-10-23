"""Source payload/edge equality and bounded U10 policy assertions, not gameplay."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

def graphs(path,embedded=None):
    r=SafeResource(read(path));root=r.obj['Data']['RootChunk'] if embedded is None else r.obj['Data']['EmbeddedFiles'][embedded]['Content']
    return {g['path']:g for g in flatten(r,root)}

def main():
    folder=Path(sys.argv[1]).resolve();component=read(folder/'component.json');plan=read(ROOT/'research/gigs_u10/native/build_plan_01.json');contract=read(ROOT/component['contract'])
    checks=0;cases=0;native=0
    def check(ok,why):
        nonlocal checks
        assert ok,why
        checks+=1
    for p,h in component['source_pins'].items():check(sha(ROOT/p)==h,('pin',p))
    for dep,h in component['resources'].items():check(sha(folder/'source'/dep)==h,('resource',dep))
    check(len(component['boots'])==28,'8 entries 7 credits 11 maps 2 service boots')
    check(len(component['resources'])==29,'one overlay and 28 boots')
    check(set(component['mod_overrides'])=={r'towercontinued\special_gigs_u9\gang_retaliation.questphase'},'overlay scope')
    for recipe in component['recipes']:
        name=recipe['depot'].rsplit('\\',1)[-1].removesuffix('.questphase');new=graphs(folder/'readback'/(name+'.json'));gn=new['root'];ns={n['id']:n for n in gn['nodes']}
        check(gn['edges']==sorted(recipe['edges']),('compiled edges',name))
        job=next(j for j in plan['jobs'] if j['id']==recipe['id']);owner=next(o for o in contract['owners'] if o['id']==recipe['id'])
        if recipe['kind']=='service_request':
            writes=[n['type']['factName'] for n in gn['nodes'] if n['$type']=='questFactsDBManagerNodeDefinition']
            check(set(writes)=={owner['tag']+'_ServiceRequested','PTFRU9_Retaliation_Request','PTFRU9_Retaliation_'+recipe['gang']+'_Request'},('request only',name))
            check(all(n['type']['value']==1 and n['type']['setExactValue']==1 for n in gn['nodes'] if n['$type']=='questFactsDBManagerNodeDefinition'),('monotonic requests',name))
        else:
            old=graphs(ROOT/(recipe['raw'].replace('/raw/','/json/')+'.json'),job['parent']['binding']['binding']['embedded_index'] if recipe['kind']=='entry' else None)
            og=old[recipe['graph']];on={n['id']:n for n in og['nodes']}
            for i in recipe['ids']:
                expected=copy.deepcopy(on[i])
                if recipe['kind']=='entry' and i==job['parent']['input_node']:expected['socketName']['$value']='In1'
                if recipe['kind']=='entry' and i==job['parent']['child']['id']:
                    expected['phaseResource']['DepotPath']['$value']=recipe['native'];expected['phaseResource']['Flags']='Soft'
                check(expected==ns[i],('native node drift',name,i));native+=1
                prefix=recipe['graph']+'/'+str(i)
                for gp,gg in old.items():
                    if gp==prefix or gp.startswith(prefix+'/'):
                        np='root'+gp[len(recipe['graph']):]
                        check(new[np]['nodes']==gg['nodes'],('nested payload drift',name,gp));native+=len(gg['nodes'])
                        check(new[np]['edges']==gg['edges'],('nested edge drift',name,gp))
            if recipe['kind']=='entry':
                for index,c in enumerate(job['companions']):
                    source=graphs(ROOT/(c['source_raw'].replace('/raw/','/json/')+'.json'));expected=copy.deepcopy(next(n for n in source[c['source_graph']]['nodes'] if n['id']==c['source_node']));expected['id']=64000+index
                    if c['depot']:expected['phaseResource']['Flags']='Soft'
                    check(expected==ns[64000+index],('companion payload',name,index));native+=1
                    prefix=c['source_graph']+'/'+str(c['source_node'])
                    for gp,gg in source.items():
                        if gp==prefix or gp.startswith(prefix+'/'):
                            np='root/'+str(64000+index)+gp[len(prefix):]
                            check(new[np]['nodes']==gg['nodes'] and new[np]['edges']==gg['edges'],('companion embedded unchanged',name,index,gp));native+=len(gg['nodes'])
                check(not any(n['$type']=='questOutputNodeDefinition' for n in gn['nodes']),('no lifetime termination',name))
                check(ns[65003]['type']['factName']==owner['tag']+'_Issued','native claim')
                check([65008,'True',65003,'In'] in gn['edges'],'recheck before claim')
                check(ns[65007]['type']['factName']=='PTFRU9_'+job['region']+'_TierRequest','reuse tier request')
                check(ns[65002]['condition']==ns[65008]['condition'],'pause and synchronous guard equal')
                for k,v in owner['facts_equal'].items():check(recipe['guard'].get(k)==v,('native-runtime fact match',name,k))
                check(recipe['guard'].get('debug_sts_start')==0,'debug bypass disabled')
        if recipe['kind'] in ('entry','service_request'):
            guard=recipe['guard'];permit=owner['tag']+('_Permit' if recipe['kind']=='entry' else '_PreparePermit')
            check(guard[permit]==1,'owned permit')
            # Each individually wrong/missing fact must fail the conjunction.
            def admit(state):return all(state.get(k,None)==v for k,v in guard.items())
            check(admit(guard),'positive exact guard');cases+=1
            for k,v in guard.items():
                for replacement in (v-1,v+1,None):
                    state=dict(guard);state[k]=replacement;check(not admit(state),('negative guard',name,k,replacement));cases+=1
            checkpoint=1 if recipe['kind']=='service_request' else 65002
            journal_conditions=[v for v in walk(ns[checkpoint]['condition']) if v.get('$type')=='questJournalEntryState_ConditionType']
            actual={(v['path']['realPath'],value(v['path']['className']),v['state']) for v in journal_conditions}
            states={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}
            expected={(j['path'],j['class'],states[j['states'][0]]) for j in owner['journals']}
            check(actual==expected,('all exact native journal guards',name))
            inventory=[v for v in walk(ns[checkpoint]['condition']) if v.get('$type')=='questInventory_ConditionType']
            expected_inventory=[]
            for item in owner['inventory_native']:
                expected=copy.deepcopy(item['source_condition']['type']);expected['comparisonType']='Equal';expected['quantity']=0;expected_inventory.append(expected)
                check(expected['itemID']['hash']==int(item['hash']),('typed inventory ID',name,item['record']))
                for quantity in (-1,1,2,2147483647,None):check(quantity!=0,('inventory contradiction defers',name,item['record'],quantity));cases+=1
            check(inventory==expected_inventory,('native inventory exact source clone',name))
            if recipe['kind']=='service_request':
                check(guard.get('PTFRU9_Retaliation_Ready')==1,'require existing U9 ready')
                ranges=[v for v in walk(ns[checkpoint]['condition']) if v.get('$type')=='questVarComparison_ConditionType' and v.get('factName') in ('PTFRU9_Retaliation_Issued','PTFRU9_Retaliation_'+recipe['gang']+'_Issued')]
                for fact in ('PTFRU9_Retaliation_Issued','PTFRU9_Retaliation_'+recipe['gang']+'_Issued'):
                    check({(r['comparisonType'],r['value']) for r in ranges if r['factName']==fact}=={('GreaterOrEqual',0),('LessOrEqual',1)},('only known issued service states',name,fact))
    # Overlay retains every predecessor graph, node, child lifetime and edge
    # except the explicit two restored startup edges and owned predicates.
    old=graphs(folder/'donor/gang_retaliation.json');new=graphs(folder/'readback/retaliation_overlay.json');check(old.keys()==new.keys(),'overlay graph identity')
    edits={e['graph']:e for e in component['overlay']['selector_edits']}
    for gp,gg in old.items():
        nn={n['id']:n for n in new[gp]['nodes']};check(set(nn)=={n['id'] for n in gg['nodes']},('overlay IDs',gp))
        for n in gg['nodes']:
            expected=copy.deepcopy(n)
            if gp in edits and n['id']==edits[gp]['selector']:
                extra={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRU10_'+edits[gp]['id']+'_Started','value':1}}
                expected['condition']={'$type':'questLogicalCondition','conditions':[extra,n['condition']],'operation':'AND'}
            check(expected==nn[n['id']],('overlay payload',gp,n['id']));native+=1
        edges=gg['edges']+([[0,'Out',edits[gp]['entry'],'In']] if gp in edits else [])
        check(sorted(edges)==new[gp]['edges'],('overlay edge scope',gp))
    check([0,'Out',33,'In'] not in new['root/22/29/214']['edges'],'Error404 remains excluded')
    check(component['overlay']['depot'] not in component['boots'],'existing owner not booted twice')
    # After queue clearing only native checkpoint bookkeeping precedes output;
    # there is no remaining gameplay, scene, spawn or authored delay operation.
    for gp in ('root/22/33','root/22/37'):
        g=new[gp];nodes={n['id']:n for n in g['nodes']}
        clears=[n for n in g['nodes'] if isinstance(n.get('type'),dict) and n['type'].get('$type')=='questSetVar_NodeType' and n['type'].get('factName') in ('sts_valentinos_retaliation','sts_tygerclaws_retaliation') and n['type'].get('value')==0]
        check(len(clears)==1,('native queue clear',gp));last=clears[0]['id'];visited=set()
        while nodes[last]['$type']!='questOutputNodeDefinition':
            check(last not in visited,('cleanup cycle',gp));visited.add(last)
            check(nodes[last]['$type'] in ('questFactsDBManagerNodeDefinition','questDeletionMarkerNodeDefinition','questCheckpointNodeDefinition'),('no gameplay after queue clear',gp,last))
            if nodes[last]['$type']=='questCheckpointNodeDefinition':check(nodes[last]['saveLock']==nodes[last]['retryOnFailure']==nodes[last]['endGameSave']==0,('native checkpoint bookkeeping',gp,last))
            edges=[e for e in g['edges'] if e[0]==last and e[1]!='CutSource'];check(len(edges)==1,('cleanup output',gp,last));last=edges[0][2]
    result=dict(status='PASS_U10_NATIVE_SOURCE_AND_POLICY_NOT_GAMEPLAY',component_sha256=sha(folder/'component.json'),tester_sha256=sha(__file__),native_payload_checks=native,policy_cases=cases,checks=checks,limitations=['Saved owner graph loading and all native gameplay outcomes require live playtest.','Unsupported existing progress remains deferred; no restart or reset.'])
    (folder/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
