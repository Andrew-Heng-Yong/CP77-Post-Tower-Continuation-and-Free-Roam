"""Render bounded native-entry bar driver and read-only diagnostics."""
from plan_b0_ordinary_vendor_batch import ROOT,read
from audit_b0_ordinary_bars import DEST
sites=read(DEST/'cohort.json')['sites']
guards={k:v for k,v in read(DEST/'validation/build_manifest.json')['common_guards'].items() if k!='PTFRB0BAR_Mode'}
auto=[];calls=[];roster=[]
for s in sites:
    p=s['prefix'];pos=s['position']
    args=', '.join(f'n"{p}{suffix}"' for suffix in ('Enabled','Ready','Excluded','Near','Far'))
    auto.append(f'this.AutoSite(q, {args}, n"{s["gate"]}", COMMIT)')
    args=', '.join(f'n"{p}{suffix}"' for suffix in ('Enabled','Near','Far'))
    calls.append(f'    this.UpdateSite(q, player, position, {args}, n"{s["gate"]}", n"{s["drinking_fact"]}", {pos["x"]:.9f}, {pos["y"]:.9f}, {pos["z"]:.9f}, {s["rearm_radius"]**2:.1f}, {s["exit_radius"]**2:.1f});')
    roster.append(f'{s["key"]}={{prefix="{p}",gate="{s["gate"]}",drink="{s["drinking_fact"]}",x={pos["x"]},y={pos["y"]},z={pos["z"]}}}')
red=ROOT/'redscript/PTFR_B0_OrdinaryBars/OrdinaryBarDriver.reds.in'
body=red.read_text().replace('@@AUTO_CHECKS@@','\n'.join('    pending = '+a.replace('COMMIT','false')+' || pending;' for a in auto))
body=body.replace('@@AUTO_COMMITS@@','\n'.join('    '+a.replace('COMMIT','true')+';' for a in auto))
body=body.replace('@@GUARDS@@','\n'.join(f'    if this.Read(q,n"{k}") != {v} {{ eligible = false; }}' for k,v in guards.items()))
red.with_suffix('').write_text(body.replace('@@SITE_CALLS@@','\n'.join(calls)))
lua=ROOT/'diagnostics/PTFR_B0_OrdinaryBars/init.lua.in'
lua.with_suffix('').write_text(lua.read_text().replace('@@SITES@@',',\n'.join(roster)).replace('@@GUARDS@@',','.join(f'{k}={v}' for k,v in guards.items())))
print('Rendered four-bar automatic driver and strictly read-only durable logger')
