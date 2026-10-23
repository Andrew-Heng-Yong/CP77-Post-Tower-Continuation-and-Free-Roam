"""Generate one shared runtime and CET roster from the frozen cohort."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent.parent
def main():
    cohort=json.loads((ROOT/'research/b0_ordinary_vendor_batch/cohort.json').read_text())
    manifest=json.loads((ROOT/'research/b0_ordinary_vendor_batch/validation/build_manifest.json').read_text())
    guards={k:v for k,v in manifest['common_guards'].items() if k!='PTFRB0OVB_Mode'}
    red=ROOT/'redscript/PTFR_B0_OrdinaryVendors/OrdinaryVendorDriver.reds.in'
    body=red.read_text()
    lines=[]
    for fact,want in guards.items():
        lines += ['    this.factReads += 1;',f'    if q.GetFact(n"{fact}") != {want} {{ eligible = false; }}']
    body=body.replace('@@GUARD_READS@@','\n'.join(lines))
    auto=[]
    for s in cohort['sites']:
        p=s['prefix']
        args=', '.join(f'n"{p}{suffix}"' for suffix in ('Enabled','Ready','Excluded','Near','Far'))
        auto.append(f'this.AutoSite(q, {args}, n"{s["gate"]}", COMMIT)')
    body=body.replace('@@AUTO_CHECKS@@','\n'.join('    pending = '+s.replace('COMMIT','false')+' || pending;' for s in auto))
    body=body.replace('@@AUTO_COMMITS@@','\n'.join('    '+s.replace('COMMIT','true')+';' for s in auto))
    lines=[]
    for s in cohort['sites']:
        p=s['prefix'];pos=s['position']
        lines.append(f'    this.UpdateSite(q, position, n"{p}Enabled", n"{p}Near", n"{p}Far", n"{s["gate"]}", {pos["x"]:.9f}, {pos["y"]:.9f}, {pos["z"]:.9f});')
    red.with_suffix('').write_text(body.replace('@@SITE_CALLS@@','\n'.join(lines)))
    lua=ROOT/'diagnostics/PTFR_B0_OrdinaryVendors/init.lua.in'
    entries=[]
    for s in cohort['sites']:
        p=s['position']
        entries.append('  {id="'+s['id']+'",prefix="'+s['prefix']+'",gate="'+s['gate']+'",category="'+s['category']+'",x='+str(p['x'])+',y='+str(p['y'])+',z='+str(p['z'])+'},')
    text=lua.read_text().replace('@@SITES@@','\n'.join(entries))
    text=text.replace('@@GUARDS@@',','.join(k+'='+str(v) for k,v in guards.items()))
    lua.with_suffix('').write_text(text)
    print(f'Rendered shared driver and CET roster: {len(entries)} sites; original scenes untouched')

if __name__=='__main__':main()
