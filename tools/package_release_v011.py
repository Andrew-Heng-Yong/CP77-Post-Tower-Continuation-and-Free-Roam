"""Assemble the reviewed v0.1.1 mod ZIP without changing the installed game."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
TAG='v0.1.1-prealpha.20261024'
def sha(data):return hashlib.sha256(data).hexdigest().upper()
def allowed_path(value):
 if not isinstance(value,str) or '\\' in value or ':' in value:return False
 p=PurePosixPath(value)
 if p.is_absolute() or p.as_posix()!=value or any(x in ('','.','..') for x in value.split('/')):return False
 if re.fullmatch(r'archive/pc/mod/(?:0+_)?TowerContinued_[A-Za-z0-9_]+\.archive(?:\.xl)?',value):return True
 if re.fullmatch(r'r6/scripts/(?:PTFR_PreAlpha|TowerContinued_[A-Za-z0-9_]+)/[A-Za-z0-9_./-]+\.reds',value):return True
 return value in {'r6/tweaks/TowerContinued_PreAlpha.yaml',
                  'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha/init.lua',
                  'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua'}
def package(installed_root,manifest_path,output):
 installed_root=Path(installed_root).resolve(strict=True);manifest_path=Path(manifest_path).resolve(strict=True);output=Path(output).resolve()
 if not output.is_relative_to(ROOT/'dist') or output.is_relative_to(installed_root):raise ValueError('Invalid output root')
 checksum=output.with_suffix(output.suffix+'.sha256')
 if output.exists() or checksum.exists():raise FileExistsError('Release output already exists')
 manifest=json.loads(manifest_path.read_text(encoding='utf-8-sig'));rows=manifest['files']
 if manifest['release']!=TAG or len(rows)!=manifest['file_count'] or len(rows)!=117:raise ValueError('Invalid manifest version/count')
 payload={};seen=set()
 for row in rows:
  name=row['path']
  if not allowed_path(name) or name.casefold() in seen:raise ValueError('Unexpected or duplicate package path: '+name)
  seen.add(name.casefold());source=(installed_root/name).resolve(strict=True)
  if not source.is_relative_to(installed_root) or not source.is_file():raise ValueError('Input escapes game root: '+name)
  data=source.read_bytes()
  if len(data)!=row['bytes'] or sha(data)!=row['sha256']:raise ValueError('Installed file changed: '+name)
  payload[name]=data
 payload['TowerContinuation/FILES.json']=manifest_path.read_bytes()
 payload['TowerContinuation/INSTALL.md']=(ROOT/f'release/INSTALL-{TAG}.md').read_bytes()
 payload['TowerContinuation/BETA_RELEASE_CONTRACT.md']=(ROOT/'docs/beta_release_contract.md').read_bytes()
 output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for name,data in sorted(payload.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,10,24,0,0,0));info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
   archive.writestr(info,data,compresslevel=9)
 with zipfile.ZipFile(output) as archive:
  if archive.testzip() is not None or set(archive.namelist())!=set(payload):raise ValueError('ZIP integrity or set mismatch')
  for name,data in payload.items():
   if archive.read(name)!=data:raise ValueError('ZIP readback mismatch: '+name)
 digest=sha(output.read_bytes())
 with checksum.open('x',encoding='ascii',newline='\n') as f:f.write(f'{digest}  {output.name}\n')
 return {'zip':str(output),'sha256':digest,'mod_files':len(rows),'zip_entries':len(payload),'bytes':output.stat().st_size,'zip_readback':'PASS','game_writes':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--installed-root',type=Path,required=True);p.add_argument('--manifest',type=Path,default=ROOT/f'release/manifest-{TAG}.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(package(a.installed_root,a.manifest,a.output),indent=2))
if __name__=='__main__':main()
