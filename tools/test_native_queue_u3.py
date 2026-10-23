"""U3 exact source delta, native gate provenance, queue models and full compilation."""
import itertools,json,re,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,sha,read
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
OUT=ROOT/'research/gig_restoration/native_queue_u3'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    manifest=OUT/'manifest.json';m=read(manifest)
    old=(ROOT/'redscript/PTFR_NativeReuseU1/NativeReuseU1.reds').read_text()
    new=(ROOT/m['files'][0]['source']).read_text()
    method=re.search(r'  // U3: reserve Watson.*?\n  }\n',new,re.S).group()
    normalized=new.replace(method,'').replace(' && this.NativeTierEligible()','').replace('Native reuse U3 Shark:','Native reuse U1 Shark:').replace(' | U3 tier-aware queue; waiting does not reserve Watson. Original phases/calls/rewards; fixer-credit repair still pending.',' | Original phases/calls/rewards; no custom payout acknowledgement or fixer-credit repair.')
    assert normalized==old,'Unexpected U1 delta'
    oldb=(ROOT/'build/NativeReuseU1/GigFamilyB7.reds').read_text()
    newb=(ROOT/m['files'][1]['source']).read_text()
    extra=' && (this.Fact("PTFRU1_Shark_Permit")==1 || this.Fact("PTFRU1_Shark_Started")==1)'
    assert newb.count(extra)==1 and newb.replace(extra,'')==oldb,'Unexpected B7 delta'
    assert new.count('.SetFact(')==old.count('.SetFact(')==1
    assert 'SetFact(StringToName("PTFRU1_Shark_"+s),v)' in new
    # Original native unlock threshold, not inferred from a sample counter.
    path=ROOT/'research/gig_restoration/family_b7/fixers/json/base/open_world/fixers/reggie/phases/reggie.questphase.json'
    obj=read(path);r=SafeResource(obj);g=flatten(r,obj['Data']['RootChunk'])[0];nodes={n['id']:n for n in g['nodes']}
    assert nodes[161]['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'wat_sts_counter','value':11}
    assert nodes[162]['type']['factName']=='sts_wat_kab_tier_1_4'
    chain=[161,209,210,211,212,231,162]
    assert all([a,'Out',b,'In'] in g['edges'] for a,b in zip(chain,chain[1:]))
    # Translate the exact source predicate; tests are model evidence, not engine execution.
    expr=re.search(r'return (.*);',method).group(1)
    expr=re.sub(r'this.Fact\("([^"]+)"\)',r'f["\1"]',expr).replace('||',' or ').replace('&&',' and ')
    cases=0
    for t1,t11,t14,request,started,finished,safe,idle in itertools.product(range(2),repeat=8):
        f=dict(sts_wat_kab_tier_1=t1,sts_wat_kab_tier_1_1=t11,sts_wat_kab_tier_1_4=t14)
        tier=eval(expr,{'__builtins__':{}},{'f':f})
        assert tier==(t14>0 or(t1>0 and t11==0))
        permit=bool(request and not started and tier and safe and idle)
        blocked=bool(request and not finished and(permit or started))
        if request and not started and not tier:assert not permit and not blocked
        if request and started and not finished:assert blocked
        if finished:assert not blocked
        if not idle:assert not permit
        cases+=1
    # Tier-ineligible stale Permit=1 from U1 is cleared by its next safe polling tick.
    assert 'if this.Own("Permit")!=permit && !this.Set("Permit",permit)' in new
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
    for n in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/n,cache/n)
    deps={}
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        deps[str(p)]=sha(p);dest=stage/'scripts'/p.relative_to(GAME/'r6/scripts');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for f in m['files']:shutil.copy2(ROOT/f['source'],stage/'scripts'/Path(f['relative']).relative_to('r6/scripts'))
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
    cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
    args=[str(cli),'compile']
    for name in ('PTFR_NativeReuseU1','PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_MinefieldG3','PTFR_JohnnyVoiceJV1','PTFR_FreshGigsB5','PTFR_FreshGigsB6','PTFR_GigMarkersM6','PTFR_GigFamilyB7','PTFR_ActivityStateR3'):
        args+=['-s',str(stage/'scripts'/name)]
    args+=['-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=120);log=run.stdout+run.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-5000:]
    # -compile already supplies staged scripts. Listing that directory a second
    # time produces duplicate definitions in SCC (and an error dialog).
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(map(str,map(Path,plugins)))+'\n',encoding='utf-8')
    compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=120)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-5000:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=90);assert run.returncode==0
    compiledtext=flat.read_text(encoding='utf-8-sig')
    for symbol in ('NativeTierEligible','Native reuse U3 Shark','PTFRU1_Shark_Permit','Shark copied adapter disabled','TemporaryHide(true);'):assert symbol in compiledtext,symbol
    for p,h in {**protected,**deps}.items():assert sha(p)==h,p
    for f in m['files']:assert sha(ROOT/f['source'])==f['sha256'] and sha(GAME/f['relative'])==f['predecessor']
    result=dict(status='PASS_U3_OFFLINE_LIVE_PENDING',manifest_sha256=sha(manifest),test_sha256=sha(__file__),source_delta_exact=True,native_gate_source_sha256=sha(path),native_unlock_counter=11,queue_model_cases=cases,cli=True,full_scc=True,equipmentex=True,compiled_readback=True,compiled_sha256=sha(compiled),dependencies=deps,protected=protected,native_engine_proof=False)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
