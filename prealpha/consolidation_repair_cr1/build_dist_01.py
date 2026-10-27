"""Full same51-path successor ZIP; no publication."""
import zipfile
from common import *
files={r['path']:r['sha256'] for r in read(CANDIDATE/'manifest.json')['files']}
assert len(files)==51
dest=CANDIDATE/'dist';assert not dest.exists();dest.mkdir()
out=dest/'Post-Tower-Continuation-and-Free-Roam-CR1-unreleased.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for rel in sorted(files):
        assert sha(CANDIDATE/'package'/rel)==files[rel]
        z.write(CANDIDATE/'package'/rel,rel)
with zipfile.ZipFile(out) as z:
    assert len(z.namelist())==len(set(z.namelist()))==51 and set(z.namelist())==set(files)
    for rel,h in files.items():assert hashlib.sha256(z.read(rel)).hexdigest().upper()==h,rel
write_new(dest/'manifest.json',{'status':'FULL_51_PATH_UNRELEASED_ZIP_VERIFIED','path':str(out),'sha256':sha(out),'bytes':out.stat().st_size,'files':51,'published':False})
print(json.dumps(read(dest/'manifest.json')))
