"""Compile presentation-only JV1 in workspace, including all installed scripts."""
import json, shutil, subprocess, tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, sha

GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
OUT=ROOT/'research/gig_restoration/minefield_g3'
SOURCE=ROOT/'redscript/PTFR_MinefieldG3'
STATE=ROOT/'redscript/PTFR_ActivityStateR3'

def main():
    assert not (OUT/'install_receipt.json').exists(), 'Installed evidence pinned'
    OUT.mkdir(exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
    for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
    deps={}
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        rel=p.relative_to(GAME/'r6/scripts')
        if rel.parts[0]==STATE.name:
            assert sha(p)=='3C1FABD8E0BD8D123243B2A32CD143860AF05C7D93404335A0B3FB379E4BCC7F' if p.name=='ActivityStateR3.reds' else True
            deps[str(p)]=sha(p);continue
        assert rel.parts[0]!=SOURCE.name,'Already installed'
        target=stage/'scripts'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);deps[str(p)]=sha(p)
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for d in plugins:
        for p in Path(d).rglob('*.reds'):deps[str(p)]=sha(p)
    cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
    args=[str(cli),'compile']
    for s in [SOURCE,STATE]+[GAME/'r6/scripts'/n for n in ('PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3','PTFR_GigPilotR1','PTFR_SideJobPilotS1','PTFR_RiteG2','PTFR_JohnnyVoiceJV1')]+[GAME/'red4ext/plugins/Codeware/Scripts']:args+=['-s',str(s)]
    args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=90);log=run.stdout+run.stderr
    (OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-14000:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(map(str,[SOURCE,STATE,stage/'scripts']+list(map(Path,plugins))))+'\n',encoding='utf-8')
    compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(SOURCE),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=90)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-14000:]
    assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=60)
    assert 'Output successfully saved' in run.stdout+run.stderr
    text=flat.read_text(encoding='utf-8-sig')
    for symbol in ('class PTFR.MinefieldG3.MinefieldG3','func MinefieldHistory(', 'Explicit history override; saved early-stage/outcome guards retained:', 'class PTFR.RiteG2.RiteG2','func CheckDeparture(','func PTFRJ1RestoreEmptyTitle(', 'TemporaryHide(true);', 'EquipmentEx.OutfitSystem.GetInstance'):assert symbol in text,symbol
    for p,digest in {**protected,**deps}.items():assert sha(p)==digest,p
    result={'status':'PASS_G3_OFFLINE_COMPILE_NOT_ENGINE_PROOF','source_sha256':sha(SOURCE/'MinefieldG3.reds'),'state_sha256':sha(STATE/'ActivityStateR3.reds'),'compiled_sha256':sha(compiled),'compiled_path':str(compiled),'equipmentex':True,'protected':protected,'dependencies':deps}
    (OUT/'compile_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','source_sha256','equipmentex')},indent=2))
if __name__=='__main__':main()
