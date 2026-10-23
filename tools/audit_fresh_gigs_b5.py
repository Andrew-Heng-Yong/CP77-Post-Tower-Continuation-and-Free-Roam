"""Two concrete fresh owners, not a universal fresh/replay certification."""
import json
from catalog_gig_rollout_r2 import ROOT, read, sha, walk
from audit_activity_lifecycles_b1 import scene_summary
from test_gig_pilot_r1 import Resource
from audit_activity_batches_b1 import flatten

OUT = ROOT / 'research/gig_restoration/fresh_b5'
IDS = ('sts_wbr_hil_07', 'sts_wbr_hil_01')

def main():
    assert not (OUT/'install_receipt.json').exists(), 'Installed evidence pinned'
    review = read(ROOT/'research/gig_restoration/batch_b4/source_review.json')
    pair = read(ROOT/'research/gig_restoration/rollout_r2/live_pair.json')
    jobs = []
    pins = {}
    for ident in IDS:
        j = next(j for j in review['jobs'] if j['id'] == ident)
        assert not j['unresolved'] and not j['cast'] and len(j['resources']) == 3
        resources=[]
        for res in j['resources']:
            p=ROOT/res['binding']['source']; assert sha(p)==res['binding']['sha256']
            raw=ROOT/str(p.relative_to(ROOT)).replace('\\','/').replace('/json/', '/raw/')[:-5]
            assert raw.exists() and res['binding']['embedded_index'] is None
            pins[str(p.relative_to(ROOT))]=sha(p);pins[str(raw.relative_to(ROOT))]=sha(raw)
            resources.append({'depot':res['depot'], 'json':str(p.relative_to(ROOT)), 'raw':str(raw.relative_to(ROOT)), 'raw_sha256':sha(raw), 'graphs':res['graphs'], 'prefabs':res['prefabs']})
        scenes=[]
        for s in j['scenes']:
            p=ROOT/s['source'];z=scene_summary(p);pins[s['source']]=sha(p)
            names={str(a['name']).lower() for a in z['actors']}
            assert not names.intersection({'johnny','panam','kerry','judy'})
            scenes.append(z)
        # Historical captured samples are evidence, not hard-coded admission totals.
        for row in pair['pair']:
            assert all(row['snapshot']['journal'][e['path']]['state']==1 for e in j['journal_entries'])
        jobs.append({'id':ident,'title':j['title'],'entries':j['journal_entries'],'resources':resources,'scenes':scenes,'parent':j['owner']['bindings'][0], 'fresh_only':True,'completed_replay':False})
    fixer=OUT/'sources/json/base/open_world/fixers/wakako/phases/wakako.questphase.json'
    r=Resource(read(fixer));g=flatten(r,r.obj['Data']['RootChunk'])[0];nodes={n['id']:n for n in g['nodes']}
    assert [(nodes[n]['condition']['type']['factName'],nodes[n]['condition']['type']['value']) for n in (72,81,82,83)] == [('wbr_sts_counter',2),('wbr_sts_counter',5),('wbr_sts_counter',7),('wbr_sts_counter',8)]
    assert nodes[107]['condition']['type']['factName']=='q103_rogue_done'
    assert [(nodes[n]['type']['factName'],nodes[n]['type']['setExactValue']) for n in (76,77,64,67,65,68,66,69)] == [(f,0) for f in ('sts_wbr_hil_tier_1_2','sts_wbr_jpn_tier_1_2','sts_wbr_hil_tier_2','sts_wbr_jpn_tier_2','sts_wbr_hil_tier_3','sts_wbr_jpn_tier_3','sts_wbr_hil_tier_4','sts_wbr_jpn_tier_4')]
    for p in (OUT/'sources').rglob('*'):
        if p.is_file():pins[str(p.relative_to(ROOT))]=sha(p)
    result={'status':'B5_TWO_FRESH_OWNER_SOURCE_AUDIT_NOT_ENGINE_PROOF','jobs':jobs,'pins':pins,'tier_thresholds':[2,5,7,8], 'tier_scope':'Wakako gig tiers only; no NCPD tiers, counter observers, default fixer owner or final rewards', 'vendor_scope':'Tyger native quest-owned clue and bounded vendor scenes retained; no global vendor owner restart. Admission rejects pre-existing default/drinking owner indicators.', 'entry_policy':'Native non-debug tier alternatives retained; fresh journals/local progress/item prerequisites. Explicit override skips history ONLY.'}
    (OUT/'source_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'fresh_owners':len(jobs),'pinned_inputs':len(pins)}))
if __name__=='__main__':main()
