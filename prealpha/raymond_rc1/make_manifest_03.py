"""Pin the full CR1 successor and two exact replacement install paths."""
import hashlib,json
from pathlib import Path

H=Path(__file__).resolve().parent
W=H.parent.parent
B=W/'prealpha/consolidation_repair_cr1/candidate_01'
P=H/'candidate_03'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest().upper()
old={r['path']:r['sha256'] for r in json.loads((B/'manifest.json').read_text())['files']}
new={r['path']:r['sha256'] for r in json.loads((P/'manifest.json').read_text())['files']}
assert len(old)==len(new)==51 and old.keys()==new.keys()
for rel,digest in old.items():assert sha(G/rel)==digest,rel
for rel,digest in new.items():assert sha(P/'package'/rel)==digest,rel
files=[{'target':rel,'before':old[rel],'after':new[rel]} for rel in sorted(old) if old[rel]!=new[rel]]
assert {r['target'] for r in files}=={'archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'}
proof_rels=['candidate_03/manifest.json','evidence_02/validation.json','evidence_02/collisions.json','compile_03/result.json','build_03.ps1','validate_03.py','deploy_03.ps1','test_deploy_03.py']
proofs=[{'path':str(H/rel),'sha256':sha(H/rel)} for rel in proof_rels]
manifest={'status':'RC2_CONSOLIDATED_SUCCESSOR_STAGED','game_root':str(G),'backup_root':str(W/'recovery/raymond_rc2_01'),
          'files':files,'package_files':[{'path':rel,'before':old[rel],'after':new[rel]} for rel in sorted(old)],
          'proofs':proofs,'new_install_paths':0,'removed_install_paths':0,'resource_changes':2,'live_result':'pending'}
out=P/'install_manifest_03.json'
assert not out.exists(),out
out.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
(P/'install_manifest_03.json.sha256').write_text(sha(out)+'\n',encoding='utf-8')
print(json.dumps({'replaced_files':len(files),'full_package_files':51,'sha256':sha(out)}))
