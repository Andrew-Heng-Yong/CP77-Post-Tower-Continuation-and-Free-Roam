"""Prepare source-pinned B7 owner recipes and runtime data, never legacy evidence."""
import json,re
from catalog_gig_rollout_r2 import ROOT,read,sha,walk,value
OUT=ROOT/'research/gig_restoration/family_b7'

def ancestors(edges,ends):
    seen=set(ends)
    while True:
        new=seen|{e[0] for e in edges if e[2] in seen and e[3]!='CutDestination'}
        if new==seen:return seen
        seen=new

def descendants(edges,start):
    seen={start}
    while True:
        new=seen|{e[2] for e in edges if e[0] in seen and e[3]!='CutDestination'}
        if new==seen:return seen
        seen=new

def main():
    assert not (OUT/'install_receipt.json').exists()
    source=read(OUT/'owner_review.json');old=read(ROOT/'research/gig_restoration/batch_b4/source_review.json')
    jobs=[];pins={};pending=[]
    for job in source['jobs']:
        if job['blockers']:
            pending.append(dict(id=job['id'],title=job['title'],reasons=job['blockers']));continue
        if job['id']=='sts_hey_rey_09':
            # Wakako's active binding; the Heywood copy has no input path.
            job['parents']=[p for p in job['parents'] if 'westbrook\\japantown' in p['binding']['parent']]
        if len(job['parents'])!=1:
            pending.append(dict(id=job['id'],title=job['title'],reasons=['Multiple native owner bindings require a single-entry selection audit.']));continue
        parent=job['parents'][0]
        parent['edits']=[]
        if job['id']=='sts_bls_ina_03':
            parent['edits']=[dict(graph='root/3',remove=[5,'Out',6,'Active'],add=[5,'Out',1,'In'])]
        if job['id']=='sts_cct_dtn_05':
            parent['edits']=[dict(graph='root/4',remove=[0,'Out',6,'In'],add=None)]
        parent_nodes=parent['ancestors']+[n for g in parent['nested'] for n in g['nodes']]
        foreign=[n for n in parent_nodes if n['$type']=='questJournalNodeDefinition' and n['type']['path']['realPath']!='points_of_interest/street_stories/'+job['id']]
        if foreign and not (job['id']=='sts_bls_ina_03' and len(foreign)==1 and foreign[0]['id']==6):
            pending.append(dict(id=job['id'],title=job['title'],reasons=['Original parent prelude writes another activity: '+str([n['type']['path']['realPath'] for n in foreign])]))
            continue
        # Preserve the original tier/POI/outside-trigger prelude, including nested
        # fact-only eligibility phases. Nothing from sibling gig branches is copied.
        allowed={'questInputNodeDefinition','questOutputNodeDefinition','questPhaseNodeDefinition','questJournalNodeDefinition','questPauseConditionNodeDefinition','questLogicalXorNodeDefinition','questDeletionMarkerNodeDefinition','questFactsDBManagerNodeDefinition','questConditionNodeDefinition'}
        # Exact official prelude operations reviewed above: own ambient default
        # community, own access-blocker variant, or native elevator floor access.
        if job['id'] in ('sts_cct_dtn_04','sts_cct_dtn_05'):allowed.add('questSpawnManagerNodeDefinition')
        if job['id']=='sts_pac_cvi_02':allowed.add('questWorldDataManagerNodeDefinition')
        if job['id']=='sts_wat_lch_03':allowed.add('questInteractiveObjectManagerNodeDefinition')
        extra=[n for n in parent_nodes if n['$type'] not in allowed]
        if extra:
            pending.append(dict(id=job['id'],title=job['title'],reasons=['Parent prelude requires separate world mutation review: '+str(extra)]));continue
        for n in parent['ancestors']+[n for g in parent['nested'] for n in g['nodes']]:
            assert n['$type'] in allowed,(job['id'],n)
            if n['$type']=='questFactsDBManagerNodeDefinition':
                assert n['type']['setExactValue']==1 and n['type']['value']==1 and n['type']['factName'].endswith('_activated')
            if n['$type']=='questJournalNodeDefinition':assert n['type']['path']['realPath']=='points_of_interest/street_stories/'+job['id'] or (job['id']=='sts_bls_ina_03' and n['id']==6),(job['id'],n)
        root_inputs=[n for n in parent['ancestors'] if n['$type']=='questInputNodeDefinition']
        normal=[n for n in root_inputs if value(n['socketName']).lower() in ('in','in1')]
        assert len(normal)==1,(job['id'],root_inputs)
        parent['input_node']=normal[0]['id']
        # The exact child input name (IN/In1, including original casing) matters.
        ports={e[3] for e in parent['binding']['incoming']}
        if len(ports)!=1:
            pending.append(dict(id=job['id'],title=job['title'],reasons=['Native owner uses multiple lifecycle inputs: '+str(sorted(ports))]));continue
        parent['child_input']=next(iter(ports))
        resources=[]
        for index,res in enumerate(job['resources']):
            meta=res['binding'];p=ROOT/meta['source'];assert sha(p)==meta['sha256']
            raw=meta['source'].replace('/json/','/raw/')[:-5];assert (ROOT/raw).exists()
            pins[meta['source']]=sha(p);pins[raw]=sha(ROOT/raw)
            resources.append(dict(depot=res['depot'],binding=meta,raw=raw,key='r'+str(index),graphs=res['graphs'],prefabs=res['prefabs']))
        p=ROOT/parent['binding']['binding']['source'];pins[str(p.relative_to(ROOT))]=sha(p)
        parent['raw']=str(p.relative_to(ROOT)).replace('\\','/').replace('/json/','/raw/')[:-5]
        pins[parent['raw']]=sha(ROOT/parent['raw'])
        native=next(r for r in resources if r['depot']==parent['child']['phaseResource']['DepotPath']['$value'])
        outputs=[value(n['socketName']) for n in native['graphs'][0]['nodes'] if n['$type']=='questOutputNodeDefinition']
        assert outputs,(job['id'],'No owner output')
        original=next(j for j in old['jobs'] if j['id']==job['id'])
        local='_'.join(job['id'].split('_')[-2:]);prefixes=(local,job['id'],job['id'].removeprefix('sts_'))
        facts=set(job['start']+job['terminal'])
        for res in resources:
            for g in res['graphs']:
                for n in g['nodes']:
                    for v in walk(n):
                        f=value(v.get('factName',''))
                        if f and f.startswith(prefixes):facts.add(f)
        for scene in original['scenes']:
            path=ROOT/scene['source'];assert sha(path)==scene['sha256'];pins[scene['source']]=scene['sha256']
            for v in walk(read(path)):
                f=value(v.get('factName',''))
                if isinstance(f,str) and f.startswith(prefixes):facts.add(f)
        mutations=[]
        for kind,rows in [('Reward',job['rewards']),('Achievement',job['achievements'])]:
            for index,m in enumerate(rows):
                res=next(r for r in resources if r['depot']==m['depot']);g=next(g for g in res['graphs'] if g['path']==m['graph'])
                node=m['node'];incoming=[e for e in g['edges'] if e[2]==node['id'] and e[3]!='CutDestination'];out=[e for e in g['edges'] if e[0]==node['id']]
                assert all(e[3]=='In' for e in incoming) and all(e[1]=='Out' for e in out),(job['id'],node)
                if kind=='Achievement':assert node['type']['setExactValue']==0 and node['type']['value']==1
                mutations.append(dict(depot=m['depot'],graph=m['graph'],node=node['id'],kind=kind,key=kind+str(index),payload=node,incoming=incoming,outgoing=out))
        region='wbr' if job['id']=='sts_hey_rey_09' else job['id'].split('_')[1]
        jobs.append(dict(id=job['id'],title=job['title'],tag='PTFRB7_'+job['id'].removeprefix('sts_'),region=region,entries=job['entries'],facts=sorted(facts),start=job['start'],terminal=job['terminal'],resources=resources,parent=parent,outputs=outputs,calls=job['calls'],mutations=mutations))
    # Native earned-tier fragments only. Final fixer rewards and counter loops
    # are excluded by selecting paths that end at authored tier setters.
    tiers=[]
    for fixer in read(OUT/'fixer_review.json'):
        if 'wakako.questphase' in fixer['path']:continue # Existing tested B5 tier owner.
        root=fixer['graphs'][0];nodes={n['id']:n for n in root['nodes']};edges=root['edges']
        for n in root['nodes']:
            var=n.get('condition',{}).get('type',{})
            if n['$type']!='questPauseConditionNodeDefinition' or not isinstance(var,dict) or not var.get('factName','').endswith('_sts_counter'):continue
            reach=descendants(edges,n['id'])
            targets={i for i in reach if nodes[i].get('type',{}).get('$type')=='questSetVar_NodeType' and '_tier_' in nodes[i]['type'].get('factName','')}
            if not targets:continue
            keep=reach & ancestors(edges,targets)
            assert var['comparisonType']=='GreaterOrEqual'
            assert all(nodes[i]['$type'] in ('questPauseConditionNodeDefinition','questFactsDBManagerNodeDefinition','questPhoneManagerNodeDefinition','questConditionNodeDefinition') for i in keep),(fixer['path'],keep)
            assert all(nodes[i]['type']['value']==1 for i in targets)
            region=var['factName'].split('_')[0]
            path=fixer['path'];raw=path.replace('\\','/').replace('/json/','/raw/')[:-5]
            pins[path]=sha(ROOT/path);pins[raw]=sha(ROOT/raw)
            tiers.append(dict(region=region,threshold=var['value'],raw=raw,start=n['id'],nodes=[nodes[i] for i in sorted(keep)],edges=[e for e in edges if e[0] in keep and e[2] in keep],targets=sorted(targets)))
    result=dict(status='B7_BUILD_RECIPES_NOT_ENGINE_PROOF',jobs=jobs,pending=pending,tiers=tiers,pins=pins,selected_count=72)
    (OUT/'build_plan.json').write_text(json.dumps(result,indent=2)+'\n')
    q=lambda s:json.dumps(s,ensure_ascii=True)
    arr=lambda values:'['+','.join(q(s) for s in values)+']'
    lines=['module PTFR.ActivityStateR3','public abstract class GigDataB7 {',f'  public static func Count() -> Int32 {{ return {len(jobs)}; }}']
    lines+=['  public static func IDs() -> array<String> { return '+arr(j['id'] for j in jobs)+'; }', '  public static func Selected() -> array<String> { return '+arr(j['id'] for j in source['jobs'])+'; }']
    for method,field in [('ID','id'),('Title','title'),('Tag','tag'),('Region','region')]:
        lines+=['  public static func '+method+'(i: Int32) -> String { let values: array<String>='+arr(j[field] for j in jobs)+'; return values[i]; }']
    lines+=['  public static func Index(id: String) -> Int32 { let values=GigDataB7.IDs();let i=0;while i<ArraySize(values) { if Equals(values[i],id) { return i; };i+=1; };return -1; }']
    for method,getter in [('Paths',lambda j:[e['path'] for e in j['entries']]),('Classes',lambda j:[e['className'] for e in j['entries']]),('Facts',lambda j:j['facts']),('FinishedFacts',lambda j:[f for f in j['terminal'] if f.endswith('_finished')]),('Rewards',lambda j:[m['key'] for m in j['mutations'] if m['kind']=='Reward']),('Achievements',lambda j:[m['key'] for m in j['mutations'] if m['kind']=='Achievement'])]:
        lines+=['  public static func '+method+'(i: Int32) -> array<String> {']
        for i,j in enumerate(jobs):lines+=['    if i=='+str(i)+' { return '+arr(getter(j))+'; }']
        lines+=['    return [];','  }']
    lines+=['  public static func Pending(id: String) -> String {']
    for j in pending:lines+=['    if Equals(id,'+q(j['id'])+') { return '+q('; '.join(j['reasons']))+'; }']
    lines+=['    return "Not selected.";','  }','}']
    folder=ROOT/'redscript/PTFR_GigFamilyB7';folder.mkdir(exist_ok=True)
    (folder/'GigDataB7.generated.reds').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(owners=len(jobs),earned_tier_fragments=len(tiers),pending=len(pending),native_resources=sum(len(j['resources']) for j in jobs))))

if __name__=='__main__':main()
