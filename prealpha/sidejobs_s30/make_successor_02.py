"""Preserve the first workspace candidate and create corrected S30 sources."""
from pathlib import Path
H=Path(__file__).resolve().parent
scripts=[
 'prepare_01.py','prepare_contracts_01.py','serialize_01.ps1','build_lipmap_01.ps1',
 'build_runtime_01.py','build_entries_01.ps1','compile_01.py','package_01.ps1',
 'test_assets_01.py','test_entries_01.py','scan_collisions_01.ps1',
]
for name in scripts:
 source=(H/name).read_text(encoding='utf-8')
 if name=='prepare_01.py':
  old="mine=value(ref.get('dynamicEntityUniqueName')) in names or str(value(ref.get('sceneActorContextName',''))).lower() in {a['actorName'].lower() for a in actors}"
  new="actor_names={a['actorName'].lower() for a in actors};mine=value(ref.get('dynamicEntityUniqueName')) in names or str(value(ref.get('sceneActorContextName',''))).lower() in actor_names or any(str(value(n)).lower() in actor_names for n in ref.get('names',[])) or str(value(ref.get('reference'))).lower() in {'#'+n for n in actor_names}"
  assert source.count(old)==1;source=source.replace(old,new)
 if name=='package_01.ps1':
  source=source.replace('$overlaid.Count -ne 19','$overlaid.Count -ne 20').replace('$final.Count -ne 1171','$final.Count -ne 1172').replace('new_members=18','new_members=19')
 if name=='scan_collisions_01.ps1':source=source.replace('$paths.Count -ne 18','$paths.Count -ne 19').replace('Expected 18 new','Expected 19 new')
 source=source.replace('prepared_01','prepared_02').replace('serialized_01','serialized_02').replace('candidate_01','candidate_02').replace('compile_01','compile_02').replace('test_assets_01','test_assets_02').replace('test_entries_01','test_entries_02').replace('collisions_01','collisions_02')
 # The consolidation source must remain the pinned original candidate_01.
 source=source.replace('full_consolidation_v1/candidate_02','full_consolidation_v1/candidate_01')
 target=H/name.replace('_01.','_02.');assert not target.exists(),target
 target.write_text(source,encoding='utf-8')
 print(target.name)
