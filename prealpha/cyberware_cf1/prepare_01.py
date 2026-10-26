"""Prepare one-file CF1 candidate without changing installed files or saves."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
TARGET='r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/CyberwarePreservationCF1.reds'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def new(p,s):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:f.write(s)
assert not (G/TARGET).exists()
C.mkdir(exist_ok=False)
dest=C/'package'/TARGET;dest.parent.mkdir(parents=True);shutil.copyfile(H/'CyberwarePreservationCF1.reds',dest)
text=(W/'prealpha/cyberware_cd1/compile_local_01.py').read_text(encoding='utf-8-sig').replace("C=H/'build/local_install_01'","C=H/'candidate_01'")
text=text.replace("'PTFR.RestrictionsR1.CyberwareDiagnosticsCD1']:","'PTFR.RestrictionsR1.CyberwareDiagnosticsCD1','PTFRCF1PreservesExactItem']:")
new(H/'compile_01.py',text)
subprocess.run([sys.executable,str(H/'compile_01.py'),'compile_01'],check=True)
compiled=json.loads((C/'compile_01/result.json').read_text());assert compiled['status']=='PASS_FULL_SCC_NOT_LIVE'
text=(W/'prealpha/cyberware_cd1/deploy_local_01.ps1').read_text(encoding='utf-8-sig')
text=text.replace("'build/local_install_01'","'candidate_01'").replace('cyberware_cd1_local_01','cyberware_cf1_01').replace('CD1_INSTALLED','CF1_INSTALLED')
text=text.replace('-ne 2','-ne 1').replace('files=2','files=1').replace('replacements=2;additions=0','replacements=0;additions=1')
lines=text.splitlines();i=next(i for i,l in enumerate(lines) if 'Unexpected target scope' in l)
lines[i]=" if($f.target -cne '"+TARGET+"'){throw 'Unexpected target scope'}"
new(H/'deploy_01.ps1','\n'.join(lines)+'\n')
text=(W/'prealpha/cyberware_cd1/test_deploy_local_01.py').read_text(encoding='utf-8-sig').replace("O=H/'build/local_install_01'","O=H/'candidate_01'").replace('deploy_local_01.ps1','deploy_01.ps1')
text=text.replace("p=g/M['files'][0]['target'];p.write_text", "p=g/M['files'][0]['target'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text")
new(H/'test_deploy_01.py',text)
protected=[]
for folder in (G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix.lower() not in ('.log','.jsonl','.dmp'):
   protected.append({'path':str(p),'sha256':sha(p),'kind':'save' if p.is_relative_to(S) else 'game'})
proofs=[H/'CyberwarePreservationCF1.reds',H/'prepare_01.py',H/'compile_01.py',H/'deploy_01.ps1',H/'test_deploy_01.py',C/'compile_01/result.json',W/'diagnostics/alpha_cyberware_20261025_01/local_repro_02/capture_01.json',W/'diagnostics/alpha_cyberware_20261025_01/local_repro_02/cleanup_records_02.json']
manifest={'schema':1,'game_root':str(G),'backup_root':str(W/'recovery/cyberware_cf1_01'),'files':[{'target':TARGET,'before':None,'after':sha(dest)}],'protected':protected,'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'live_status':'fix_candidate_not_installed','framework_changes':0,'archive_changes':0,'save_edits':0,'compiled_sha256':compiled['compiled_sha256']}
p=C/'install_manifest_01.json';new(p,json.dumps(manifest,indent=2)+'\n');new(Path(str(p)+'.sha256'),sha(p)+'\n')
print(json.dumps({'status':'CF1_CANDIDATE_PINNED','sources':compiled['sources'],'protected':len(protected),'saves':sum(r['kind']=='save' for r in protected),'manifest_sha256':sha(p)}),flush=True)
