"""Eight explicitly selected U10 native entry recipes. No predecessor mains."""
import copy,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_batch_b4 import library
from catalog_gig_rollout_r2 import read,sha,walk,value,journal
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten,references
from prepare_gig_family_b7 import ancestors,descendants
from prepare_native_gigs_u9 import facts,typ,raw

OUT=ROOT/'research/gigs_u10/native'
IDS=['sts_hey_gle_03','sts_hey_gle_05','sts_hey_rey_01','sts_hey_rey_02','sts_std_arr_03','sts_wat_nid_07','sts_wbr_hil_06','sts_wbr_jpn_12']
COUNT='research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_new_fixer_loop.questphase.json'

def dump(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def main():
    lib=library();pins={};memo={}
    def pin(path):
        pins[path]=sha(ROOT/path)
        rp=raw(path)
        assert (ROOT/rp).exists(),rp
        pins[rp]=sha(ROOT/rp)
        return rp
    for path in ['research/omitted_jobs_audit/native_screen_03.json','research/omitted_jobs_audit/review_02/native_audit_02.json']:
        idx=read(ROOT/path);pins[path]=sha(ROOT/path)
        for dep,m in idx['resources'].items():
            obj=read(ROOT/m['source']);lib[dep]=(obj,obj['Data']['RootChunk'],dict(source=m['source'],sha256=sha(ROOT/m['source']),embedded_index=None))
    def graphs(dep):
        if dep not in memo:
            obj,root,meta=lib[dep];r=SafeResource(obj)
            memo[dep]=flatten(r,root)
        return memo[dep]
    parents={}
    for dep,(obj,root,meta) in lib.items():
        if root.get('$type')!='questQuestPhaseResource' or not dep.endswith('.questphase'):continue
        # Only district parents can be candidates; avoids unconnected historical embeds.
        if any('/'+i+'/' in dep.replace('\\','/') for i in IDS):continue
        if not any(dep.endswith('\\'+p+'.questphase') for p in ('sts_hey_glenn','sts_hey_vista_del_rey','sts_std_arroyo','sts_wat_northside_industrial_district','sts_wbr_charter_hill','sts_wbr_japantown')):continue
        for g in graphs(dep):
            for n in g['nodes']:
                ref=value(n.get('phaseResource',{}).get('DepotPath'))
                if ref and any('/'+i+'/' in ref.replace('\\','/') for i in IDS):
                    incoming=[e for e in g['edges'] if e[2]==n['id'] and e[3]!='CutDestination']
                    if incoming:parents.setdefault(ref,[]).append(dict(parent=dep,graph=g['path'],node=n['id'],incoming=incoming,binding=meta))
    loc={}
    for p in ['research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json','research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens/onscreens.json.json']:
        pins[p]=sha(ROOT/p)
        for row in read(ROOT/p)['Data']['RootChunk']['root']['Data']['entries']:loc[str(row['primaryKey'])]=row['femaleVariant']
    jp='research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json';pin(jp)
    journals={j['id']:j for j in journal(ROOT/jp,loc)}
    cobj=read(ROOT/COUNT);cg={g['path']:g for g in flatten(SafeResource(cobj),cobj['Data']['RootChunk'])};craw=pin(COUNT)
    jobs=[];credits=[];maps=[];details=[];warnings=[]
    for ident in IDS:
        candidates=[(dep,b) for dep,bindings in parents.items() if '/'+ident+'/' in dep.replace('\\','/') for b in bindings if b['graph']=='root']
        child_ids={b['node'] for _,b in candidates}
        candidates=[(d,b) for d,b in candidates if not any(e[0] in child_ids for e in b['incoming'])]
        assert len(candidates)==1,(ident,candidates)
        main,binding=candidates[0];pg=graphs(binding['parent']);g=next(g for g in pg if g['path']==binding['graph']);ns={n['id']:n for n in g['nodes']}
        keep=ancestors(g['edges'],{binding['node']});inputs=[n for n in g['nodes'] if n['id'] in keep and n['$type']=='questInputNodeDefinition' and value(n['socketName']).lower() in ('in','in1')]
        assert len(inputs)==1,(ident,inputs)
        reachable=descendants(g['edges'],inputs[0]['id']);keep &= reachable
        parent=dict(binding=binding,raw=pin(binding['binding']['source']),ancestors=[n for n in g['nodes'] if n['id'] in keep and n['id']!=binding['node']],nested=[gg for gg in pg if any(gg['path'].startswith(g['path']+'/'+str(i)) for i in keep if ns[i]['$type']=='questPhaseNodeDefinition' and i!=binding['node'])],edges=[e for e in g['edges'] if e[0] in keep and e[2] in keep and e[3]!='CutDestination'],child=ns[binding['node']],input_node=inputs[0]['id'],edits=[])
        pending=[main];seen=set();resources=[];scenes=[];ownfacts=set();mutations=[];external=set();companions=[]
        prefix='_'.join(ident.split('_')[-2:]);prefixes=(prefix,ident,ident.removeprefix('sts_'),'sts_'+prefix,'#'+prefix)
        while pending:
            dep=pending.pop(0)
            if dep in seen:continue
            seen.add(dep);assert dep in lib,(ident,'missing',dep)
            obj,root,meta=lib[dep];rp=pin(meta['source'])
            pending += references(root,'phaseResource')+references(root,'sceneFile')
            for f in facts(root):
                if f.startswith(prefixes):ownfacts.add(f)
                else:external.add(f)
            if dep.endswith('.scene'):scenes.append(dict(depot=dep,binding=meta,raw=rp));continue
            gg=graphs(dep);resources.append(dict(depot=dep,binding=meta,raw=rp,key='r'+str(len(resources)),graphs=gg,prefabs=root.get('phasePrefabs',[])))
            for gg0 in gg:
                for n in gg0['nodes']:
                    if any(v.get('$type') in ('questSetVar_NodeType','questGiveReward_NodeType','questAddRemoveItem_NodeType','questInjectLoot_NodeType','questGiveItem_NodeType') for v in walk(n)):mutations.append(dict(depot=dep,graph=gg0['path'],node=n))
        # Exact standalone prestate companion from native fixer-loop owner only.
        for n in cg['root/3']['nodes']:
            dep=value(n.get('phaseResource',{}).get('DepotPath')) or ''
            if '/'+ident+'/' not in dep.replace('\\','/'):continue
            assert dep.endswith('_prestate_control.questphase')
            incoming=[e for e in cg['root/3']['edges'] if e[2]==n['id']]
            assert incoming==[[0,'Out',n['id'],'In1']]
            assert dep in lib,(ident,dep)
            obj,root,meta=lib[dep];rp=pin(meta['source'])
            assert not references(root,'phaseResource') and not references(root,'sceneFile')
            companions.append(dict(kind='parallel_prestate',source_raw=craw,source_graph='root/3',source_node=n['id'],depot=dep,raw=rp,input='In1',outputs=[]))
        # Preserve any original main output companions instead of silently dropping.
        for e in g['edges']:
            if e[0]!=binding['node']:continue
            n=ns[e[2]];dep=value(n.get('phaseResource',{}).get('DepotPath'))
            if dep=='0':
                embedded=[gg for gg in pg if gg['path']==g['path']+'/'+str(n['id']) or gg['path'].startswith(g['path']+'/'+str(n['id'])+'/')]
                assert embedded,(ident,'missing embedded companion')
                assert not [ee for ee in g['edges'] if ee[0]==n['id']],(ident,'companion downstream needs review')
                outs=[value(nn['socketName']) for nn in embedded[0]['nodes'] if nn['$type']=='questOutputNodeDefinition']
                for gg in embedded:
                    ownfacts.update(f for f in facts(gg) if f.startswith(prefixes))
                companions.append(dict(kind='cleanup',source_raw=parent['raw'],source_graph=g['path'],source_node=n['id'],depot=None,raw=parent['raw'],input=e[3],from_output=e[1],outputs=outs,embedded=embedded))
            else:
                assert dep and '/'+ident+'/' in dep.replace('\\','/'),(ident,'output requires review',e,n)
                obj,root,meta=lib[dep];rp=pin(meta['source']);outs=[value(nn['socketName']) for nn in graphs(dep)[0]['nodes'] if nn['$type']=='questOutputNodeDefinition']
                companions.append(dict(kind='cleanup',source_raw=parent['raw'],source_graph=g['path'],source_node=n['id'],depot=dep,raw=rp,input=e[3],from_output=e[1],outputs=outs))
        # Include full reachable companion closure and its facts; an embedded
        # source pin alone is not closure for external after-gig dependencies.
        pending=[c['depot'] for c in companions if c['depot']]
        for c in companions:
            for gg in c.get('embedded',[]):pending+=references(gg,'phaseResource')+references(gg,'sceneFile')
        while pending:
            dep=pending.pop(0)
            if dep in seen:continue
            seen.add(dep);assert dep in lib,(ident,'companion missing',dep)
            obj,root,meta=lib[dep];rp=pin(meta['source']);pending+=references(root,'phaseResource')+references(root,'sceneFile')
            # Prestate flags can already be natively initialized without player
            # progression; preserve those native guards rather than zeroing.
            if not dep.endswith('_prestate_control.questphase'):
                ownfacts.update(f for f in facts(root) if f.startswith(prefixes))
            if dep.endswith('.scene'):scenes.append(dict(depot=dep,binding=meta,raw=rp));continue
            resources.append(dict(depot=dep,binding=meta,raw=rp,key='r'+str(len(resources)),graphs=graphs(dep),prefabs=root.get('phasePrefabs',[])))
        terminal=sorted(f for f in ownfacts if f in (prefix+'_finished',prefix+'_failed',ident+'_finished',ident+'_failed'))
        start=sorted(f for f in ownfacts if f in (prefix+'_start',ident+'_start'))
        outputs=[value(n['socketName']) for n in resources[0]['graphs'][0]['nodes'] if n['$type']=='questOutputNodeDefinition']
        gangs=[f.removeprefix('sts_').removesuffix('_retaliation') for f in external if f.startswith('sts_') and f.endswith('_retaliation')];assert len(gangs)<=1
        job=dict(id=ident,title=journals[ident]['title'].removeprefix('Gig: '),tag='PTFRU10_'+ident,region=ident.split('_')[1],entries=journals[ident]['journal_entries'],facts=sorted(ownfacts),start=start,terminal=terminal,resources=resources,scenes=scenes,parent=parent,outputs=outputs,companions=companions,mutations=mutations,legacy_tags=[],legacy_owner_facts=[],retaliation_dependency=bool(gangs),retaliation_gang=gangs[0] if gangs else '',counter=ident.split('_')[1]+'_sts_counter')
        # Each exact native success/outcome chain through its own district +1.
        found=[]
        for gp,gg in cg.items():
            if not gp.startswith('root/2/'):continue
            gn={n['id']:n for n in gg['nodes']};es=gg['edges'];ends=[n['id'] for n in gg['nodes'] if typ(n).get('factName')==job['counter']]
            if not ends:continue
            starts={n['id'] for n in gg['nodes'] if n['$type'] in ('questPauseConditionNodeDefinition','questConditionNodeDefinition') and facts(n) and all(f.startswith((prefix+'_',ident+'_')) for f in facts(n))}
            if not starts:continue
            kk=set().union(*(descendants(es,s) for s in starts)) & ancestors(es,set(ends))
            if not set(ends)&kk:continue
            kk |= ancestors(es,starts);kk.add(0)
            assert not [e for e in es if e[2] in kk and e[2] not in ends and e[0] not in kk and e[0]!=0]
            assert len(ends)==1
            assert gn[ends[0]]['type']=={'$type':'questSetVar_NodeType','factName':job['counter'],'setExactValue':0,'value':1}
            found.append(dict(id=ident,raw=craw,graph=gp,ids=sorted(kk),edges=[e for e in es if e[0] in kk and e[2] in kk],end=ends[0],nodes=[gn[i] for i in sorted(kk)]))
        assert len(found)<=1,(ident,'credit branches',len(found));credits+=found;job['credit_branch']=bool(found)
        if not found:
            assert ident=='sts_wbr_hil_06'
            warnings.append(dict(id=ident,kind='native_credit',reason='Native root/2/6 node5 watches hil_06_finished but has no outgoing edge. Rogue gig does not have a connected Wakako counter increment; no synthetic credit added.'))
        details.append(dict(id=ident,parent_types=sorted({n['$type'] for n in parent['ancestors']}),parent_nodes=parent['ancestors'],nested=parent['nested'],external_facts=sorted(external),companions=companions,main=main,closure=len(resources)+len(scenes)))
        jobs.append(job)
    for fixer in read(ROOT/'research/gig_restoration/family_b7/fixer_review.json'):
        path=fixer['path'];region=next((r for r,f in [('hey','padre'),('std','el_capitan'),('wat','reggie'),('wbr','wakako')] if '/'+f+'/' in path.replace('\\','/')),None)
        if not region:continue
        pin(path)
        for j in jobs:
            if j['region']!=region:continue
            target='points_of_interest/street_stories/'+j['id']
            for gg in fixer['graphs'][1:]:
                ns={n['id']:n for n in gg['nodes']};own={n['id'] for n in gg['nodes'] if typ(n).get('path',{}).get('realPath')==target}
                if not own:continue
                es=copy.deepcopy(gg['edges']);foreign={n['id'] for n in gg['nodes'] if n['$type']=='questJournalNodeDefinition' and n['id'] not in own};rebased=[]
                for i in sorted(foreign):
                    new=[[a[0],a[1],b[2],b[3]] for a in es if a[2]==i for b in es if b[0]==i];es=[e for e in es if e[0]!=i and e[2]!=i]+new;rebased+=new
                keep=ancestors(es,own);inputs=[i for i in keep if ns[i]['$type']=='questInputNodeDefinition'];assert len(inputs)==1
                maps.append(dict(id=j['id'],raw=raw(path),graph=gg['path'],ids=sorted(keep),nodes=[ns[i] for i in sorted(keep)],edges=[e for e in es if e[0] in keep and e[2] in keep],input=inputs[0],foreign_poi_contraction=sorted(foreign),rebased_edges=rebased))
    for j in jobs:j['map_count']=sum(m['id']==j['id'] for m in maps)
    q103='research/afterlife_world/rogue_owners/json/base/quest/main_quests/part1/q103/q103.questphase.json';pin(q103)
    dump('details_01.json',details)
    dump('build_plan_01.json',dict(status='U10_NATIVE_RECIPES_NOT_LIVE_PROOF',jobs=jobs,credits=credits,maps=maps,tiers=[],pins=pins,warnings=warnings,coverage=[dict(id=j['id'],title=j['title']) for j in jobs]))
    contracts=[]
    for j in jobs:
        equal={f:0 for f in j['facts']};equal['debug_sts_start']=0
        service={}
        if j['retaliation_dependency']:
            equal.update({'sts_'+j['retaliation_gang']+'_retaliation':0,'sts_gang_retaliation_cancel':0,'mws_chase_active':0})
            service={'PTFRU9_Retaliation_Issued':1,'PTFRU9_Retaliation_Fault':0,'PTFRU9_Retaliation_'+j['retaliation_gang']+'_Issued':1,'PTFRU9_Retaliation_'+j['retaliation_gang']+'_Fault':0}
        contracts.append(dict(id=j['id'],title=j['title'],tag=j['tag'],region=j['region'],journals=[{'path':e['path'],'class':e['className'],'states':[1]} for e in j['entries'] if e['className']!='gameJournalQuestDescription'],facts_equal=equal,fact_ranges={},service_facts_equal=service,terminal=j['terminal'],map_facts_zero=j['terminal'],map_root_states=['Inactive'],map_count=j['map_count'],resume='DEFER_UNSUPPORTED_PROGRESS_PRESERVE'))
        if j['id']=='sts_wbr_hil_06':
            contracts[-1]['journals'].append({'path':'quests/main_quest/act_01/q103_warhead','class':'gameJournalQuest','states':[3]})
            contracts[-1]['fact_ranges']={'q103_done':{'min':1,'max':2147483647},'q103_rogue_done':{'min':1,'max':2147483647}}
            contracts[-1]['pre_tower_history']={'required':True,'kind':'genuine_runtime_witness_before_q307_started','parent_journal':'quests/main_quest/act_01/q103_warhead','unknown':'DEFER_NO_RETROACTIVE_CERTIFICATE'}
    dump('contracts_01.json',dict(owners=contracts))
    print(json.dumps(dict(jobs=len(jobs),resources=sum(len(j['resources'])+len(j['scenes']) for j in jobs),credits=len(credits),maps=len(maps),pins=len(pins))))

if __name__=='__main__':main()
