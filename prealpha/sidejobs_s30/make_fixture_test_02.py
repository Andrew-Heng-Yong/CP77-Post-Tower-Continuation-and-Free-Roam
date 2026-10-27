from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parent.parent
source=(W/'prealpha/sidejob_repair_sr1/test_production_deploy_01.py').read_text(encoding='utf-8')
for old,new in {
    "here / 'production_01'":"here / 'candidate_02'",
    "here / 'deploy_production_01.ps1'":"here / 'deploy_02.ps1'",
}.items():
 assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
out=H/'test_deploy_02.py';assert not out.exists();out.write_text(source,encoding='utf-8')
print(out)
