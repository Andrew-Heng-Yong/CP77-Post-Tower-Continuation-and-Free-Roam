"""Compile S1.1 with copied installed dependencies; preserve original S1 evidence."""
import json,shutil,subprocess,tempfile
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,sha,read
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
OUT=ROOT/'research/side_job_cleanup_s1_1';SOURCE=ROOT/'redscript/PTFR_SideJobPilotS1'

def main():
    receipt=read(ROOT/'research/side_job_pilot_s1/install_receipt.json')
    # Preserve exact predecessor sources before changing their installed paths.
    prior=OUT/'predecessor';prior.mkdir(exist_ok=True)
    for i in (0,2,3):
        f=receipt['files'][i];p=GAME/f['relative'];assert sha(p)==f['sha256']
        backup=prior/Path(f['relative']).name
        if backup.exists():assert sha(backup)==f['sha256']
        else:shutil.copy2(p,backup)
    stage=Path(tempfile.mkdtemp(prefix='compile_',dir=OUT));cache=stage/'cache';cache.mkdir()
    protected={str(p):sha(p) for p in (GAME/'r6/cache').iterdir() if p.is_file()}
    for name in ('final.redscripts','final.redscripts.ts'):shutil.copy2(GAME/'r6/cache'/name,cache/name)
    deps={};predecessors={}
    for p in (GAME/'r6/scripts').rglob('*.reds'):
        rel=p.relative_to(GAME/'r6/scripts')
        if rel.parts[0]==SOURCE.name:predecessors[str(p)]=sha(p);continue
        target=stage/'scripts'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);deps[str(p)]=sha(p)
    plugins=(ROOT/'research/restriction_profiles/implementation_r1/compile_paths.txt').read_text(encoding='utf-8-sig').splitlines()[2:]
    for d in plugins:
        for p in Path(d).rglob('*.reds'):deps[str(p)]=sha(p)
    cli=ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'
    args=[str(cli),'compile']
    for s in [SOURCE]+[GAME/'r6/scripts'/n for n in ('PTFR_Restrictions_R1','PTFR_Restrictions_R2','PTFR_Restrictions_R3')]+[GAME/'red4ext/plugins/Codeware/Scripts']:args+=['-s',str(s)]
    args+=['-b',str(cache/'final.redscripts'),'-o',str(stage/'headless.redscripts')]
    run=subprocess.run(args,capture_output=True,text=True,timeout=90);log=run.stdout+run.stderr;(OUT/'headless_compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Output successfully saved' in log and '[ERROR' not in log,log[-12000:]
    paths=stage/'compile_paths.txt';paths.write_text('\n'.join(map(str,[SOURCE,stage/'scripts']+list(map(Path,plugins))))+'\n',encoding='utf-8');compiled=cache/'compiled.redscripts'
    run=subprocess.run([str(GAME/'engine/tools/scc.exe'),'-compile',str(SOURCE),'-compilePathsFile',str(paths),'-customCacheDir',str(cache),'-outputCacheFile',str(compiled),str(cache/'final.redscripts')],capture_output=True,text=True,timeout=90)
    log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log,encoding='utf-8')
    assert run.returncode==0 and 'Compilation complete' in log and 'Output successfully saved' in log and '[ERROR' not in log,log[-12000:];assert 'EquipmentEx.reds' in log
    flat=OUT/'compiled_flat.script';run=subprocess.run([str(cli),'decompile','-i',str(compiled),'-o',str(flat)],capture_output=True,text=True,timeout=60);assert 'Output successfully saved' in run.stdout+run.stderr
    text=flat.read_text(encoding='utf-8-sig')
    for token in ('func CompletedPoliceLeftRoute(', 'func CheckDeparture(', 'PTFRS1_CleanupDeparture', 'PTFRS1_CleanupJoined', 'func PTFRJ1RestoreEmptyTitle(', 'EquipmentEx.OutfitSystem.GetInstance'):assert token in text,token
    for p,digest in {**protected,**deps,**predecessors}.items():assert sha(p)==digest,p
    result={'status':'PASS_S1_1_OFFLINE_COMPILE_NOT_ENGINE_PROOF','source_sha256':sha(SOURCE/'SideJobPilotS1.reds'),'compiled_sha256':sha(compiled),'compiled_path':str(compiled),'equipmentex':True,'journal_label_preserved':True,'protected':protected,'dependencies':deps,'predecessors':predecessors}
    (OUT/'compile_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k in ('status','source_sha256','equipmentex','journal_label_preserved')},indent=2))
if __name__=='__main__':main()
