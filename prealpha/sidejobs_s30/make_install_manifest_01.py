"""Pin the three replacement files against the complete installed 51-file stack."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parent.parent
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
B=W/'prealpha/full_consolidation_v1/candidate_01/package'
N=H/'candidate_01/package'
R=W/'recovery/sidejobs_s30_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
old={str(p.relative_to(B)).replace('\\','/'):sha(p) for p in B.rglob('*') if p.is_file()}
new={str(p.relative_to(N)).replace('\\','/'):sha(p) for p in N.rglob('*') if p.is_file()}
assert len(old)==len(new)==51 and old.keys()==new.keys()
assert all(sha(G/p)==v for p,v in old.items()),'Game no longer matches pinned consolidated baseline'
files=[{'target':p,'before':old[p],'after':new[p]} for p in sorted(old) if old[p]!=new[p]]
assert {r['target'] for r in files}=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'},files
proofs=[]
for rel in ('candidate_01/manifest.json','candidate_01/collisions_01.json','serialized_01/test_assets_01.json','serialized_01/test_entries_01.json','compile_01/result.json'):
 p=H/rel;proofs.append({'path':str(p),'sha256':sha(p)})
m={'status':'THREE_FILE_CONSOLIDATED_SUCCESSOR_STAGED_NOT_INSTALLED','game_root':str(G),'backup_root':str(R),'full_package_files':51,'files':files,'proofs':proofs}
out=H/'candidate_01/install_manifest_01.json';assert not out.exists()
out.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
(H/'candidate_01/install_manifest_01.json.sha256').write_text(sha(out)+'\n',encoding='utf-8')
print(json.dumps({'status':m['status'],'replacements':len(files),'unchanged':48,'sha256':sha(out)}))
