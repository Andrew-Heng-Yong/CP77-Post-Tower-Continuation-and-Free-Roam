"""Pure QR7 Ronald source helpers; no runtime/build/deployment side effects."""
from pathlib import Path
import json,hashlib,sys,collections
W=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def val(x):return x.get('$value',x)if isinstance(x,dict)else x
def path(g,a,b):
 todo=collections.deque([(str(a),[])]);seen=set()
 while todo:
  n,p=todo.popleft()
  if n in seen:continue
  seen.add(n)
  if n==str(b):return p
  for e in g['edges']:
   if e[0]==n and e[1]!='CutSource'and e[3]!='CutDestination':todo.append((e[2],p+[e]))
 return None
RN=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'
NS=r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene'
BO=r'towercontinued\b0_story_eight\ronald.questphase';BS=BO.replace('.questphase','.scene')
