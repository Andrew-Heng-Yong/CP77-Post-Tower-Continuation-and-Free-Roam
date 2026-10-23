"""Bounded R3 booth/source trace audit. Read-only game access; workspace output."""
import json
import hashlib
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'
OUT=BASE/'booth_r6'
LOG=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Behavior_Audit\afterlife_behavior_20261006T035459Z.jsonl')
def value(x): return x.get('$value',x) if isinstance(x,dict) else x
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def main():
    spots=[]
    for p in sorted((BASE/'idles_r3/entry_sources/json/base/workspots').rglob('*.json')):
        data=json.loads(p.read_text()); nodes=list(walk(data))
        trees=[n for n in nodes if n.get('$type')=='workWorkspotTree']
        summaries=[]
        for n in nodes:
            if n.get('$type') not in ('workSequence','workRandomList'): continue
            summaries.append({k:value(v) for k,v in n.items() if k not in ('list','conditions','items')})
        spots.append({'path':str(p.relative_to(ROOT)),'types':dict(Counter(n.get('$type') for n in nodes if str(n.get('$type','')).startswith('work'))),'sequences':summaries,'tree_settings':[{k:value(v) for k,v in t.items() if k not in ('rootEntry','finalAnimsets','animsets','workspotRig','tags','properties')} for t in trees]})
    raw=LOG.read_bytes(); lines=raw.splitlines(); rows=[]
    for line in lines:
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: pass
    trace=[]; previous=None
    for r in rows:
        actors=[{k:a.get(k) for k in ('id','position','in_workspot','in_scene','in_combat','classification','unowned_stationary_seconds')} for a in r.get('actors',[]) if 'Character.q005_afterlife_mercenary_male ' in a.get('record','')]
        state=[(a['id'],a['in_workspot'],a['in_scene'],a['position']) for a in actors]
        if state!=previous:
            trace.append({'utc':r.get('utc'),'elapsed':r.get('elapsed'),'facts':{k:v for k,v in r.get('facts',{}).items() if k.startswith('PTFRAL3_') or k.startswith('PTFRAL2_')},'actors':actors}); previous=state
    report={'log':str(LOG),'sha256_bounded_snapshot':hashlib.sha256(raw).hexdigest(),'rows':len(rows),'first':rows[0].get('utc'),'last':rows[-1].get('utc'),'transitions':trace,'spots':spots,'limits':'Sparse sampled state, original diagnostic lacks correct exact binding getter. Workspot flag not animation proof; no render/despawn inference.'}
    OUT.mkdir(exist_ok=True)
    (OUT/'source_trace_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'first':report['first'],'last':report['last'],
                     'transition_count':len(trace),'spot_sequences':[{ 'path':s['path'],
                     'sequences':s['sequences']} for s in spots]},indent=2))
if __name__=='__main__': main()
