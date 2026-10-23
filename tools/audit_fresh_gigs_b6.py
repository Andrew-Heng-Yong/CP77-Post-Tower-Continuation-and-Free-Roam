"""New Jpn02 source audit. Never reruns or changes installed revision evidence."""
import json
from catalog_gig_rollout_r2 import ROOT, read, sha, walk
from test_gig_pilot_r1 import Resource
from audit_activity_batches_b1 import flatten
from audit_activity_lifecycles_b1 import scene_summary

OUT = ROOT/'research/gig_restoration/fresh_b6'
ID = 'sts_wbr_jpn_02'

def main():
    assert not (OUT/'install_receipt.json').exists()
    OUT.mkdir(exist_ok=True)
    j = next(x for x in read(ROOT/'research/gig_restoration/batch_b4/source_review.json')['jobs'] if x['id']==ID)
    assert not j['unresolved'] and not j['cast'] and len(j['resources'])==3
    pins={}; resources=[]; brief=[]
    for item in j['resources']:
        p=ROOT/item['binding']['source']; assert sha(p)==item['binding']['sha256']
        raw=ROOT/str(p.relative_to(ROOT)).replace('\\','/').replace('/json/','/raw/')[:-5]
        assert raw.exists() and item['binding']['embedded_index'] is None
        pins[str(p.relative_to(ROOT))]=sha(p);pins[str(raw.relative_to(ROOT))]=sha(raw)
        r=Resource(read(p)); graphs=flatten(r,r.obj['Data']['RootChunk'])
        resources.append(dict(depot=item['depot'],json=str(p.relative_to(ROOT)),raw=str(raw.relative_to(ROOT)),graphs=graphs,prefabs=item['prefabs']))
        for g in graphs:
            brief.append(dict(depot=item['depot'],graph=g['path'],nodes=g['nodes'],edges=g['edges']))
    scenes=[]
    for s in j['scenes']:
        p=ROOT/s['source']; summary=scene_summary(p)
        assert not {str(a['name']).lower() for a in summary['actors']}&{'johnny','panam','kerry','judy'}
        pins[s['source']]=sha(p);scenes.append(summary)
    parent=j['owner']['bindings'][0]
    p=ROOT/parent['binding']['source'];pins[parent['binding']['source']]=sha(p)
    result=dict(status='SOURCE_REVIEW_NOT_NATIVE_GAMEPLAY_PROOF',id=ID,title=j['title'],entries=j['journal_entries'],resources=resources,scenes=scenes,parent=parent,pins=pins)
    (OUT/'source_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (OUT/'graph_review.json').write_text(json.dumps(brief,indent=2)+'\n',encoding='utf-8')
    summaries=[]
    for g in brief:
        rows=[]
        for n in g['nodes']:
            if any(s in n['$type'] for s in ('FactsDB','Reward','Phone','Journal','Phase','Scene','Condition','Input','Output')):
                rows.append(n)
        summaries.append(dict(depot=g['depot'],graph=g['graph'],nodes=rows,edges=g['edges']))
    (OUT/'lifecycle_brief.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(id=ID,entries=result['entries'],parent=parent,graphs=[(x['depot'],x['graph'],len(x['nodes'])) for x in brief],scenes=len(scenes))))

if __name__=='__main__':main()
