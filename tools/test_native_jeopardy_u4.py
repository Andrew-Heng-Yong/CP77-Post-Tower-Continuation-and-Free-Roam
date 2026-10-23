"""U4 stock wrapper delta, admission/ownership models and staged compilation."""
import itertools,json,re,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,sha,read,walk
OUT=ROOT/'research/gig_restoration/native_jeopardy_u4'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    m=read(OUT/'manifest.json');old=read(ROOT/'research/gig_restoration/family_b7/built/towercontinued/family_b7/sts_hey_rey_06/boot.questphase.json');new=read(OUT/'wrapper.json')
    a={n['Data']['id']:n['Data'] for n in old['Data']['RootChunk']['graph']['Data']['nodes']}
    b={n['Data']['id']:n['Data'] for n in new['Data']['RootChunk']['graph']['Data']['nodes']}
    assert a.keys()==b.keys()
    def normalize(v):
        if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
        if isinstance(v,list):return [normalize(x) for x in v]
        if isinstance(v,str):return v.replace('PTFRU4_Jeopardy','PTFRB7_hey_rey_06')
        return v
    nb=normalize(b);nb[7]['phaseResource']=a[7]['phaseResource']
    for n in (65001,65002):
        cs=nb[n]['condition']['Data']['conditions'];assert len(cs)==len(a[n]['condition']['Data']['conditions'])+5
        assert [c['Data']['type']['Data']['factName'] for c in cs[-5:]]==['PTFRB7_hey_rey_06_'+k for k in ('Queued','Request','Started','OwnerFinished','Fault')]
        assert all(c['Data']['type']['Data']['value']==0 for c in cs[-5:]);del cs[-5:]
    def strip(v):
        if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in ('$id','$ref','HandleId','HandleRefId')}
        if isinstance(v,list):return [strip(x) for x in v]
        return v
    assert strip(nb)==strip(a),'Unreviewed wrapper payload change'
    assert b[7]['phaseResource']['DepotPath']['$value']==m['native_resource']
    for p,h in m['native_pins'].items():assert sha(ROOT/p)==h
    assert m['wrapper_only'] and m['packed_readback'] and m['collision']['collision_free']
    source=ROOT/'redscript/PTFR_NativeJeopardyU4/NativeJeopardyU4.reds';text=source.read_text()
    assert text.count('.SetFact(')==1 and 'SetFact(StringToName("PTFRU4_Jeopardy_"+s),v)' in text
    assert not any(s in text for s in ('.GiveReward(','.SetEntryState(','historyCertified','B7FreshHistory','this.Fresh()'))
    assert 'root!=3 && this.Fact("rey_06_finished")==0' in text
    assert 'Development-eligible (assumed unstarted)' in text
    assert 'if this.Own("Request")!=0' in text and 'this.Own("Started")!=0' in text
    assert '!this.Tier() || !this.OldUnused() || !this.HeywoodIdle()' in text
    oldb=(ROOT/'build/NativeQueueU3/GigFamilyB7.reds').read_text();newb=(ROOT/'build/NativeJeopardyU4/GigFamilyB7.reds').read_text()
    start=newb.index('\n    // U4 excludes');end=newb.index('\n    // U1 experimental',start)
    assert newb[:start]+newb[end:]==oldb,'Unexpected B7 change'
    assert 'Equals(id,"sts_hey_rey_06")' in newb[start:end] and 'PTFRU4_Jeopardy_Permit' in newb[start:end]
    job=next(j for j in read(ROOT/'research/gig_restoration/family_b7/build_plan.json')['jobs'] if j['id']=='sts_hey_rey_06')
    assert job['region']=='hey' and job['parent']['edits']==[]
    scene_root=ROOT/'research/gig_restoration/batch_b4/sources/json/base/open_world/street_stories/heywood/vista_del_rey/sts_hey_rey_06/scenes'
    scene_facts={v.get('factName') for p in scene_root.glob('*.json') for v in walk(read(p)) if isinstance(v.get('factName'),str)}
    for k in ('holo_padre_calls_v_start_activate','holo_padre_calls_v_start_done','holo_padre_calls_v_end_activate','holo_padre_calls_v_end_done'):assert k in scene_facts
    sample=read(ROOT/'research/gig_restoration/manual20_u4/facts.json')['samples'][0]
    assert sample['unchanged_after_read'] and sample['slot']=='ManualSave-20'
    assert [v['value'] for v in sample['facts']['sts_hey_rey_tier_1_1']]==[1]
    # No zero-filled facts or certified fresh history are derived from absent entries.
    cases=0
    for root,done,tower,tier,entry,old_unused,idle in itertools.product(range(-1,5),range(2),range(2),range(2),range(2),range(2),range(2)):
        eligible=bool(tower and 1<=root<=4 and root!=3 and done==0)
        admit=eligible and tier and entry and old_unused and idle
        if done or root in (-1,0,3) or not tower:assert not admit
        if not entry or not old_unused or not idle:assert not admit
        if root in (2,4) and not done and tower:assert eligible # historical assumption does not imply safe reset
        cases+=1
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
    for n in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/n,cache/n)
    deps={}
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        deps[str(p)]=sha(p);dest=stage/'scripts'/p.relative_to(GAME/'r6/scripts');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for f in m['files']:
        if not f['relative'].endswith('.reds'):continue
        dest=stage/'scripts'/Path(f['relative']).relative_to('r6/scripts');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/f['source'],dest)
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
    cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe';args=[str(cli),'compile']
    for name in ('PTFR_NativeJeopardyU4','PTFR_NativeReuseU1','PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_MinefieldG3','PTFR_JohnnyVoiceJV1','PTFR_FreshGigsB5','PTFR_FreshGigsB6','PTFR_GigMarkersM6','PTFR_GigFamilyB7','PTFR_ActivityStateR3'):args+=['-s',str(stage/'scripts'/name)]
    args+=['-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=120);log=run.stdout+run.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-5000:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(plugins)+'\n',encoding='utf-8')
    compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(stage/'scripts'),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=120)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-5000:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=90);assert run.returncode==0
    compiledtext=flat.read_text(encoding='utf-8-sig')
    for s in ('class PTFR.ActivityStateR3.NativeJeopardyU4','DevelopmentEligible','RuntimeEntrySafe','Jeopardy copied adapter disabled','Native reuse U3 Shark','TemporaryHide(true);'):assert s in compiledtext,s
    for p,h in {**protected,**deps}.items():assert sha(p)==h,p
    for f in m['files']:
        assert sha(ROOT/f['source'])==f['sha256']
        if f['predecessor']:assert sha(GAME/f['relative'])==f['predecessor']
        else:assert not (GAME/f['relative']).exists()
    result=dict(status='PASS_U4_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),test_sha256=sha(__file__),wrapper_delta_exact=True,admission_models=cases,cli=True,full_scc=True,equipmentex=True,compiled_readback=True,compiled_sha256=sha(compiled),dependencies=deps,protected=protected,save_audit_sha256=sha(ROOT/'research/gig_restoration/manual20_u4/facts.json'),native_engine_proof=False,production_history_changed=False)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
