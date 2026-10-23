"""Automatic bootstrap contract model + source checks, not an engine test."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'research/b0_ordinary_vendor_batch'
cohort = json.loads((OUT / 'cohort.json').read_text())['sites']
guards = json.loads((OUT / 'validation/build_manifest.json').read_text())['common_guards']
guards = {k: v for k, v in guards.items() if k != 'PTFRB0OVB_Mode'}
driver = ROOT / 'redscript/PTFR_B0_OrdinaryVendors/OrdinaryVendorDriver.reds'
text = driver.read_text()
assert '@@' not in text
assert text.index('if !eligible') < text.index('this.AutoEnable(q, player);')
assert text.index('if !pending') < text.index('GetSceneSystem')
assert 'this.ReadFact(q, n"PTFRB0OVB_Suspended") != 0' in text
assert 'mode != 1 && (challenge == 0 || challenge == ack)' not in text
for expr in ('enabled) != 0', 'excluded) != 0', 'ready) != 1', 'near) != 0', 'far) != 0', 'gate) <= 0'):
    assert expr in text
for s in cohort:
    p = s['prefix']
    args = ', '.join(f'n"{p}{suffix}"' for suffix in ('Enabled','Ready','Excluded','Near','Far'))
    for commit in ('false', 'true'):
        assert f'this.AutoSite(q, {args}, n"{s["gate"]}", {commit})' in text

def seed():
    f = dict(guards)
    for s in cohort:
        f[s['gate']] = 1
        f[s['prefix'] + 'Ready'] = 1
    return f

def tick(f, *, scene=False, combat=False, workspot=False, player=True):
    # A deliberately small semantic model of AutoSite/AutoEnable guards.
    writes = []
    if not player or any(f.get(k, 0) != v for k,v in guards.items()) or f.get('PTFRB0OVB_Suspended',0) != 0:
        return writes
    pending = [s for s in cohort if all(f.get(s['prefix']+x,0)==0 for x in ('Enabled','Excluded','Near','Far'))
               and f.get(s['prefix']+'Ready',0)==1 and f.get(s['gate'],0)>0]
    if not pending or scene or combat or workspot:
        return writes
    for s in pending:
        f[s['prefix']+'Enabled']=1; writes.append(s['prefix']+'Enabled')
    if f.get('PTFRB0OVB_Mode',0)!=1:
        f['PTFRB0OVB_Mode']=1; writes.append('PTFRB0OVB_Mode')
    f['PTFRB0OVB_AutoPasses']=f.get('PTFRB0OVB_AutoPasses',0)+1; writes.append('PTFRB0OVB_AutoPasses')
    return writes

for key,want in guards.items():
    f=seed(); f[key]=1-want; before=dict(f)
    assert tick(f)==[] and f==before
for unsafe in ('scene','combat','workspot'):
    f=seed(); assert tick(f,**{unsafe:True})==[]
assert tick(seed(),player=False)==[]
f=seed(); f['PTFRB0OVB_Suspended']=1; assert tick(f)==[]
f=seed()
for s,key,val in zip(cohort, ('gate','Excluded','Ready','Near','Far','Enabled'), (0,1,0,1,1,1)):
    f[s['gate'] if key=='gate' else s['prefix']+key]=val
prior=dict(f); writes=tick(f)
assert sum(key.endswith('Enabled') for key in writes)==19
assert all(k.startswith('PTFRB0OV') for k in writes)
assert all(f[k]==v for k,v in prior.items())
assert tick(f)==[]  # idempotent repeated poll and saved-state reload
# A naturally unlocked gate or a late Ready owner may join on a later pass.
f[cohort[0]['gate']]=1; f[cohort[2]['prefix']+'Ready']=1
assert sum(k.endswith('Enabled') for k in tick(f))==2
# Stopping survives further bootstrap attempts and saving/loading facts.
f['PTFRB0OVB_Suspended']=1; f['PTFRB0OVB_Mode']=0
for s in cohort:
    f[s['prefix']+'Enabled']=0
assert tick(dict(f))==[]
report = {'status':'PASS','kind':'source assertions and semantic model; not live redscript execution',
          'driver_sha256':hashlib.sha256(driver.read_bytes()).hexdigest().upper(),
          'cases':['each Tower guard', 'no player', 'scene/combat/workspot deferral', 'explicit suspension',
                   'locked/excluded/not-ready/in-flight preservation', 'late gate/owner readiness', 'idempotent reload', 'mod-only writes']}
(OUT/'validation/auto_test.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: automatic bootstrap source and contract model; live result unverified')
