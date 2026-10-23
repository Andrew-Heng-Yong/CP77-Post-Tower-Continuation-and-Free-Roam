"""Inspect the whole selected gig set for shared native-owner build rules.

This writes a new review only; previous installed builders are never rerun.
"""
import json
from collections import Counter, defaultdict
from catalog_gig_rollout_r2 import ROOT, read, sha, walk, value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

OUT = ROOT / 'research/gig_restoration/family_b7'
OLD = {'sts_wat_nid_02','sts_wat_nid_05','sts_bls_ina_07','sts_wbr_hil_07','sts_wbr_hil_01','sts_wbr_jpn_02'}

def main():
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'install_receipt.json').exists()
    review=read(ROOT/'research/gig_restoration/batch_b4/source_review.json')
    rows=[]
    for job in review['jobs']:
        blockers=[];calls=[];parent_summaries=[]
        for res in job['resources']:
            for g in res['graphs']:
                nodes={n['id']:n for n in g['nodes']}
                for n in g['nodes']:
                    if n['$type']!='questSceneNodeDefinition':continue
                    depot=value(n.get('sceneFile',{}).get('DepotPath')) or ''
                    if not any(v in depot.lower() for v in ('holocall','prebrief','debrief')):continue
                    outgoing=[e for e in g['edges'] if e[0]==n['id']]
                    incoming=[e for e in g['edges'] if e[2]==n['id'] and e[3]!='CutDestination']
                    rejected=[e for e in outgoing if e[1].lower().startswith('rejected')]
                    alternatives=[e[2:] for e in rejected] if len({e[1] for e in rejected})==1 else []
                    fallback=None
                    if not alternatives and len(incoming)==1:
                        src,port,_,_=incoming[0];up=nodes[src];cond=up.get('condition',{}).get('type',{})
                        if isinstance(cond,dict) and ((cond.get('$type')=='questPhoneMuted_ConditionType' and cond.get('inverted')==0 and port=='False') or (cond.get('$type')=='questContentLock_ConditionType' and cond.get('isContentBlocked')==0 and port=='True')):
                            alternatives=[e[2:] for e in g['edges'] if e[0]==src and e[1]==('True' if port=='False' else 'False')]
                            fallback=up
                    calls.append(dict(depot=res['depot'],graph=g['path'],node=n['id'],scene=depot,incoming=incoming,alternative=alternatives,outputs=outgoing,authored_fallback_condition=fallback))
                    if incoming and not alternatives:blockers.append('Call lacks direct rejected/text alternative: '+depot+':'+str(n['id']))
        for binding in job['owner']['bindings']:
            p=ROOT/binding['binding']['source'];r=SafeResource(read(p));embedded=binding['binding']['embedded_index']
            root=r.obj['Data']['RootChunk'] if embedded is None else r.obj['Data']['EmbeddedFiles'][embedded]['Content']
            allgraphs=flatten(r,root)
            graph=next(g for g in allgraphs if g['path']==binding['graph'])
            ancestors={binding['node']};previous=set()
            while previous!=ancestors:
                previous=set(ancestors)
                ancestors|={e[0] for e in graph['edges'] if e[2] in ancestors and e[3]!='CutDestination'}
            nodes=[n for n in graph['nodes'] if n['id'] in ancestors and n['id']!=binding['node']]
            nested=[g for g in allgraphs if any(g['path']==binding['graph']+'/'+str(n['id']) or g['path'].startswith(binding['graph']+'/'+str(n['id'])+'/') for n in nodes if n['$type']=='questPhaseNodeDefinition')]
            parent_summaries.append(dict(binding=binding,ancestors=nodes,nested=nested,edges=[e for e in graph['edges'] if e[0] in ancestors and e[2] in ancestors and e[3]!='CutDestination'],child=next(n for n in graph['nodes'] if n['id']==binding['node'])))
        if job['unresolved']:blockers+=['Source gap: '+d for d in job['unresolved']]
        if job['cast'] and set(job['cast'])-{'johnny'}:blockers.append('Excluded cast')
        if job['id'].startswith('sts_ep1_'):blockers.append('Dogtown companion owner/accounting review')
        if job['id'] in OLD:blockers.append('Existing adapter preserved')
        rows.append(dict(id=job['id'],title=job['selected_title'],resources=job['resources'],entries=job['journal_entries'],parents=parent_summaries,calls=calls,rewards=job['reward_nodes'],achievements=job['achievement_nodes'],start=job['start_markers'],terminal=job['terminal_markers'],facts=job['written_facts'],blockers=blockers))
    result=dict(status='B7_REVIEW_ONLY_NOT_RESTORATION',source_sha256=sha(ROOT/'research/gig_restoration/batch_b4/source_review.json'),jobs=rows)
    (OUT/'owner_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    summary=[]
    for j in rows:
        summary.append(dict(id=j['id'],title=j['title'],calls=len(j['calls']),blockers=j['blockers'],parent_types=dict(Counter(n['$type'] for p in j['parents'] for n in p['ancestors']))))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(candidates=[j['id'] for j in rows if not j['blockers']],blocked=[dict(id=j['id'],reasons=j['blockers']) for j in rows if j['blockers']]),indent=2))

if __name__=='__main__':main()
