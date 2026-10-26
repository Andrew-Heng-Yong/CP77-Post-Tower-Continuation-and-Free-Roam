"""Pin the tested four-file local package and an exact rollback baseline."""
from common import *
import shutil
H=ROOT/'prealpha/sidejobs_s29';C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
pack=read(C/'package_proof_01.json');assert pack['status']=='PASS_PACKED_READBACK_AND_LOAD_ORDER'
compiled=read(C/'compile_04/result.json');assert compiled['status']=='PASS_FULL_SCC_NOT_LIVE'
assert read(C/'compiled_check_02.json')['status']=='PASS_COMPILED_PRESERVATION'
files=sorted(p.relative_to(C/'package').as_posix() for p in (C/'package').rglob('*') if p.is_file());assert len(files)==4
snapshot='r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds'
assert sum((G/f).exists() for f in files)==1 and (G/snapshot).exists()
rt=read(H/'runtime_06/manifest.json');assert sha(G/snapshot)==rt['before']
rows=[]
for f in files:
    before=sha(G/f) if (G/f).exists() else None
    if before:
        dest=C/'before'/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(G/f,dest);assert sha(dest)==before
    rows.append(dict(target=f,before=before,after=sha(C/'package'/f)))
source=(ROOT/'prealpha/cyberware_cf1/deploy_01.ps1').read_text(encoding='utf-8-sig')
source=source.replace('cyberware_cf1_01','sidejobs_s29_01').replace('CF1_INSTALLED','S29_INSTALLED').replace('-ne 1','-ne 4').replace('files=1','files=4').replace('replacements=0;additions=1','replacements=1;additions=3')
old=" if($f.target -cne 'r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/CyberwarePreservationCF1.reds'){throw 'Unexpected target scope'}"
assert source.count(old)==1
source=source.replace(old," if($f.target -cnotin @("+','.join("'"+f+"'" for f in files)+")){throw 'Unexpected target scope'}")
dest=H/'deploy_01.ps1';assert not dest.exists();dest.write_text(source,encoding='utf-8')
tester=H/'test_deploy_01.py';assert not tester.exists();shutil.copyfile(ROOT/'prealpha/cyberware_cf1/test_deploy_01.py',tester)
protected=[]
for folder in (G/'archive/pc/mod',G/'r6/scripts',G/'r6/tweaks',G/'r6/cache',G/'red4ext/plugins',G/'bin/x64/plugins/cyber_engine_tweaks/mods',S):
    for path in folder.rglob('*'):
        if path.is_file() and path.suffix.lower() not in ('.log','.jsonl','.dmp') and path not in [G/f for f in files]:
            protected.append(dict(path=str(path),sha256=sha(path),kind='save' if path.is_relative_to(S) else 'game'))
proofs=[H/'install_manifest_01.py',H/'deploy_01.ps1',H/'test_deploy_01.py',H/'build_05.ps1',H/'prepare_04.py',H/'runtime_06.py',H/'test_03.py',H/'package_03.ps1',H/'compiled_check_02.py',H/'compile_01.py',H/'build/native_04/component.json',H/'build/native_04/tests_01.json',C/'package_proof_01.json',C/'compile_04/result.json',C/'compiled_check_02.json',H/'runtime_06/manifest.json']
m=dict(schema=1,game_root=str(G),backup_root=str(ROOT/'recovery/sidejobs_s29_01'),files=rows,protected=protected,proofs=[dict(path=str(p),sha256=sha(p)) for p in proofs],compiled_sha256=compiled['compiled_sha256'],live_status='PENDING',framework_changes=0,save_edits=0,story_fact_edits=0)
path=C/'install_manifest_01.json';assert not path.exists();path.write_text(json.dumps(m,indent=2)+'\n');Path(str(path)+'.sha256').write_text(sha(path)+'\n')
print(json.dumps(dict(status='PINNED_FOR_LOCAL_INSTALL',files=4,protected=len(protected),saves=sum(p['kind']=='save' for p in protected),manifest_sha256=sha(path))))
