"""Pin the full package and explicit single-path installation change."""
from common import *
base=read(CANDIDATE/'baseline_01.json');packed=read(CANDIDATE/'manifest.json')
old={r['path']:r['sha256'] for r in base['package_files']}
new={r['path']:r['sha256'] for r in packed['files']}
assert len(old)==len(new)==51 and old.keys()==new.keys()
for rel,digest in old.items():assert sha(GAME/rel)==digest,rel
for rel,digest in new.items():assert sha(CANDIDATE/'package'/rel)==digest,rel
files=[{'target':rel,'before':old[rel],'after':new[rel]} for rel in sorted(old) if old[rel]!=new[rel]]
assert len(files)==1 and files[0]['target']==ARCHIVE
assert read(HERE/'compile_01/result.json')['status']=='PASS'
assert read(HERE/'validation/candidate_positive_01.json')['status']=='PASS_INDEPENDENT_SEMANTIC_REPAIR_AND_PRESERVATION_NOT_LIVE'
assert read(HERE/'validation/s30_negative_01.json')['status']=='NEGATIVE_CONTROL_DETECTED_KNOWN_S30_REGRESSIONS'
assert read(CANDIDATE/'archive_readback_01.json')['external_collisions']==[]
proof_paths=['candidate_01/manifest.json','candidate_01/selected_resources_01.json','candidate_01/archive_readback_01.json',
             'donor_review/selection_01.json','donor_review/review_01.json','validation/checks_contract_01.json',
             'validation/test_semantics_01.py','validation/candidate_positive_01.json','validation/s30_negative_01.json',
             'compile_01/result.json','deploy_01.ps1','test_deploy_01.py']
proofs=[{'path':str(HERE/rel),'sha256':sha(HERE/rel)} for rel in proof_paths]
assert all(r['sha256'] for r in proofs)
manifest={'status':'CR1_CONSOLIDATED_SUCCESSOR_STAGED','game_root':str(GAME),'backup_root':str(WS/'recovery/consolidation_repair_cr1_01'),
          'files':files,'package_files':[{'path':rel,'before':old[rel],'after':new[rel]} for rel in sorted(old)],
          'proofs':proofs,'new_install_paths':0,'removed_install_paths':0,'resource_changes':30,'live_result':'pending'}
out=CANDIDATE/'install_manifest_01.json';write_new(out,manifest)
(CANDIDATE/'install_manifest_01.json.sha256').write_text(sha(out)+'\n',encoding='utf-8')
print(json.dumps({'replaced_files':len(files),'package_files':51,'manifest_sha256':sha(out)}))
