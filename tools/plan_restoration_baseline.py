"""Freeze startup rules from existing reviewed owners; no new world restoration."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'research/restoration_baseline'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def lua_facts(path,name):
    body=(ROOT/path).read_text()
    block=re.search(r'local '+name+r'\s*=\s*\{(.*?)\}',body,re.S).group(1)
    return {k:int(v) for k,v in re.findall(r'(\w+)\s*=\s*(-?\d+)',block)}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    common={k:v for k,v in read('research/b0_vendor_variants/validation/build_manifest.json')['common_guards'].items() if k!='PTFRB0VV_Mode'}
    sources=[('diagnostics/PTFR_B0_VendorBatch/init.lua','SHOPS'),('diagnostics/PTFR_B0_JunkMelee_Pair/init.lua','SHOPS'),('diagnostics/PTFR_B0_RipNet_Eight/init.lua','SITES')]
    vendors=[]
    for path,blockname in sources:
        body=(ROOT/path).read_text().split('local '+blockname+'=')[-1] if blockname+'=' in (ROOT/path).read_text() else (ROOT/path).read_text()
        # Only roster entries containing a prefix, gate and world coordinates.
        pattern=r'\{[^{}]*?prefix\s*=\s*"(PTFR\w+_)"\s*,\s*gate\s*=\s*"([^"]+)"\s*,\s*x\s*=\s*([-\d.]+)\s*,\s*y\s*=\s*([-\d.]+)\s*,\s*z\s*=\s*([-\d.]+)[^{}]*?\}'
        for p,g,x,y,z in re.findall(pattern,body,re.S):
            vendors.append(dict(prefix=p,gate=g,x=float(x),y=float(y),z=float(z),auto=p!='PTFRB0NETREY_',source=path))
    vendors.append(dict(prefix='PTFRB0JPNNET1_',gate='wbr_jpn_netrun_01_default_on',x=-354.645905,y=1366.60144,z=42.1621017,auto=True,source='diagnostics/PTFR_B0_JpnNetrunner01/init.lua'))
    assert len(vendors)==15 and len({v['prefix'] for v in vendors})==15
    rules=[]
    # Named regional owners already have native guard, spawn, and scene nodes.
    for v in vendors:
        if not v['auto']:continue # Vista del Rey has never passed its gate/test.
        p=v['prefix']
        rules.append(dict(name=p+'auto',write=p+'Enabled',guards={**common,v['gate']:1,p+'Ready':1,p+'Enabled':0,p+'Near':0,p+'Far':0,p+'Excluded':0},kind='vendor'))
    wilson=lua_facts('diagnostics/PTFR_B0_Wilson_Vendor/init.lua','REQUIRED')
    rules.append(dict(name='Wilson',write='PTFRB0WV_Enabled',kind='vendor',guards={**wilson,'PTFRB0WV_Ready':1,'PTFRB0WV_Enabled':0,'PTFRB0WV_Near':0,'PTFRB0WV_SpawnActionOut':0,'PTFRB0WV_ActorDistanceGate':0,'PTFRB0WV_Excluded':0}))
    floor=read('research/b0_h10_floor/validation/build_manifest.json')['native_guard']
    living=read('research/b0_h10_living/validation/build_manifest.json')['native_guard']
    arch=read('research/b0_h10_architecture/validation/build_manifest.json')['guards']
    for prefix,guards in [('PTFRB0H10_',floor),('PTFRB0H10L_',living),('PTFRB0H10A_E_',arch['entrance']),('PTFRB0H10A_B_',arch['bedroom']),('PTFRB0H10A_W_',arch['bathroom'])]:
        rules.append(dict(name=prefix+'geometry',write=prefix+'Request',kind='geometry',guards={**guards,prefix+'Ready':1,prefix+'Request':0,prefix+'Rejected':0}))
    h10=read('research/b0_h10_persistent/validation/build_manifest.json')['guard_facts']
    h10.update(PTFRB0H10P_Enabled=0,PTFRB0H10P_Ready=1,PTFRB0H10P_Active=0)
    rules.append(dict(name='H10 interactions',write='PTFRB0H10P_Enabled',kind='h10',guards=h10))
    rules.append(dict(name='Coyote public mirror',write='PTFRCM2_Requested',kind='coyote',guards={**common,'mirror_interaction_disabled':0,'PTFRCM1_Requested':0,'PTFRCM2_Boot':1,'PTFRCM2_Requested':0,'PTFRCM2_Active':0,'PTFRCM2_Interrupted':0}))
    data=dict(version='Baseline-R1',common=common,vendors=vendors,wilson=wilson,rules=rules,
        unchanged_automatic=['OrdinaryMirrors_C4','OrdinaryVendors (25)','VendorVariants (6 partial smoke pass)','DeferredVendors (Christine; Chang remains locally gated)'],
        excluded=['Vista del Rey netrunner automatic enabling','Streetkid mirror','other unbuilt vendors/mirrors','time-unpause debug request','old H10 one-shot scenes','story/market/default fact changes'])
    (OUT/'rules.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Frozen rules:',len(rules),'regional distance owners:',len(vendors),'new automatic legacy vendors: 15 including Wilson')
if __name__=='__main__':main()
