import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
data=json.loads((ROOT/'research/restoration_baseline/rules.json').read_text())
template=ROOT/'redscript/PTFR_RestorationBaseline/RestorationBaseline.reds.in'
text=template.read_text()
lines=[]
for r in data['rules']:
    conditions=[f'q.GetFact(n"{f}") == {v}' for f,v in r['guards'].items()]
    if r['kind'] in ('geometry','h10','coyote'):conditions.insert(0,{'geometry':'corridor','h10':'h10','coyote':'coyoteOutside'}[r['kind']])
    lines.append('    // '+r['name']+'\n    if '+' &&\n       '.join(conditions)+' {\n      this.Set(q,n"'+r['write']+'",1);\n    }')
text=text.replace('@@RULES@@','\n'.join(lines))
text=text.replace('@@COMMON@@','\n'.join(f'    if q.GetFact(n"{f}") != {v} {{ eligible = false; }}' for f,v in data['common'].items()))
text=text.replace('@@WILSON@@','\n'.join(f'      if q.GetFact(n"{f}") != {v} {{ allowed = false; }}' for f,v in data['wilson'].items()))
lines=[]
for s in data['vendors']:
    p=s['prefix'];args=', '.join('n"'+p+n+'"' for n in ('Enabled','Near','Far'))
    lines.append(f'    this.Far(q,p,{args},n"{s["gate"]}",{s["x"]:.9f},{s["y"]:.9f},{s["z"]:.9f});')
template.with_suffix('').write_text(text.replace('@@FAR@@','\n'.join(lines)))
facts=set(data['common'])|{'PTFRBASE_Ready','PTFRBASE_Suspended','PTFRALMA1_Requested','PTFRB0ALM_Enabled','PTFRB0ALM_Near','PTFRB0ALM_Active','PTFRALMA2_Requested','PTFRALMA2_Active','PTFRALMA2_Interrupted','PTFRALMA2_SceneRequests','PTFRALMA2_SceneReturns','PTFRCM2_Requested','PTFRCM2_Active','PTFRCM2_SceneRequests','PTFRCM2_SceneReturns'}
for r in data['rules']:facts.update(r['guards']);facts.add(r['write'])
for s in data['vendors']:
    facts.add(s['gate']);facts.update(s['prefix']+suffix for suffix in ['Enabled','Ready','Near','Far','SpawnActionOut','DespawnActionOut','ActorDistanceGate'])
for src in ['b0_ordinary_vendor_batch','b0_vendor_variants']:
    for s in json.loads((ROOT/f'research/{src}/cohort.json').read_text())['sites']:
        facts.add(s['gate']);facts.update(s['prefix']+n for n in ['Enabled','Ready','Near','Far','Entries','Exits'])
facts.update(['PTFRB0OVB_Mode','PTFRB0OVB_Suspended','PTFRB0VV_Mode','PTFRB0VV_Suspended','PTFRB0DOVC_Enabled','PTFRB0DOVN_Enabled','PTFRB0DOV_Suspended'])
lua=ROOT/'diagnostics/PTFR_RestorationBaseline/init.lua.in'
lua.with_suffix('').write_text(lua.read_text().replace('@@FACTS@@',','.join(json.dumps(f) for f in sorted(facts))))
print('Rendered Baseline-R1 with',len(data['rules']),'startup rules and',len(facts),'read-only diagnostic facts')
