"""Instruction-maintenance evidence only. Never builds, deploys, or edits game files.
Run baseline before documentation edits, verify after; writes only this report folder.
"""
import os,sys,json,hashlib,datetime,collections,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[2]
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(n,v):(H/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def scan(root,repo=False):
 out={};links=[];stack=[root]
 while stack:
  dp=stack.pop()
  with os.scandir(dp) as entries:
   for e in entries:
    p=Path(e.path);rel=p.relative_to(root).as_posix()
    if repo and (rel=='.git' or p==H):continue
    st=e.stat(follow_symlinks=False)
    if getattr(st,'st_file_attributes',0)&0x400:
     links.append({'path':rel,'mode':st.st_mode,'mtime_ns':st.st_mtime_ns,'target':os.readlink(p) if p.is_symlink() else 'reparse point; not followed'});continue
    if e.is_dir(follow_symlinks=False):stack.append(p)
    else:out[rel]=[st.st_size,st.st_mtime_ns]
 return out,links
def protected(repo):
 paths=set()
 # Source code in this project's working trees, not vendored research or generated fixture copies.
 for top in ['tools','redscript','profiles','tweaks','archive','release']:
  for p in (W/top).rglob('*'):
   if p.is_file() and not p.is_symlink():paths.add(p)
 for rel in repo:
  parts=Path(rel).parts
  if parts[0]=='prealpha' and len(parts)==3 and Path(rel).suffix.lower() in ('.py','.ps1','.reds','.lua'):paths.add(W/rel)
 for top in ['dist','prealpha/phone_studios_ph3/candidate_01/package','prealpha/phone_studios_ph3/candidate_01/archive_source']:
  for p in (W/top).rglob('*'):
   if p.is_file() and not p.is_symlink():paths.add(p)
 m=read(W/'prealpha/phone_studios_ph3/candidate_01/install_manifest_01.json')
 for r in m['package_files']:paths.add(G/r['path'])
 for r in read(W/'prealpha/phone_studios_ph3/candidate_01/external_baseline_01.json')['files']:paths.add(G/r['path'])
 paths.add(G/'r6/scripts/virtual-atelier-full/SetupNewTab.reds')
 for p in S.rglob('*'):
  if p.is_file() and not p.is_symlink():paths.add(p)
 for p in [Path(r'C:\Users\Ayong\.codex\config.toml'),Path(r'C:\Users\Ayong\.codex\AGENTS.md')]:
  if p.exists():paths.add(p)
 return {str(p):sha(p) for p in sorted(paths)}
mode=sys.argv[1];assert mode in ('baseline','verify')
if mode=='baseline':
 assert not (H/'generated_baseline/baseline.json').exists(),'Do not replace original evidence'
 repo,links=scan(W,True);game,game_links=scan(G)
 pins=protected(repo)
 write('generated_baseline/baseline.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo':repo,'repo_links':links,'game':game,'game_links':game_links,'sha256':pins})
 # Byte-preserving instruction snapshots are historical data, not active AGENTS.md files.
 hist=W/'docs/history/instructions/2026-10-29';hist.mkdir(parents=True,exist_ok=True)
 for n in ['AGENTS.md','PROJECT.md','ROADMAP.md','README.md']:
  target=hist/(n.removesuffix('.md')+'.original.md');assert not target.exists();target.write_bytes((W/n).read_bytes())
 write('originals.json',{n:{'bytes':(W/n).stat().st_size,'sha256':sha(W/n),'snapshot':str((hist/(n.removesuffix('.md')+'.original.md')).relative_to(W))} for n in ['AGENTS.md','PROJECT.md','ROADMAP.md','README.md']})
 print(json.dumps({'status':'BASELINE_CAPTURED','repo_files':len(repo),'repo_GB':sum(v[0] for v in repo.values())/1e9,'game_files':len(game),'hashed_files':len(pins),'repo_reparse_points_not_followed':len(links)}))
else:
 b=read(H/'generated_baseline/baseline.json');repo,links=scan(W,True);game,game_links=scan(G)
 changed=sorted(p for p in b['repo'] if p not in repo or repo[p]!=b['repo'][p]);added=sorted(set(repo)-set(b['repo']))
 def allowed(p):return p in ['AGENTS.md','PROJECT.md','ROADMAP.md','README.md'] or (p.endswith('/AGENTS.md') and p.split('/')[0] in ['docs','tools','prealpha','research','release','redscript','profiles','archive']) or p.startswith(('docs/knowledge/','docs/history/instructions/2026-10-29/'))
 assert all(allowed(p) for p in changed+added),[p for p in changed+added if not allowed(p)]
 assert all(p in repo for p in b['repo']),'No deletion authorized'
 assert sorted(links,key=lambda x:x['path'])==sorted(b['repo_links'],key=lambda x:x['path']),'Repository reparse metadata changed'
 assert game==b['game'] and sorted(game_links,key=lambda x:x['path'])==sorted(b['game_links'],key=lambda x:x['path']),'Game tree metadata changed; investigate external activity'
 mismatches=[p for p,h in b['sha256'].items() if not Path(p).is_file() or sha(p)!=h];assert not mismatches,mismatches
 originals=read(H/'originals.json')
 assert all(sha(W/r['snapshot'])==r['sha256'] for r in originals.values())
 result={'status':'PASS_INSTRUCTION_AND_DOCUMENTATION_ONLY','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_sizes':{n:r['bytes'] for n,r in originals.items()},'new_sizes':{n:(W/n).stat().st_size for n in originals},'changed_existing':changed,'added':added,'repo_files_metadata_checked':len(b['repo']),'game_files_metadata_checked':len(game),'sha256_protected_files_checked':len(b['sha256']),'removed_files':0,'reparse_points_followed':False,'runtime_build_deploy_or_quest_auditor_executed':False,'scope_limit':'All repository/game file path-size-mtime metadata compared; SHA256 covers project source, top-level candidate utilities, all current package/source files, dist, release, 51 installed Tower files, Atelier, 49 Lizzie files, all saves and global Codex configuration. Historical extracted/vendor/fixture resource payloads and native game archives receive metadata comparison, not whole-content rehash.'}
 write('verification.json',result);print(json.dumps(result,indent=2))
