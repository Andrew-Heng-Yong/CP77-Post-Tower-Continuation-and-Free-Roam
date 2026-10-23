"""Independent source/ownership/readiness audit of the Afterlife population."""
import copy
import json
from collections import defaultdict
from pathlib import Path
from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_access_r10 import read, sha
from test_zetatech_population_r12 import inflate, normalize

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'

def evaluate(c,f,loaded):
    kind=c['$type']
    if kind=='questLogicalCondition':
        values=[evaluate(x,f,loaded) for x in c['conditions']]
        return all(values) if c['operation']=='AND' else any(values)
    if kind=='questNodeLoadingCondition':
        result=loaded[c['objectRef']['$value']]
        return not result if c['inverted'] else result
    assert kind=='questFactsDBCondition',kind
    p=c['type'];a=f.get(p['factName'],0);b=p['value']
    return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'LessOrEqual':a<=b}[p['comparisonType']]

def action(p):
    kind=p['$type']
    if kind=='questCommunityTemplate_NodeType':
        return ('community',p['spawnerReference']['$value'],p['communityEntryName']['$value'],p['communityEntryPhaseName']['$value'],p['action'])
    assert kind=='questSpawnSet_NodeType',kind
    return ('spawnset',p['reference']['$value'],p['entryName']['$value'],p['phaseName']['$value'],p['action'])

class Model:
    def __init__(self,nn,edges,facts,loaded):
        self.nn=nn;self.facts=dict(facts);self.loaded=dict(loaded);self.pending={0};self.actions=[];self.variants={};self.edges=defaultdict(list)
        for a,s,b,_ in edges:self.edges[a,s].append(b)
    def settle(self,before=None):
        for _ in range(500):
            progress=False
            for i in sorted(self.pending):
                if i==before:return
                n=self.nn[i];kind=n['$type'];socket='Out'
                if kind=='questPauseConditionNodeDefinition':
                    if not evaluate(n['condition'],self.facts,self.loaded):continue
                elif kind=='questConditionNodeDefinition':socket='True' if evaluate(n['condition'],self.facts,self.loaded) else 'False'
                elif kind=='questFactsDBManagerNodeDefinition':
                    p=n['type'];assert p['$type']=='questSetVar_NodeType';name=p['factName'];value=p['value']
                    self.facts[name]=value if p['setExactValue'] else self.facts.get(name,0)+value
                elif kind=='questSpawnManagerNodeDefinition':
                    self.actions.extend((i,*action(a['type'])) for a in n['actions'])
                elif kind=='questWorldDataManagerNodeDefinition':
                    p=n['type'];assert p['$type']=='questTogglePrefabVariant_NodeType'
                    for row in p['params']:
                        for v in row['variantStates']:
                            k=(row['prefabNodeRef']['$value'],v['name']['$value']);self.variants[k]=bool(v['show']);self.actions.append((i,'variant',k,bool(v['show'])))
                else:assert kind=='questInputNodeDefinition',kind
                self.pending.remove(i);self.pending.update(self.edges[i,socket]);progress=True
            if not progress:return
        raise AssertionError('Population graph failed to settle')

def world(path):
    root=read(path)['Data']['RootChunk']
    return inflate(root,handles(root))

def match_source_entry(actual,source,phase,refmap,appearance=None):
    expected=copy.deepcopy(source)
    expected['phases']=[p for p in expected['phases'] if p['Data']['phaseName']['$value']==phase]
    assert len(expected['phases'])==1
    p=expected['phases'][0]['Data']
    if appearance is not None:
        assert len(p['appearances'])==1
        p['appearances'][0]['$value']=appearance;p['appearances'][0]['$storage']='string'
    for period in p['timePeriods']:
        for ref in period['spotNodeRefs']:
            old=ref['$value'];matches=[v for k,v in refmap.items() if k==old or k.endswith('/'+old)]
            assert len(matches)==1,(old,matches)
            ref['$value']=matches[0];ref['$storage']='string'
    assert normalize(actual)==normalize(expected),'Private community entry exceeds approved source delta'

