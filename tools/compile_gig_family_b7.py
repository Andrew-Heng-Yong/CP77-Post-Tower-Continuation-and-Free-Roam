"""Independent full-mod compilation; live caches and pinned revisions untouched."""
import json,re,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,sha
OUT=ROOT/'research/gig_restoration/family_b7'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
MODULES=('PTFR_GigFamilyB7','PTFR_ActivityStateR3')
def main():
    assert not (OUT/'install_receipt.json').exists()
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
    for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
    deps={}
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        deps[str(p)]=sha(p);rel=p.relative_to(GAME/'r6/scripts')
        if rel.parts[0] in MODULES:continue
        target=stage/'scripts'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for folder in plugins:
        for p in Path(folder).rglob('*.reds'):deps[str(p)]=sha(p)
    cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
    custom=[ROOT/'redscript'/name for name in MODULES]
    args=[str(cli),'compile']
    for p in custom:args+=['-s',str(p)]
    for name in ('PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_MinefieldG3','PTFR_JohnnyVoiceJV1','PTFR_FreshGigsB5','PTFR_FreshGigsB6','PTFR_GigMarkersM6'):args+=['-s',str(GAME/'r6/scripts'/name)]
    args+=['-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=90);log=run.stdout+run.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-12000:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(map(str,custom+[stage/'scripts']+list(map(Path,plugins))))+'\n',encoding='utf-8')
    compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(custom[1]),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=90)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-12000:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=60)
    assert run.returncode==0 and 'Output successfully saved' in run.stdout+run.stderr
    text=flat.read_text(encoding='utf-8-sig')
    for symbol in ('class PTFR.ActivityStateR3.GigFamilyB7','class PTFR.ActivityStateR3.GigDataB7','func B7FreshHistory(','TemporaryHide(true);','EquipmentEx.OutfitSystem.GetInstance'):assert symbol in text,symbol
    for struct,names in {'FreshSlotB5':['stage','inflight','countBase','achBase','accountPrepared','counterAck'],'ActivitySnapshot':['states','optional','tracked','counters','facts']}.items():
        b=re.search(r'public struct PTFR\.ActivityStateR3\.'+struct+r' \{(.*?)\n\}',text,re.S)[1]
        assert all('public persistent let '+n+':' in b for n in names)
    for path,h in {**protected,**deps}.items():assert sha(path)==h,path
    result=dict(status='PASS_B7_COMPILE_NOT_ENGINE_PROOF',sources={str(p.relative_to(ROOT)):sha(p) for folder in custom for p in folder.glob('*.reds')},compiled_sha256=sha(compiled),compiled_path=str(compiled),equipmentex=True,persistence_readback=True,protected=protected,dependencies=deps,game_scripts_and_cache_unchanged=True)
    (OUT/'compile_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k in ('status','equipmentex','persistence_readback')}))
if __name__=='__main__':main()
