"""Prepare source-exact original gig slices; never run predecessor build mains.

Only source recipes and new generated runtime data are written. Live semantics
remain unproven until playtesting. Unknown graph shapes are reported, not guessed.
"""
import copy,json,re
from catalog_gig_rollout_r2 import ROOT,read,sha,walk,normalize
from review_stock_shark_u2 import graph
from prepare_gig_family_b7 import ancestors,descendants

OUT=ROOT/'research/gig_restoration/native_gigs_u9'
COUNT='research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_new_fixer_loop.questphase.json'
REGIONS={'dakota':'bls','dyno':'cct','el_capitan':'std','mr_hands':'pac','padre':'hey','reggie':'wat','wakako':'wbr'}

def facts(n):return {v['factName'] for v in walk(n) if isinstance(v.get('factName'),str)}
def typ(n):return n.get('type') if isinstance(n.get('type'),dict) else {}
def raw(p):return p.replace('\\','/').replace('/json/','/raw/')[:-5]
def dump(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    OUT.mkdir(parents=True,exist_ok=True)
    old=read(ROOT/'research/gig_restoration/family_b7/build_plan.json')
    review=read(ROOT/'research/gig_restoration/family_b7/owner_review.json')
    selected=read(ROOT/'research/gig_restoration/lore_whitelists_v4_cast.json')['ignore_two_year_gap']['gigs']
    assert len(selected)==72 and len(set(map(normalize,selected)))==72
    jobs=copy.deepcopy(old['jobs']);special_path=ROOT/'research/gig_restoration/special_gigs_u9/recipes.json'
    special=read(special_path) if special_path.exists() else {}
    for j in special.get('jobs',[]):
        assert j['id'] not in {x['id'] for x in jobs};jobs.append(j)
    approved={normalize(s) for s in selected}
    assert all(normalize(j['title']) in approved for j in jobs)
    pins={'research/gig_restoration/family_b7/build_plan.json':sha(ROOT/'research/gig_restoration/family_b7/build_plan.json'),
          'research/gig_restoration/lore_whitelists_v4_cast.json':sha(ROOT/'research/gig_restoration/lore_whitelists_v4_cast.json'),COUNT:sha(ROOT/COUNT)}
    if special:
        pins[str(special_path.relative_to(ROOT)).replace('\\','/')]=sha(special_path)
        for p,h in special.get('pins',{}).items():assert sha(ROOT/p)==h;pins[p]=h
    counters=graph(COUNT);credits=[];maps=[];tiers=[];warnings=[];prestates=[]
    # The original fixer loop starts these companions beside the district
    # owners, not inside each gig's main resource. Restore only the admitted
    # gig's exact child reference; do not restart the whole credit/reward loop.
    prestate_parent=counters['root/3']
    for node in prestate_parent['nodes']:
        depot=node.get('phaseResource',{}).get('DepotPath',{}).get('$value','')
        job=next((j for j in jobs if '/'+j['id']+'/' in depot.replace('\\','/')),None)
        if not job:continue
        assert depot.endswith('_prestate_control.questphase')
        assert [e for e in prestate_parent['edges'] if e[2]==node['id']]==[[0,'Out',node['id'],'In1']]
        assert not any(e[0]==node['id'] for e in prestate_parent['edges'])
        source='research/gig_restoration/batch_b4/sources/json/'+depot.replace('\\','/')+'.json'
        pg=graph(source);document=read(ROOT/source)
        assert any(n.get('socketName',{}).get('$value')=='In1' for n in pg['root']['nodes'] if n['$type']=='questInputNodeDefinition')
        assert not any(v.get('$type')=='questStartQuest_NodeType' for v in walk(document))
        assert not any(v.get('$type')=='ResourcePath' and str(v.get('$value')).endswith(('.questphase','.scene')) for v in walk(document)),depot
        pins[source]=sha(ROOT/source);pins[raw(source)]=sha(ROOT/raw(source))
        job.setdefault('companions',[]).append(dict(kind='parallel_prestate',source_raw=raw(COUNT),source_graph='root/3',source_node=node['id'],depot=depot,raw=raw(source),input='In1',outputs=[]))
        prestates.append(dict(id=job['id'],source=source,depot=depot,node=node['id'],source_facts=sorted(facts(document)),native_node_count=sum(len(g['nodes']) for g in pg.values()),guard='Same admitted unused original parent entry; original prestate tier/device/service predicates preserved, no fact resets or inferred fresh history.'))
    assert len(prestates)==11
    for source in ['research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories.questphase.json','research/gig_restoration/shutdown_sources/json/base/quest/cyberpunk2077.questphase.json']:
        pins[source]=sha(ROOT/source)
    for job in jobs:
        prefix='_'.join(job['id'].split('_')[-2:])
        job.setdefault('legacy_tags',[job['tag']]);job.setdefault('legacy_owner_facts',[])
        job['counter']=job['region']+'_sts_counter'
        retaliation=[f[len('sts_'):-len('_retaliation')] for f in facts(job['resources']) if f.startswith('sts_') and f.endswith('_retaliation')]
        assert len(retaliation)<=1
        job['retaliation_gang']=retaliation[0] if retaliation else ''
        job['retaliation_dependency']=bool(retaliation)
        # Each exact native completion branch is selected by its own outcome
        # predicates and followed only to that district's original +1 node.
        found=[]
        for gp,g in counters.items():
            if not gp.startswith('root/2/'):continue
            ns={n['id']:n for n in g['nodes']};es=g['edges']
            end=[n['id'] for n in g['nodes'] if typ(n).get('factName')==job['counter']]
            if not end:continue
            starts={n['id'] for n in g['nodes'] if n['$type'] in ('questPauseConditionNodeDefinition','questConditionNodeDefinition') and facts(n) and all(f.startswith((prefix+'_',job['id']+'_')) for f in facts(n))}
            if not starts:continue
            reach=set().union(*(descendants(es,s) for s in starts))
            keep=reach & ancestors(es,set(end))
            if not (set(end)&keep):continue
            keep |= ancestors(es,starts)
            # A shared join/XOR must not depend on an omitted other-gig input.
            bad=[e for e in es if e[2] in keep and e[2] not in end and e[0] not in keep and e[0]!=0]
            assert not bad,(job['id'],'foreign credit predecessor',bad)
            keep.add(0);chosen=[e for e in es if e[0] in keep and e[2] in keep]
            assert len(end)==1 and ns[end[0]]['type']=={'$type':'questSetVar_NodeType','factName':job['counter'],'setExactValue':0,'value':1}
            assert all(n['$type'] in ('questInputNodeDefinition','questPauseConditionNodeDefinition','questConditionNodeDefinition','questLogicalXorNodeDefinition','questFactsDBManagerNodeDefinition','questDeletionMarkerNodeDefinition') for i,n in ns.items() if i in keep)
            found.append(dict(id=job['id'],raw=raw(COUNT),graph=gp,ids=sorted(keep),edges=chosen,end=end[0],nodes=[ns[i] for i in sorted(keep)]))
        found += [copy.deepcopy(c) for c in special.get('credits',[]) if c['id']==job['id']]
        assert len(found)<=1,(job['id'],'multiple credit branches')
        credits+=found;job['credit_branch']=bool(found)
        if not found:warnings.append(dict(id=job['id'],kind='native_credit',reason='No connected matching branch in inspected stock completion loop; no synthetic credit added.'))
        for r in job['resources']:
            p=r['binding']['source'];assert sha(ROOT/p)==r['binding']['sha256'];pins[p]=sha(ROOT/p);pins[r['raw']]=sha(ROOT/r['raw'])
        p=job['parent'];pins[p['raw']]=sha(ROOT/p['raw'])
    for fixer in read(ROOT/'research/gig_restoration/family_b7/fixer_review.json'):
        path=fixer['path'];assert sha(ROOT/path)==fixer['sha256'];pins[path]=sha(ROOT/path);pins[raw(path)]=sha(ROOT/raw(path))
        region=next(v for k,v in REGIONS.items() if '/'+k+'/' in path.replace('\\','/'))
        root=fixer['graphs'][0];ns={n['id']:n for n in root['nodes']};edges=root['edges']
        # Exact original earned tiers (including Wakako, skipped by old B7).
        for n in root['nodes']:
            v=n.get('condition',{}).get('type',{})
            if n['$type']!='questPauseConditionNodeDefinition' or not isinstance(v,dict) or v.get('factName')!=region+'_sts_counter':continue
            reach=descendants(edges,n['id']);ends={i for i in reach if typ(ns[i]).get('$type')=='questSetVar_NodeType' and '_tier_' in typ(ns[i]).get('factName','')}
            if not ends:continue
            keep=reach & ancestors(edges,ends)
            assert v['comparisonType']=='GreaterOrEqual'
            assert all(ns[i]['$type'] in ('questPauseConditionNodeDefinition','questFactsDBManagerNodeDefinition','questPhoneManagerNodeDefinition','questConditionNodeDefinition') for i in keep)
            last={i for i in ends if not any(e[0]==i and e[2] in keep for e in edges)}
            assert len(last)==1,(region,v['value'],last)
            tiers.append(dict(region=region,threshold=v['value'],raw=raw(path),start=n['id'],ids=sorted(keep),nodes=[ns[i] for i in sorted(keep)],edges=[e for e in edges if e[0] in keep and e[2] in keep],end=next(iter(last)),facts=[ns[i]['type']['factName'] for i in sorted(ends)],messages=[ns[i]['type']['msg']['realPath'] for i in keep if ns[i]['$type']=='questPhoneManagerNodeDefinition']))
        for job in jobs:
            if job['region']!=region:continue
            target='points_of_interest/street_stories/'+job['id']
            for g in fixer['graphs'][1:]:
                ns={n['id']:n for n in g['nodes']};own={n['id'] for n in g['nodes'] if typ(n).get('path',{}).get('realPath')==target}
                if not own:continue
                # Contract only foreign POI writes. Preserve every condition,
                # trigger and visited/discovery operation on the chosen leaf.
                es=copy.deepcopy(g['edges']);foreign={n['id'] for n in g['nodes'] if n['$type']=='questJournalNodeDefinition' and n['id'] not in own}
                rebased=[]
                for i in sorted(foreign):
                    incoming=[e for e in es if e[2]==i];outgoing=[e for e in es if e[0]==i]
                    new=[[a[0],a[1],b[2],b[3]] for a in incoming for b in outgoing]
                    es=[e for e in es if e[0]!=i and e[2]!=i]+new;rebased+=new
                keep=ancestors(es,own)
                kinds={'questInputNodeDefinition','questPauseConditionNodeDefinition','questConditionNodeDefinition','questLogicalXorNodeDefinition','questLogicalAndNodeDefinition','questJournalNodeDefinition'}
                bad=[ns[i] for i in keep if ns[i]['$type'] not in kinds]
                if bad:warnings.append(dict(id=job['id'],kind='map',reason='Unsupported map ancestor types',graph=g['path'],nodes=bad));continue
                inputs=[i for i in keep if ns[i]['$type']=='questInputNodeDefinition']
                if len(inputs)!=1:warnings.append(dict(id=job['id'],kind='map',reason='Ambiguous map input',graph=g['path']));continue
                maps.append(dict(id=job['id'],raw=raw(path),graph=g['path'],ids=sorted(keep),nodes=[ns[i] for i in sorted(keep)],edges=[e for e in es if e[0] in keep and e[2] in keep],input=inputs[0],foreign_poi_contraction=sorted(foreign),rebased_edges=rebased))
    for j in jobs:j['map_count']=sum(m['id']==j['id'] for m in maps)
    assert sum(j['retaliation_dependency'] for j in jobs)==13
    index={normalize(j['title']):j for j in review['jobs']}
    coverage=[]
    for title in selected:
        source=index[normalize(title)];j=next((x for x in jobs if x['id']==source['id']),None)
        coverage.append(dict(id=source['id'],title=title,status='ORIGINAL_SOURCE_RECIPE_READY_NOT_LIVE_PROOF' if j else 'DEFERRED_SOURCE_RECIPE',reasons=[] if j else source.get('blockers',[]) or ['Special source lifecycle recipe pending'],credit_branch=j['credit_branch'] if j else None,map_branches=j['map_count'] if j else None))
    result=dict(status='U9_ORIGINAL_SOURCE_RECIPES_NOT_ENGINE_PROOF',jobs=jobs,credits=credits,maps=maps,tiers=tiers,pins=pins,coverage=coverage,warnings=warnings,prestates=prestates,phone_dependency='PTFRU9_Support_Issued=1, Fault=0; one source-native expanded initializer only on unused predecessor lifetime')
    dump(OUT/'build_plan.json',result)
    q=lambda x:json.dumps(x,ensure_ascii=True);arr=lambda xs:'['+','.join(q(x) for x in xs)+']'
    lines=['module PTFR.ActivityStateR3','public abstract class NativeGigDataU9 {',f'  public static func Count() -> Int32 {{ return {len(jobs)}; }}', '  public static func IDs() -> array<String> { return '+arr(j['id'] for j in jobs)+'; }', '  public static func Index(id: String) -> Int32 { let a=NativeGigDataU9.IDs();let k=0;while k<ArraySize(a) { if Equals(a[k],id) { return k; };k+=1; };return -1; }']
    for method,field in [('ID','id'),('Title','title'),('Region','region'),('Counter','counter')]:lines+=['  public static func '+method+'(i: Int32) -> String { let a: array<String>='+arr(j[field] for j in jobs)+';return a[i]; }']
    for method,fn in [('Paths',lambda j:[e['path'] for e in j['entries']]),('Classes',lambda j:[e['className'] for e in j['entries']]),('Facts',lambda j:j['facts']),('TerminalFacts',lambda j:j['terminal']),('LegacyTags',lambda j:j['legacy_tags']),('LegacyOwnerFacts',lambda j:j['legacy_owner_facts'])]:
        lines+=['  public static func '+method+'(i: Int32) -> array<String> {']+[f'    if i=={i} {{ return '+arr(fn(j))+'; }' for i,j in enumerate(jobs)]+['    return [];','  }']
    lines+=['  public static func MapCount(i: Int32) -> Int32 { let a: array<Int32>=['+','.join(str(j['map_count']) for j in jobs)+'];return a[i]; }']
    lines+=['  public static func NeedsRetaliation(i: Int32) -> Bool { let a: array<Bool>=['+','.join('true' if j['retaliation_dependency'] else 'false' for j in jobs)+'];return a[i]; }']
    lines+=['  public static func RetaliationGang(i: Int32) -> String { let a: array<String>='+arr(j['retaliation_gang'] for j in jobs)+';return a[i]; }']
    lines+=['  public static func TierCount() -> Int32 { return '+str(len(tiers))+'; }']
    for method,fn in [('TierID',lambda t:t['region']+'_Tier'+str(t['threshold'])),('TierRegion',lambda t:t['region'])]:lines+=['  public static func '+method+'(i: Int32) -> String { let a: array<String>='+arr(fn(t) for t in tiers)+';return a[i]; }']
    for method,field in [('TierFacts','facts'),('TierMessages','messages')]:lines+=['  public static func '+method+'(i: Int32) -> array<String> {']+[f'    if i=={i} {{ return '+arr(t[field])+'; }' for i,t in enumerate(tiers)]+['    return [];','  }']
    lines+=['}'];folder=ROOT/'redscript/PTFR_NativeGigsU9';folder.mkdir(parents=True,exist_ok=True);(folder/'NativeGigDataU9.generated.reds').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(jobs=len(jobs),credits=len(credits),maps=len(maps),tiers=len(tiers),warnings=len(warnings),deferred=72-len(jobs))))

if __name__=='__main__':main()