def audit_world(m,pm,rm):
    paths={depot:Path(m['source_root'])/depot for depot in m['resources']}
    assert all(d.startswith('towercontinued\\afterlife_r1\\') for d in paths)
    for p in m['payloads']:assert sha(paths[p['depot']])==p['sha256']
    registries=[world(BASE/'patrons_registry.streamingsector.json'),world(BASE/'rogue_registry.streamingsector.json')]
    spots=[world(BASE/'patrons_spots.streamingsector.json'),world(BASE/'rogue_spot.streamingsector.json')]
    blocks=[world(BASE/'patrons_world.streamingblock.json'),world(BASE/'rogue.streamingblock.json')]
    all_aliases=[];all_community_ids=[];all_spot_ids=[];entry_count=0;max_actors=0
    for registry,spot,block in zip(registries,spots,blocks):
        assert registry['category']=='AlwaysLoaded'
        rn=[n['Data'] for n in registry['nodes']];reg=[n for n in rn if n['$type']=='worldCommunityRegistryNode'];assert len(reg)==1;reg=reg[0]
        area=[n for n in rn if n['$type'].startswith('worldCompiledCommunityAreaNode')]
        assert len(area)==len(reg['communitiesData'])
        private_refs=[r['$value'] for r in registry['nodeRefs']]+[r['$value'] for r in spot['nodeRefs']]
        assert all(s.startswith('$/03_night_city/#PTFR') for s in private_refs)
        assert len(private_refs)==len(set(private_refs));all_aliases+=private_refs
        for d in registry['nodeData']['Data']+spot['nodeData']['Data']:
            assert d['QuestPrefabRefHash']['$value'] in private_refs
        for item in reg['communitiesData']:
            cid=item['communityId']['entityId']['hash'];all_community_ids.append(cid)
            tp=item['template']['Data'];assert not tp['crowdEntries'];assert tp['spawnSetReference']['$value'] in ('None','0','')
            assert not any(s['entryActiveOnStart'] for s in item['entriesInitialState'])
            assert len(item['entriesInitialState'])==len(tp['entries'])
            ca=next(a['area']['Data'] for a in area if a['sourceObjectId']['hash']==cid)
            assert len(ca['entriesData'])==len(tp['entries'])
            for h in tp['entries']:
                e=h['Data'];entry_count+=1
                assert not e['initializers'] and len(e['phases'])==1
                p=e['phases'][0]['Data'];max_actors+=max(t['quantity'] for t in p['timePeriods'])
                compiled=next(e2 for e2 in ca['entriesData'] if e2['entryName']==e['entryName'])
                assert len(compiled['phasesData'])==1
                assert compiled['phasesData'][0]['entryPhaseName']==p['phaseName']
                assert len(compiled['phasesData'][0]['timePeriodsData'])==len(p['timePeriods'])
                for tc,te in zip(compiled['phasesData'][0]['timePeriodsData'],p['timePeriods']):
                    assert len(tc['spotNodeIds'])>=te['quantity']
                    for sid in tc['spotNodeIds']:
                        assert any(pd['globalNodeId']['hash']==sid['hash'] for pd in reg['workspotsPersistentData'])
            assert not any('tiny_mike' in e['Data']['entryName']['$value'] for e in tp['entries'])
        all_spot_ids += [pd['globalNodeId']['hash'] for pd in reg['workspotsPersistentData']]
        assert len(spot['nodeData']['Data'])==len(spot['nodes'])
        assert all(n['Data']['$type']=='worldAISpotNode' for n in spot['nodes'])
        # Native sector layout: range starts [0,0] give empty default range0
        # and final range1 through the end of the node array. VariantNodes is
        # a separate optional remapping array; both are empty as in passed R12.
        assert spot['variantNodes']==[[],[]]
        assert spot['variantIndices']==[0,0],spot['variantIndices']
        ds=block['descriptors'];assert len(ds)==2
        assert ds[0]['category']=='AlwaysLoaded' and not ds[0]['variants']
        assert len(ds[1]['variants'])==1 and ds[1]['variants'][0]['enabledByDefault']==0
        v=ds[1]['variants'][0]
        assert (v['nodeRef']['$value'],v['name']['$value']) in {(x['owner'],x['name']) for x in m['private_variants']}
        assert v['rangeIndex']==1 and ds[1]['numNodeRanges']==2
        for n in spot['nodes']:
            n=n['Data'];assert n['sourcePrefabHash']=='0'
            for ref in (n['lookAtTarget'],n['spot']['Data']['masterNodeRef']):assert ref['$value'] in ('0','') or ref['$value'] in private_refs
    assert len(all_aliases)==len(set(all_aliases)), 'Duplicate private alias across blocks'
    assert len(all_community_ids)==len(set(all_community_ids))==3
    assert len(all_spot_ids)==len(set(all_spot_ids))
    assert entry_count==28 and max_actors==pm['maximum_actors']+1
    # Compare actual selected records, appearances, schedules and quantities to
    # original registry templates. Only private aliases and Rogue's 2079 look change.
    original=read(BASE/'patron_vanilla_registry.json');ot={r['community_index']:r['community'] for r in original if r['community_index'] in (115,7725)}
    for k in ot:ot[k]=inflate(ot[k],handles(ot[k]))
    rp={s['source_ref']:s['private_ref'] for s in pm['workspots']}
    byname={e['Data']['entryName']['$value']:e['Data'] for i in registries[0]['nodes'][0]['Data']['communitiesData'] for e in i['template']['Data']['entries']}
    for row in pm['entries']:
        k=115 if row['role']=='emmerick' else 7725
        src=next(e['Data'] for e in ot[k]['template']['Data']['entries'] if e['Data']['entryName']['$value']==row['entry'])
        match_source_entry(byname[row['entry']],src,row['phase'],rp)
    # Bounded raw-source world exports preserve placement and complete animation
    # payload, except debug/private identities and internal private look-at aliases.
    cache={}
    for i,row in enumerate(pm['workspots']):
        p=ROOT/row['source'];parts=list(p.parts);parts[parts.index('raw')]='json';p=Path(*parts).with_suffix(p.suffix+'.json')
        if p not in cache:cache[p]=world(p)
        src=cache[p];expected=copy.deepcopy(src['nodes'][row['source_node']]['Data']);actual=spots[0]['nodes'][i]['Data']
        for key in ('debugName','sourcePrefabHash'):expected[key]=actual[key]
        for obj,key in ((expected,'lookAtTarget'),(expected['spot']['Data'],'masterNodeRef')):
            old=obj[key]['$value']
            if old not in ('0',''):
                matches=[v for k,v in rp.items() if k==old or k.endswith('/'+old)];assert len(matches)==1
                obj[key]['$value']=matches[0];obj[key]['$storage']='string'
        assert normalize(actual)==normalize(expected),('workspot delta',row['source_ref'])
        srcd=[d for d in src['nodeData']['Data'] if d['NodeIndex']==row['source_node']];assert len(srcd)==1
        got=spots[0]['nodeData']['Data'][i]
        for key in ('Position','Orientation','Scale'):assert got[key]==srcd[0][key]
    # The compiled crowd area has a spatially meaningful placement. Its
    # original streamed area uses node563; Emmerick's nonspatial original has
    # no placement, so its private metadata is anchored at his exact idle spot.
    area_source=world(ROOT/'research/misty_viktor_world/r7_showworld_sources/json/base/worlds/03_night_city/_compiled/default/exterior_-12_8_0_1.streamingsector.json')
    source_area_datum=[d for d in area_source['nodeData']['Data'] if d['NodeIndex']==563]
    assert len(source_area_datum)==1
    area_data=registries[0]['nodeData']['Data']
    for key in ('Position','Orientation','Scale','Bounds'):
        assert area_data[1][key]==source_area_datum[0][key]
        assert area_data[2][key]==spots[0]['nodeData']['Data'][-1][key]
    rogue_actual=spots[1]['nodes'][0]['Data'];rogue_expected=copy.deepcopy(rm['workspot_payload'])
    for key in ('debugName','sourcePrefabHash'):rogue_expected[key]=rogue_actual[key]
    assert normalize(rogue_actual)==normalize(rogue_expected)
    for key in ('Position','Orientation','Scale'):assert spots[1]['nodeData']['Data'][0][key]==rm['source_transform'][key]
    rogue_entry=registries[1]['nodes'][0]['Data']['communitiesData'][0]['template']['Data']['entries'][0]['Data']
    assert rogue_entry['entryName']['$value']=='rogue'
    assert rogue_entry['phases'][0]['Data']['appearances'][0]['$value']=='rogue_ep__q307__two_years_later'
    assert normalize(rogue_entry['characterRecordId'])==normalize({'$type':'TweakDBID','$storage':'string','$value':'Character.Rogue'})
    return dict(private_entries=entry_count,maximum_private_actors=max_actors,private_community_ids=len(all_community_ids),private_spots=len(all_spot_ids),private_aliases=len(all_aliases),all_entries_initially_inactive=True,all_spots_default_off=True,source_workspot_and_entry_delta_pass=True,compiled_area_placement_pass=True)

