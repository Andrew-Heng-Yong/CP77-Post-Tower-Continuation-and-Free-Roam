"""Pinned original-entry recipes for the 17 exceptional whitelisted U9 gigs.

No previous recipe/evidence or game files are modified. No stock quest gameplay
is rewritten. Output is consumed by the new unified U9 native wrapper builder.
"""
import copy, json
from catalog_gig_rollout_r2 import ROOT, read, sha, value, walk
from inspect_special_gigs_u9 import graphs,AuditResource
from audit_activity_batches_b1 import flatten

OUT=ROOT/'research/gig_restoration/special_gigs_u9'
OLD={'sts_wat_nid_02':'PTFRG1','sts_wat_nid_05':'PTFRG2','sts_bls_ina_07':'PTFRG3',
     'sts_wbr_hil_07':'PTFRB5_H7','sts_wbr_hil_01':'PTFRB5_H1','sts_wbr_jpn_02':'PTFRB6_J2'}
EP1='research/gig_restoration/rollout_r2/native_sources/json/ep1/openworld/street_stories/ep1_street_stories.questphase.json'
COUNTER='research/gig_restoration/fixer_sources/json/ep1/openworld/fixers/mr_hands/phases/mr_hands_fixers_loop.questphase.json'

def reach(edges,initial):
    seen=set(initial)
    while True:
        nxt=seen|{e[2] for e in edges if e[0] in seen and e[3]!='CutDestination'}
        if seen==nxt:return seen
        seen=nxt

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'install_receipt.json').exists()
    old=read(ROOT/'research/gig_restoration/family_b7/owner_review.json')
    plan=read(ROOT/'research/gig_restoration/family_b7/build_plan.json')
    batch=read(ROOT/'research/gig_restoration/batch_b4/source_review.json')
    jobs=[];pins={};reviews=[];ep={g['path']:g for g in graphs(EP1)}
    def pin(path):
        pins[path]=sha(ROOT/path)
        raw=path.replace('/json/','/raw/')[:-5]
        assert (ROOT/raw).exists(),raw
        pins[raw]=sha(ROOT/raw)
        return raw
    epraw=pin(EP1);counterraw=pin(COUNTER)
    for original in old['jobs']:
        if original['id'] in {j['id'] for j in plan['jobs']}:continue
        j=copy.deepcopy(original);id=j['id'];p=j['parents'][0]
        assert len(j['parents'])==1,id
        normal=[n for n in p['ancestors'] if n['$type']=='questInputNodeDefinition' and value(n['socketName']).lower() in ('in','in1')]
        assert len(normal)==1,id
        entry=normal[0]['id'];live=reach(p['edges'],[entry]);removed=[n['id'] for n in p['ancestors'] if n['id'] not in live]
        # Unconnected original repair/debug inputs are not part of normal startup.
        p['ancestors']=[n for n in p['ancestors'] if n['id'] in live]
        p['edges']=[e for e in p['edges'] if e[0] in live and e[2] in live]
        p['raw']=pin(p['binding']['binding']['source']);p['input_node']=entry;p['edits']=[]
        p['child_inputs']=sorted({e[3] for e in p['edges'] if e[2]==p['child']['id']})
        p['child_input']=p['child_inputs'][0];p['preserve_child_edges']=len(p['child_inputs'])>1
        prefix=p['binding']['graph']+'/'
        livephase={n['id'] for n in p['ancestors'] if n['$type']=='questPhaseNodeDefinition'}
        p['nested']=[g for g in p['nested'] if int(g['path'][len(prefix):].split('/')[0]) in livephase]
        resources=[];facts=set(j['start']+j['terminal'])
        local='_'.join(id.split('_')[-2:]);prefixes=(id,local,id.removeprefix('sts_'))
        for index,r in enumerate(j['resources']):
            raw=pin(r['binding']['source']);assert pins[r['binding']['source']]==r['binding']['sha256']
            r['raw']=raw;r['key']='r'+str(index);resources.append(r)
            for g in r['graphs']:
                for v in walk(g['nodes']):
                    f=value(v.get('factName',''))
                    if isinstance(f,str) and f.startswith(prefixes):facts.add(f)
        if id=='sts_ep1_08':
            # The old B4 resolver did not collect the independently extracted
            # gameplay definition. It exists in the official source extraction.
            dep='ep1\\openworld\\street_stories\\sts_ep1_08\\phases\\sts_ep1_08_gameplay.questphase'
            rp='research/gig_restoration/batch_b4/sources/json/'+dep.replace('\\','/')+'.json'
            rr=pin(rp);ar=AuditResource(read(ROOT/rp));gg=flatten(ar,ar.obj['Data']['RootChunk'])
            resources.append(dict(depot=dep,binding=dict(source=rp,sha256=pins[rp],embedded_index=None),raw=rr,key='r'+str(len(resources)),graphs=gg,prefabs=read(ROOT/rp)['Data']['RootChunk'].get('phasePrefabs',[]),native_orphan_edges=ar.orphan_edges))
            for v in walk(gg):
                f=value(v.get('factName',''))
                if isinstance(f,str) and f.startswith(prefixes):facts.add(f)
        assert value(p['child']['phaseResource']['DepotPath'])==resources[0]['depot'],id
        native=resources[0]['graphs'][0]
        outputs=[value(n['socketName']) for n in native['nodes'] if n['$type']=='questOutputNodeDefinition']
        terminal=list(j['terminal'])
        if id=='sts_ep1_13':terminal.append('sts_ep1_13_finished');facts.add('sts_ep1_13_finished')
        scenes=next(x['scenes'] for x in batch['jobs'] if x['id']==id)
        for s in scenes:
            pin(s['source'])
            for v in walk(read(ROOT/s['source'])):
                f=value(v.get('factName',''))
                if isinstance(f,str) and f.startswith(prefixes):facts.add(f)
        companions=[]
        if id.startswith('sts_ep1_'):
            cleanup=ep['root/51'];cn={n['id']:n for n in cleanup['nodes']}
            main=ep['root/50'];mn={n['id']:n for n in main['nodes']}
            outputs=sorted({e[1] for e in main['edges'] if e[0]==p['child']['id']})
            for edge in main['edges']:
                if edge[0]!=p['child']['id']:continue
                parentport=value(mn[edge[2]]['socketName'])
                ci=next(n['id'] for n in cleanup['nodes'] if n['$type']=='questInputNodeDefinition' and value(n['socketName'])==parentport)
                ce=[e for e in cleanup['edges'] if e[0]==ci];assert len(ce)==1
                cleanupnode=cn[ce[0][2]];depot=value(cleanupnode['phaseResource']['DepotPath'])
                cpath='research/gig_restoration/rollout_r2/native_sources/json/'+depot.replace('\\','/')+'.json'
                craw=pin(cpath)
                cgraphs=graphs(cpath)
                companions.append(dict(kind='cleanup',source_graph='root/51',source_node=cleanupnode['id'],source_raw=epraw,
                    from_output=edge[1],input=ce[0][3],depot=depot,raw=craw,
                    outputs=[value(n['socketName']) for n in cgraphs[0]['nodes'] if n['$type']=='questOutputNodeDefinition']))
            bug=next(n for n in ep['root/52']['nodes'] if n['$type']=='questPhaseNodeDefinition' and id in value(n['phaseResource']['DepotPath']))
            bdepot=value(bug['phaseResource']['DepotPath']);braw=pin('research/gig_restoration/rollout_r2/native_sources/json/'+bdepot.replace('\\','/')+'.json')
            companions.append(dict(kind='parallel_bugfix',source_graph='root/52',source_node=bug['id'],source_raw=epraw,input='In1',depot=bdepot,raw=braw))
            if id=='sts_ep1_04':
                after=ep['root/53']['nodes'][1];dep=value(after['phaseResource']['DepotPath'])
                ar=pin('research/gig_restoration/rollout_r2/native_sources/json/'+dep.replace('\\','/')+'.json')
                companions.append(dict(kind='after_cleanup',source_graph='root/53',source_node=after['id'],source_raw=epraw,input='In1',from_output='Out1',depot=dep,raw=ar))
        blocked=[]
        region='std' if id=='sts_pac_wwd_05' else ('ep1' if id.startswith('sts_ep1_') else id.split('_')[1])
        row=dict(id=id,title=j['title'],tag='PTFRB7_'+id.removeprefix('sts_'),legacy_tags=[OLD[id]] if id in OLD else [],region=region,
            entries=j['entries'],facts=sorted(facts),start=j['start'],terminal=sorted(set(terminal)),resources=resources,parent=p,outputs=outputs,calls=j['calls'],mutations=[],
            companions=companions,shared_gate=('ep1_tier3' if id in ('sts_ep1_06','sts_ep1_07') else None),blockers=blocked)
        jobs.append(row)
        if row['shared_gate']:p['shared_gate_node']=9
        reviews.append(dict(id=id,title=j['title'],normal_input=entry,removed_unreachable_ancestor_nodes=removed,child_inputs=p['child_inputs'],outputs=outputs,companions=companions,
            original_blockers=j['blockers'],notes=['Original gameplay is referenced unchanged; unreachable legacy references are not rewritten.']))
    assert len(jobs)==17
    cg=graphs(COUNTER)[0];cn={n['id']:n for n in cg['nodes']};credits=[]
    for j in jobs:
        if not j['id'].startswith('sts_ep1_'):continue
        nodes=[n for n in cg['nodes'] if n.get('condition',{}).get('type',{}).get('factName')==j['id']+'_finished']
        assert len(nodes)==1
        watch=nodes[0]['id'];ids=[0,watch,14]
        edges=[e for e in cg['edges'] if e[0] in ids and e[2] in ids]
        assert edges==[[0,'Out',watch,'In'],[watch,'Out',14,'In']]
        assert cn[14]['type']=={'$type':'questSetVar_NodeType','factName':'ep1_sts_counter','setExactValue':0,'value':1}
        credits.append(dict(id=j['id'],raw=counterraw,graph='root',ids=ids,edges=edges,end=14,nodes=[cn[i] for i in ids]))
    result=dict(status='SOURCE_RECIPES_ONLY_REQUIRES_UNIFIED_BUILDER_AND_TESTS',jobs=jobs,pins=pins,credits=credits,
        ep1_parent=EP1,ep1_parent_raw=epraw,ep1_counter_raw=counterraw,
        shared_gate=dict(graph='root/50/9',raw=epraw,source_node=9,consumers=['sts_ep1_06','sts_ep1_07'],requirement='One shared original phase owner; fan its Out1 pulse to only admitted selected consumers. Never copy same message owner per gig.'),reviews=reviews)
    (OUT/'recipes.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'jobs':len(jobs),'pins':len(pins),'legacy_base':len(OLD),'special_base':2,'dogtown':9}))

if __name__=='__main__':main()
