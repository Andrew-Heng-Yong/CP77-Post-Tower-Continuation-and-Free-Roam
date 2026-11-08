"""Download/hash only the official pinned offline fixture wheel into private QR9 evidence."""
from pathlib import Path
import urllib.request,json,hashlib
H=Path(__file__).resolve().parent;out=H/'tooling_provenance_01'
if out.exists():raise RuntimeError('Fresh output required')
out.mkdir()
url='https://pypi.org/pypi/lupa/2.8/json'
with urllib.request.urlopen(url,timeout=20)as r:b=r.read(5*1024*1024)
metadata=json.loads(b);assert metadata['info']['name']=='lupa'and metadata['info']['version']=='2.8'
record=next(r for r in metadata['urls']if r['filename']=='lupa-2.8-cp314-cp314-win_amd64.whl')
assert record['url'].startswith('https://files.pythonhosted.org/packages/')
with urllib.request.urlopen(record['url'],timeout=20)as r:wheel=r.read(10*1024*1024)
h=hashlib.sha256(wheel).hexdigest();assert h==record['digests']['sha256']
(out/record['filename']).write_bytes(wheel);(out/'pypi.json').write_bytes(b)
(out/'manifest.json').write_text(json.dumps({'status':'OFFICIAL_PINNED_PRIVATE_OFFLINE_TOOLING','metadata_url':url,'metadata_sha256':hashlib.sha256(b).hexdigest().upper(),'wheel_url':record['url'],'filename':record['filename'],'wheel_sha256':h.upper(),'bytes':len(wheel),'version':'2.8','installed_scope':'worker_b/tooling only; no global/game dependency change','game_or_CET_calls':0},indent=2)+'\n',encoding='utf-8')
print(record['filename'],h.upper())
