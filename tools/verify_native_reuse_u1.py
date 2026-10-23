"""New U1 evidence only: compare wrapper to pinned shell, compile full mod set."""
import json, re, shutil, subprocess, tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, sha

OUT=ROOT/'research/gig_restoration/native_reuse_u1'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')

def main():
    assert not (OUT/'install_receipt.json').exists()
    m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8-sig'))
    source=ROOT/'redscript/PTFR_NativeReuseU1/NativeReuseU1.reds'
    text=source.read_text()
    # Structural CR2W JSON comparison: only own fact namespace, original child
    # resource, and explicit cross-adapter guards may differ from audited shell.
    old=json.loads((ROOT/'research/gig_restoration/family_b7/built/towercontinued/family_b7/sts_wat_kab_06/boot.questphase.json').read_text(encoding='utf-8-sig'))
    new=json.loads((OUT/'wrapper.json').read_text(encoding='utf-8-sig'))
    og=old['Data']['RootChunk']['graph']['Data'];ng=new['Data']['RootChunk']['graph']['Data']
    oldnodes={n['Data']['id']:n['Data'] for n in og['nodes']}
    newnodes={n['Data']['id']:n['Data'] for n in ng['nodes']}
    assert oldnodes.keys()==newnodes.keys()
    # Normalize only reviewed differences, retaining all serialized socket links.
    changes=[]
    def normalize(v):
        if isinstance(v,dict): return {k:normalize(x) for k,x in v.items()}
        if isinstance(v,list): return [normalize(x) for x in v]
        if isinstance(v,str): return v.replace('PTFRU1_Shark','PTFRB7_wat_kab_06')
        return v
    nn=normalize(newnodes)
    nn[11]['phaseResource']=oldnodes[11]['phaseResource']
    for n in (65001,65002):
        conditions=nn[n]['condition']['Data']['conditions']
        assert len(conditions)==len(oldnodes[n]['condition']['Data']['conditions'])+5
        extra=conditions[-5:]
        assert [x['Data']['type']['Data']['factName'] for x in extra]==['PTFRB7_wat_kab_06_'+s for s in ('Queued','Request','Started','OwnerFinished','Fault')]
        assert all(x['Data']['type']['Data']['value']==0 for x in extra)
        del conditions[-5:]
    # Handle IDs are serialization bookkeeping and may be renumbered.
    def strip(v):
        if isinstance(v,dict):return {k:strip(x) for k,x in v.items() if k not in ('$id','$ref','HandleId','HandleRefId')}
        if isinstance(v,list):return [strip(x) for x in v]
        return v
    assert strip(nn)==strip(oldnodes),'Unreviewed wrapper payload change'
    assert newnodes[11]['phaseResource']['DepotPath']['$value']==m['native_resource']
    assert m['original_resources_packed']==0 and m['packed_readback']
    for p,h in m['native_pins'].items(): assert sha(ROOT/p)==h
    assert 'SetFact(StringToName("PTFRU1_Shark_"+s),v)' in text
    assert text.count('.SetFact(')==1 and '.GiveReward(' not in text
    b7=(ROOT/'build/NativeReuseU1/GigFamilyB7.reds').read_text()
    assert all(s in text for s in ('!this.OldUnused()','!this.Fresh()','!this.WatsonIdle()',
                                  'this.Own("Request")!=0','this.Own("Started")!=0',
                                  ))
    assert 'Equals(id,"sts_wat_kab_06")' in b7 and 'native Shark U1 trial owns' in b7
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
    for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
    deps={}
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        deps[str(p)]=sha(p);target=stage/'scripts'/p.relative_to(GAME/'r6/scripts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    shutil.copy2(ROOT/'build/NativeReuseU1/GigFamilyB7.reds',stage/'scripts/PTFR_GigFamilyB7/GigFamilyB7.reds')
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
    custom=source.parent;cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
    args=[str(cli),'compile','-s',str(custom)]
    for name in ('PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_MinefieldG3','PTFR_JohnnyVoiceJV1','PTFR_FreshGigsB5','PTFR_FreshGigsB6','PTFR_GigMarkersM6','PTFR_GigFamilyB7','PTFR_ActivityStateR3'):
        args+=['-s',str(stage/'scripts'/name)]
    args+=['-s',str(GAME/'red4ext/plugins/Codeware/Scripts')]
    args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=120);log=run.stdout+run.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-12000:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(map(str,[custom,stage/'scripts']+list(map(Path,plugins))))+'\n',encoding='utf-8')
    compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(custom),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=120)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-12000:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=90)
    assert run.returncode==0
    compiledtext=flat.read_text(encoding='utf-8-sig')
    for symbol in ('class PTFR.ActivityStateR3.NativeReuseU1','Shark copied adapter disabled','native Shark U1 trial owns','Original phases/calls/rewards','TemporaryHide(true);'):
        assert symbol in compiledtext,symbol
    for path,h in {**protected,**deps}.items():assert sha(path)==h,path
    for f in m['files']:assert sha(ROOT/f['source'])==f['sha256']
    result=dict(status='PASS_U1_OFFLINE_ENGINE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),wrapper_payload_comparison=True,
                headless_compile=True,full_scc=True,equipmentex=True,compiled_readback=True,
                compiled_sha256=sha(compiled),source_sha256=sha(source),protected=protected,dependencies=deps,
                limitations=['Native phase instance is new, not resumption of original saved owner.',
                'Original phone calls may wait on unavailable shared handlers.',
                'Native reward/achievement unchanged; district fixer-credit loop not restarted.',
                'In-game activation, payout, cleanup and save/reload NOT yet tested.'])
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'])
if __name__=='__main__':main()
