"""Build the requested four-folder beta ZIP with cleanup reference files only."""
import hashlib,json,re,shutil,zipfile
from pathlib import Path
W=Path(__file__).resolve().parents[1];C=W/'prealpha/viktor_door_vd1/candidate_02'
TAG='v0.2.0-beta';D=W/'dist'/TAG;P=D/'package'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(value,indent=2)+'\n').encode())
def obsolete_manifest():
 current={x['path'] for x in read(C/'install_manifest_01.json')['package_files']};rows={}
 for p in [W/'release/manifest.json',W/'release/manifest-v0.1.1-alpha.20261024.json',W/'prealpha/full_consolidation_v1/candidate_01/install_manifest_01.json']:
  data=read(p)
  for row in data.get('old_files',data.get('files',[])):
   if row['path'] not in current:rows.setdefault(row['path'],set()).add(row['sha256'])
 return {'purpose':'AI/manual cleanup without an old ZIP or backups','files':[{'path':p,'accepted_sha256':sorted(v)} for p,v in sorted(rows.items())]}
def package():
 m=read(W/'release/manifest-v0.2.0-beta.json');rows=m['files'];assert len(rows)==51
 obsolete=obsolete_manifest();assert len(obsolete['files'])==124
 assert not {x['path'] for x in rows}&{x['path'] for x in obsolete['files']}
 # Validate the manual Atelier instructions against the exact reviewed patch.
 manual=(W/'release/MANUAL_CLEANUP_INSTRUCTIONS.md').read_text(encoding='utf-8')
 before,after=re.findall(r'```reds\n(.*?)\n```',manual,re.S)
 original=(W/'prealpha/computer_overlay_co1/candidate_02/original/SetupNewTab.reds').read_bytes()
 old=before.replace('\n','\r\n').encode();new=after.replace('\n','\r\n').encode()
 assert original.count(old)==1
 assert hashlib.sha256(original.replace(old,new)).hexdigest().upper()=='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
 payload={}
 for row in rows:
  src=C/'package'/row['path'];assert sha(src)==row['sha256']
  payload[row['path']]=src.read_bytes()
  dest=P/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 m['required_compatibility']['installed_by']='readme/MANUAL_CLEANUP_INSTRUCTIONS.md — required Atelier correction'
 m['cleanup']='readme/AI_CLEANUP_INSTRUCTIONS.md or readme/MANUAL_CLEANUP_INSTRUCTIONS.md; no old ZIP or backups'
 refs={name:(W/'release'/name).read_bytes() for name in ['AI_CLEANUP_INSTRUCTIONS.md','MANUAL_CLEANUP_INSTRUCTIONS.md']}
 files={'release':TAG,'file_count':51,'files':rows,'required_compatibility':m['required_compatibility']}
 refs['FILES.json']=(json.dumps(files,indent=2)+'\n').encode()
 refs['OBSOLETE_FILES.json']=(json.dumps(obsolete,indent=2)+'\n').encode()
 for name,data in refs.items():
  payload['readme/'+name]=data;dest=P/'readme'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 # Remove exactly the old reference files, then its empty directory; no recursion.
 olddir=P/'TowerContinuation'
 if olddir.exists():
  assert olddir.resolve().is_relative_to(P.resolve()) and not olddir.is_symlink()
  allowed={'AI_CLEANUP_INSTRUCTIONS.md','Apply-Atelier-Compatibility.ps1','BETA_RELEASE_CONTRACT.md','FILES.json','INSTALL.md','OBSOLETE_FILES.json','PERSISTENCE_BASELINE.json','RELEASE_NOTES.md'}
  for path in olddir.iterdir():
   assert path.is_file() and not path.is_symlink() and path.name in allowed
   path.unlink()
  olddir.rmdir()
 expected=set(payload);actual={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()}
 assert actual==expected and len(payload)==55
 assert {name.split('/')[0] for name in payload}=={'archive','bin','r6','readme'}
 zp=D/'Post-Tower-Continuation-and-Free-Roam-v0.2.0-beta.zip';checksum=Path(str(zp)+'.sha256')
 for p in (zp,checksum):
  assert p.resolve().is_relative_to(D.resolve())
  if p.exists():p.unlink()
 with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(payload.items()):
   info=zipfile.ZipInfo(name,(2026,10,29,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,data,compresslevel=9)
 with zipfile.ZipFile(zp) as z:
  assert z.testzip() is None and set(z.namelist())==expected
  for name,data in payload.items():assert z.read(name)==data
 digest=sha(zp);checksum.write_bytes((digest+'  '+zp.name+'\n').encode())
 write(W/'release/manifest-v0.2.0-beta.json',m)
 proof={'status':'PASS_OPEN_BETA_PACKAGE_READBACK','revision':'FOUR_FOLDERS_README_ONLY','release':TAG,'zip':str(zp.relative_to(W)),'zip_sha256':digest,'zip_bytes':zp.stat().st_size,'core_files':51,'zip_entries':55,'top_level':['archive','bin','r6','readme'],'readme_files':sorted(refs),'manual_Atelier_edit_exact_hash':'PASS','helper_scripts_in_zip':False,'game_writes':0,'save_writes':0,'published':False}
 write(W/'release/package-v0.2.0-beta.json',proof)
 print(json.dumps(proof))
if __name__=='__main__':package()