def main():
    m=read(BASE/'manifest.json');pm=read(BASE/'patrons_manifest.json');rm=read(BASE/'rogue_world_manifest.json')
    root=read(BASE/'population_phase.json')['Data']['RootChunk'];hh=handles(root)
    for o in walk(root):
        if 'HandleRefId' in o:assert str(o['HandleRefId']) in hh
        assert o.get('$type') not in ('questSceneNodeDefinition','questInteractiveObjectManagerNodeDefinition')
        if o.get('$type')=='questSetVar_NodeType':assert o['factName'].startswith('PTFRAL1_')
    nn={k:canonical(v,hh) for k,v in nodes(root).items()};edges=quest_edges(root)[0]
    assert len(nn)==262 and not root['phasePrefabs']
    assert edges=={(a,s,b,'In') for a,s,b in m['population_edges']}
    branches=m['population_branches'];assert len(branches)==28
    assert sum(b['role']=='rogue' for b in branches)==sum(b['role']=='emmerick' for b in branches)==1
    assert sum(b['role']=='patron' for b in branches)==26
    refs={r for b in branches for r in b['refs']};loaded=dict.fromkeys(refs,True)
    facts=m['guards']|{'rogue_default_on':1,'q116_rogue_dead':0}
    expected={b['entry'] for b in branches}
    for b in branches:
        i=b['start'];actual=[action(a['type']) for a in nn[i+2]['actions']]
        assert actual==[(b['original_type'],b['original_spawner'],b['original_entry'],b['original_phase'],'Deactivate'),('community',b['private_spawner'],b['entry'],b['phase'],'Reactivate')]
        assert [action(a['type']) for a in nn[i+6]['actions']]==[('community',b['private_spawner'],b['entry'],b['phase'],'Deactivate')]
        assert b['private_spawner'].startswith('$/03_night_city/#PTFR') and all(r.startswith('$/03_night_city/#PTFR') for r in b['refs'])
    def simulate(f=facts,l=loaded):
        s=Model(nn,edges,f,l);s.settle();return s
    def acquired(s):return {a[3] for a in s.actions if a[1]=='community' and a[-1]=='Reactivate'}
    s=simulate();assert acquired(s)==expected and len(s.actions)==58
    assert all(s.facts[b['ready_fact']]==1 for b in branches)
    negatives=0
    for k,v in m['guards'].items():
        for bad in {-1,0,1,2}-{v}:
            assert not simulate(facts|{k:bad}).actions
            release=simulate();release.actions.clear();release.facts[k]=bad;release.settle()
            acts=[a for a in release.actions if a[1]!='variant'];assert len(acts)==28
            assert all(a[1]=='community' and a[2].startswith('$/03_night_city/#PTFR') and a[-1]=='Deactivate' for a in acts)
            assert not any(release.variants.values())
            release.actions.clear();release.facts[k]=v;release.settle();assert acquired(release)==expected;negatives+=1
    for bad in (0,-1):assert acquired(simulate(facts|{'rogue_default_on':bad}))==expected-{'rogue'}
    for bad in (1,2,-1):assert acquired(simulate(facts|{'q116_rogue_dead':bad}))==expected-{'rogue'}
    assert not acquired(simulate(l=dict.fromkeys(refs,False)))
    for ref in refs:
        blocked={b['entry'] for b in branches if ref in b['refs']}
        assert acquired(simulate(l=loaded|{ref:False}))==expected-blocked
        cycle=simulate();cycle.actions.clear();cycle.loaded[ref]=False;cycle.settle()
        assert {a[3] for a in cycle.actions}==blocked and all(a[-1]=='Deactivate' for a in cycle.actions)
        assert all(a[2].startswith('$/03_night_city/#PTFR') for a in cycle.actions)
        cycle.actions.clear();cycle.loaded[ref]=True;cycle.settle();assert acquired(cycle)==blocked
    races=0
    for b in branches:
        for bad in [None]+list(m['guards']):
            state=Model(nn,edges,facts,loaded);state.settle(before=b['start']+1);before=len(state.actions)
            if bad is None:state.loaded[b['refs'][0]]=False
            else:state.facts[bad]=1-m['guards'][bad]
            state.settle();assert not any(a[0]==b['start']+2 for a in state.actions[before:]);races+=1
    for b in [b for b in branches if b['role']=='rogue']:
        for k,v in [('rogue_default_on',0),('q116_rogue_dead',1)]:
            state=simulate();state.actions.clear();state.facts[k]=v;state.settle()
            assert len(state.actions)==1 and state.actions[0][2]==b['private_spawner'] and state.actions[0][-1]=='Deactivate'
    for key,value in m['guards'].items():
        state=Model(nn,edges,facts,loaded);state.settle(before=11);state.facts[key]=1-value;state.settle()
        assert not state.actions, 'World recheck allowed a pre-Tower/private-variant race'
    world_result=audit_world(m,pm,rm)
    report=dict(status='PASS_POPULATION_OFFLINE_NOT_LIVE',archive_sha256=m['sha256'],xl_sha256=m['xl_sha256'],population_phase_sha256=sha(Path(m['source_root'])/m['population_phase']),patrons_manifest_sha256=sha(BASE/'patrons_manifest.json'),rogue_world_manifest_sha256=sha(BASE/'rogue_world_manifest.json'),nodes=len(nn),branches=len(branches),negative_guard_cases=negatives,individual_stream_cases=len(refs),wait_recheck_races=races,world_recheck_races=len(m['guards']),original_then_private_acquisition=True,private_only_release=True,rogue_availability_and_death_preserved=True,story_writes=0,scene_starts=0,world=world_result)
    (BASE/'population_tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
