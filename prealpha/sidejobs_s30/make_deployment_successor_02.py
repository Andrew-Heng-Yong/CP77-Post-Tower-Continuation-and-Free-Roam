"""Keep S30 candidate 01 evidence and derive corrected deployment tooling."""
from pathlib import Path
H=Path(__file__).resolve().parent
specs={
 'make_install_manifest_01.py':{
  "H/'candidate_01/package'":"H/'candidate_02/package'",
  "recovery/sidejobs_s30_01":"recovery/sidejobs_s30_02",
  "candidate_01/manifest.json":"candidate_02/manifest.json",
  "candidate_01/collisions_01.json":"candidate_02/collisions_02.json",
  "serialized_01/test_assets_01.json":"serialized_02/test_assets_02.json",
  "serialized_01/test_entries_01.json":"serialized_02/test_entries_02.json",
  "compile_01/result.json":"compile_02/result.json",
  "candidate_01/install_manifest_01.json":"candidate_02/install_manifest_01.json",
 },
 'make_deployer_01.py':{
  "Join-Path $PSScriptRoot 'candidate_01'":"Join-Path $PSScriptRoot 'candidate_02'",
  "recovery/sidejobs_s30_01":"recovery/sidejobs_s30_02",
  "out=H/'deploy_01.ps1'":"out=H/'deploy_02.ps1'",
 },
 'make_fixture_test_01.py':{
  "here / 'candidate_01'":"here / 'candidate_02'",
  "here / 'deploy_01.ps1'":"here / 'deploy_02.ps1'",
  "out=H/'test_deploy_01.py'":"out=H/'test_deploy_02.py'",
 },
}
for name,repls in specs.items():
 source=(H/name).read_text(encoding='utf-8')
 for old,new in repls.items():
  assert source.count(old)>=1,(name,old,source.count(old));source=source.replace(old,new)
 target=H/name.replace('_01.','_02.');assert not target.exists(),target
 target.write_text(source,encoding='utf-8');print(target.name)
