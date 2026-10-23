import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'research/b0_deferred_ordinary'
sites=json.loads((BASE/'sites.json').read_text())
guards=json.loads((BASE/'validation/build_manifest.json').read_text())['common_guards']
red=ROOT/'redscript/PTFR_B0_DeferredVendors/DeferredVendorDriver.reds.in'
calls=[]
for s in sites:
    positive=' && '.join('q.GetFact(n"'+f+'") > 0' for f in [s['gate'],*s['extra_positive_gates']])
    names=', '.join('n"'+s['prefix']+n+'"' for n in ('Ready','Enabled','Excluded','Near','Approach','Far'))
    calls.append(f'    this.Site(q, position, safe, {positive}, suspended, {names}, {s["x"]:.9f}, {s["y"]:.9f}, {s["z"]:.9f}, {s["approach_radius"]**2}.0, {s["exit_radius"]**2}.0);')
red.with_suffix('').write_text(red.read_text().replace('@@GUARDS@@','\n'.join(f'    if q.GetFact(n"{f}") != {v} {{ eligible = false; }}' for f,v in guards.items())).replace('@@SITES@@','\n'.join(calls)))
lua=ROOT/'diagnostics/PTFR_B0_DeferredVendors/init.lua.in'
roster=[]
for s in sites:
    extra='{'+','.join(json.dumps(f) for f in s['extra_positive_gates'])+'}'
    roster.append(s['key']+'={prefix="'+s['prefix']+'",gate="'+s['gate']+'",extra='+extra+',x='+str(s['x'])+',y='+str(s['y'])+',z='+str(s['z'])+',exit='+str(s['exit_radius'])+'}')
lua.with_suffix('').write_text(lua.read_text().replace('@@SITES@@',','.join(roster)).replace('@@GUARDS@@',','.join(f'{k}={v}' for k,v in guards.items())))
print('Rendered two-site automatic driver and optional diagnostics')
