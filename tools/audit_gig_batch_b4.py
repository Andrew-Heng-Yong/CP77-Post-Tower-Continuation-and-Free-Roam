"""All selected gig owner/scene closure and mutation inventory, not admission."""
import json,re
from collections import defaultdict,Counter
from catalog_gig_batch_b4 import ROOT,OUT,library,LIBROOTS
from catalog_gig_rollout_r2 import read,sha,value,walk
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten,references

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    lib=library();scenes={}
    for folder in LIBROOTS+[ROOT/'research/gig_restoration/expanded_scene_sources/json',ROOT/'research/activity_batches_b1/gig_sources/json',ROOT/'research/gig_restoration/minefield_g3/sources/json']:
        if folder.exists():
            for p in folder.rglob('*.scene.json'):scenes[str(p.relative_to(folder))[:-5].replace('/','\\')]=p
    parents=defaultdict(list);graph_errors={}
    for depot,(obj,root,meta) in lib.items():
        if root.get('$type')!='questQuestPhaseResource':continue
        r=SafeResource(obj)
        try:graphs=flatten(r,root)
        except (KeyError,TypeError) as error:
            graph_errors[depot]=str(error);continue
        for graph in graphs:
            for node in graph['nodes']:
                target=value(node.get('phaseResource',{}).get('DepotPath'))
                if target and target!='0':
                    parents[target].append({'parent':depot,'graph':graph['path'],'node':node['id'],'incoming':[e for e in graph['edges'] if e[2]==node['id'] and e[3]!='CutDestination'],'binding':meta})
    jobs=[];missing=set();source_inputs={}
    for job in read(OUT/'catalogue.json')['jobs']:
        known={m['depot_path'] for m in job['native_resources']}
        candidates=[]
        for depot in known:
            external=[p for p in parents[depot] if p['parent'] not in known and p['incoming']]
            if external:candidates.append({'depot':depot,'bindings':external})
        # Explicit normal district/root binding, rather than catalogue ordering
        # or assuming every prefab-bearing combat/cleanup resource is an owner.
        mains=[c for c in candidates if any(b['graph']=='root' for b in c['bindings'])]
        if not mains:
            mains=[c for c in candidates if any(b['graph']=='root/50' and b['parent'].endswith('ep1_street_stories.questphase') for b in c['bindings'])]
        if not mains and len(candidates)==1 and all(b['parent'].endswith('street_stories_dlc.questphase') for b in candidates[0]['bindings']):
            mains=candidates
        if len(mains)!=1:
            jobs.append(job|{'disposition':'OWNER_BINDING_PENDING','candidates':candidates});continue
        first=mains[0]['depot'];pending=[first];seen=set();resources=[];scene_rows=[];unresolved=[];cast=set();mutations=[]
        while pending:
            depot=pending.pop()
            if depot in seen:continue
            seen.add(depot)
            if depot.endswith('.questphase') and depot in lib:
                obj,root,meta=lib[depot];r=SafeResource(obj)
                try:graphs=flatten(r,root)
                except (KeyError,TypeError) as error:
                    # Selected malformed/unsupported graph is an explicit gap,
                    # never an empty graph or a source-closed admission.
                    graph_errors[depot]=str(error);unresolved.append(depot);missing.add(depot);continue
                source_inputs[meta['source']]=meta['sha256'];resources.append({'depot':depot,'binding':meta,'graphs':graphs,'prefabs':root.get('phasePrefabs',[])})
                pending+=references(root,'phaseResource')+references(root,'sceneFile')
                for graph in graphs:
                    for node in graph['nodes']:
                        if node['$type'] in ('questFactsDBManagerNodeDefinition','questJournalNodeDefinition','questEntityManagerNodeDefinition','questCombatNodeDefinition','questItemManagerNodeDefinition','questRewardManagerNodeDefinition') or any(v.get('$type') in ('questGiveReward_NodeType','questInjectLoot_NodeType','questGiveItem_NodeType','questAddRemoveItem_NodeType') for v in walk(node)):
                            mutations.append({'depot':depot,'graph':graph['path'],'node':node})
                        for v in walk(node):
                            p=v.get('realPath','')
                            if isinstance(p,str) and p.startswith(('contacts/panam/','contacts/judy/','contacts/kerry/')):cast.add(p.split('/')[1])
            elif depot.endswith('.scene') and depot in scenes:
                p=scenes[depot];obj=read(p);source=str(p.relative_to(ROOT)).replace('\\','/');source_inputs[source]=sha(p)
                actors=[]
                for v in walk(obj):
                    if v.get('$type') in ('scnActorDef','scnPlayerActorDef'):
                        name=value(v.get('actorName',v.get('playerName')));actors.append({'name':name,'acquisition':v.get('acquisitionPlan'),'spawn':v.get('spawnDespawnParams'),'community':v.get('communityParams'),'context':v.get('findActorInContextParams')})
                        text=json.dumps(v).lower()
                        for who in ('panam','judy','kerry','johnny'):
                            if re.search(r'(?<![a-z])'+who+r'(?![a-z])',text):cast.add(who)
                        if 'character.silverhand' in text:cast.add('johnny')
                scene_rows.append({'depot':depot,'source':source,'sha256':sha(p),'actors':actors})
                pending+=references(obj,'phaseResource')+references(obj,'sceneFile')
            else:unresolved.append(depot);missing.add(depot)
        facts=[];reward=[];foreign=[];hazards=[];achievements=[]
        for mutation in mutations:
            node=mutation['node']
            for v in walk(node):
                if v.get('$type')=='questSetVar_NodeType':
                    facts.append(v['factName'])
                    if v['factName'].endswith('_achievement'):achievements.append(mutation)
                if v.get('$type')=='questGiveReward_NodeType':reward.append(mutation)
                if v.get('$type') in ('questInjectLoot_NodeType','questGiveItem_NodeType','questAddRemoveItem_NodeType'):hazards.append(mutation)
                if v.get('realPath','').startswith('quests/') and job['id'] not in v['realPath']:foreign.append(mutation)
        short='_'.join(job['id'].split('_')[-2:]);prefixes=(short,job['id'],job['id'].removeprefix('sts_'))
        terminal=sorted({f for f in facts if any(f in (p+'_finished',p+'_failed') for p in prefixes)})
        start=sorted({f for f in facts if any(f==p+'_start' for p in prefixes)})
        jobs.append(job|{'owner':mains[0],'resources':resources,'scenes':scene_rows,'unresolved':sorted(unresolved),'cast':sorted(cast),'written_facts':sorted(set(facts)),'start_markers':start,'terminal_markers':terminal,'achievement_nodes':achievements,'reward_nodes':reward,'item_nodes':hazards,'foreign_journal_nodes':foreign,'disposition':'CAST_EXCLUDED' if cast&{'panam','judy','kerry'} else 'SOURCE_CLOSURE_PENDING' if unresolved else 'SOURCE_CLOSED_REQUIRES_STAGE_REWARD_ACCOUNT_AUDIT'})
    result={'status':'ALL_72_SOURCE_REVIEW_NOT_RUNTIME_RESTORATION','jobs':jobs,'source_inputs':source_inputs,'missing_resources':sorted(missing),'unrelated_graph_errors':graph_errors,'counts':dict(Counter(j['disposition'] for j in jobs)),'game_writes':0,'direct_save_writes':0}
    (OUT/'source_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'counts':result['counts'],'missing':result['missing_resources'],'bindings_pending':[j['id'] for j in jobs if j['disposition']=='OWNER_BINDING_PENDING'],'closed_count':sum(not j.get('unresolved') and 'owner' in j for j in jobs)},indent=2))
if __name__=='__main__':main()
