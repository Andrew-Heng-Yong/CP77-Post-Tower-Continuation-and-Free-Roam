"""Build a full 51-path unreleased successor ZIP from the verified package."""
import hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;P=H/'candidate_02';source=P/'package';manifest=json.loads((P/'manifest.json').read_text(encoding='utf-8'))
dist=P/'dist';assert not dist.exists();dist.mkdir()
name='Post-Tower-Continuation-and-Free-Roam-S30-unreleased.zip';out=dist/name
files={r['path']:r['sha256'] for r in manifest['files']};assert len(files)==51
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for rel in sorted(files):z.write(source/rel,rel)
with zipfile.ZipFile(out) as z:
 assert set(z.namelist())==set(files)
 for rel,digest in files.items():assert hashlib.sha256(z.read(rel)).hexdigest().upper()==digest,rel
report={'status':'UNRELEASED_FULL_SUCCESSOR_ZIP_VERIFIED','name':name,'files':len(files),'sha256':hashlib.sha256(out.read_bytes()).hexdigest().upper(),'bytes':out.stat().st_size,'published':False}
(dist/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
