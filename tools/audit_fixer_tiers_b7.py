import json
from collections import Counter
from catalog_gig_rollout_r2 import ROOT, read, walk, sha
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
OUT=ROOT/'research/gig_restoration/family_b7'

def main():
    assert not (OUT/'install_receipt.json').exists()
    rows=[]
    for p in (OUT/'fixers/json').rglob('*.questphase.json'):
        r=SafeResource(read(p));graphs=flatten(r,r.obj['Data']['RootChunk'])
        row=dict(path=str(p.relative_to(ROOT)),sha256=sha(p),graphs=graphs)
        rows.append(row)
        counters=sorted({v['factName'] for g in graphs for n in g['nodes'] for v in walk(n) if 'counter' in v.get('factName','')})
        tiers=[]
        for g in graphs:
            for n in g['nodes']:
                if 'Condition' not in n['$type']:continue
                conditions=[v for v in walk(n) if v.get('$type')=='questVarComparison_ConditionType' and v.get('factName') in counters]
                if conditions:tiers.append(dict(graph=g['path'],id=n['id'],conditions=conditions,out=[e for e in g['edges'] if e[0]==n['id']]))
        print(json.dumps(dict(fixer=p.stem,counters=counters,tiers=tiers)))
    (OUT/'fixer_review.json').write_text(json.dumps(rows,indent=2)+'\n')

if __name__=='__main__':main()
