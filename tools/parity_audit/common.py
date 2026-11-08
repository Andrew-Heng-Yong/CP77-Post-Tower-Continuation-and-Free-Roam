"""Pure Python audit primitives. No game APIs, runtime mutation, or build imports."""
import hashlib,json,csv,re,os
from pathlib import Path
SCHEMA=1
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def csvwrite(p,rows):
 rows=list(rows)
 with Path(p).open('w',encoding='utf-8',newline='') as f:
  if not rows:return
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def value(x):return x.get('$value',x) if isinstance(x,dict) else x
def depots(x):return sorted({str(value(n['DepotPath'])).replace('/','\\') for n in walk(x) if 'DepotPath'in n and str(value(n['DepotPath'])).lower() not in ('0','none','')})
def rawdeps(data):return sorted({m.decode('utf-8') for m in re.findall(rb'(?:base|ep1|towercontinued)\\[A-Za-z0-9_\\.\-]+\.(?:questphase|scene|quest|ent|app|workspot|mesh|effect|anim|streamingsector|streamingblock|journal|xbm)',data)})
def fnv(s):
 n=14695981039346656037
 for c in s.encode():n=((n^c)*1099511628211)&((1<<64)-1)
 return str(n)
def path(w,p):
 p=Path(p);return p if p.is_absolute() else Path(w)/p
def snapshot(paths):return {str(p):{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,'sha256':sha(p)} for p in sorted(set(map(Path,paths))) if p.is_file() and not p.is_symlink()}
def tree_metadata(root):
 out={};stack=[Path(root)]
 while stack:
  with os.scandir(stack.pop()) as es:
   for e in es:
    st=e.stat(follow_symlinks=False)
    if getattr(st,'st_file_attributes',0)&0x400:continue
    if e.is_dir(follow_symlinks=False):stack.append(Path(e.path))
    else:out[str(Path(e.path).relative_to(root))]=[st.st_size,st.st_mtime_ns]
 return out
