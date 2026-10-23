"""Render the six-site native-entry/shared-exit runtime and passive logger."""
from plan_b0_ordinary_vendor_batch import ROOT, read

BASE=ROOT/'research/b0_vendor_variants'
sites=read(BASE/'cohort.json')['sites']
guards={k:v for k,v in read(BASE/'validation/build_manifest.json')['common_guards'].items() if k!='PTFRB0VV_Mode'}
red=ROOT/'redscript/PTFR_B0_VendorVariants/VendorVariantDriver.reds.in'
body=red.read_text().replace('@@GUARD_READS@@','\n'.join(f'    this.factReads += 1;\n    if q.GetFact(n"{f}") != {v} {{ eligible = false; }}' for f,v in guards.items()))
auto=[]; calls=[]; roster=[]
for s in sites:
    p=s['prefix'];pos=s['position']
    args=', '.join(f'n"{p}{suffix}"' for suffix in ('Enabled','Ready','Excluded','Near','Far'))
    auto.append(f'this.AutoSite(q, {args}, n"{s["gate"]}", COMMIT)')
    calls.append(f'    this.UpdateSite(q, position, n"{p}Enabled", n"{p}Near", n"{p}Far", n"{s["gate"]}", {pos["x"]:.9f}, {pos["y"]:.9f}, {pos["z"]:.9f}, {s["rearm_radius"]**2:.1f}, {s["exit_radius"]**2:.1f});')
    roster.append(f'{s["key"]}={{prefix="{p}",gate="{s["gate"]}",x={pos["x"]},y={pos["y"]},z={pos["z"]},exit={s["exit_radius"]}}}')
body=body.replace('@@AUTO_CHECKS@@','\n'.join('    pending = '+a.replace('COMMIT','false')+' || pending;' for a in auto))
body=body.replace('@@AUTO_COMMITS@@','\n'.join('    '+a.replace('COMMIT','true')+';' for a in auto))
red.with_suffix('').write_text(body.replace('@@SITE_CALLS@@','\n'.join(calls)))
lua=ROOT/'diagnostics/PTFR_B0_VendorVariants/init.lua.in'
lua.with_suffix('').write_text(lua.read_text().replace('@@SITES@@',',\n'.join(roster)).replace('@@GUARDS@@',','.join(f'{k}={v}' for k,v in guards.items())))
print('Rendered six-site automatic runtime and passive durable diagnostics')
