"""Pin a recoverable two-file CD1 installation against the current local stack."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys

H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'build/local_install_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
ORIGINAL=H/'build/candidate_01'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def new(p,text):
    with p.open('x',encoding='utf-8') as f:f.write(text)

C.mkdir(parents=True,exist_ok=False)
changes=read(ORIGINAL/'changes_01.json')['changes']
assert len(changes)==2
for row in changes:
    name=row['path'];assert sha(G/name)==row['before']
    assert sha(ORIGINAL/'package'/name)==row['after']
    for root,src in [('before',G/name),('package',ORIGINAL/'package'/name)]:
        dest=C/root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)

text=(W/'prealpha/h10_h5/compile_01.py').read_text(encoding='utf-8-sig')
text=text.replace("C=H/'candidate_01'","C=H/'build/local_install_01'")
text=text.replace("'PTFR.LoadingCoverLC1.SetupPopupLC1']:","'PTFR.LoadingCoverLC1.SetupPopupLC1','PTFR.RestrictionsR1.CyberwareDiagnosticsCD1']:")
new(H/'compile_local_01.py',text)
subprocess.run([sys.executable,str(H/'compile_local_01.py'),'compile_01'],check=True)
compiled=read(C/'compile_01/result.json');assert compiled['status']=='PASS_FULL_SCC_NOT_LIVE'

text=(W/'prealpha/h10_h5/deploy_01.ps1').read_text(encoding='utf-8-sig')
text=text.replace("'candidate_01'","'build/local_install_01'").replace('h10_h5_01','cyberware_cd1_local_01').replace('H5_INSTALLED','CD1_INSTALLED')
text=text.replace('-ne 5','-ne 2').replace('files=5','files=2').replace('replacements=2;additions=3','replacements=2;additions=0')
lines=text.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
lines[i]=" if($f.target -cnotin @("+','.join("'"+r['path']+"'" for r in changes)+")){throw 'Unexpected target scope'}"
new(H/'deploy_local_01.ps1','\n'.join(lines)+'\n')
text=(W/'prealpha/h10_h5/test_deploy_01.py').read_text(encoding='utf-8-sig')
text=text.replace("O=H/'candidate_01'","O=H/'build/local_install_01'").replace('deploy_01.ps1','deploy_local_01.ps1').replace("'-TestFailAfter','4'","'-TestFailAfter','1'")
new(H/'test_deploy_local_01.py',text)

targets={(G/r['path']).resolve() for r in changes};protected=[]
for folder in (G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S):
    for p in folder.rglob('*'):
        if p.is_file() and p.suffix.lower() not in ('.log','.jsonl','.dmp') and p.resolve() not in targets:
            protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[H/'prepare_local_01.py',H/'compile_local_01.py',H/'deploy_local_01.ps1',H/'test_deploy_local_01.py',C/'compile_01/result.json',ORIGINAL/'changes_01.json',ORIGINAL/'package_result_01.json',W/'dist/cyberware-cd1/PTFR-CD1-diagnostics-for-alpha.zip']
manifest={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/cyberware_cd1_local_01'),'files':[{'target':r['path'],'before':r['before'],'after':r['after']} for r in changes],'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'diagnostic_reproduction_pending','framework_changes':0,'archive_changes':0,'save_edits':0,'compiled_sha256':compiled['compiled_sha256']}
p=C/'install_manifest_01.json';new(p,json.dumps(manifest,indent=2)+'\n');new(Path(str(p)+'.sha256'),sha(p)+'\n')
print(json.dumps({'status':'CD1_LOCAL_PACKAGE_PINNED','files':2,'sources':compiled['sources'],'protected':len(protected),'saves':sum(r['kind']=='save' for r in protected),'manifest_sha256':sha(p)}),flush=True)
