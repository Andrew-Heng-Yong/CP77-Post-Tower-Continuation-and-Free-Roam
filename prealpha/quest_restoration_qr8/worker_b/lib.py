"""QR8 B pure read/pin helpers; no candidate/build/deployment side effects."""
from pathlib import Path
import json,hashlib,sys,os,collections
W=Path(__file__).resolve().parents[3];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
OBS={}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 p=Path(p);key=os.path.normcase(str(p.resolve()));s=p.stat();tag=(s.st_size,s.st_mtime_ns)
 if key in OBS and OBS[key]['metadata']==tag:return OBS[key]['sha256']
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 t=p.stat()
 if(t.st_size,t.st_mtime_ns)!=tag:raise RuntimeError('Input changed during current SHA: '+str(p))
 value=h.hexdigest().upper();OBS[key]={'path':str(p.resolve()),'metadata':tag,'sha256':value};return value
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def val(x):return x.get('$value',x)if isinstance(x,dict)else x
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def reachable(g,seeds,cut=True):
 seen=set();todo=list(map(str,seeds))
 while todo:
  n=todo.pop()
  if n in seen:continue
  seen.add(n)
  todo += [e[2]for e in g['edges']if e[0]==n and(cut or(e[1]!='CutSource'and e[3]!='CutDestination'))]
 return seen
RN=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'
NS=r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene'
BO=r'towercontinued\b0_story_eight\ronald.questphase';BS=BO.replace('.questphase','.scene')
NEWS=r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase'
